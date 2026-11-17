// Public synthetic engineering only. Requires the actual compiled Domains
// WASM and pinned published Methods; no mock is an execution substitute.
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createDomainsRuntime} from '../index.js';
import * as rust from '../native/nirs4all_domains.js';

const fixtureBytes=await readFile(new URL('./scoped-fixtures.json',import.meta.url));
const fixtures=JSON.parse(fixtureBytes);
const fixtureHash=createHash('sha256').update(fixtureBytes).digest('hex');
const sourceHash=createHash('sha256').update(fixtures.source_content_utf8).digest('hex');
assert.equal(sourceHash,fixtures.source_content_sha256);
assert.equal(fixtures.protocol_version,'domains.browser_scoped_parity_fixtures.v1');
const fixtureById=new Map(fixtures.fixtures.map(fixture=>[fixture.id,fixture]));
assert.equal(fixtureById.size,4);
const wasmBytes=await readFile(new URL('../native/nirs4all_domains_bg.wasm',import.meta.url));
const runtime=await createDomainsRuntime({wasmModule:wasmBytes});
const reports={};
const clone=id=>structuredClone(fixtureById.get(id).input);
const hashPattern=/^[0-9a-f]{64}$/;

function finiteJson(value) {
  if(typeof value==='number')assert.ok(Number.isFinite(value));
  else if(Array.isArray(value))value.forEach(finiteJson);
  else if(value&&typeof value==='object')Object.values(value).forEach(finiteJson);
}
function receipt(report,input,expected) {
  assert.equal(report.protocol_version,'domains.browser_scoped_result.v1');
  assert.equal(report.operation,input.operation);
  assert.equal(report.status,'computed');assert.equal(report.reason,null);
  const r=report.receipt;
  assert.deepEqual(r.dataset,input.dataset);
  assert.equal(r.dataset.content_sha256,sourceHash);
  assert.deepEqual(r.reference_keys,input.reference_keys);
  assert.deepEqual(r.query_keys,input.query_keys);
  assert.deepEqual(r.fit_keys,input.fit==='none'?[]:input.x.row_keys);
  assert.deepEqual(r.requested_fit_keys,input.fit==='none'?[]:input.x.row_keys);
  assert.equal(r.fit_attempted,input.fit!=='none');
  assert.equal(r.fit_executed,input.fit!=='none');
  assert.equal(r.reference_keys.length,expected.reference_rows);
  assert.equal(r.query_keys.length,expected.query_rows);
  assert.equal(r.fit_keys.length,expected.fit_rows);
  assert.equal(r.fit,input.fit);assert.equal(r.representation,'raw');
  assert.deepEqual(r.parameters,input.parameters);
  assert.equal(r.explicit_transductive,input.explicit_transductive);
  assert.equal(r.test_x_accessed,expected.test_x_accessed);
  assert.equal(r.y_accessed,false);assert.deepEqual(r.fields_read.y,[]);
  assert.deepEqual(r.fields_read.m,[]);
  assert.deepEqual(r.fields_read.x.row_keys,input.x.row_keys);
  assert.deepEqual(r.fields_read.x.matrix.shape,[input.x.row_keys.length,2]);
  assert.equal(r.fields_read.x.axis_unit,'nm');
  for(const key of ['request_sha256','manifest_sha256','receipt_sha256'])assert.match(r[key],hashPattern);
  assert.match(r.fields_read.x.matrix.sha256,hashPattern);
  assert.match(r.fields_read.x.axis_sha256,hashPattern);
  assert.ok(!r.reference_keys.includes('predict-0'));
  assert.ok(!r.query_keys.includes('predict-0'));
  assert.ok(!r.fit_keys.includes('predict-0'));
  assert.equal(r.physical_independence,'unverified');
  for(const call of r.provider_calls) {
    assert.match(call.request_sha256,hashPattern);
    assert.ok(['computed','unsupported','error'].includes(call.status));
    assert.equal(call.status==='computed',call.reason===null);
    for(const key of ['matrix','query','reference','values'])if(call.matrices[key]) {
      assert.match(call.matrices[key].sha256,hashPattern);
      assert.equal(Object.hasOwn(call.matrices[key],'data'),false);
      assert.equal(Object.hasOwn(call.matrices[key],'values'),false);
    }
  }
  // Receipts never carry the prediction sentinel or raw spectral arrays.
  JSON.parse(JSON.stringify(r),(_key,value)=>{
    if(typeof value==='number')assert.notEqual(Math.abs(value),999999);
    return value;
  });
  assert.equal(Object.hasOwn(r,'x'),false);
  finiteJson(report);
}

