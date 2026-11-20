import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import Ajv2020 from '../../../demo/node_modules/ajv/dist/2020.js';

const readJson=async url=>JSON.parse(await readFile(url,'utf8'));
const [scopedSchema,inputSchema,resultSchema,localRefusalSchema,fixtureFile]=await Promise.all([
  readJson(new URL('../scoped-input.schema.json',import.meta.url)),
  readJson(new URL('../support-input.schema.json',import.meta.url)),
  readJson(new URL('../support-result.schema.json',import.meta.url)),
  readJson(new URL('../support-local-refusal.schema.json',import.meta.url)),
  readJson(new URL('./support-fixtures.json',import.meta.url)),
]);
// The registered legacy scoped schema has an existing items-only refinement;
// disable only Ajv's strictTypes warning for that companion schema.
const ajv=new Ajv2020({strict:true,strictTypes:false,allErrors:true});
ajv.addSchema(scopedSchema);
ajv.addSchema(inputSchema);
const validateInput=ajv.compile(inputSchema),validateResult=ajv.compile(resultSchema),validateLocalRefusal=ajv.compile(localRefusalSchema);
const baseRequest=structuredClone(fixtureFile.find(item=>item.id==='baseline-two-feature').request);
const hash='a'.repeat(64),provider='1.5.1+abi.2.24.0';
const state=(value,reason=null,status='computed')=>({status,reason,value});

function resultFixture(request=baseRequest){
  const train=request.scope.reference_keys,test=request.scope.query_keys;
  const summary={count:train.length,min:-1,max:1,mean:0,sample_sd:0.5,q25:-0.5,median:0,q75:0.5,backend_version:provider};
  const monitor={eigenvalues:[2,1],effective_components:2,reference_t2:train.map(()=>1),reference_q:train.map(()=>0),
    monitored_t2:test.map(()=>1),monitored_q:test.map(()=>0),n_beyond_t2:0,n_beyond_q:0,n_beyond_either:0,
    n_near_t2:0,n_near_q:0,n_near_either:0,
    descriptive_fractions:Object.fromEntries(['t2','q','either'].map(key=>[key,{numerator:0,denominator:test.length,value:0,
      unit:'query acquisitions; descriptive threshold exceedance, not predictive failure or independent-unit probability'}])),
    t2_limit:2,q_limit:1,tolerance:1e-12,condition:2,
    q_tolerance_scale:1,eigenvalue_resolution:1e-12,reference_total_variance:3,monitored_total_variance:1,
    centroid_distance:0,centroid_subspace_distance:0,centroid_residual_distance:0,centroid_t2:0,retained_fraction:1,
    undefined_field_reasons:{monitored_total_variance:'METHODS_NUMERICALLY_UNDEFINED'},
    undefined_array_entries:{eigenvalues:[],reference_t2:[],reference_q:[],monitored_t2:[],monitored_q:[]},backend_version:provider,
    reference_protocol:'Methods statsPcaMonitor; out-of-fold row-index-modulo reference, separate full-reference PCA for query'};
  return {protocol_version:'domains.browser_train_fitted_support_result.v1',status:'computed',reason:null,
    projection:state({train_scores:train.map((_,i)=>[i/10,-i/20]),test_scores:test.map((_,i)=>[0.1+i/10,0.2]),components:2,
      display_components:[0,1],component_summaries:[{component:0,summary:state(summary)},{component:1,summary:state(summary)}],
      fit_state_sha256:hash,fit_identity_sha256:'b'.repeat(64),fitted_state_unchanged:true,
      reference_variance:state(null,'FLEXIBLE_PCA_PUBLIC_STATE_HAS_NO_EIGENVALUES','unavailable'),
      numerical_rank:state(null,'FLEXIBLE_PCA_PUBLIC_STATE_HAS_NO_RANK_RESOLUTION','unavailable'),
      basis:'Methods FlexiblePCA centered, unscaled'}),
    monitoring:state(monitor),
    limit_qualification:{status:'unknown',reasons:['NO_EXTERNAL_EVIDENCE_OF_INDEPENDENT_REFERENCE_UNITS'],source:null,
      fold_scheme:'row_index_modulo_n_folds',independent_units_certified:false,interpretation:'Empirical indexed-fold reference values; assumptions not certified.'},
    dependence:{fields:[],physical_independence_inferred_from_unique_ids:false,context_categories_alone_require_no_group_split:true},
    receipt:{dataset:request.scope.dataset,fit_keys:train,query_keys:test,fit_population:'train',query_population:'test',representation:'raw',
      axis_sha256:hash,parameters:request.parameters,train_spectra_sha256:hash,query_spectra_sha256:'c'.repeat(64),
      source_request_sha256:'d'.repeat(64),provider,provider_calls:[
        {operation:'pca_fit',row_keys:train,request_sha256:hash,provider_success:true},
        {operation:'pca_transform',row_keys:train,request_sha256:'b'.repeat(64),provider_success:true},
        {operation:'pca_transform',row_keys:test,request_sha256:'c'.repeat(64),provider_success:true},
        {operation:'pca_monitor',row_keys:test,request_sha256:'d'.repeat(64),provider_success:true},
        {operation:'pca_destroy',row_keys:[],request_sha256:'e'.repeat(64),provider_success:true}],
      x_test_accessed:true,y_train_accessed:false,y_test_accessed:false,x_predict_accessed:false,f41_pca_reused:false,
      monitoring_and_projection_same_fitted_object:false},
    supported_claims:['Position in this train-fitted FlexiblePCA coordinate system'],
    limitations:['No predictive validation, leakage probability or non-calibrability conclusion follows from distances or limit crossings'],
    evidence_sha256:'f'.repeat(64)};
}

