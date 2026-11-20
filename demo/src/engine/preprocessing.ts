/** F4.3 access projection and plan transport only. All numerical work belongs to Methods/Rust. */
import type {SensitivityPlan,SensitivityRequest,SensitivityResult,FactorColumn,RepresentationSpec} from '@nirs4all/domains';
import type {ImportedMetadata,LocalDataset} from './types';
import {factorKind} from './factor';
import {initialSupportParameters} from './support';
import catalog from '../../../bindings/wasm/aom-bank.json';
export const sensitivityBank=catalog;
export const representationChoices=catalog.entries.map(entry=>({spec:entry.spec as RepresentationSpec,origin:entry.origin,default:entry.default}));
export interface SensitivityRun {plan:SensitivityPlan;factorIds:string[];stage:SensitivityRequest['stage'];frozenReference:SensitivityResult|null;reuseExactPrefixes:boolean}
export interface SensitivityLocalRefusal {protocol_version:'domains.browser_preprocessing_sensitivity_local_refusal.v1';status:'unavailable';reason:string;stage:SensitivityRequest['stage'];plan:SensitivityPlan;evidence_sha256:null;local_refusal:true;receipt:{execution_receipt:string};limitations:string[]}
export type SensitivityHistory=SensitivityResult|SensitivityLocalRefusal;
const dependencyRoles=new Set(['specimen','physical_sample_id','reference','reference_id','reference_group_id','repetition','group','group_id','instrument','campaign']);
const factorRoles=new Set(['factor','group','instrument','campaign']);
export const sensitivityFactors=(data:LocalDataset)=>data.metadata.filter(f=>factorRoles.has(f.role??'')&&f.derived_from_target!==true&&factorKind(f)!=='unknown').map(f=>({id:f.name,label:f.name}));
const canonical=(v:unknown):unknown=>Array.isArray(v)?v.map(canonical):v!==null&&typeof v==='object'?Object.fromEntries(Object.entries(v).sort(([a],[b])=>a.localeCompare(b)).map(([k,x])=>[k,canonical(x)])):v;
export const sensitivitySignature=(plan:SensitivityPlan,factorIds:readonly string[],reuseExactPrefixes:boolean)=>JSON.stringify(canonical({plan,factorIds:[...factorIds].sort(),reuseExactPrefixes}));
/** Changed scientific controls after an actual reference result are documented as a new exploration. */
export function effectiveSensitivityPlan(plan:SensitivityPlan,factorIds:readonly string[],reuseExactPrefixes:boolean,previous:{result:SensitivityResult;signature:string}|null):SensitivityPlan{
 return previous&&sensitivitySignature(plan,factorIds,reuseExactPrefixes)!==previous.signature
  ?{...plan,kind:'exploratory_revision',parent_plan_sha256:previous.result.plan_sha256}:plan;
}

