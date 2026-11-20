import {describe,it,expect} from 'vitest';
import {preprocessingRequest,initialSensitivityPlan,parseSensitivityPlan,sensitivitySignature,effectiveSensitivityPlan,type SensitivityRun} from './preprocessing';
import type {LocalDataset} from './types';
import type {SensitivityResult} from '@nirs4all/domains';
function fixture():LocalDataset{
 const roles=['train','test','predict','train'] as const;
 return {input:{schema_version:1,dataset_id:'transport-only',source_id:'X',content_sha256:'a'.repeat(64),observation_ids:roles.map((_,i)=>`k${i}`),spectra:[],axis:[2000,1000],axis_unit:'nm'},
 rawX:[[1,2],[3,4],[999,999],[5,6]],rowManifest:roles.map((partition,i)=>({key:`k${i}`,observation_id:null,partition,original_partition:partition,source_id:'X'})),
 metadata:[{name:'factor',role:'factor',type:'numeric',values:[1,101,999,2]},{name:'specimen',role:'specimen',values:['s1','s2','P','s3']},{name:'derived',role:'factor',type:'numeric',derived_from_target:true,values:[9,9,9,9]}],
 partitions:[],headers:[],warnings:[],importSpec:{content_version:'v1'},identityOrigin:'declared',license:'synthetic',mode:'user_computed_live'};
}
const run=():SensitivityRun=>({plan:initialSensitivityPlan(),factorIds:['factor'],stage:'reference_only',frozenReference:null,reuseExactPrefixes:true});
function frozen(data:LocalDataset,request:SensitivityRun):SensitivityResult{
 const r=preprocessingRequest(data,request);
 return {protocol_version:'domains.browser_preprocessing_sensitivity_result.v1',status:'computed',stage:'reference_only',dataset:r.dataset,plan:r.plan,plan_sha256:'b'.repeat(64),receipt:{reference_keys:r.reference_keys,query_keys:[],test_x_accessed:false}} as unknown as SensitivityResult;
}
describe('F4.3 transport-only access contracts (no numeric provider)',()=>{
 it('projects only reference X/M on first action, preserving original axes and row order, without reading Y/test/predict',()=>{
  const d=fixture();Object.defineProperty(d,'targets',{get(){throw new Error('Y_READ');}});
  for(const i of [1,2]){Object.defineProperty(d.rawX!,i,{get(){throw new Error('NONREFERENCE_X_READ');}});for(const f of d.metadata)Object.defineProperty(f.values,i,{get(){throw new Error('NONREFERENCE_M_READ');}});}
  const r=preprocessingRequest(d,run());expect(r.reference_keys).toEqual(['k0','k3']);expect(r.query_keys).toEqual([]);expect(r.x.matrix).toEqual([[1,2],[5,6]]);expect(r.x.axis).toEqual([2000,1000]);expect(r.x.row_keys).toEqual(r.reference_keys);expect(r.access.y_fields).toEqual([]);expect(r.factors[0].values).toEqual([1,2]);expect(r.dependencies[0].row_keys).toEqual(r.reference_keys);expect(r.frozen_reference).toBeNull();
 });
 it('audits test only explicitly, using the actual frozen result and reference-only factors while projecting documentary dependencies to both populations',()=>{
  const d=fixture(),r=run(),f=frozen(d,r);Object.defineProperty(d,'targets',{get(){throw new Error('Y_READ');}});Object.defineProperty(d.rawX!,2,{get(){throw new Error('PREDICT_X_READ');}});Object.defineProperty(d.metadata[0].values,1,{get(){throw new Error('TEST_FACTOR_READ');}});
  const request=preprocessingRequest(d,{...r,stage:'test_audit',frozenReference:f});expect(request.frozen_reference).toBe(f);expect(request.x.row_keys).toEqual(['k0','k3','k1']);expect(request.query_keys).toEqual(['k1']);expect(request.factors[0].row_keys).toEqual(['k0','k3']);expect(request.dependencies[0].values).toEqual(['s1','s3','s2']);expect(JSON.stringify(request)).not.toContain('999');
 });
 it('refuses frozen plan/source/order mismatches and invalid factor grants',()=>{
  const d=fixture(),r=run(),f=frozen(d,r);expect(()=>preprocessingRequest(d,{...r,stage:'test_audit'})).toThrow('FROZEN_REFERENCE_MISMATCH');
  const changed={...r,stage:'test_audit' as const,frozenReference:f,plan:{...r.plan,compare_neighbors:false}};expect(()=>preprocessingRequest(d,changed)).toThrow('FROZEN_REFERENCE_MISMATCH');
  expect(()=>preprocessingRequest({...d,input:{...d.input,content_sha256:'c'.repeat(64)}},{...r,stage:'test_audit',frozenReference:f})).toThrow('FROZEN_REFERENCE_MISMATCH');
  const reordered=fixture();reordered.rowManifest!.reverse();expect(()=>preprocessingRequest(reordered,{...r,stage:'test_audit',frozenReference:f})).toThrow('FROZEN_REFERENCE_MISMATCH');
  expect(()=>preprocessingRequest(d,{...r,factorIds:['derived']})).toThrow('INELIGIBLE');expect(()=>preprocessingRequest(d,{...r,factorIds:['factor','factor']})).toThrow('TWO_DISTINCT');
 });
 it('retains selected group dependencies and exact exclusion policy while granting selected group/instrument names only once',()=>{
  const d=fixture();d.metadata.push({name:'group',role:'group',values:['g1','g2','predict','g3']},{name:'instrument',role:'instrument',values:['i1','i2','predict','i1']});
  const r=run();r.factorIds=['group','instrument'];const reference=preprocessingRequest(d,r);
  expect(reference.exclusion_field).toBe('group');expect(reference.factors.map(f=>f.name)).toEqual(['group','instrument']);
  expect(reference.dependencies.find(f=>f.name==='group')).toEqual(reference.factors.find(f=>f.name==='group'));
  expect(reference.dependencies.find(f=>f.name==='instrument')).toEqual(reference.factors.find(f=>f.name==='instrument'));
  expect(reference.access.m_fields.filter(name=>name==='group')).toHaveLength(1);expect(reference.access.m_fields.filter(name=>name==='instrument')).toHaveLength(1);
  const audit=preprocessingRequest(d,{...r,stage:'test_audit',frozenReference:frozen(d,r)});
  expect(audit.exclusion_field).toBe('group');expect(audit.factors.find(f=>f.name==='group')?.values).toEqual(['g1','g3']);expect(audit.dependencies.find(f=>f.name==='group')?.values).toEqual(['g1','g3','g2']);expect(audit.dependencies.find(f=>f.name==='instrument')?.row_keys).toEqual(['k0','k3','k1']);
 });
 it('marks every changed plan/factor selection after an actual reference as exploratory, retaining exact first-plan audit parameters',()=>{
  const d=fixture(),r=run(),result=frozen(d,r),previous={result,signature:sensitivitySignature(r.plan,r.factorIds,r.reuseExactPrefixes)};
  expect(effectiveSensitivityPlan(r.plan,r.factorIds,true,null)).toBe(r.plan);
  expect(effectiveSensitivityPlan(r.plan,r.factorIds,true,previous)).toBe(r.plan);
  for(const [plan,factorIds] of [[{...r.plan,correlation_method:'spearman' as const},r.factorIds],[r.plan,[]]] as const){
   const effective=effectiveSensitivityPlan(plan,factorIds,true,previous);expect(effective.kind).toBe('exploratory_revision');expect(effective.parent_plan_sha256).toBe(result.plan_sha256);expect(effective.representations).toEqual(plan.representations);expect(effective.support).toEqual(plan.support);
   expect(sensitivitySignature(effective,factorIds,true)).not.toBe(previous.signature);
  }
  const editDeclaringProspective={...r.plan,kind:'prospective' as const,compare_clusters:false};expect(effectiveSensitivityPlan(editDeclaringProspective,r.factorIds,true,previous).kind).toBe('exploratory_revision');
 });
 it('supports fully unpartitioned reference while refusing mixed populations/test audit and preserving plan snapshots',()=>{
  const d=fixture();d.rowManifest!.forEach(r=>r.partition='unpartitioned');const r=run(),request=preprocessingRequest(d,r);expect(request.reference_keys).toEqual(['k0','k1','k2','k3']);expect(request.population).toBe('unpartitioned');r.plan.compare_clusters=false;expect(request.plan.compare_clusters).toBe(true);
  expect(()=>preprocessingRequest(d,{...r,stage:'test_audit'})).toThrow('DECLARED_TEST_REQUIRED');d.rowManifest![0].partition='train';expect(()=>preprocessingRequest(d,r)).toThrow('MIXED_ASSIGNED');
 });
 it('requires raw first, bounded distinct entries and a changed controls signature for every explicit factor/plan/cache change',()=>{
  const p=initialSensitivityPlan();expect(p.representations).toHaveLength(12);expect(parseSensitivityPlan(JSON.stringify(p))).toEqual(p);expect(()=>parseSensitivityPlan(JSON.stringify({...p,representations:p.representations.slice(1)}))).toThrow('RAW_FIRST');expect(()=>parseSensitivityPlan(JSON.stringify({...p,representations:[...p.representations,p.representations[0]]}))).toThrow('DISTINCT');
  expect(sensitivitySignature(p,['factor'],true)).not.toBe(sensitivitySignature(p,[],true));expect(sensitivitySignature(p,[],true)).not.toBe(sensitivitySignature(p,[],false));
 });
});
