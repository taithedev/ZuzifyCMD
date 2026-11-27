const {Pool} = require('pg');
const {randomBytes, createHash, scrypt, timingSafeEqual} = require('node:crypto');
const {promisify} = require('node:util');
const derive = promisify(scrypt);
let pool;
function db(){
  if(!process.env.DATABASE_URL) throw Error('Missing database configuration');
  return pool ||= new Pool({connectionString:process.env.DATABASE_URL,max:4,connectionTimeoutMillis:5000, idleTimeoutMillis:10000});
}
const sha = value => createHash('sha256').update(value).digest('hex');
const validName = s => typeof s==='string' && /^[a-z0-9_]{3,24}$/.test(s);
const validPassword = s => typeof s==='string' && s.length>=12 && Buffer.byteLength(s)<=128;
async function hashPassword(password,salt=randomBytes(16).toString('hex')){
  const key=await derive(password,salt,64,{N:32768,r:8,p:1,maxmem:64*1024*1024});
  return salt+':'+key.toString('hex');
}
async function verifyPassword(password,stored){
  const valid=typeof stored==='string' && /^[a-f0-9]{32}:[a-f0-9]{128}$/.test(stored);
  const [salt,key]=(valid?stored:'0'.repeat(32)+':'+'0'.repeat(128)).split(':');
  const actual=(await hashPassword(password,salt)).split(':')[1];
  return timingSafeEqual(Buffer.from(key,'hex'),Buffer.from(actual,'hex')) && valid;
}
function reply(res,status,data){
  res.statusCode=status;res.setHeader('Content-Type','application/json; charset=utf-8');
  res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');res.end(JSON.stringify(data));
}
async function body(req){
  if(req.body !== undefined){
    const value=typeof req.body==='string'?JSON.parse(req.body):req.body;
    if(!value || typeof value!=='object' || Array.isArray(value) || Buffer.byteLength(JSON.stringify(value))>4096)throw Error('Bad body');
    return value;
  }
  let data='';for await(const chunk of req){data+=chunk;if(Buffer.byteLength(data)>4096)throw Error('Bad body');}
  const value=JSON.parse(data);if(!value || typeof value!=='object' || Array.isArray(value))throw Error('Bad body');return value;
}
async function limit(bucket,cap){
  const window=Math.floor(Date.now()/900000);
  const r=await db().query('INSERT INTO zuzifycmd.auth_attempts(bucket,window_id) VALUES($1,$2) ON CONFLICT(bucket,window_id) DO UPDATE SET hits=zuzifycmd.auth_attempts.hits+1 RETURNING hits',[sha(bucket),window]);
  return r.rows[0].hits<=cap;
}
function token(req){const m=/^Bearer ([a-f0-9]{64})$/.exec(req.headers.authorization||'');return m?sha(m[1]):null;}
async function session(req){
  const t=token(req);if(!t)return null;
  const r=await db().query('SELECT a.username FROM zuzifycmd.sessions s JOIN zuzifycmd.accounts a ON a.id=s.account_id WHERE s.token_hash=$1 AND s.expires_at>now()',[t]);return r.rows[0]||null;
}
async function handler(req,res){
  if(req.method!=='POST')return reply(res,405,{error:'POST required'});
  let b;try{b=await body(req);}catch{return reply(res,400,{error:'Invalid request'});}
  try{
    if(b.action==='health'){await db().query('SELECT 1');return reply(res,200,{ok:true});}
    if(b.action==='catalog'){
      const r=await db().query('SELECT name,description,category,handler,enabled FROM zuzifycmd.commands ORDER BY category,name LIMIT 500');
      return reply(res,200,{commands:r.rows});
    }
    if(b.action==='register'||b.action==='login'){
      const username=typeof b.username==='string'?b.username.toLowerCase().trim():'';
      const password=b.password;
      if(!validName(username)||!validPassword(password))return reply(res,400,{error:'Username: 3–24 letters, digits or underscores. Password: at least 12 characters, max 128 bytes.'});
      const ip=String(req.headers['x-vercel-forwarded-for']||req.socket?.remoteAddress||'unknown').slice(0,128);
      if(!await limit('ip:'+ip,50)||!await limit('user:'+username,10))return reply(res,429,{error:'Too many attempts; retry later.'});
      let account;
      if(b.action==='register'){
        const hash=await hashPassword(password);
        const r=await db().query('INSERT INTO zuzifycmd.accounts(username,password_hash) VALUES($1,$2) ON CONFLICT(username) DO NOTHING RETURNING id,username',[username,hash]);
        account=r.rows[0];if(!account)return reply(res,409,{error:'Username unavailable'});
      }else{
        const r=await db().query('SELECT id,username,password_hash FROM zuzifycmd.accounts WHERE username=$1',[username]);account=r.rows[0];
        if(!await verifyPassword(password,account?.password_hash))return reply(res,401,{error:'Invalid username or password'});
      }
      const raw=randomBytes(32).toString('hex');
      await db().query("INSERT INTO zuzifycmd.sessions(token_hash,account_id,expires_at) VALUES($1,$2,now()+interval '12 hours')",[sha(raw),account.id]);
      return reply(res,200,{username:account.username,token:raw});
    }
    if(b.action==='me'){const a=await session(req);return a?reply(res,200,a):reply(res,401,{error:'Sign in required'});}
    if(b.action==='logout'){const t=token(req);if(t)await db().query('DELETE FROM zuzifycmd.sessions WHERE token_hash=$1',[t]);return reply(res,200,{ok:true});}
    return reply(res,400,{error:'Unknown action'});
  }catch(e){console.error('CMD API failure',e.code||e.name);return reply(res,503,{error:'Cloud service unavailable'});}
}
module.exports=handler;
module.exports.validName=validName;module.exports.validPassword=validPassword;
module.exports.hashPassword=hashPassword;module.exports.verifyPassword=verifyPassword;
