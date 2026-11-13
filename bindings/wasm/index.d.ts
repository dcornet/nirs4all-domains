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
