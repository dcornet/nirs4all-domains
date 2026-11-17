/** Least-access projection. Imported Y values never enter these objects. Rust revalidates grants. */
import type {ScopedOperation,ScopedRequest,ScopedMetadata,ScopedResult,PartitionRole} from '@nirs4all/domains';
import type {LocalDataset} from './types';
export interface ScopeOptions {
  diagnostic?:'exact_spectra'|'declared_identities'; explicit_transductive?:boolean;
  selection_context?:ScopedRequest['selection_context'];
}
const identityRoles=new Set(['observation_id','specimen','group','reference','repetition','instrument','campaign']);
export function scopedRequest(data:LocalDataset,operation:ScopedOperation,options:ScopeOptions={}):ScopedRequest {
  if(!data.rowManifest||!data.rawX)throw new Error('SCOPED_IMPORT_MANIFEST_REQUIRED');
  const rows=data.rowManifest;
  const train=rows.filter(row=>row.partition==='train').map(row=>row.key);
  const test=rows.filter(row=>row.partition==='test').map(row=>row.key);
  const metadataOnly=operation==='metadata_factor_audit'||operation==='cross_partition_metadata_audit';
  const identityOnly=operation==='integrity_audit'&&options.diagnostic==='declared_identities';
  const structural=operation==='train_structure'||operation==='global_descriptive_transductive';
  const reference_keys=operation==='metadata_factor_audit'&&!train.length&&!test.length
    ?rows.filter(row=>row.partition==='unpartitioned').map(row=>row.key):train;
  const query_keys=operation==='train_structure'||operation==='metadata_factor_audit'?[]:test;
  const keys=[...reference_keys,...query_keys];
  const index=new Map(rows.map((row,i)=>[row.key,i]));
  const fields=data.metadata.filter(field=>field.derived_from_target!==true&&
    (!identityOnly||identityRoles.has(field.role??'unknown'))&&
    (!(structural||operation==='train_reference_test_query'||operation==='integrity_audit'&&!identityOnly)||field.role==='group'||field.role==='specimen'));
  // Numerical structure/support reads only a single explicitly declared exclusion field.
  const exclusion=structural||operation==='train_reference_test_query'
    ?fields.find(field=>field.role==='group'&&field.values.length===rows.length&&keys.every(key=>{const v=field.values[index.get(key)!];return v!==null&&v!==undefined&&String(v).trim();})):undefined;
  const allowed=structural||operation==='train_reference_test_query'?exclusion?[exclusion]:[]
    :operation==='integrity_audit'&&!identityOnly?fields.filter(field=>field.role==='specimen').slice(0,1):fields;
  const metadata:ScopedMetadata[]=allowed.map(field=>({name:field.name,role:field.role??'unknown',
    kind:identityRoles.has(field.role??'unknown')?'categorical':field.type==='numeric'?'continuous':field.type==='unknown'?'unknown':'categorical',
    origin:field.origin??'unknown',derived_from_target:typeof field.derived_from_target==='boolean'?field.derived_from_target:null,
    evidence:field.evidence??'unknown',row_keys:keys,
    values:keys.map(key=>field.values[index.get(key)!]??null)}));
  const xAccess=!metadataOnly&&!identityOnly;
  const version=(data.importSpec as {content_version?:unknown}|null)?.content_version;
  return {schema_version:1,protocol_version:'domains.browser_scoped_analysis.v1',operation,
    diagnostic:operation==='integrity_audit'?options.diagnostic??'exact_spectra':null,
    dataset:{dataset_id:data.input.dataset_id,source_id:data.input.source_id,content_sha256:data.input.content_sha256,content_version:typeof version==='string'?version:'not_declared'},
    manifest:rows.map(row=>({key:row.key,partition:row.partition as PartitionRole})),reference_keys,query_keys,
    access:{x:xAccess,m_fields:metadata.map(field=>field.name),y_fields:[]},
    fit:operation==='train_structure'?'train':operation==='global_descriptive_transductive'?'transductive':'none',
    representation:'raw',selection_context:options.selection_context??'unspecified',
    explicit_transductive:options.explicit_transductive===true,parameters:{preset:'f4_fixed_raw_v1'},
    exclusion_field:exclusion?.name??null,
    x:xAccess?{row_keys:keys,matrix:keys.map(key=>data.rawX![index.get(key)!]),axis:data.input.axis,axis_unit:data.input.axis_unit}:null,
    metadata};
}
/** Build an existing-protocol view of exactly the selected, already-validated fit rows. */
export function structureDataset(data:LocalDataset,result:ScopedResult):LocalDataset|undefined {
  if(!result.value?.structure||!data.rowManifest||!data.rawX)return;
  const keys=result.operation==='train_structure'?data.rowManifest.filter(row=>row.partition==='train').map(row=>row.key)
    :[...data.rowManifest.filter(row=>row.partition==='train'),...data.rowManifest.filter(row=>row.partition==='test')].map(row=>row.key);
  const index=new Map(data.rowManifest.map((row,i)=>[row.key,i]));
  const group=data.metadata.find(field=>field.derived_from_target!==true&&field.role==='group'&&field.values.length===data.rowManifest!.length&&keys.every(key=>{const v=field.values[index.get(key)!];return v!==null&&v!==undefined&&String(v).trim();}));
  return {...data,input:{...data.input,observation_ids:keys,spectra:keys.map(key=>data.rawX![index.get(key)!] as number[]),
    ...(group?{group_ids:keys.map(key=>String(group.values[index.get(key)!]))}:{})}};
}
