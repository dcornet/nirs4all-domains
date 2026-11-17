import type {BrowserReport} from './index.js';
export type ScopedOperation = 'integrity_audit'|'train_structure'|'metadata_factor_audit'|'cross_partition_metadata_audit'|'train_reference_test_query'|'global_descriptive_transductive';
export type PartitionRole = 'train'|'test'|'predict'|'unpartitioned';
export interface ScopedMetadata {
  name:string; role:string; kind:'categorical'|'continuous'|'unknown'; origin:string;
  derived_from_target:boolean|null; evidence:'declared'|'verified'|'unknown';
  row_keys:string[]; values:(string|number|boolean|null)[];
}
export interface ScopedRequest {
  schema_version:1; protocol_version:'domains.browser_scoped_analysis.v1';
  operation:ScopedOperation; diagnostic:'exact_spectra'|'declared_identities'|null;
  dataset:{dataset_id:string;source_id:string;content_version:string;content_sha256:string};
  manifest:{key:string;partition:PartitionRole}[];
  reference_keys:string[]; query_keys:string[];
  access:{x:boolean;m_fields:string[];y_fields:never[]};
  fit:'none'|'train'|'transductive'; representation:'raw';
  selection_context:'pre_selection_integrity_audit'|'post_evaluation_explanation'|'unspecified';
  explicit_transductive:boolean; parameters:{preset:'f4_fixed_raw_v1'};
  exclusion_field:string|null;
  x:{row_keys:string[];matrix:(number|null)[][];axis:number[];axis_unit:string}|null;
  metadata:ScopedMetadata[];
}
export interface ScopedResult {
  protocol_version:'domains.browser_scoped_result.v1'; operation:ScopedOperation;
  diagnostic:string|null; status:'computed'|'unavailable'|'unsupported'|'error';
  reason:string|null; value:{structure?:BrowserReport;[key:string]:unknown}|null;
  receipt:Record<string,unknown>;
  supported_claims:string[]; limitations:string[]; action:string;
}
