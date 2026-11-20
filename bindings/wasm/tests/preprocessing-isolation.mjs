// Same-input synthetic attribution through public Methods APIs. Diagnostic only.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import * as methods from '@nirs4all/methods';
import {createPreprocessingCallback} from '../preprocessing-provider.js';
import {createFactorCallback} from '../factor-provider.js';

const version='1.3.13+abi.2.20.0',sha=x=>createHash('sha256').update(x).digest('hex');
const [phase,folder,source]=process.argv.slice(2),out=resolve(folder);
assert(['prepare','extend'].includes(phase),'prepare or extend required');
await mkdir(out,{recursive:true});
await methods.loadModule();assert.equal(methods.version(),version);
assert.deepEqual(Array.from(methods.abiVersion()),[2,20,0]);
const prep=createPreprocessingCallback(version),factor=createFactorCallback(version);
const flatten=v=>Array.isArray(v)?v.flatMap(flatten):[v];
const bits=v=>Array.isArray(v)?v.map(bits):(()=>{assert(Number.isFinite(v));const b=Buffer.alloc(8);b.writeDoubleBE(v);return b.toString('hex');})();
const floatHash=v=>{const a=flatten(v),b=Buffer.alloc(a.length*8);a.forEach((x,i)=>b.writeDoubleLE(x,i*8));return sha(b);};
const matrix=rows=>({data:Float64Array.from(rows.flat()),rows:rows.length,cols:rows[0].length});
function call(operation,r){
 if(operation==='pca'){
  const p=methods.preflightPca(matrix(r.matrix),r.n_components);
  return {eigenvalues:Array.from(p.eigenvalues),scores:Array.from({length:p.scores.rows},(_,i)=>Array.from(p.scores.data.slice(i*p.scores.cols,(i+1)*p.scores.cols))),full_moments:Array.from(p.fullMoments),resolution:p.resolution,unresolved:Array.from(p.unresolved,Boolean),backend_version:version};
 }
 const response=JSON.parse((operation.startsWith('preprocess_')?prep:factor)(operation,JSON.stringify(r)));
 assert.equal(response.provider_error,undefined,JSON.stringify(response.provider_error));return response.ok;
}
const requests=[],results=[];
function add(id,operation,request){
 const f64_fields=Object.fromEntries(['matrix','scores','values'].filter(k=>request[k]!==undefined).map(k=>[k,bits(request[k])]));
 requests.push({id,operation,request,f64_fields});
 results.push({id,operation,input_f64_le_sha256:Object.fromEntries(Object.keys(f64_fields).map(k=>[k,floatHash(request[k])])),result:call(operation,request)});
 return results.at(-1).result;
}
async function save(name,value){await writeFile(resolve(out,name),JSON.stringify(value,null,2)+'\n',{flag:'wx'});}
let context;
if(phase==='prepare'){
 const bytes=await readFile(source);
 const artifact=JSON.parse(bytes);
 if(artifact.protocol_version==='domains.f43_same_input_fixture.v1'){
  assert.equal(sha(bytes),'5f6312f4655385c26b292812b6f5e36c0113df90300104667e1d1d0d1c388c5f');
  assert.equal(artifact.provider_version,version);assert.equal(artifact.synthetic_only,true);
  assert.equal(artifact.original_artifact_sha256,'295729f134798353128e516ec367e8a6028c795c3912fa388fb4f3970307557f');
 }else{
  assert.equal(sha(bytes),'295729f134798353128e516ec367e8a6028c795c3912fa388fb4f3970307557f');
  assert.equal(artifact.provider.version,version);assert.equal(artifact.new_real_scientific_fits,0);
  assert.equal(artifact.fixture_sha256,sha(await readFile(new URL('./preprocessing-fixtures.json',import.meta.url))));
 }
 context={source_sha256:sha(bytes),original_artifact_sha256:artifact.original_artifact_sha256??sha(bytes),provider_version:version,cases:[]};
 for(const id of ['low-frequency-reference','baseline-reference']){
  const original=artifact.cases.find(c=>c.id===id);assert(original);assert.equal(original.request.stage,'reference_only');
  assert.deepEqual(original.request.query_keys,[]);assert.deepEqual(original.request.access.y_fields,[]);
  const {matrix:X}=original.request.x;
  const snv=original.request.plan.representations.find(r=>r.id==='snv');assert(snv);
  const step=snv.steps[0];assert.equal(step.operator,'SNV');
  add(id+'/fit','preprocess_fit',{operator:step.operator,parameters:step.parameters,matrix:X});
  const transformed=add(id+'/transform','preprocess_transform',{matrix:X});
  add(id+'/destroy','preprocess_destroy',{});
  const meta=original.request.factors,continuous=meta.find(f=>f.kind==='continuous'),categorical=meta.find(f=>f.kind==='categorical');
  const levels=[...new Set(categorical.values)].sort(),codes=categorical.values.map(v=>levels.indexOf(v));
  const entry={id,original_request_sha256:sha(JSON.stringify(original.request)),ordered_keys:original.request.reference_keys,axis:original.request.x.axis,factors:{continuous,categorical,levels,codes},pca:[]};
  for(const [representation,derived] of [['raw',X],['snv',transformed.matrix]]){
   const pcaId=id+'/'+representation+'/pca';const pca=add(pcaId,'pca',{source_id:original.request.dataset.source_id+'::same-input::'+representation,sample_ids:original.request.reference_keys,matrix:derived,n_components:20});
   entry.pca.push({id:pcaId,representation,frozen_matrix_sha256:floatHash(derived),frozen_matrix:derived});
   for(let j=0;j<pca.eigenvalues.length;j++){
    const scores=pca.scores.map(row=>row[j]);
    add(pcaId+`/wasm-scores/pc${j+1}/pearson`,'correlation_descriptive',{scores,values:continuous.values,method:'pearson'});
    add(pcaId+`/wasm-scores/pc${j+1}/eta`,'factor_descriptive',{scores,codes});
   }
  }
  context.cases.push(entry);
 }
 await save('context.json',context);
}else{
 context=JSON.parse(await readFile(resolve(out,'context.json')));
 const bytes=await readFile(source),native=JSON.parse(bytes),first=await readFile(resolve(out,'prepare-requests.json'));
 assert.equal(native.input_sha256,sha(first));assert.equal(native.provider_version,version);
 context.native_prepare_sha256=sha(bytes);
 for(const entry of context.cases){
  const transformed=native.results.find(r=>r.id===entry.id+'/transform').result.matrix;
  add(entry.id+'/snv/native-transform/pca','pca',{source_id:entry.id+'::native-transform',sample_ids:entry.ordered_keys,matrix:transformed,n_components:20});
  for(const p of entry.pca){
   const pca=native.results.find(r=>r.id===p.id).result;
   for(let j=0;j<pca.eigenvalues.length;j++){
    const scores=pca.scores.map(row=>row[j]);
    add(p.id+`/native-scores/pc${j+1}/pearson`,'correlation_descriptive',{scores,values:entry.factors.continuous.values,method:'pearson'});
    add(p.id+`/native-scores/pc${j+1}/eta`,'factor_descriptive',{scores,codes:entry.factors.codes});
   }
  }
 }
}
const request={protocol_version:'domains.f43_same_input_requests.v1',synthetic_only:true,provider_version:version,source_sha256:context.source_sha256,requests};
const bytes=Buffer.from(JSON.stringify(request,null,2)+'\n');
assert(bytes.length<=4_000_000&&requests.length<=256);
await writeFile(resolve(out,phase+'-requests.json'),bytes,{flag:'wx'});
await save(phase+'-wasm.json',{protocol_version:'domains.f43_same_input_wasm.v1',status:'diagnostic_only',provider_version:version,abi:Array.from(methods.abiVersion()),input_sha256:sha(bytes),source_sha256:context.source_sha256,results,new_real_scientific_fits:0});
console.log(JSON.stringify({phase,requests:requests.length,bytes:bytes.length,provider:version,abi:Array.from(methods.abiVersion()),status:'DIAGNOSTIC_ONLY_NOT_A_PARITY_GATE'}));
