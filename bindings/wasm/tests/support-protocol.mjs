// Actual pinned Methods + compiled Domains WASM execution of public synthetic F4.2 fixtures.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {dirname} from 'node:path';
import {createDomainsRuntime} from '../index.js';
import * as rust from '../native/nirs4all_domains.js';
import Ajv2020 from '../../../demo/node_modules/ajv/dist/2020.js';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const close = (actual, expected, label, tolerance=1e-10) => {
  assert.equal(typeof actual, 'number', label);
  assert.ok(Number.isFinite(actual) && Math.abs(actual-expected) <= tolerance + tolerance*Math.abs(expected), `${label}: ${actual} != ${expected}`);
};
const finite = value => {
  if(typeof value==='number') assert.ok(Number.isFinite(value));
  else if(Array.isArray(value)) value.forEach(finite);
  else if(value&&typeof value==='object') Object.values(value).forEach(finite);
};
const hashPattern=/^[0-9a-f]{64}$/;
const fixtureBytes=await readFile(new URL('./support-fixtures.json',import.meta.url));
const fixtures=JSON.parse(fixtureBytes);
assert.equal(fixtures.length,34);
assert.equal(new Set(fixtures.map(x=>x.id)).size,fixtures.length);
const [scopedSchema,inputSchema,resultSchema]=await Promise.all([
  readFile(new URL('../scoped-input.schema.json',import.meta.url),'utf8').then(JSON.parse),
  readFile(new URL('../support-input.schema.json',import.meta.url),'utf8').then(JSON.parse),
  readFile(new URL('../support-result.schema.json',import.meta.url),'utf8').then(JSON.parse),
]);
const ajv=new Ajv2020({strict:true,strictTypes:false,allErrors:true});
ajv.addSchema(scopedSchema);
const validateInput=ajv.compile(inputSchema),validateResult=ajv.compile(resultSchema);
const [mode,...args]=process.argv.slice(2);

