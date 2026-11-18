import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import Ajv2020 from '../../../demo/node_modules/ajv/dist/2020.js';

const names=['report','scoped-input','scoped-result','factor-input','factor-result','support-input','support-result','preprocessing-input','preprocessing-result'];
const schemas=await Promise.all(names.map(async name=>JSON.parse(await readFile(new URL(`../${name}.schema.json`,import.meta.url),'utf8'))));
// Existing companion schemas have pre-existing items/properties-only refinements.
const ajv=new Ajv2020({strict:true,strictTypes:false,allErrors:true});
function legacyDeclarations(value){
  if(!value||typeof value!=='object')return;
  if(Array.isArray(value)){value.forEach(legacyDeclarations);return;}
  for(const key of value.required??[]){
    if(value.properties?.[key])continue;
    assert.notEqual(value.additionalProperties,false,'Never relax a closed legacy contract');
    (value.properties??={})[key]={}; // Declaring an unconstrained, already-permitted field is semantics-neutral.
  }
  Object.values(value).forEach(legacyDeclarations);
}
for(const schema of schemas){
  if(!schema.$id.startsWith('domains.browser_preprocessing_'))legacyDeclarations(schema);
  ajv.addSchema(schema);
}
const input=ajv.getSchema('domains.browser_preprocessing_sensitivity.v1.input');
const result=ajv.getSchema('domains.browser_preprocessing_sensitivity_result.v1');
const bank=JSON.parse(await readFile(new URL('../aom-bank.json',import.meta.url),'utf8'));
const hash='a'.repeat(64),provider='1.3.13+abi.2.20.0';
const unavailable=reason=>({status:'unavailable',reason,value:null});
const dataset={dataset_id:'synthetic',source_id:'public',content_version:'1',content_sha256:hash};
const plan={bank_id:bank.bank_id,kind:'prospective',parent_plan_sha256:null,representations:[{id:'raw',family:'raw',steps:[]}],structure:false,compare_neighbors:false,compare_clusters:false,correlation_method:'pearson',support:{n_components:1,max_components:1,n_folds:2,alpha:0.05,monitoring:false}};
const request=()=>({schema_version:1,protocol_version:'domains.browser_preprocessing_sensitivity.v1',dataset,manifest:['a','b','c'].map(key=>({key,partition:'train'})),population:'train',reference_keys:['a','b','c'],query_keys:[],x:{row_keys:['a','b','c'],matrix:[[1,2],[3,4],[5,6]],axis:[1000,1100],axis_unit:'nm'},factors:[],dependencies:[],exclusion_field:null,access:{x:true,m_fields:[],y_fields:[]},plan:structuredClone(plan),stage:'reference_only',frozen_reference:null,reuse_exact_prefixes:true});
const output=()=>({schema_version:1,protocol_version:'domains.browser_preprocessing_sensitivity_result.v1',status:'computed',reason:null,dataset,population:'train',stage:'reference_only',plan:structuredClone(plan),plan_sha256:hash,reference_input_sha256:hash,input_sha256:hash,evidence_sha256:hash,representations:[{id:'raw',family:'raw',steps:[],status:'computed',reason:null,value:{source:{...dataset,dataset_id:'synthetic::f43::plan::raw',source_id:'public::f43::plan::raw',content_version:'derived-reference-v1'},axis:[1000,1100],axis_unit:'nm',original_axis_sha256:hash,reference_matrix_sha256:hash,query_matrix_sha256:null,transformations:[],structure:unavailable('STRUCTURE_NOT_REQUESTED'),factors:[],support:unavailable('TEST_AUDIT_NOT_REQUESTED'),comparisons:{pca:unavailable('NO_QUALIFIED_SUBSPACE_COMPARISON_API'),neighbors:unavailable('NEIGHBOR_COMPARISON_NOT_REQUESTED'),clusters:unavailable('CLUSTER_COMPARISON_NOT_REQUESTED')}}}],receipt:{provider,reference_keys:['a','b','c'],query_keys:[],test_x_accessed:false,y_accessed:false,x_predict_accessed:false,query_raw_sha256:null,provider_calls:[],exact_prefix_reuse_enabled:true,exact_prefix_cache_hits:0,descriptor_catalog_sha256:hash,aom_source:bank.aom_source,derived_source_semantics:'The inner raw representation names the derived source.',frozen_reference_sha256:null},findings:[{observation:'Declared panel completed.',confidence:'Validated counts.',consequence:'Descriptive only.',action:'Review all entries.'}],limitations:['No predictive or causal conclusion.']});