function localRefusalFixture(){
  const reason='INVALID_FOLD_CONFIGURATION';
  return {protocol_version:'domains.browser_train_fitted_support_local_refusal.v1',status:'unavailable',reason,local_refusal:true,evidence_sha256:null,
    projection:{status:'unavailable',reason,value:null},monitoring:{status:'unavailable',reason,value:null},
    limit_qualification:{status:'unknown',reasons:['NO_SUCCESSFUL_PROVIDER_RECEIPT'],source:null,fold_scheme:'row_index_modulo_n_folds',
      independent_units_certified:false,interpretation:'No provider receipt returned; limits unavailable.'},
    dependence:{},receipt:{dataset_id:'synthetic-fixture',content_sha256:'fixture-content-digest',
      execution_receipt:'not_returned; no successful execution inferred'},supported_claims:[],
    limitations:['Operation refused locally. Earlier results and imported data remain available.']};
}

test('support input accepts the baseline fixture against the registered scoped schema',()=>{
  assert.ok(validateInput(baseRequest),JSON.stringify(validateInput.errors));
});

test('nullable external plan and invalid-fold/alpha parameter values pass shape validation',()=>{
  const request=structuredClone(baseRequest);
  request.external_limit_plan=null;
  for(const [nComponents,maxComponents,nFolds,alpha] of [[0,-1,0,0],[21,30,1,1],[-3,2,-5,-0.25]]){
    request.parameters={n_components:nComponents,monitoring:true,max_components:maxComponents,n_folds:nFolds,alpha};
    assert.ok(validateInput(request),JSON.stringify(validateInput.errors));
  }
});

test('support input requires train protocol and rejects root raw-X/Y or unrecognized fields',()=>{
  for(const mutate of [
    r=>{r.raw_X=[[1]];},r=>{r.Y_test=[1];},r=>{r.fit='test';},r=>{delete r.external_limit_plan;},
    r=>{r.scope.unrecognized=true;},r=>{r.scope.operation='train_structure';},r=>{r.dependencies=[{name:'specimen',role:'specimen',kind:'categorical',origin:'declared',derived_from_target:false,evidence:'declared',row_keys:['k'],values:['s'],raw_values:['s']}];},
  ]){
    const request=structuredClone(baseRequest);mutate(request);assert.equal(validateInput(request),false);
  }
});

test('external plan has complete explicit fields and rejects extra payload',()=>{
  const request=structuredClone(baseRequest);request.external_limit_plan={protocol_version:'domains.monitor_indexed_folds_design.v1',
    dataset_content_sha256:request.scope.dataset.content_sha256,reference_keys:request.scope.reference_keys,
    max_components:2,n_folds:5,alpha:0.05,independent_unit_ids:request.scope.reference_keys,
    indivisible_dependency_fields:[],source:'synthetic declaration',prospective:true,row_index_modulo_folds_authorized:true};
  assert.ok(validateInput(request),JSON.stringify(validateInput.errors));
  request.external_limit_plan.raw_rows=[[1]];assert.equal(validateInput(request),false);
});