async function wasm(output) {
  const runtime=await createDomainsRuntime({wasmModule:await readFile(new URL('../native/nirs4all_domains_bg.wasm',import.meta.url))});
  assert.equal(runtime.provider.version,'1.3.13+abi.2.20.0');
  assert.deepEqual(runtime.provider.abi.slice(0,2),[2,20]);
  const cases=[],refusals=[];
  for(const fixture of fixtures) {
    const raw=typeof fixture.request==='string'?fixture.request:JSON.stringify(fixture.request);
    if(fixture.expected_access_refusal) {
      const schemaValid=typeof fixture.request==='object' && validateInput(fixture.request);
      let calls=0;
      assert.throws(()=>rust.analyze_support_json(raw,()=>{calls++;throw new Error('REFUSAL_REACHED_PROVIDER');},runtime.provider.version),
        error=>String(error).includes(fixture.expected_access_refusal),fixture.id);
      assert.equal(calls,0,`${fixture.id} accessed Methods before admission refusal`);
      refusals.push({id:fixture.id,reason:fixture.expected_access_refusal,provider_calls:calls,schema_valid:schemaValid,request:fixture.request});
      continue;
    }
    assert.ok(validateInput(fixture.request),`${fixture.id} input schema: ${JSON.stringify(validateInput.errors)}`);
    const result=runtime.analyzeSupport(fixture.request);
    finite(result);
    assert.ok(validateResult(result),`${fixture.id} result schema: ${JSON.stringify(validateResult.errors)}`);
    assert.equal(result.protocol_version,'domains.browser_train_fitted_support_result.v1',fixture.id);
    const expected=fixture.expect;
    assert.equal(result.status,expected.status,fixture.id);
    assert.equal(result.projection.status,expected.projection_status,fixture.id);
    assert.equal(result.monitoring.status,expected.monitoring_status,fixture.id);
    assert.equal(result.limit_qualification.status,expected.qualification_status,fixture.id);
    if(expected.projection_reason) assert.equal(result.projection.reason,expected.projection_reason,fixture.id);
    if(expected.monitoring_reason) assert.equal(result.monitoring.reason,expected.monitoring_reason,fixture.id);
    if(expected.independent_units_certified!==undefined) assert.equal(result.limit_qualification.independent_units_certified,expected.independent_units_certified,fixture.id);
    if(expected.qualification_reasons) assert.deepEqual(result.limit_qualification.reasons,expected.qualification_reasons,fixture.id);
    if(expected.monitor_invariants) for(const [key,value] of Object.entries(expected.monitor_invariants)) {
      const actual=result.monitoring.value[key];
      if(Array.isArray(value)) { assert.equal(actual.length,value.length,`${fixture.id}/${key}`); value.forEach((v,i)=>{
        if(typeof v==='number') close(actual[i],v,`${fixture.id}/${key}/${i}`);
        else assert.deepEqual(actual[i],v,`${fixture.id}/${key}/${i}`);
      }); }
      else if(typeof value==='number') close(actual,value,`${fixture.id}/${key}`);
      else assert.deepEqual(actual,value,`${fixture.id}/${key}`);
    }
    if(expected.dependence) for(const [field,values] of Object.entries(expected.dependence)) {
      const actual=result.dependence.fields.find(item=>item.field===field);
      assert.ok(actual,`${fixture.id}: missing dependence ${field}`);
      for(const [key,value] of Object.entries(values)) assert.equal(actual[key],value,`${fixture.id}/${field}/${key}`);
    }
    const receipt=result.receipt;
    assert.deepEqual(receipt.fit_keys,fixture.request.scope.reference_keys,`${fixture.id} fit keys`);
    assert.deepEqual(receipt.query_keys,fixture.request.scope.query_keys,`${fixture.id} query keys`);
    assert.equal(receipt.fit_population,'train');assert.equal(receipt.query_population,'test');
    assert.equal(receipt.x_test_accessed,true);assert.equal(receipt.y_train_accessed,false);assert.equal(receipt.y_test_accessed,false);
    assert.equal(receipt.x_predict_accessed,false);assert.equal(receipt.f41_pca_reused,false);
    assert.equal(receipt.monitoring_and_projection_same_fitted_object,false);
    for(const call of receipt.provider_calls) {
      assert.match(call.request_sha256,hashPattern);
      assert.ok(['pca_fit','pca_transform','pca_destroy','summary','pca_monitor'].includes(call.operation));
      assert.ok(Array.isArray(call.row_keys));
    }
    if(result.projection.status==='computed') {
      const p=result.projection.value;
      assert.equal(p.fitted_state_unchanged,true);
      assert.match(p.fit_state_sha256,hashPattern);assert.match(p.fit_identity_sha256,hashPattern);
      assert.equal(p.train_scores.length,receipt.fit_keys.length);
      assert.equal(p.test_scores.length,receipt.query_keys.length);
      assert.ok(p.components>=1 && p.components<=fixture.request.parameters.n_components);
      assert.deepEqual(p.reference_variance,{status:'unavailable',reason:'FLEXIBLE_PCA_PUBLIC_STATE_HAS_NO_EIGENVALUES',value:null});
      assert.deepEqual(p.numerical_rank,{status:'unavailable',reason:'FLEXIBLE_PCA_PUBLIC_STATE_HAS_NO_RANK_RESOLUTION',value:null});
      assert.ok(p.component_summaries.every(x=>x.summary.status==='computed' || x.summary.status==='unavailable'));
      assert.ok(p.display_components.length<=2 && p.display_components.every(i=>Number.isInteger(i)&&i>=0&&i<p.components));
      assert.ok(receipt.provider_calls.some(c=>c.operation==='pca_destroy'));
      if(fixture.id==='degenerate-all-constant') assert.deepEqual(p.display_components,[]);
    }
    if(fixture.id==='degenerate-all-constant') {
      const monitor=result.monitoring.value;
      assert.equal(monitor.effective_components,0);
      assert.equal(monitor.undefined_array_entries.eigenvalues[0].reason,'NOT_RETAINED_OR_NUMERICALLY_UNDEFINED_BY_METHODS');
      assert.equal(monitor.undefined_array_entries.monitored_t2.length,2);
      assert.ok(monitor.undefined_array_entries.monitored_t2.every(item=>item.reason==='NOT_RETAINED_OR_NUMERICALLY_UNDEFINED_BY_METHODS'));
      assert.ok(result.limit_qualification.reasons.includes('MONITORING_REFERENCE_HAS_NO_RESOLVED_COMPONENT'));
    }
    assert.equal(Object.hasOwn(result,'state_bytes'),false);
    cases.push({id:fixture.id,request:fixture.request,result});
  }
  await mkdir(dirname(output),{recursive:true});
  await writeFile(output,JSON.stringify({protocol_version:'domains.browser_train_fitted_support_wasm.v1',fixture_sha256:sha(fixtureBytes),
    provider:runtime.provider,tolerance:{absolute:1e-10,relative:1e-10},
    schema_validation:{input_schema:'support-input.schema.json',result_schema:'support-result.schema.json',
      valid_compute_inputs:cases.length,valid_compute_results:cases.length},
    cases,refusals,new_real_scientific_fits:0})+'\n');
  console.log(`Train-fitted support WASM: ${cases.length} computational cases; ${refusals.length} pre-provider refusals`);
}

if(mode==='wasm'&&args.length===1) await wasm(args[0]);
else throw new Error('Usage: support-protocol.mjs wasm OUT');