test('actual scoped WASM rejects forbidden values and role/grant/consent mistakes before callback',()=>{
  const adversaries=[];
  for(const field of ['y','Y_test','targets']) {
    const request=clone('train');request[field]=[987654321];adversaries.push(request);
  }
  const yGrant=clone('train');yGrant.access.y_fields=['target'];adversaries.push(yGrant);
  const hiddenTest=clone('train');
  hiddenTest.reference_keys[0]='test-0';hiddenTest.x.row_keys[0]='test-0';
  hiddenTest.x.matrix[0]=[20.7,14.6];adversaries.push(hiddenTest);
  const xGrant=clone('train');xGrant.access.x=false;adversaries.push(xGrant);
  const mGrant=clone('train');mGrant.access.m_fields=['not-projected'];adversaries.push(mGrant);
  const consent=clone('global');consent.explicit_transductive=false;adversaries.push(consent);
  const rowOrder=clone('support');rowOrder.x.row_keys.reverse();adversaries.push(rowOrder);
  const missing=clone('support');missing.x.matrix[8][0]=null;adversaries.push(missing);
  const extraParameter=clone('train');extraParameter.parameters.n_components=1;adversaries.push(extraParameter);
  const unsupportedProjection=clone('support');unsupportedProjection.representation='train_fitted_pca';adversaries.push(unsupportedProjection);
  for(const request of adversaries) {
    let calls=0;
    assert.throws(()=>rust.analyze_scoped_json(JSON.stringify(request),()=>{
      calls++;throw new Error('FORBIDDEN_PROVIDER_CALL');
    }));
    assert.equal(calls,0,`${request.operation}: invalid input reached provider`);
  }
});

test('actual Preflight exact audit reports zero for distinct and near nonidentical spectra without a numerical callback',()=>{
  for(const query of [[100,200],[Number.EPSILON,0]]){
    const input=clone('exact');input.x.matrix[8]=query;
    input.dataset.content_version='synthetic-zero-pair-variant-v1';
    input.dataset.content_sha256=createHash('sha256').update(JSON.stringify(input.x)).digest('hex');
    let calls=0;
    const report=JSON.parse(rust.analyze_scoped_json(JSON.stringify(input),()=>{calls++;throw new Error('EXACT_AUDIT_MUST_NOT_FIT');}));
    assert.equal(report.status,'computed');assert.equal(calls,0);
    const metric=report.value.metrics.find(m=>m.metric_id==='integrity.cross_partition_exact_duplicate_pairs');
    assert.equal(metric.status,'computed');assert.equal(metric.value,0);
    assert.deepEqual(report.receipt.fit_keys,[]);assert.equal(report.receipt.y_accessed,false);
  }
});

test('actual scoped WASM reports declared technical repetitions across partitions without X or provider access',()=>{
  const input=clone('exact');input.diagnostic='declared_identities';input.access.x=false;input.x=null;
  const row_keys=[...input.reference_keys,...input.query_keys];
  input.access.m_fields=['technical_repeat'];
  input.metadata=[{name:'technical_repeat',role:'repetition',kind:'categorical',origin:'synthetic declaration',
    derived_from_target:false,evidence:'declared',row_keys,values:row_keys.map((_,i)=>i===8?'repeat-0':`repeat-${i}`)}];
  input.dataset.content_version='synthetic-technical-repetition-v1';
  input.dataset.content_sha256=createHash('sha256').update(JSON.stringify(input.metadata)).digest('hex');
  let calls=0;
  const report=JSON.parse(rust.analyze_scoped_json(JSON.stringify(input),()=>{calls++;throw new Error('DOCUMENTARY_AUDIT_MUST_NOT_FIT');}));
  assert.equal(report.status,'computed');assert.equal(calls,0);
  assert.equal(report.value.columns[0].role,'repetition');
  assert.equal(report.value.columns[0].literal_shared_nonmissing_value_count,1);
  assert.equal(report.receipt.fields_read.x,null);assert.deepEqual(report.receipt.fields_read.y,[]);
  assert.deepEqual(report.receipt.provider_calls,[]);assert.equal(report.receipt.physical_independence,'unverified');
});

