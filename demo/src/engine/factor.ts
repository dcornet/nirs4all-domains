/** Project only the declared PCA population and explicitly admitted M; never inspect X or Y values. */
import type {BrowserReport,FactorColumn,FactorRequest,FactorPopulation,ScopedResult,FactorInferencePlan} from '@nirs4all/domains';
import type {LocalDataset,ImportedMetadata} from './types';
import type {FactorAssociationRun} from '../FactorAssociationControls';
const factorRoles=new Set(['factor','group','instrument','campaign']);
const dependencyRoles=new Set(['observation_id','specimen','group','reference','repetition','instrument','campaign','factor']);
export const factorKind=(f:ImportedMetadata):'continuous'|'categorical'|'unknown'=>
  ['group','instrument','campaign'].includes(f.role??'')?'categorical':f.type==='numeric'?'continuous':f.type==='unknown'||!f.type?'unknown':'categorical';
export const factorChoices=(data:LocalDataset)=>data.metadata.filter(f=>factorRoles.has(f.role??'')).map(f=>({
  id:f.name,label:f.name,kind:factorKind(f),unit:f.unit??null,origin:f.origin??'unknown',derivedFromTarget:f.derived_from_target??'unknown' as const}));
export interface FactorSource {report:BrowserReport;receipt:Record<string,unknown>|null}
export function factorSource(population:FactorPopulation,operations:readonly ScopedResult[],unpartitioned:BrowserReport|null):FactorSource|undefined{
  if(population==='unpartitioned')return unpartitioned?{report:unpartitioned,receipt:null}:undefined;
  const operation=population==='train'?'train_structure':'global_descriptive_transductive';
  const found=[...operations].reverse().find(r=>r.operation===operation&&r.status==='computed'&&r.value?.structure);
  return found?.value?.structure?{report:found.value.structure,receipt:found.receipt}:undefined;
}
export async function parseFactorInferencePlan(text:string):Promise<FactorInferencePlan>{
  if(new TextEncoder().encode(text).length>65_536)throw new Error('FACTOR_DESIGN_RECORD_64_KIB_BUDGET_EXCEEDED');
  const value:unknown=JSON.parse(text);
  const [{default:Ajv2020},{default:schema}]=await Promise.all([import('ajv/dist/2020'),import('../../../bindings/wasm/factor-input.schema.json')]);
  const validate=new Ajv2020({strict:true,allErrors:false}).compile({$schema:schema.$schema,$defs:schema.$defs,$ref:'#/$defs/plan'});
  if(!validate(value))throw new Error('INVALID_FACTOR_DESIGN_RECORD: '+JSON.stringify(validate.errors));
  return value as FactorInferencePlan;
}
export function factorRequest(data:LocalDataset,source:FactorSource,run:FactorAssociationRun,plan:FactorInferencePlan|null=null):FactorRequest{
  const manifest=data.rowManifest;if(!manifest)throw new Error('FACTOR_IMPORT_MANIFEST_REQUIRED');
  if(run.population==='global_transductive'&&!run.explicitTransductive)throw new Error('EXPLICIT_TRANSDUCTIVE_ASSOCIATION_CONSENT_REQUIRED');
  if(run.population==='unpartitioned'&&manifest.some(r=>r.partition!=='unpartitioned'))throw new Error('UNPARTITIONED_SCOPE_CANNOT_HIDE_ASSIGNED_PARTITIONS');
  const rows=run.population==='global_transductive'?[...manifest.filter(r=>r.partition==='train'),...manifest.filter(r=>r.partition==='test')]
    :manifest.filter(r=>r.partition===run.population);
  const keys=rows.map(r=>r.key),index=new Map(manifest.map((r,i)=>[r.key,i]));
  if(index.size!==manifest.length)throw new Error('AMBIGUOUS_FACTOR_ROW_KEYS');
  const selected=data.metadata.find(f=>f.name===run.factorId);
  if(!selected||!factorRoles.has(selected.role??'')||selected.derived_from_target===true||factorKind(selected)==='unknown')throw new Error('INELIGIBLE_FACTOR_SELECTION');
  const deps=data.metadata.filter(f=>f!==selected&&dependencyRoles.has(f.role??'')&&f.derived_from_target!==true);
  if(deps.length>24)throw new Error('FACTOR_DEPENDENCY_FIELD_BUDGET_EXCEEDED');
  const project=(f:ImportedMetadata):FactorColumn=>{
    if(f.values.length!==manifest.length)throw new Error('METADATA_ROW_KEY_MAPPING_UNAVAILABLE');
    return {name:f.name,role:f.role??'unknown',kind:factorKind(f),unit:f.unit??null,origin:f.origin??'unknown',
      derived_from_target:typeof f.derived_from_target==='boolean'?f.derived_from_target:null,evidence:f.evidence??'unknown',
      row_keys:keys,values:keys.map(k=>f.values[index.get(k)!]??null)};
  };
  const factors=[project(selected)],dependencies=deps.map(project);
  // Only original X-only evidence fields enter the association request. UI declarations/transport extensions do not.
  const {schema_version,protocol_version,status,scope,metrics,input_sha256,evidence_sha256,test_target_accessed,raw_spectra_included}=source.report;
  const version=(data.importSpec as {content_version?:unknown}|null)?.content_version;
  return {schema_version:1,protocol_version:'domains.browser_factor_association.v1',
    dataset:{dataset_id:data.input.dataset_id,source_id:data.input.source_id,content_sha256:data.input.content_sha256,content_version:typeof version==='string'?version:'not_declared'},
    manifest:manifest.map(({key,partition})=>({key,partition})),population:run.population,
    pca:{report:{schema_version,protocol_version,status,scope,metrics,input_sha256,evidence_sha256,test_target_accessed,raw_spectra_included} as FactorRequest['pca']['report'],row_keys:keys,fit_receipt:source.receipt as FactorRequest['pca']['fit_receipt']},
    factors,dependencies,access:{x:false,y_fields:[],m_fields:[...factors,...dependencies].map(f=>f.name)},
    representation:'raw',explicit_transductive:run.population==='global_transductive'&&run.explicitTransductive,
    components:'all_resolved',correlation_method:run.correlationMethod,
    inference:{mode:run.inference,plan:run.inference==='exact_if_qualified'?plan??null:null},parameters:{preset:'f41_factor_pc_v1'}};
}
