import type { Operation, WorkerReply } from './types';
import type { ProcessingStage } from '../ui-types';

/** Killing the worker interrupts synchronous kernels; request IDs reject obsolete work. */
export class BrowserEngine {
  private worker: Worker | null = null;
  private sequence = 0;
  private pending: { id: number; resolve(value: unknown): void; reject(reason: Error): void; progress(stage: string, step?: ProcessingStage): void; timer: ReturnType<typeof setTimeout> } | null = null;
  constructor(private factory: () => Worker = () => new Worker(new URL('./worker.ts', import.meta.url), { type: 'module' })) {}
  async request<T>(operation: Operation, payload: unknown, progress: (stage: string, step?: ProcessingStage) => void = () => {}): Promise<T> {
    this.cancel();
    const id = ++this.sequence;
    const worker = this.factory();
    this.worker = worker;
    const current = () => this.worker === worker && this.pending?.id === id;
    return new Promise<T>((resolve, reject) => {
      this.pending = { id, resolve: value => resolve(value as T), reject, progress,
        timer: setTimeout(() => { if (current()) this.fail(new Error('WORKER_TIME_BUDGET_EXCEEDED')); }, 120_000) };
      worker.onmessage = ({ data }: MessageEvent<WorkerReply>) => {
        if (!current()) return;
        if (!data || typeof data.id !== 'number' || typeof data.ok !== 'boolean') { this.fail(new Error('WORKER_INVALID_REPLY')); return; }
        if (data.id !== id) return;
        if ('stage' in data) {
          if (typeof data.stage !== 'string' || !data.stage || !data.ok) { this.fail(new Error('WORKER_INVALID_REPLY')); return; }
          try { this.pending!.progress(data.stage, data.stage_id); }
          catch (error) { this.fail(error instanceof Error ? error : new Error(String(error))); }
          return;
        }
        if (data.ok && !('result' in data)) { this.fail(new Error('WORKER_INVALID_REPLY')); return; }
        const task = this.pending!; this.pending = null; clearTimeout(task.timer);
        worker.terminate(); this.worker = null;
        if (data.ok) task.resolve(data.result);
        else task.reject(Object.assign(new Error(data.error?.message ?? 'WORKER_ERROR'), { code: data.error?.code }));
      };
      worker.onerror = event => { if (current()) this.fail(new Error(event.message || 'WORKER_LOADING_FAILED')); };
      worker.onmessageerror = () => { if (current()) this.fail(new Error('WORKER_MESSAGE_DESERIALIZATION_FAILED')); };
      try {
        // Main owns browser File objects; these fresh byte buffers are consumed by
        // import. Transfer once instead of cloning, without changing their bytes.
        const buffers = (operation === 'import'||operation==='prepare_import') && Array.isArray(payload)
          ? [...new Set(payload.flatMap(file => file?.bytes instanceof Uint8Array && file.bytes.buffer instanceof ArrayBuffer ? [file.bytes.buffer] : []))] : [];
        worker.postMessage({ id, operation, payload }, buffers);
      } catch (error) { if (current()) this.fail(error instanceof Error ? error : new Error(String(error))); }
    });
  }
  private fail(error: Error) {
    if (this.pending) { clearTimeout(this.pending.timer); this.pending.reject(error); this.pending = null; }
    this.worker?.terminate(); this.worker = null;
  }
  cancel() { this.sequence++; this.fail(Object.assign(new Error('CANCELLED'), { code: 'CANCELLED' })); }
}