test('compiled Rust callback spy and receipt agree on the exact projected train rows',()=>{
  const input=clone('train'),calls=[];
  const report=JSON.parse(rust.analyze_scoped_json(JSON.stringify(input),(operation,payload)=>{
    const request=JSON.parse(payload);calls.push({operation,request});
    return JSON.stringify(operation==='capabilities'?{ok:[]}:
      {provider_error:{kind:'unsupported',reason:'ENGINEERING_RECEIPT_SPY_ONLY'}});
  }));
  const pca=calls.find(call=>call.operation==='pca');
  assert.deepEqual(pca.request.matrix,input.x.matrix);
  assert.deepEqual(pca.request.sample_ids,input.reference_keys);
  assert.equal(pca.request.source_id,input.dataset.source_id);
  assert.equal(pca.request.n_components,2);
  assert.deepEqual(calls.find(call=>call.operation==='nearest_neighbors').request.reference,input.x.matrix);
  const recorded=report.receipt.provider_calls.find(call=>call.operation==='pca');
  assert.deepEqual(recorded.matrices.matrix.shape,[8,2]);
  assert.deepEqual(recorded.matrices.sample_ids,pca.request.sample_ids);
  assert.equal(recorded.matrices.matrix.sha256,report.receipt.fields_read.x.matrix.sha256);
  assert.equal(recorded.status,'unsupported');assert.equal(recorded.reason,'ENGINEERING_RECEIPT_SPY_ONLY');
  assert.equal(report.value.structure.metrics.pca.value,null);
});

