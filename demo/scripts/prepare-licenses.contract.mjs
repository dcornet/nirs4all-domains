import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,rmSync,cpSync} from 'node:fs';
import {createHash} from 'node:crypto';
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

test('repository-owned AOM notice and catalog are portable while upstream notice bytes stay exact',()=>{
  const root=mkdtempSync(join(tmpdir(),'domains-notice-test-'));
  try{
    const demo=join(root,'demo'),scripts=join(demo,'scripts'),binding=join(root,'bindings/wasm');
    const methods=join(binding,'node_modules/@nirs4all/methods');
    const commit='25041f88bebb21a19748799c1681e138a3d55dfb';
    for(const p of [scripts,methods,join(root,'LICENSES'),join(demo,'src/report/assets'),join(demo,'node_modules/@pdf-lib/fontkit')])mkdirSync(p,{recursive:true});
    writeFileSync(join(scripts,'prepare-licenses.mjs'),readFileSync(new URL('./prepare-licenses.mjs',import.meta.url)));
    cpSync(new URL(`../public/licenses/methods/${commit}/`,import.meta.url),join(demo,'public/licenses/methods',commit),{recursive:true});
    for(const name of ['CeCILL-2.1.txt','AGPL-3.0-or-later.txt'])writeFileSync(join(root,'LICENSES',name),'Application license fixture\n');
    writeFileSync(join(demo,'src/report/assets/OFL.txt'),'Font notice fixture\n');
    writeFileSync(join(demo,'node_modules/@pdf-lib/fontkit/README.md'),'Published attribution fixture\r\n');
    writeFileSync(join(demo,'package-lock.json'),JSON.stringify({packages:{}}));
    const metadata={name:'@nirs4all/methods',version:'1.5.1',license:'CECILL-2.1 OR AGPL-3.0-or-later'};
    writeFileSync(join(binding,'package-lock.json'),JSON.stringify({packages:{'node_modules/@nirs4all/methods':metadata}}));
    writeFileSync(join(binding,'package.json'),JSON.stringify({name:'@nirs4all/domains',version:'0.2.0',license:metadata.license}));
    writeFileSync(join(methods,'package.json'),JSON.stringify(metadata));
    const upstream='Exact published notice fixture\r\n';
    writeFileSync(join(methods,'LICENSE-CeCILL-2.1'),upstream);
    const run=ending=>{
      writeFileSync(join(binding,'AOM_BANK_NOTICE.md'),['Domains notice','Second line',''].join(ending));
      writeFileSync(join(binding,'aom-bank.json'),JSON.stringify({aom_source:{fixture:true}},null,2).replace(/\n/g,ending)+ending);
      const result=spawnSync(process.execPath,[join(scripts,'prepare-licenses.mjs')],{encoding:'utf8'});
      assert.equal(result.status,0,result.stderr);
      return readFileSync(join(demo,'public/licenses/dependency-manifest.json'),'utf8');
    };
    assert.equal(run('\n'),run('\r\n'));
    const output=join(demo,'public/licenses');
    assert.equal(readFileSync(join(output,'aom-descriptors/NOTICE.md'),'utf8'),'Domains notice\nSecond line\n');
    assert.equal(readFileSync(join(output,'packages/@nirs4all/methods/1.5.1/LICENSE-CeCILL-2.1'),'utf8'),upstream);
    const manifest=JSON.parse(readFileSync(join(output,'dependency-manifest.json'),'utf8'));
    const copied=manifest.prepared_files.find(f=>f.path.endsWith('/LICENSE-CeCILL-2.1'));
    assert.equal(copied.sha256,createHash('sha256').update(upstream).digest('hex'));
  }finally{
    const target=resolve(root);assert.equal(dirname(target),resolve(tmpdir()));assert(basename(target).startsWith('domains-notice-test-'));
    rmSync(target,{recursive:true,force:true});
  }
});
