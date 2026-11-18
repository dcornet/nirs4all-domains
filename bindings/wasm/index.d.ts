import type {ScopedMetadata} from './scoped.js';
import type {SupportRequest,SupportResult} from './support.js';
export type {SupportRequest,SupportResult,SupportParameters,SupportLimitPlan,SupportProjection,SupportMonitor} from './support.js';
export type PredictionIntent = 'study' | 'known_acquisitions' | 'new_specimens' | 'new_groups' | 'new_context' | 'unknown';
export interface BrowserRequest {
  schema_version: 1;
  dataset_id: string;
  source_id: string;
  content_sha256: string;
  observation_ids: string[];
  axis: number[];
  axis_unit: string;
  spectra: number[][];
  group_ids?: string[];
  prediction_intent?: PredictionIntent;
}
export interface Evidence<T = unknown> {
  status: 'computed' | 'unavailable' | 'unsupported' | 'error';
  reason: string | null;
  value: T | null;
}
export interface PcaEvidence {
  scores: number[][];
  eigenvalues: number[];
  full_moments: [number,number];
  resolution: number;
  unresolved: boolean[];
  n_components_requested: number;
  n_components_resolved: number;
  backend_version: string;
  scope: string;
}
export interface DensityEvidence {
  labels: number[];
  membership: number[];
  n_clusters: number;
  noise_count: number;
  persistence: number[];
  persistence_summary: Evidence;
  min_cluster_size: number;
  min_samples: number;
  backend_version: string;
  qualification: string;
  support_unit: string;
}
export interface BrowserReading {
  protocol_version: 'domains.browser_reading.v1';
  prediction_intent: PredictionIntent;
  declaration_only: true;
  conditional_scenarios: {intended_use:'study'|'new_specimens'|'new_context';question:string;not_established:string}[];
  boundaries: {physical_independence_verified:false;predictive_performance_established:false;universally_preferred_split:null;authorization_granted:false;new_execution:false};
  evidence_sha256: string;
  scope: Record<string,unknown>;
  observation: string;
  confidence: string;
  consequence: string;
  action: string;
  readiness: Evidence;
  execution: 'not_executed';
  qualification: string;
}
export interface BrowserReport {
  schema_version: 1;
  protocol_version: 'domains.browser_x.v1';
  engine_version: string;
  status: 'computed';
  scope: Record<string,unknown>;
  input_sha256: string;
  evidence_sha256: string;
  metrics: {
    pca: Evidence<PcaEvidence>;
    density: Evidence<DensityEvidence>;
    raw_neighbors: Evidence;
    projected_neighbors: Evidence;
    metadata_factor_association: Evidence;
    resampling_stability: Evidence;
    parameter_sensitivity: Evidence;
    predictive_performance: Evidence;
  };
  capabilities: Capability[];
  findings: {observation:string;confidence:string;consequence:string;action:string}[];
  interpretation: BrowserReading;
  test_target_accessed: false;
  raw_spectra_included: false;
  limitations: string[];
}
export interface Capability { capability_id: string; available: boolean; qualified: boolean; reason: string | null }
export interface DomainsRuntime {
  analyzeSupport(input:SupportRequest):SupportResult;
  analyzeSupportJson(text:string):string;
  analyzeFactor(input: FactorRequest): FactorResult;
  analyzeFactorJson(text:string):string;
  analyzeScoped(input: import('./scoped.js').ScopedRequest): import('./scoped.js').ScopedResult;
  analyzeScopedJson(text:string):string;
  analyze(input: BrowserRequest): BrowserReport;
  analyzeJson(text: string): string;
  validate(input: BrowserRequest): {valid:true};
  interpret(report: BrowserReport,intent: PredictionIntent): BrowserReading;
  capabilities(): Capability[];
  provider: { name:string;version:string;abi:number[] };
}
export function createDomainsRuntime(options?: {wasmModule?:BufferSource | WebAssembly.Module}): Promise<DomainsRuntime>;
/** Requires the Domains WASM initialized by createDomainsRuntime; invokes no provider or fit. */
export function interpret(report: BrowserReport,intent: PredictionIntent): BrowserReading;
export type {ScopedRequest,ScopedResult,ScopedOperation,ScopedMetadata,PartitionRole} from './scoped.js';