export const initialRepresentations=structuredClone(catalog.default_representations) as RepresentationSpec[];
export const initialSensitivityPlan=():SensitivityPlan=>({bank_id:catalog.bank_id,kind:'prospective',parent_plan_sha256:null,representations:structuredClone(initialRepresentations),structure:true,compare_neighbors:true,compare_clusters:true,correlation_method:'pearson',support:{...initialSupportParameters}});
export function parseSensitivityPlan(text:string):SensitivityPlan{
 if(new TextEncoder().encode(text).length>65536)throw new Error('SENSITIVITY_PLAN_64_KIB_BUDGET_EXCEEDED');
 const p=JSON.parse(text) as SensitivityPlan;
 if(!p||typeof p!=='object'||!Array.isArray(p.representations)||!p.representations.length||p.representations.length>16||p.representations[0]?.id!=='raw'||p.representations[0]?.steps?.length!==0||p.representations.some(r=>!r||typeof r.id!=='string'||!r.id||!Array.isArray(r.steps)||r.steps.length>3)||new Set(p.representations.map(r=>r.id)).size!==p.representations.length)throw new Error('SENSITIVITY_PLAN_REQUIRES_RAW_FIRST_AND_DISTINCT_BOUNDED_ENTRIES');
 return p;
}
export function preprocessingRequest(data:LocalDataset,run:SensitivityRun):SensitivityRequest{
 const manifest=data.rowManifest;if(!manifest||!data.rawX)throw new Error('SENSITIVITY_IMPORT_MANIFEST_REQUIRED');
 const index=new Map(manifest.map((row,i)=>[row.key,i]));if(index.size!==manifest.length)throw new Error('AMBIGUOUS_SENSITIVITY_ROW_KEYS');
 const unpartitioned=manifest.every(r=>r.partition==='unpartitioned');
 if(!unpartitioned&&manifest.some(r=>r.partition==='unpartitioned'))throw new Error('MIXED_ASSIGNED_UNPARTITIONED_POPULATIONS');
 const reference_keys=manifest.filter(r=>r.partition===(unpartitioned?'unpartitioned':'train')).map(r=>r.key);
 if(!reference_keys.length)throw new Error('SENSITIVITY_REFERENCE_REQUIRED');
 const query_keys=run.stage==='test_audit'?manifest.filter(r=>r.partition==='test').map(r=>r.key):[];
 if(run.stage==='test_audit'&&(unpartitioned||!query_keys.length))throw new Error('SENSITIVITY_DECLARED_TEST_REQUIRED');
 if(run.factorIds.length>2||new Set(run.factorIds).size!==run.factorIds.length)throw new Error('SENSITIVITY_MAXIMUM_TWO_DISTINCT_FACTORS');
 const selected=run.factorIds.map(id=>data.metadata.find(f=>f.name===id));
 if(selected.some(f=>!f||!factorRoles.has(f.role??'')||f.derived_from_target===true||factorKind(f)==='unknown'))throw new Error('INELIGIBLE_SENSITIVITY_FACTOR');
 const version=(data.importSpec as {content_version?:unknown}|null)?.content_version;
 const dataset={dataset_id:data.input.dataset_id,source_id:data.input.source_id,content_sha256:data.input.content_sha256,content_version:typeof version==='string'?version:'not_declared'};
 const keys=[...reference_keys,...query_keys];
 if(run.stage==='test_audit'){
  const frozen=run.frozenReference;
  if(!frozen||frozen.stage!=='reference_only'||frozen.status!=='computed'||JSON.stringify(canonical(frozen.plan))!==JSON.stringify(canonical(run.plan))||JSON.stringify(canonical(frozen.dataset))!==JSON.stringify(canonical(dataset))||JSON.stringify(frozen.receipt.reference_keys)!==JSON.stringify(reference_keys))throw new Error('SENSITIVITY_FROZEN_REFERENCE_MISMATCH');
 }
 const project=(f:ImportedMetadata,populationKeys:string[]):FactorColumn=>{
  if(f.values.length!==manifest.length)throw new Error('METADATA_ROW_KEY_MAPPING_UNAVAILABLE');
  return {name:f.name,role:f.role??'unknown',kind:factorKind(f),unit:f.unit??null,origin:f.origin??'unknown',derived_from_target:typeof f.derived_from_target==='boolean'?f.derived_from_target:null,evidence:f.evidence??'unknown',row_keys:populationKeys,values:populationKeys.map(k=>f.values[index.get(k)!]??null)};
 };
 const factors=selected.map(f=>project(f!,reference_keys));
 const dependencies=data.metadata.filter(f=>dependencyRoles.has(f.role??'')&&f.derived_from_target!==true).map(f=>project(f,keys));
 const exclusion=dependencies.find(f=>f.role==='group'&&f.values.every(v=>v!==null&&String(v).trim().length>0));
 return {schema_version:1,protocol_version:'domains.browser_preprocessing_sensitivity.v1',dataset,manifest:manifest.map(({key,partition})=>({key,partition})),population:unpartitioned?'unpartitioned':'train',reference_keys,query_keys,
  x:{row_keys:keys,matrix:keys.map(k=>data.rawX![index.get(k)!]),axis:[...data.input.axis],axis_unit:data.input.axis_unit},factors,dependencies,exclusion_field:exclusion?.name??null,
  access:{x:true,m_fields:[...new Set([...factors,...dependencies].map(f=>f.name))],y_fields:[]},plan:structuredClone(run.plan),stage:run.stage,frozen_reference:run.stage==='test_audit'?run.frozenReference:null,reuse_exact_prefixes:run.reuseExactPrefixes};
}