test('all strict schema references compile and backend-own frozen result is admitted',()=>{
  assert.ok(input(request()),JSON.stringify(input.errors));assert.ok(result(output()),JSON.stringify(result.errors));
  const next=request();next.stage='test_audit';next.frozen_reference=output();assert.ok(input(next),JSON.stringify(input.errors));
});
test('unknown operator remains a local-operation shape rather than a global schema failure',()=>{
  const r=request();r.plan.representations.push({id:'unavailable-owner',family:'declared',steps:[{operator:'UnavailableOwnerClass',parameters:{finite:1,mode:'declared',enabled:true}}]});assert.ok(input(r),JSON.stringify(input.errors));
  r.plan.representations[1].steps[0].parameters.forbidden=[];assert.equal(input(r),false);
});
test('unknown fields, Y grants, raw matrix/state leakage and invalid slots are rejected',()=>{
  for(const mutate of [r=>{r.Y=[1,2,3];},r=>{r.access.y_fields=['Y_test'];},r=>{r.plan.secret_selection=true;}]){const r=request();mutate(r);assert.equal(input(r),false);}
  for(const mutate of [r=>{r.raw_X=[[1,2]];},r=>{r.receipt.state_bytes=[1,2];},r=>{r.representations[0].value.matrix=[[1,2]];},r=>{r.representations[0].value.structure.reason=null;},r=>{r.representations[0].reason='computed cannot have a reason';},r=>{r.representations[0].value.axis[0]=NaN;}]){const r=output();mutate(r);assert.equal(result(r),false);}
});
test('provider receipt allows exact matrix shape only and rejects payload/state contents',()=>{
  const r=output();r.receipt.provider_calls=[{operation:'preprocess_fit',representation_id:'raw',row_keys:['a','b','c'],reference_row_keys:null,monitored_row_keys:null,payload_sha256:hash,request_sha256:hash,shapes:{matrix:[3,2]},provider_success:true}];assert.ok(result(r),JSON.stringify(result.errors));
  r.receipt.provider_calls[0].shapes.matrix=[[1,2],[3,4]];assert.equal(result(r),false);
});

test('F4.0 receipt accepts historical omission and current fit fields while staying closed',()=>{
  const validate=ajv.compile({$ref:'domains.browser_scoped_result.v1#/$defs/receipt'});
  const receipt={protocol_version:'domains.browser_scoped_analysis.v1',operation:'train_structure',diagnostic:null,dataset,request_sha256:hash,manifest_sha256:hash,reference_keys:['a','b','c'],query_keys:[],fit_keys:['a','b','c'],reference_population:{role:'train',row_keys:['a','b','c']},query_population:{role:'test',row_keys:[]},fit:'train',representation:'raw',parameters:{preset:'f4_fixed_raw_v1'},selection_context:'unspecified',explicit_transductive:false,exclusion_field:null,fields_read:{x:null,m:[],y:[]},provider_calls:[],test_x_accessed:false,y_accessed:false,physical_independence:'unverified',physical_id_encoding:'type-preserving',receipt_sha256:hash};
  assert.ok(validate(receipt),JSON.stringify(validate.errors));
  Object.assign(receipt,{fit_attempted:true,fit_executed:true,requested_fit_keys:['a','b','c']});
  assert.ok(validate(receipt),JSON.stringify(validate.errors));
  receipt.state_bytes=[1,2,3];assert.equal(validate(receipt),false);delete receipt.state_bytes;
  receipt.arbitrary=true;assert.equal(validate(receipt),false);delete receipt.arbitrary;
  receipt.fit_attempted='true';assert.equal(validate(receipt),false);
});
