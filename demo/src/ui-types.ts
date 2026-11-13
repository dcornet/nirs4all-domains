/** Presentation contracts. Values and scientific statuses are supplied by the runtime adapter. */
export type Locale = 'en' | 'fr';
export type PredictionIntent = 'study' | 'known_acquisitions' | 'new_specimens' | 'new_groups' | 'new_context' | 'unknown';
export type EvidenceStatus = 'available' | 'unavailable' | 'conditional' | 'contradicted' | 'not_qualified' | 'not_tested' | 'computed' | 'supported';
export interface UiFinding {
  id: string; title: string; status: EvidenceStatus; observation: string;
  hypothesis: string; relevance: string; verification: string; limitation: string;
  confidence: string; evidenceIds: string[];
}
export interface UiEvidence {
  id: string; method: string; status: EvidenceStatus; reason: string | null;
  value: unknown; scope: string; provider: string;
}
export interface UiDataset {
  name: string; id: string; source: string; contentHash: string;
  observations: number; variables: number | null; axisUnit: string;
  axis: number[]; spectra: { id: string; values: (number | null)[]; group?: string }[];
  metadata: string[]; identity: string; provenance: string; license: string;
}
export interface UiResult {
  mode: 'live' | 'saved'; dataset: UiDataset; summary: string; protocol: string;
  findings: UiFinding[]; evidence: UiEvidence[];
  pca: { points: { id: string; x: number; y: number; group?: string }[];
    eigenvalues: number[]; totalVariance: number | null; xLabel: string; yLabel: string } | null;
  geometryReason: string | null; limitations: string[]; provenance: Record<string, unknown>;
}
export interface UiExample { id: string; name: string; description: string; mode: 'live' | 'saved'; dimensions: string; license: string; }
export interface UiState {
  phase: 'idle' | 'loading' | 'running' | 'cancelled' | 'error';
  progress: string; error: { code: string; message: string } | null;
  result: UiResult | null; examples: UiExample[]; intent: PredictionIntent;
  importHint: string;
  declarations?: UiDeclarations;
}
export interface UiDeclarations { population: string; prediction_unit: string; new_context: string; }
export interface UiCallbacks {
  onImport(files: File[]): void; onExample(id: string): void; onCancel(): void;
  onReset(): void; onIntent(intent: PredictionIntent): void;
  onExport(format: 'html' | 'markdown' | 'json', locale: Locale): void;
  onDeclaration?(key: keyof UiDeclarations, value: string): void;
}
export interface AppProps { state: UiState; callbacks: UiCallbacks; }
