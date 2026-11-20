// Shape tests are separate from execution: schemas cannot authenticate PCA/design evidence.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import Ajv2020 from '../../../demo/node_modules/ajv/dist/2020.js';

const ajv = new Ajv2020({strict:true,allErrors:true});
const inputSchema=JSON.parse(await readFile(new URL('../factor-input.schema.json',import.meta.url)));
const resultSchema=JSON.parse(await readFile(new URL('../factor-result.schema.json',import.meta.url)));
const validateInput=ajv.compile(inputSchema),validateResult=ajv.compile(resultSchema);
const hash='a'.repeat(64),keys=['a','b','c'];
const absent=()=>({status:'unavailable',reason:'NOT_REQUESTED',value:null});
const request={schema_version:1,protocol_version:'domains.browser_factor_association.v1',dataset:{dataset_id:'synthetic',source_id:'x',content_version:'v1',content_sha256:hash},
  manifest:keys.map(key=>({key,partition:'unpartitioned'})),population:'unpartitioned',
  pca:{report:{schema_version:1,protocol_version:'domains.browser_x.v1',status:'computed',scope:{},metrics:Object.fromEntries(['pca','density','raw_neighbors','projected_neighbors','metadata_factor_association','resampling_stability','parameter_sensitivity','predictive_performance'].map(k=>[k,absent()])),input_sha256:hash,evidence_sha256:hash,test_target_accessed:false,raw_spectra_included:false},row_keys:keys,fit_receipt:null},
  factors:[{name:'dose',role:'factor',kind:'continuous',unit:null,origin:'synthetic',derived_from_target:false,evidence:'declared',row_keys:keys,values:[0,null,2]}],dependencies:[],
  access:{x:false,m_fields:['dose'],y_fields:[]},representation:'raw',explicit_transductive:false,components:'all_resolved',correlation_method:'pearson',inference:{mode:'descriptive',plan:null},parameters:{preset:'f41_factor_pc_v1'}};
request.pca.report.scope={dataset_id:'synthetic',source_id:'x',content_sha256:hash,n_observations:3,n_bands:1,axis_unit:'nm',axis_sha256:hash,observation_ids_sha256:hash,
  population:'complete imported source; descriptive full-X fit',split:'none; no predictive evaluation',target:'absent',identity_evidence:'observation_identity_only',
  groups:'Declaration only',metadata_coverage:'Declaration only',n_declared_groups:null,policy:'Shape fixture only'};

test('input schema accepts nullable declarations/zero and rejects extra values, absent keys and ambiguous identities',()=>{
  assert.ok(validateInput(request),JSON.stringify(validateInput.errors));
  for(const mutate of [r=>{r.Y_test=[1];},r=>{delete r.factors[0].unit;},r=>{r.factors[0].values[0]='zero';},r=>{r.factors[0].row_keys[1]='a';},r=>{r.access.x=true;},r=>{r.pca.report.metrics.pca={spectra:[[1]]};},r=>{r.pca.report.extra=true;}]) {
    const r=structuredClone(request);mutate(r);assert.equal(validateInput(r),false);
  }
  const labels=structuredClone(request);labels.factors[0].kind='categorical';
  labels.factors[0].values=[0,9007199254740991,'9007199254740992'];
  assert.ok(validateInput(labels),JSON.stringify(validateInput.errors));
  for(const n of [9007199254740992,-9007199254740992]) {
    labels.factors[0].values[0]=n;assert.equal(validateInput(labels),false);
  }
  const continuous=structuredClone(request);continuous.factors[0].values[0]=9007199254740992;
  assert.ok(validateInput(continuous),JSON.stringify(validateInput.errors));
});

