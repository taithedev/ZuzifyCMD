const {Pool}=require('pg');
const pool=()=>globalThis.cmdPool ||= new Pool({connectionString:process.env.DATABASE_URL,max:3,connectionTimeoutMillis:5000});
const actions=new Set('bootstrap register login logout me heartbeat redeem friends friend_add friend_accept friend_remove discord_pair discord_unlink pro_status admin_stats admin_users admin_license admin_motd admin_audit admin_ban admin_unban admin_kick admin_rank'.split(' '));
module.exports=async(req,res)=>{
  res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');
  if(req.method!=='POST')return res.status(405).json({error:'POST required'});
  try{
    if(!process.env.DATABASE_URL)return res.status(503).json({error:'Cloud unavailable'});
    const b=typeof req.body==='string'?JSON.parse(req.body):req.body;
    if(!b||typeof b!=='object'||Array.isArray(b)||Buffer.byteLength(JSON.stringify(b))>4096||!actions.has(b.action))return res.status(400).json({error:'Invalid request'});
    const token=/^Bearer ([a-f0-9]{64})$/.exec(req.headers.authorization||'')?.[1]||null;
    const result=await pool().query('SELECT zuzifycmd.gateway($1,$2::jsonb,$3) AS result',[b.action,JSON.stringify(b),token]);
    return res.status(200).json(result.rows[0].result);
  }catch(e){console.error('CMD gateway error',e.code||e.name);return res.status(503).json({error:'Cloud unavailable'});}
};
