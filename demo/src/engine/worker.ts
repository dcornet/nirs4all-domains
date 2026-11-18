/// <reference lib="webworker" />
import { importFiles } from './dataset-io';
import {prepareImport,assembleImport,type ReviewedImport} from './import-draft';
import type {ScopedRequest,FactorRequest,SupportRequest,SensitivityRequest} from '@nirs4all/domains';
import type { BrowserInput, BrowserReport, InputFile, WorkerReply, WorkerRequest } from './types';
import type { PredictionIntent } from '../ui-types';

self.onmessage = async ({ data }: MessageEvent<WorkerRequest>) => {
  const { id, operation, payload } = data;
  const reply = (message: Omit<WorkerReply, 'id'>) => self.postMessage({ id, ...message });
  try {
    if(operation==='prepare_import'){
      reply({ok:true,stage:'Reviewing IO roles and declared partitions',stage_id:'import'});
      reply({ok:true,result:await prepareImport(payload as InputFile[])});return;
    }
    if(operation==='assemble_import'){
      const r=payload as ReviewedImport;
      reply({ok:true,stage:'Assembling reviewed X/Y/M with IO',stage_id:'import'});
      reply({ok:true,result:await assembleImport(r.draft,r.config,r.sources)});return;
    }
    if (operation === 'import') {
      reply({ ok: true, stage: 'Reading with IO / Formats WASM', stage_id: 'import' });
      reply({ ok: true, result: await importFiles(payload as InputFile[]) }); return;
    }
    reply({ ok: true, stage: 'Loading Domains Rust / Methods WASM', stage_id: 'prepare' });
    const { createDomainsRuntime } = await import('@nirs4all/domains');
    const runtime = await createDomainsRuntime();
    if(operation==='preprocessing_sensitivity'){
      reply({ok:true,stage:'Validating the frozen representation panel and executing reference-scoped Methods operations',stage_id:'compute'});
      reply({ok:true,result:runtime.analyzeSensitivity(payload as SensitivityRequest)});return;
    }
    if(operation==='train_fitted_support'){
      reply({ok:true,stage:'Fitting train reference and projecting test in Methods; no target access',stage_id:'compute'});
      reply({ok:true,result:runtime.analyzeSupport(payload as SupportRequest)});return;
    }
    if(operation==='factor_association'){
      reply({ok:true,stage:'Validating recorded PCA provenance and factor grants; no PCA fit',stage_id:'compute'});
      reply({ok:true,result:runtime.analyzeFactor(payload as FactorRequest)});return;
    }
    if(operation==='scoped'){
      reply({ok:true,stage:'Validating operation grants in Rust and executing permitted providers',stage_id:'compute'});
      reply({ok:true,result:runtime.analyzeScoped(payload as ScopedRequest)});return;
    }
    if (operation === 'interpret') {
      reply({ ok: true, stage: 'Reading the declared prediction objective; no fit', stage_id: 'interpret' });
      const request = payload as { report: BrowserReport; intent: PredictionIntent };
      reply({ ok: true, result: runtime.interpret(request.report, request.intent) }); return;
    }
    reply({ ok: true, stage: 'Validating the full-X request', stage_id: 'validate' });
    reply({ ok: true, stage: 'Computing complete-population X evidence', stage_id: 'compute' });
    reply({ ok: true, result: runtime.analyze(payload as BrowserInput) });
  } catch (error) {
    const value = error as { code?: string; message?: string };
    reply({ ok: false, error: { code: value.code ?? 'DOMAINS_WORKER_REFUSAL', message: value.message ?? String(error) } });
  }
};
