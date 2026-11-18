/** Presentation contracts. Values and scientific statuses are supplied by the runtime adapter. */
import type {ExportSelection} from './report/selection';
import type {DatasetDraft,ReviewedImport} from './engine/import-draft';
import type {ScopedOperation} from '@nirs4all/domains';
import type {ScopeOptions} from './engine/scoped';
import type {FactorAssociationControlsProps,FactorAssociationRun} from './FactorAssociationControls';
import type {FactorResult} from '@nirs4all/domains';
import type {FactorColorLegendDescriptor} from './report/factor-colors';
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
  sensitivityResults?:import('./engine/preprocessing').SensitivityHistory[];
  sensitivityControls?:import('./SensitivityPanel').SensitivityControls;
  supportResults?:import('./engine/support').SupportRun[];
  factorControls?:Omit<FactorAssociationControlsProps,'busy'|'locale'|'onRun'|'onColor'|'onAuthorizeColorExport'|'onLoadInferencePlan'>;
  factorAssociations?:FactorResult[];
  factorLegend?:FactorColorLegendDescriptor;
  factorGroupColors?:Record<string,string>;
  mode: 'live' | 'saved'; dataset: UiDataset; summary: string; protocol: string;
  findings: UiFinding[]; evidence: UiEvidence[];
  pca: { points: { id: string; x: number; y: number; group?: string }[];
    eigenvalues: number[]; totalVariance: number | null; xLabel: string; yLabel: string; resolvedComponents?: number } | null;
  geometryReason: string | null; limitations: string[]; provenance: Record<string, unknown>;
}
export interface UiExample { id: string; name: string; description: string; mode: 'live' | 'saved'; dimensions: string; license: string; }
export interface UiState {
  importDraft?:DatasetDraft;
  phase: 'idle' | 'loading' | 'running' | 'cancelled' | 'error';
  progress: string; error: { code: string; message: string;diagnostic?:import('./engine/runtime-diagnostic').WorkerDiagnostic } | null;
  workerDiagnostic?:import('./engine/runtime-diagnostic').WorkerDiagnostic;
  canRetryImport?:boolean;
  result: UiResult | null; examples: UiExample[]; intent: PredictionIntent;
  importHint: string;
  declarations?: UiDeclarations;
  processingStage?: ProcessingStage;
}
export interface UiDeclarations { population: string; prediction_unit: string; new_context: string; }
export interface UiCallbacks {
  onSensitivity?(run:import('./engine/preprocessing').SensitivityRun):void;
  onRetryImport?():void;
  onSupport?(parameters:import('./engine/support').SupportParameters):void;
  onFactorInferencePlan?(file:File):void;
  onFactorAssociation?(request:FactorAssociationRun):void;
  onAssociationColor?(factorId:string):void;
  onAuthorizeFactorColorExport?(factorId:string,authorized:boolean):void;
  onConfirmImport?(config:ReviewedImport['config'],sources:ReviewedImport['sources']):void;
  onScopedOperation?(operation:ScopedOperation,options?:ScopeOptions):void;
  onColorFactor?(field:string):void;
  onImport(files: File[]): void; onExample(id: string): void; onCancel(): void;
  onReset(): void; onIntent(intent: PredictionIntent): void;
  onExport(format: 'html' | 'markdown' | 'json', locale: Locale, reading?: ReadingMode, selection?:ExportSelection): void;
  onDeclaration?(key: keyof UiDeclarations, value: string): void;
}
export interface AppProps { state: UiState; callbacks: UiCallbacks; }
