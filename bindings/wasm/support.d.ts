import type {ScopedRequest,ScopedMetadata} from './scoped.js';
import type {Evidence} from './index.js';
export interface SupportParameters {
  n_components:number; monitoring:boolean; max_components:number; n_folds:number; alpha:number;
}
export interface SupportLimitPlan {
  protocol_version:'domains.monitor_indexed_folds_design.v1'; dataset_content_sha256:string;
  reference_keys:string[]; max_components:number; n_folds:number; alpha:number;
  independent_unit_ids:string[]; indivisible_dependency_fields:string[];
  source:string; prospective:boolean; row_index_modulo_folds_authorized:boolean;
}
export interface SupportRequest {
  schema_version:1; protocol_version:'domains.browser_train_fitted_support.v1'; fit:'train';
  scope:ScopedRequest; parameters:SupportParameters; dependencies:ScopedMetadata[];
  dependency_fields:string[]; external_limit_plan:SupportLimitPlan|null;
}
export interface SupportProjection {
  train_scores:number[][]; test_scores:number[][]; components:number; display_components:number[];
  component_summaries:Array<{component:number;summary:Evidence<Record<string,unknown>>}>;
  fit_state_sha256:string; fit_identity_sha256:string; fitted_state_unchanged:boolean;
  reference_variance:Evidence; numerical_rank:Evidence; basis:string;
}
export interface SupportMonitor {
  [key:string]:unknown;
  eigenvalues:Array<number|null>; effective_components:number;
  reference_t2:Array<number|null>; reference_q:Array<number|null>;
  monitored_t2:Array<number|null>; monitored_q:Array<number|null>;
  n_beyond_t2:number; n_beyond_q:number; n_beyond_either:number;
  n_near_t2:number; n_near_q:number; n_near_either:number;
  t2_limit:number|null; q_limit:number|null; tolerance:number|null; condition:number|null;
  q_tolerance_scale:number|null; eigenvalue_resolution:number|null;
  reference_total_variance:number|null; monitored_total_variance:number|null;
  centroid_distance:number|null; centroid_subspace_distance:number|null;
  centroid_residual_distance:number|null; centroid_t2:number|null; retained_fraction:number|null;
}
export interface SupportResult {
  protocol_version:'domains.browser_train_fitted_support_result.v1';
  status:'computed'|'partial'|'unavailable'; reason:string|null;
  projection:Evidence<SupportProjection>;
  monitoring:{status:Evidence['status']|'not_requested';reason:string|null;value:SupportMonitor|null};
  limit_qualification:{status:'unknown'|'not_qualified'|'conditional_external';reasons:string[];
    source:string|null;fold_scheme:'row_index_modulo_n_folds';independent_units_certified:false;interpretation:string};
  dependence:Record<string,unknown>; receipt:Record<string,unknown>;
  supported_claims:string[]; limitations:string[]; evidence_sha256:string;
}