test('actual published Methods execute complete train/global/support and public Preflight exact operations',async()=>{
  assert.equal(runtime.provider.version,'1.3.13+abi.2.20.0');
  assert.equal(runtime.provider.abi[0],2);assert.ok(runtime.provider.abi[1]>=20);
  for(const fixture of fixtures.fixtures) {
    const before=JSON.stringify(fixture.input);
    const report=runtime.analyzeScoped(fixture.input);
    receipt(report,fixture.input,fixture.expected);
    assert.equal(JSON.stringify(fixture.input),before);
    reports[fixture.id]=report;
  }
  for(const id of ['train','global']) {
    const r=reports[id],n=id==='train'?8:10;
    const structure=r.value.structure;
    assert.equal(structure.scope.n_observations,n);
    assert.equal(structure.scope.n_bands,2);
    assert.equal(structure.raw_spectra_included,false);
    assert.equal(structure.test_target_accessed,false);
    assert.equal(structure.metrics.pca.status,'computed');
    assert.equal(structure.metrics.pca.value.scores.length,n);
    assert.equal(structure.metrics.raw_neighbors.status,'computed');
    assert.equal(structure.metrics.raw_neighbors.value.n_reference,n);
    assert.equal(structure.metrics.raw_neighbors.value.n_query,n);
    const calls=r.receipt.provider_calls;
    const pca=calls.find(call=>call.operation==='pca');
    assert.deepEqual(pca.matrices.matrix.shape,[n,2]);
    assert.deepEqual(pca.matrices.sample_ids,r.receipt.fit_keys);
    assert.equal(pca.matrices.matrix.sha256,r.receipt.fields_read.x.matrix.sha256);
    assert.equal(pca.status,'computed');
    const raw=calls.find(call=>call.operation==='nearest_neighbors');
    assert.deepEqual(raw.matrices.reference.shape,[n,2]);
    assert.deepEqual(raw.matrices.query.shape,[n,2]);
    assert.equal(raw.matrices.reference.sha256,pca.matrices.matrix.sha256);
    assert.equal(raw.matrices.query.sha256,pca.matrices.matrix.sha256);
    // Eight or ten rows meet the frozen density population minimum. A valid
    // all-noise result is evidence; no favorable cluster count is demanded.
    assert.equal(structure.metrics.density.status,'computed');
    assert.equal(structure.metrics.density.value.labels.length,n);
    assert.equal(structure.metrics.density.value.membership.length,n);
    assert.equal(structure.metrics.density.value.min_cluster_size,8);
    assert.equal(structure.metrics.density.value.min_samples,4);
    assert.equal(structure.metrics.density.value.selection,'eom');
    assert.equal(structure.metrics.density.value.allow_single_cluster,false);
    const density=calls.find(call=>call.operation==='hdbscan');
    assert.equal(density.matrices.matrix.shape[0],n);
    assert.equal(density.matrices.matrix.shape[1],structure.metrics.pca.value.n_components_resolved);
    assert.equal(density.status,'computed');
  }
  const support=reports.support;
  assert.deepEqual(support.receipt.provider_calls.map(call=>call.operation),['nearest_neighbors']);
  const nn=support.receipt.provider_calls[0];
  assert.deepEqual(nn.matrices.query.shape,[2,2]);
  assert.deepEqual(nn.matrices.reference.shape,[8,2]);
  assert.notEqual(nn.matrices.query.sha256,nn.matrices.reference.sha256);
  assert.equal(support.value.raw_neighbors.status,'computed');
  assert.equal(support.value.raw_neighbors.value.n_reference,8);
  assert.equal(support.value.raw_neighbors.value.n_query,2);
  assert.equal(support.value.raw_neighbors.value.k,8);
  assert.equal(support.value.raw_neighbors.value.approximate,false);
  assert.equal(support.value.raw_neighbors.value.indices[0][0],0);
  assert.equal(support.value.raw_neighbors.value.distances[0][0],0);
  assert.equal(support.value.pca_support.status,'unavailable');
  const exact=reports.exact;
  assert.equal(exact.value.validation.valid,true);
  const cross=exact.value.metrics.find(metric=>metric.metric_id==='integrity.cross_partition_exact_duplicate_pairs');
  assert.equal(cross.status,'computed');assert.equal(cross.value,1);
  assert.equal(cross.parameters.test_access,'X_only_integrity_no_fit_no_Y');
  assert.equal(exact.value.metrics.find(metric=>metric.metric_id==='integrity.axis_order').value,'descending');
  assert.ok(exact.value.metrics.every(metric=>metric.metric_id.startsWith('integrity.')));
  assert.equal(exact.receipt.provider_calls.length,1);
  assert.equal(exact.receipt.provider_calls[0].provider,'nirs4all-preflight@0.1.6::analyze');
  assert.equal(exact.receipt.provider_calls[0].numerical_provider,'UnavailableMethodsProvider');
  assert.equal(exact.receipt.provider_calls[0].numerical_fit_possible,false);
  let exactCallbackCalls=0;
  const directExact=JSON.parse(rust.analyze_scoped_json(JSON.stringify(clone('exact')),()=>{
    exactCallbackCalls++;throw new Error('INTEGRITY_MUST_NOT_USE_METHODS_CALLBACK');
  }));
  assert.equal(exactCallbackCalls,0);
  assert.deepEqual(directExact.value.metrics,exact.value.metrics);
  const output=process.env.N4DOMAINS_SCOPED_WASM_PARITY_OUT??
    fileURLToPath(new URL('../../../demo/test-results/scoped-wasm-parity.json',import.meta.url));
  await mkdir(dirname(output),{recursive:true});
  await writeFile(output,JSON.stringify({schema_version:1,protocol_version:'domains.browser_scoped_parity.v1',
    backend:'wasm',fixture_file_sha256:fixtureHash,source_content_sha256:sourceHash,
    domains_wasm_sha256:createHash('sha256').update(wasmBytes).digest('hex'),
    provider:runtime.provider,synthetic_operation_count:fixtures.fixtures.length,reports,new_real_scientific_fits:0})+'\n');
});

