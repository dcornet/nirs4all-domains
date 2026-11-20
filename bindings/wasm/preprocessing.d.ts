import type {ScopedRequest,FactorColumn,SupportRequest} from './index.js';
type ScopedDataset=ScopedRequest['dataset'];
type ScopedManifestRow=ScopedRequest['manifest'][number];
type ScopedSpectra=NonNullable<ScopedRequest['x']>;
export interface PreprocessingStep {operator:'SNV'|'MSC'|'Detrend'|'SavitzkyGolay'|'Gaussian'|'StandardScale'|'Normalize'|'CropTransformer';parameters:Record<string,string|number|boolean>}
export interface RepresentationSpec {id:string;family:string;steps:PreprocessingStep[]}
export interface SensitivityPlan {
  bank_id:string;kind:'prospective'|'exploratory_revision';parent_plan_sha256:string|null;
  representations:RepresentationSpec[];structure:boolean;compare_neighbors:boolean;compare_clusters:boolean;
  correlation_method:'pearson'|'spearman';support:SupportRequest['parameters'];
}
export interface SensitivityRequest {
 schema_version:1;protocol_version:'domains.browser_preprocessing_sensitivity.v1';
 dataset:ScopedDataset;manifest:ScopedManifestRow[];population:'train'|'unpartitioned';
 reference_keys:string[];query_keys:string[];x:ScopedSpectra;
 factors:FactorColumn[];dependencies:FactorColumn[];exclusion_field:string|null;
 access:{x:true;m_fields:string[];y_fields:string[]};plan:SensitivityPlan;
 stage:'reference_only'|'test_audit';frozen_reference:SensitivityResult|null;reuse_exact_prefixes:boolean;
}
export interface SensitivityRepresentation {
 id:string;family:string;steps:PreprocessingStep[];status:'computed'|'unavailable';reason:string|null;
 value:null|{
  source:ScopedDataset;axis:number[];axis_unit:string;original_axis_sha256:string;
  reference_matrix_sha256:string;query_matrix_sha256:string|null;
  transformations:Array<Record<string,unknown>>;
  structure:Record<string,unknown>;factors:Array<Record<string,unknown>>;
  support:Record<string,unknown>;comparisons:Record<string,unknown>;
 };
}
export interface SensitivityResult {
 schema_version:1;protocol_version:'domains.browser_preprocessing_sensitivity_result.v1';
 status:'computed';reason:null;dataset:ScopedDataset;population:'train'|'unpartitioned';
 stage:'reference_only'|'test_audit';plan:SensitivityPlan;plan_sha256:string;reference_input_sha256:string;
 input_sha256:string;evidence_sha256:string;representations:SensitivityRepresentation[];
 receipt:{provider:string;reference_keys:string[];query_keys:string[];test_x_accessed:boolean;
 y_accessed:false;x_predict_accessed:false;provider_calls:Array<Record<string,unknown>>;
 [key:string]:unknown};findings:Array<Record<string,unknown>>;limitations:string[];
}