test('support result accepts finite owner outputs, nullable monitor entries and unavailable metrics',()=>{
  const result=resultFixture();
  assert.ok(validateResult(result),JSON.stringify(validateResult.errors));
  result.monitoring.value.monitored_total_variance=null;
  result.monitoring.value.undefined_field_reasons.monitored_total_variance='METHODS_NUMERICALLY_UNDEFINED';
  assert.ok(validateResult(result),JSON.stringify(validateResult.errors));
  result.monitoring.value.monitored_q[0]=null;
  assert.ok(validateResult(result),JSON.stringify(validateResult.errors));
  result.status='partial';result.reason='READ_INDIVIDUAL_OPERATION_STATUSES';
  result.projection={status:'unavailable',reason:'TRAIN_REFERENCE_TOO_SMALL',value:null};
  assert.ok(validateResult(result),JSON.stringify(validateResult.errors));
  result.status='unavailable';result.projection.reason='BOTH_PROTOCOLS_UNAVAILABLE';
  result.monitoring={status:'unavailable',reason:'MONITORING_PROVIDER_ERROR',value:null};
  assert.ok(validateResult(result),JSON.stringify(validateResult.errors));
});

test('support result preserves zero-component monitoring with finite Q and undefined T2 metadata',()=>{
  const result=resultFixture(),monitor=result.monitoring.value;
  monitor.effective_components=0;
  monitor.reference_t2=monitor.reference_t2.map(()=>null);
  monitor.monitored_t2=monitor.monitored_t2.map(()=>null);
  monitor.undefined_field_reasons.reference_t2='METHODS_NUMERICALLY_UNDEFINED';
  monitor.undefined_field_reasons.monitored_t2='METHODS_NUMERICALLY_UNDEFINED';
  monitor.undefined_array_entries.reference_t2=monitor.reference_t2.map((value,index)=>value===null?{index,reason:'NOT_RETAINED_OR_NUMERICALLY_UNDEFINED_BY_METHODS'}:null).filter(Boolean);
  monitor.undefined_array_entries.monitored_t2=monitor.monitored_t2.map((value,index)=>value===null?{index,reason:'NOT_RETAINED_OR_NUMERICALLY_UNDEFINED_BY_METHODS'}:null).filter(Boolean);
  assert.ok(validateResult(result),JSON.stringify(validateResult.errors));
  monitor.descriptive_fractions.either={numerator:1,denominator:2,value:0.5,
    unit:'query acquisitions; descriptive threshold exceedance, not predictive failure or independent-unit probability'};
  assert.ok(validateResult(result),JSON.stringify(validateResult.errors));
  monitor.descriptive_fractions.either.value=1.5;
  assert.equal(validateResult(result),false);
});

test('support result rejects raw fields, fitted-state bytes and malformed status/reason/value states',()=>{
  const cases=[
    r=>{r.raw_X=[[1]];},r=>{r.Y=[1];},r=>{r.projection.value.state_bytes=[1,2,3];},
    r=>{r.projection.value.train_scores[0][0]=null;},
    r=>{r.status='unavailable';},
    r=>{r.projection={status:'computed',reason:'BAD',value:{}};},
    r=>{r.projection.value.reference_variance={status:'computed',reason:'BAD',value:{eigenvalues:[1]}};},
    r=>{r.monitoring={status:'computed',reason:'BAD',value:{}};},
    r=>{r.monitoring.value.reference_q=[NaN];},
    r=>{r.receipt.provider_calls[0].matrix=[[1]];},
  ];
  for(const mutate of cases){const result=resultFixture();mutate(result);assert.equal(validateResult(result),false);}
});

test('local refusal accepts the distinct documentary no-receipt shape',()=>{
  const refusal=localRefusalFixture();
  assert.ok(validateLocalRefusal(refusal),JSON.stringify(validateLocalRefusal.errors));
  const runtimeResult=resultFixture();
  runtimeResult.evidence_sha256=null;
  assert.equal(validateLocalRefusal(runtimeResult),false);
});

test('local refusal rejects runtime provenance, raw payloads and computed metric states',()=>{
  for(const mutate of [
    r=>{r.protocol_version='domains.browser_train_fitted_support_result.v1';},
    r=>{r.receipt.raw_X=[[1]];},
    r=>{r.monitoring={status:'computed',reason:null,value:{eigenvalues:[1]}};},
    r=>{r.projection.value={train_scores:[[1]]};},
    r=>{r.receipt.execution_receipt='successful-provider-result';},
  ]){const candidate=localRefusalFixture();mutate(candidate);assert.equal(validateLocalRefusal(candidate),false);}
});
