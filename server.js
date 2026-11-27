const http = require('node:http');
const handler = require('./api/cmd');
const port = Number(process.env.PORT || 8787);
http.createServer((req,res)=>{
  if(req.url.split('?')[0] !== '/api/cmd'){res.writeHead(404);return res.end();}
  handler(req,res);
}).listen(port,process.env.HOST || '127.0.0.1',()=>console.log('ZuzifyCMD API listening on '+port));
