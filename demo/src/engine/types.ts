export type { BrowserRequest as BrowserInput, BrowserReport, Evidence as Slot } from '@nirs4all/domains';
import type { BrowserRequest as BrowserInput } from '@nirs4all/domains';
export interface LocalDataset {
  input: BrowserInput; metadata: { name: string; values: (string | number | null)[] }[];
  partitions: { name: string; observation_ids: string[] }[]; headers: string[];
  warnings: string[]; importSpec: unknown; identityOrigin: string; license: string;
  mode: 'user_computed_live' | 'synthetic_computed_live';
}
export interface InputFile { name: string; bytes: Uint8Array }
export type Operation = 'import' | 'analyze' | 'interpret';
export interface WorkerRequest { id: number; operation: Operation; payload: unknown }
export interface WorkerReply { id: number; ok: boolean; result?: unknown; stage?: string; error?: { code: string; message: string } }
