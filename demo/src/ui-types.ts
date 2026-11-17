/** Presentation contracts. Values and scientific statuses are supplied by the runtime adapter. */
export type Locale = 'en' | 'fr';
export type ReadingMode = 'summary' | 'complete';
export type ProcessingStage = 'prepare' | 'import' | 'validate' | 'compute' | 'interpret' | 'report';
export type PredictionIntent = 'study' | 'known_acquisitions' | 'new_specimens' | 'new_groups' | 'new_context' | 'unknown';
export type EvidenceStatus = 'observed' | 'available' | 'unavailable' | 'conditional' | 'contradicted' | 'not_qualified' | 'not_tested' | 'computed' | 'supported' | 'unsupported' | 'error';
export interface UiFinding {
  id: string; title: string; status: EvidenceStatus; observation: string;
  hypothesis: string; relevance: string; verification: string; limitation: string;
  confidence: string; evidenceIds: string[];
  prerequisites?: string[]; execution?: unknown;
}
export interface UiEvidence {
  id: string; method: string; status: EvidenceStatus; reason: string | null;
  value: unknown; scope: string; provider: string;
  representation?: string; pointer?: string;
}
export interface UiDataset {
  name: string; id: string; source: string; contentHash: string;
  observations: number | null; variables: number | null; axisUnit: string;
  axis: number[]; spectra: { id: string; values: (number | null)[]; group?: string }[];
  metadata: string[]; identity: string; provenance: string; license: string;
  representation?: string; population?: string;
}
export interface UiResult {
  mode: 'live' | 'saved'; dataset: UiDataset; summary: string; protocol: string;
  findings: UiFinding[]; evidence: UiEvidence[];
  pca: { points: { id: string; x: number; y: number; group?: string }[];
    eigenvalues: number[]; totalVariance: number | null; xLabel: string; yLabel: string; resolvedComponents?: number } | null;
  geometryReason: string | null; limitations: string[]; provenance: Record<string, unknown>;
}
export interface UiExample { id: string; name: string; description: string; mode: 'live' | 'saved'; dimensions: string; license: string; }
export interface UiState {
  phase: 'idle' | 'loading' | 'running' | 'cancelled' | 'error';
  progress: string; error: { code: string; message: string } | null;
  result: UiResult | null; examples: UiExample[]; intent: PredictionIntent;
  importHint: string;
  declarations?: UiDeclarations;
  processingStage?: ProcessingStage;
}
export interface UiDeclarations { population: string; prediction_unit: string; new_context: string; }
export interface UiCallbacks {
  onImport(files: File[]): void; onExample(id: string): void; onCancel(): void;
  onReset(): void; onIntent(intent: PredictionIntent): void;
  onExport(format: 'html' | 'markdown' | 'json', locale: Locale, reading?: ReadingMode): void;
  onDeclaration?(key: keyof UiDeclarations, value: string): void;
}
export interface AppProps { state: UiState; callbacks: UiCallbacks; }