test('component slots preserve status/reason/value invariants and categorical effect bounds',()=>{
  const validate=ajv.compile({...resultSchema,$id:'domains.factor.schema.component.test',$ref:'#/$defs/component',required:undefined,properties:undefined,additionalProperties:undefined});
  const c={component:1,n_used:3,descriptive:absent(),inference:absent(),exact_owner_evidence:absent()};
  assert.ok(validate(c),JSON.stringify(validate.errors));
  for(const value of [{status:'computed',reason:null,value:null},{status:'unavailable',reason:'',value:null},{status:'error',reason:'REFUSED',value:{estimate:0}}]) {
    assert.equal(validate({...c,descriptive:value}),false);
  }
  const owner={eta_squared:.8,f_statistic:8,df1:1,df2:1,n_levels:2,n_score_values:3,log10_distinct_arrangements:1,p_value:null,n_at_least_observed:0,n_permutations_executed:0,backend_version:'1.5.1+abi.2.24.0'};
  c.descriptive={status:'computed',reason:null,value:{measure:'eta_squared',estimate:.8,owner_output:owner}};
  assert.ok(validate(c),JSON.stringify(validate.errors));
  c.descriptive.value.estimate=1.01;assert.equal(validate(c),false);
  c.descriptive.value.estimate=.8;c.descriptive.value.owner_output.codes=[0,0,1];assert.equal(validate(c),false);
});

test('result envelope refuses noncomputed outer values and raw per-row additions',()=>{
  const factor={factor_id:'dose',kind:'continuous',role:'factor',unit:null,origin:'synthetic',evidence:'declared',derived_from_target:false,
    n_fit_observations:3,n_used:2,n_missing:1,used_keys_sha256:hash,values_sha256:hash,n_levels:null,level_counts:null,range:absent(),owner_summary:absent(),warnings:[],
    components:[{component:1,n_used:2,descriptive:absent(),inference:absent(),exact_owner_evidence:absent()}]};
  const receipt={dataset:request.dataset,request_sha256:hash,manifest_sha256:hash,population:'unpartitioned',fit_keys:keys,
    source_pca_input_sha256:hash,source_pca_evidence_sha256:hash,source_pca_fit_receipt_sha256:null,scores_sha256:hash,scores_shape:[3,1],pca_id:hash,pca_refits:0,
    fields_read:{x:false,y:[],m:[{name:'dose',role:'factor',origin:'synthetic',n_rows:3,keys_sha256:hash,values_sha256:hash}]},
    source_pca_uses_test_x:false,test_scores_accessed:false,test_m_accessed:false,test_x_accessed:false,y_accessed:false,explicit_transductive:false,
    provider_version:'1.5.1+abi.2.24.0',provider_calls:[],parameters:request.parameters,components:'all_resolved',correlation_method:'pearson',receipt_sha256:hash};
  const result={protocol_version:'domains.browser_factor_association_result.v1',status:'computed',reason:null,
    value:{population:'unpartitioned',representation:'recorded raw-PCA scores',pca_id:hash,scores_sha256:hash,
      analysis_unit:{calculation_unit:'observations/acquisitions',n_observations:3,n_independent_units:null,physical_independence_verified_by_domains:false,qualification:'Shape fixture only'},
      inference:{level:'descriptive_only',reason:'DESCRIPTIVE_ONLY',family:null,no_global_risk_or_causal_claim:true},factors:[factor],
      dependency_audit:{fields:[],pairwise_context_tables:[],qualification:'Shape fixture only'}},receipt,supported_claims:['Shape fixture only'],limitations:['No execution'],action:'Review'};
  assert.ok(validateResult(result),JSON.stringify(validateResult.errors));
  for(const mutate of [r=>{r.value=null;},r=>{r.status='unavailable';},r=>{r.value.factors[0].values=[0,null,2];},r=>{r.value.factors[0].codes=[0,1];},r=>{r.receipt.fields_read.x=true;},r=>{r.receipt.scores_sha256='bad';},r=>{delete r.receipt.source_pca_fit_receipt_sha256;}]) {
    const r=structuredClone(result);mutate(r);assert.equal(validateResult(r),false);
  }
});
