/// <reference lib="webworker" />
import { importFiles } from './dataset-io';
import type { BrowserInput, BrowserReport, InputFile, WorkerReply, WorkerRequest } from './types';
import type { PredictionIntent } from '../ui-types';

self.onmessage = async ({ data }: MessageEvent<WorkerRequest>) => {
  const { id, operation, payload } = data;
  const reply = (message: Omit<WorkerReply, 'id'>) => self.postMessage({ id, ...message });
  try {
    if (operation === 'import') {
      reply({ ok: true, stage: 'Reading with IO / Formats WASM' });
      reply({ ok: true, result: await importFiles(payload as InputFile[]) }); return;
    }
    reply({ ok: true, stage: 'Loading Domains Rust / Methods WASM' });
    const { createDomainsRuntime } = await import('@nirs4all/domains');
    const runtime = await createDomainsRuntime();
    if (operation === 'interpret') {
      const request = payload as { report: BrowserReport; intent: PredictionIntent };
      reply({ ok: true, result: runtime.interpret(request.report, request.intent) }); return;
    }
    reply({ ok: true, stage: 'Computing complete-population X evidence' });
    reply({ ok: true, result: runtime.analyze(payload as BrowserInput) });
  } catch (error) {
    const value = error as { code?: string; message?: string };
    reply({ ok: false, error: { code: value.code ?? 'DOMAINS_WORKER_REFUSAL', message: value.message ?? String(error) } });
  }
};
