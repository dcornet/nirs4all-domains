export type { BrowserRequest as BrowserInput, BrowserReport, Evidence as Slot } from '@nirs4all/domains';
import type { BrowserRequest as BrowserInput } from '@nirs4all/domains';
import type { ProcessingStage } from '../ui-types';
export type ImportedValue = string | number | boolean | null;
export type PartitionRole = 'train' | 'test' | 'predict' | 'unpartitioned';
export type MetadataRole = 'observation_id' | 'specimen' | 'group' | 'reference' | 'repetition' | 'instrument' | 'campaign' | 'factor' | 'partition' | 'unknown';
export interface ImportedMetadata {
  name: string; values: ImportedValue[];
  role?: MetadataRole; type?: 'numeric' | 'categorical' | 'boolean' | 'unknown';
  unit?: string | null; origin?: string; derived_from_target?: boolean | 'unknown';
  evidence?: 'declared' | 'unknown';
}
export interface ImportedTarget {
  name: string; type: 'numeric' | 'categorical'; unit: string | null;
  values: (number | string | null)[]; mask: boolean[]; origin: string;
}
export interface ImportedRow {
  key: string; observation_id: string | null; partition: PartitionRole;
  original_partition: string; source_id: string;
}
export interface LocalDataset {
  input: BrowserInput; metadata: ImportedMetadata[];
  partitions: { name: string; observation_ids: string[] }[]; headers: string[];
  warnings: string[]; importSpec: unknown; identityOrigin: string; license: string;
  mode: 'user_computed_live' | 'synthetic_computed_live';
  /** F4 import storage. Scientific requests must project an authorized population. */
  rawX?: (number | null)[][]; missingX?: boolean[][]; targets?: ImportedTarget[];
  rowManifest?: ImportedRow[];
  importProvenance?: { protocol: 'domains.import_xy_m.v1'; files: { name: string; sha256: string }[];
    file_content_sha256?: string; reviewed_spec_sha256?: string;
    original_source_ids: string[]; roles_reviewed: boolean; identity_independence: 'unknown' };
}
export interface InputFile { name: string; bytes: Uint8Array }
export type Operation = 'import' | 'prepare_import' | 'assemble_import' | 'analyze' | 'scoped' | 'factor_association' | 'train_fitted_support' | 'interpret';
export interface WorkerRequest { id: number; operation: Operation; payload: unknown }
export interface WorkerReply { id: number; ok: boolean; result?: unknown; stage?: string; stage_id?: ProcessingStage;
 lifecycle_event?:string;component?:string;error?: { code: string; message: string;details?:{code:string;phase?:string;component?:string;asset?:unknown;original_message_available?:boolean} } }
