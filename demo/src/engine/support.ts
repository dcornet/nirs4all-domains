/** F4.2 transport projection only: Rust owns fit, transform and qualification. */
import type {SupportRequest,SupportResult,ScopedMetadata} from '@nirs4all/domains';
import type {LocalDataset} from './types';
import {scopedRequest} from './scoped';
export type SupportRun=SupportResult|(Omit<SupportResult,'evidence_sha256'|'protocol_version'|'status'>&{protocol_version:'domains.browser_train_fitted_support_local_refusal.v1';status:'unavailable';evidence_sha256:null;local_refusal:true});
export type SupportParameters=SupportRequest['parameters'];
export const initialSupportParameters:SupportParameters={n_components:2,max_components:2,n_folds:5,alpha:0.05,monitoring:true};
const roles=new Set(['specimen','physical_sample_id','reference','reference_id','reference_group_id','repetition','group','group_id','instrument','campaign']);
export function supportRequest(data:LocalDataset,parameters:SupportParameters):SupportRequest{
  const scope=scopedRequest(data,'train_reference_test_query');
  const manifest=data.rowManifest!;
  const keys=[...scope.reference_keys,...scope.query_keys],index=new Map(manifest.map((r,i)=>[r.key,i]));
  if(index.size!==manifest.length)throw new Error('AMBIGUOUS_SUPPORT_ROW_KEYS');
  const fields=data.metadata.filter(f=>roles.has(f.role??'')&&f.derived_from_target!==true);
  const dependencies:ScopedMetadata[]=fields.map(f=>{
    if(f.values.length!==manifest.length)throw new Error('METADATA_ROW_KEY_MAPPING_UNAVAILABLE');
    return {name:f.name,role:f.role??'unknown',kind:'categorical',origin:f.origin??'unknown',
      evidence:f.evidence??'unknown',derived_from_target:typeof f.derived_from_target==='boolean'?f.derived_from_target:null,
      row_keys:keys,values:keys.map(k=>f.values[index.get(k)!]??null)};
  });
  return {schema_version:1,protocol_version:'domains.browser_train_fitted_support.v1',fit:'train',scope,
    parameters:{...parameters},dependencies,dependency_fields:dependencies.map(f=>f.name),external_limit_plan:null};
}

/** A terminated or replaced worker response cannot change the current support history. */
export function recordSupportReply(currentEpoch:number,responseEpoch:number,history:readonly SupportRun[],result:SupportRun):SupportRun[]{
 return responseEpoch===currentEpoch?[...history,result]:[...history];
}
