const {test}=require('node:test');
const assert=require('node:assert/strict');
const {validName,validPassword,hashPassword,verifyPassword}=require('../api/cmd');
test('validation',()=>{assert(validName('zuzu_01'));assert(!validName('a b'));assert(!validPassword('short'));assert(validPassword('long password 123'));});
test('salted password hashes',async()=>{const p='long password 123';const a=await hashPassword(p),b=await hashPassword(p);assert.notEqual(a,b);assert(await verifyPassword(p,a));assert.equal(await verifyPassword('wrong password',a),false);assert.equal(await verifyPassword(p,null),false);});
