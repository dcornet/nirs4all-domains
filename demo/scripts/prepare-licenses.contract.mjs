import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {resolve,join,dirname,basename} from 'node:path';
import {spawnSync} from 'node:child_process';

test('a stale install cannot erase the existing distribution notices',()=>{
  const root=mkdtempSync(join(tmpdir(),'domains-notice-test-'));
  try{
    const demo=join(root,'demo'),scripts=join(demo,'scripts'),notice=join(demo,'public/licenses/packages/existing.txt');
    for(const p of [scripts,dirname(notice),join(demo,'node_modules/example'),join(root,'bindings/wasm')])mkdirSync(p,{recursive:true});
    writeFileSync(join(scripts,'prepare-licenses.mjs'),readFileSync(new URL('./prepare-licenses.mjs',import.meta.url)));
    writeFileSync(notice,'Existing qualified notice\n');
    writeFileSync(join(demo,'package-lock.json'),JSON.stringify({packages:{'node_modules/example':{version:'2.0.0',license:'MIT'}}}));
    writeFileSync(join(root,'bindings/wasm/package-lock.json'),JSON.stringify({packages:{}}));
    writeFileSync(join(demo,'node_modules/example/package.json'),JSON.stringify({name:'example',version:'1.0.0',license:'MIT'}));
    const result=spawnSync(process.execPath,[join(scripts,'prepare-licenses.mjs')],{encoding:'utf8'});
    assert.notEqual(result.status,0);assert.match(result.stderr,/Lockfile version mismatch/);
    assert.equal(readFileSync(notice,'utf8'),'Existing qualified notice\n');
  }finally{
    const target=resolve(root);assert.equal(dirname(target),resolve(tmpdir()));assert(basename(target).startsWith('domains-notice-test-'));
    rmSync(target,{recursive:true,force:true});
  }
});
