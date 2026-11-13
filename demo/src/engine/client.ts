import type { Operation, WorkerReply } from './types';

/** Killing the worker interrupts synchronous kernels; request IDs reject obsolete work. */
export class BrowserEngine {
  private worker: Worker | null = null;
  private sequence = 0;
  private pending: { id: number; resolve(value: unknown): void; reject(reason: Error): void; progress(stage: string): void; timer: ReturnType<typeof setTimeout> } | null = null;
  constructor(private factory: () => Worker = () => new Worker(new URL('./worker.ts', import.meta.url), { type: 'module' })) {}
  async request<T>(operation: Operation, payload: unknown, progress: (stage: string) => void = () => {}): Promise<T> {
    this.cancel();
    const id = ++this.sequence;
    this.worker = this.factory();
    return new Promise<T>((resolve, reject) => {
      this.pending = { id, resolve: value => resolve(value as T), reject, progress,
        timer: setTimeout(() => this.fail(new Error('WORKER_TIME_BUDGET_EXCEEDED')), 120_000) };
      this.worker!.onmessage = ({ data }: MessageEvent<WorkerReply>) => {
        if (!this.pending || data.id !== this.pending.id) return;
        if (data.stage) { this.pending.progress(data.stage); return; }
        const task = this.pending; this.pending = null; clearTimeout(task.timer);
        this.worker?.terminate(); this.worker = null;
        if (data.ok) task.resolve(data.result);
        else task.reject(Object.assign(new Error(data.error?.message ?? 'WORKER_ERROR'), { code: data.error?.code }));
      };
      this.worker!.onerror = event => this.fail(new Error(event.message || 'WORKER_LOADING_FAILED'));
      this.worker!.postMessage({ id, operation, payload });
    });
  }
  private fail(error: Error) {
    if (this.pending) { clearTimeout(this.pending.timer); this.pending.reject(error); this.pending = null; }
    this.worker?.terminate(); this.worker = null;
  }
  cancel() { this.sequence++; this.fail(Object.assign(new Error('CANCELLED'), { code: 'CANCELLED' })); }
}
