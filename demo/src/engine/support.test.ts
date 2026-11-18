import {describe,it,expect} from 'vitest';
import {supportRequest,initialSupportParameters,recordSupportReply} from './support';
import type {LocalDataset} from './types';
function fixture():LocalDataset{
 return {input:{schema_version:1,dataset_id:'transport-only',source_id:'X',content_sha256:'a'.repeat(64),observation_ids:['a','b','c'],spectra:[],axis:[2,1],axis_unit:'nm'},
 rawX:[[1,2],[3,4],[999,999]],rowManifest:['train','test','predict'].map((partition,i)=>({key:['a','b','c'][i],observation_id:null,partition,original_partition:partition,source_id:'X'})),
 metadata:[{name:'physical',role:'specimen',values:['s1','s2','SECRET_PREDICT']},{name:'target-derived',role:'group',derived_from_target:true,values:['Y','Y','Y']}],
 partitions:[],headers:[],warnings:[],importSpec:{},identityOrigin:'declared',license:'synthetic',mode:'user_computed_live'} as LocalDataset;
}
describe('F4.2 transport-only access projection (no numeric provider stub)',()=>{
 it('uses F4.0 closure, keeps axes and train/test order, never reads targets or prediction cells',()=>{
  const data=fixture();Object.defineProperty(data,'targets',{get(){throw new Error('Y_READ');}});
  Object.defineProperty(data.rawX!,2,{get(){throw new Error('PREDICT_X_READ');}});
  Object.defineProperty(data.metadata[0].values,2,{get(){throw new Error('PREDICT_M_READ');}});
  const r=supportRequest(data,initialSupportParameters);
  expect(r.fit).toBe('train');expect(r.scope.fit).toBe('none');expect(r.scope.x?.matrix).toEqual([[1,2],[3,4]]);
  expect(r.scope.x?.axis).toEqual([2,1]);expect(r.scope.access.y_fields).toEqual([]);
  expect(r.dependencies.map(d=>d.name)).toEqual(['physical']);expect(r.dependencies[0].values).toEqual(['s1','s2']);expect(r.external_limit_plan).toBeNull();
 });
 it('rejects stale/cancelled responses without changing the current history',()=>{
  const previous={status:'unavailable',local_refusal:true} as any,next={status:'computed'} as any;const history=[previous];
  expect(recordSupportReply(8,7,history,next)).toEqual(history);expect(recordSupportReply(8,8,history,next)).toEqual([previous,next]);expect(history).toEqual([previous]);
 });
 it('records an immutable parameter snapshot and refuses ambiguous dependency mapping',()=>{
  const d=fixture(),parameters={...initialSupportParameters};const r=supportRequest(d,parameters);parameters.alpha=.2;expect(r.parameters.alpha).toBe(.05);
  d.metadata[0].values=['only'];expect(()=>supportRequest(d,parameters)).toThrow('METADATA_ROW_KEY_MAPPING_UNAVAILABLE');
 });
});