test('native/WASM scoped evidence uses the established parity tolerances and geometry conventions',{
  skip:!process.env.N4DOMAINS_SCOPED_NATIVE_PARITY_IN,
},async()=>{
  const native=JSON.parse(await readFile(process.env.N4DOMAINS_SCOPED_NATIVE_PARITY_IN,'utf8'));
  assert.equal(native.protocol_version,'domains.browser_scoped_parity.v1');
  assert.equal(native.backend,'native');assert.equal(native.fixture_file_sha256,fixtureHash);
  assert.equal(native.source_content_sha256,sourceHash);assert.equal(native.new_real_scientific_fits,0);
  assert.deepEqual(Object.keys(native.reports).sort(),[...fixtureById.keys()].sort());
  assert.equal(Object.keys(reports).length,4);
  for(const fixture of fixtures.fixtures) {
    const a=native.reports[fixture.id],b=reports[fixture.id];
    receipt(a,fixture.input,fixture.expected);
    for(const key of ['operation','diagnostic','status','reason'])assert.deepEqual(a[key],b[key]);
    // Input bindings/access/populations are exact. Provider capabilities,
    // numerical request hashes after PCA, and aggregate receipt hashes need
    // not match across native/WASM backends or eigenspace sign conventions.
    for(const key of ['dataset','request_sha256','manifest_sha256','reference_keys','query_keys','fit_keys',
      'requested_fit_keys','fit_attempted','fit_executed','fit','parameters','fields_read','test_x_accessed','y_accessed'])assert.deepEqual(a.receipt[key],b.receipt[key]);
    assert.deepEqual(a.receipt.provider_calls.map(call=>call.operation),b.receipt.provider_calls.map(call=>call.operation));
    a.receipt.provider_calls.forEach((call,i)=>{
      const other=b.receipt.provider_calls[i];
      assert.equal(call.status,other.status);assert.equal(call.reason,other.reason);
      for(const key of ['matrix','query','reference','values'])if(call.matrices[key]) {
        assert.deepEqual(call.matrices[key].shape,other.matrices[key].shape);
      }
    });
  }
  // Import the existing qualified engineering comparator instead of creating
  // another score/partition oracle or silently altering its tolerances.
  const scripts=fileURLToPath(new URL('../../../scripts',import.meta.url));
  const comparison=execFileSync(process.env.PYTHON??'python',['-c',`
import json,sys
sys.path.insert(0,sys.argv[1])
import check_browser_parity as parity
payload=json.load(sys.stdin)
for name in ('train','global'):
    left=payload['native'][name]['value']['structure']
    right=payload['wasm'][name]['value']['structure']
    parity.metrics(left['metrics'],right['metrics'],'scoped/'+name)
    parity.versions(left['metrics']); parity.versions(right['metrics'])
for name in ('support','exact'):
    parity.compare(payload['native'][name]['value'],payload['wasm'][name]['value'],'scoped/'+name)
    parity.versions(payload['native'][name]['value']); parity.versions(payload['wasm'][name]['value'])
print(json.dumps({'scoped_native_wasm_parity':'passed','fixtures':4,'absolute':parity.ABS_TOL,'relative':parity.REL_TOL,'pca_scores':'Gram geometry','partitions':'pairwise membership and noise','new_real_scientific_fits':0}))
`,scripts],{input:JSON.stringify({native:native.reports,wasm:reports}),encoding:'utf8',maxBuffer:5*1024*1024});
  const proof=JSON.parse(comparison);
  assert.equal(proof.scoped_native_wasm_parity,'passed');
  assert.equal(proof.absolute,fixtures.tolerance.absolute);
  assert.equal(proof.relative,fixtures.tolerance.relative);
  const output=fileURLToPath(new URL('../../../demo/test-results/scoped-parity-check.json',import.meta.url));
  const comparisonBytes=await readFile(new URL('../../../scripts/check_browser_parity.py',import.meta.url));
  await mkdir(dirname(output),{recursive:true});
  await writeFile(output,JSON.stringify({...proof,fixture_file_sha256:fixtureHash,source_content_sha256:sourceHash,
    comparison_source:'scripts/check_browser_parity.py',comparison_source_sha256:createHash('sha256').update(comparisonBytes).digest('hex'),
    domains_wasm_sha256:createHash('sha256').update(wasmBytes).digest('hex')})+'\n');
});