export type FactorJson = null | boolean | number | string | FactorJson[] | FactorJsonObject;
export interface FactorJsonObject { [key:string]: FactorJson }
export type FactorPopulation = 'train' | 'unpartitioned' | 'global_transductive';
export interface FactorColumn extends ScopedMetadata {
  unit:string|null;
}
export interface FactorExternalEvidence {
  uri:string; content_sha256:string; qualification:string; basis:string;
}
export interface FactorInferencePlan {
  protocol_version:'domains.factor_exchangeability.v1'; population:FactorPopulation;
  dataset_content_sha256:string; pca_evidence_sha256:string;
  external_evidence:FactorExternalEvidence;
  unit_field:string; unit_kind:'specimen'|'independent_acquisition'; dependency_fields:string[];
  no_other_dependencies:boolean; selection:'prospective'; factor_ids:string[];
  components:'all_resolved'; missingness:'complete_units'; null_model:'unrestricted_exchangeability_given_fitted_x';
}
export interface FactorRequest {
  schema_version:1; protocol_version:'domains.browser_factor_association.v1';
  dataset:import('./scoped.js').ScopedRequest['dataset'];
  manifest:import('./scoped.js').ScopedRequest['manifest'];
  population:FactorPopulation;
  pca:{report:BrowserReport|FactorJsonObject;row_keys:string[];fit_receipt:FactorJsonObject|null};
  factors:FactorColumn[]; dependencies:FactorColumn[];
  access:{x:false;m_fields:string[];y_fields:never[]};
  representation:'raw'; explicit_transductive:boolean; components:'all_resolved';
  correlation_method:'pearson'|'spearman';
  inference:{mode:'descriptive'|'exact_if_qualified';plan:FactorInferencePlan|null};
  parameters:{preset:'f41_factor_pc_v1'};
}
export interface FactorLevelCount {
  level_id:string; value:string|number|boolean; label:string; count:number;
}
export interface FactorComponent {
  component:number; n_used:number;
  descriptive:Evidence<{measure:'eta_squared'|'pearson_r'|'spearman_rho';estimate:number;owner_output:FactorJsonObject}>;
  inference:Evidence<{qualification:'conditional_on_supplied_external_exchangeability_record';test:'exact_eta_squared'|'exact_absolute_correlation';owner_exact:FactorJsonObject;holm_adjusted_p:number;family_size:number;external_evidence:FactorExternalEvidence|null}>;
  exact_owner_evidence:Evidence<FactorJsonObject>;
}
export interface FactorResultColumn {
  factor_id:string; kind:FactorColumn['kind']; role:string; unit:string|null;
  origin:string; evidence:FactorColumn['evidence']; derived_from_target:boolean|null;
  n_fit_observations:number; n_used:number; n_missing:number; used_keys_sha256:string;
  values_sha256:string; n_levels:number|null; level_counts:FactorLevelCount[]|null;
  range:Evidence<{min:number;max:number}>; owner_summary:Evidence<FactorJsonObject>;
  warnings:string[]; components:FactorComponent[];
}
export interface FactorResult {
  protocol_version:'domains.browser_factor_association_result.v1';
  status:'computed'; reason:null;
  value:{
    population:FactorPopulation; representation:'recorded raw-PCA scores'; pca_id:string; scores_sha256:string;
    analysis_unit:{calculation_unit:'observations/acquisitions';n_observations:number;n_independent_units:number|null;physical_independence_verified_by_domains:false;qualification:string};
    inference:{level:'conditionally_admissible'|'descriptive_only'|'unqualified';reason:string|null;family:{factor_ids:string[];components:string;correction:'holm';external_evidence:FactorExternalEvidence}|null;no_global_risk_or_causal_claim:true};
    factors:FactorResultColumn[];
    dependency_audit:{fields:FactorJsonObject[];pairwise_context_tables:FactorJsonObject[];qualification:string};
  };
  receipt:FactorJsonObject; supported_claims:string[]; limitations:string[]; action:string;
}
