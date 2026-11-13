import { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import { BrowserEngine } from './engine/client';
import { MAX_IMPORT_BYTES, MAX_IMPORT_FILES } from './engine/dataset-io';
import type { BrowserReport, LocalDataset } from './engine/types';
import type { BrowserReading } from '@nirs4all/domains';
import { examples, synthetic } from './examples';
import { liveView, reportModel, savedView } from './report/model';
import { loadPublicSaved, validateSaved } from './report/saved';
import { downloadReport } from './report/export';
import type { UiCallbacks, UiState, PredictionIntent } from './ui-types';

function Controller() {
  const [state, setState] = useState<UiState>({ phase: 'idle', progress: '', error: null, result: null,
    examples, intent: 'unknown', importHint: 'X-only CSV/TSV, or supported spectral files; optional explicit IO configuration. Nothing is uploaded.',
    declarations: { population: '', prediction_unit: '', new_context: '' } });
  const engine = useRef(new BrowserEngine());
  const epoch = useRef(0);
  const dataset = useRef<LocalDataset | null>(null);
  const scientific = useRef<unknown>(null);
  const selectedExample = useRef<string | null>(null);
  useEffect(() => () => engine.current.cancel(), []);
  const start = () => { const token = ++epoch.current; engine.current.cancel(); setState(s => ({ ...s, result: null, error: null, phase: 'loading', progress: 'Preparing local data' })); return token; };
  const progress = (token: number) => (stage: string) => { if (token === epoch.current) setState(s => ({ ...s, progress: stage })); };
  const failed = (token: number, error: unknown) => {
    if (token !== epoch.current) return;
    const e = error as { code?: string; message?: string };
    setState(s => ({ ...s, phase: 'error', error: { code: e.code ?? 'LOCAL_ANALYSIS_REFUSED', message: e.message ?? String(error) } }));
  };
  const analyze = async (data: LocalDataset, token: number) => {
    if (token !== epoch.current) return;
    dataset.current = data;
    setState(s => ({ ...s, phase: 'running' }));
    const report = await engine.current.request<BrowserReport>('analyze', { ...data.input, prediction_intent: state.intent }, progress(token));
    if (token !== epoch.current) return;
    scientific.current = report;
    setState(s => ({ ...s, phase: 'idle', result: liveView(report, data), progress: '' }));
  };
  const callbacks: UiCallbacks = {
    async onImport(files) {
      const token = start(); selectedExample.current = null;
      try {
        if (files.length > MAX_IMPORT_FILES || files.reduce((n, f) => n + f.size, 0) > MAX_IMPORT_BYTES) throw new Error('IMPORT_BYTE_OR_FILE_BUDGET_EXCEEDED: maximum 8 MiB and 32 files; no silent sampling.');
        if (files.length === 1 && /\.json$/i.test(files[0].name) && !files[0].name.endsWith('.nirs4all.json')) {
          const source = JSON.parse(await files[0].text()); validateSaved(source);
          if (token !== epoch.current) return;
          const view = savedView(source); view.provenance.source_mode = 'user_saved_schema_validated';
          view.dataset.provenance = 'User-supplied saved evidence; structural validation only';
          view.dataset.license = 'Retain the supplied source terms; no redistribution permission is inferred';
          view.findings.forEach(finding => { finding.confidence = 'Declared by the supplied report; not independently authenticated'; });
          view.provenance.source_qualification = 'User-supplied saved evidence; schema validated, authorship and numerical qualification not authenticated.';
          view.limitations.push('Imported saved report: structural validation is not a new scientific analysis or source-authenticity check.');
          scientific.current = source; dataset.current = null;
          setState(s => ({ ...s, phase: 'idle', result: view })); return;
        }
        const payload = await Promise.all(files.map(async file => ({ name: file.webkitRelativePath || file.name, bytes: new Uint8Array(await file.arrayBuffer()) })));
        if (token !== epoch.current) return;
        const data = await engine.current.request<LocalDataset>('import', payload, progress(token));
        await analyze(data, token);
      } catch (error) { failed(token, error); }
    },
    async onExample(id) {
      const token = start(); selectedExample.current = id;
      try {
        if (id === 'tablet-saved') {
          const source = await loadPublicSaved(state.intent);
          if (token !== epoch.current) return;
          scientific.current = source; dataset.current = null;
          setState(s => ({ ...s, phase: 'idle', result: savedView(source) }));
        } else await analyze(await synthetic(id), token);
      } catch (error) { failed(token, error); }
    },
    onCancel() { ++epoch.current; engine.current.cancel(); scientific.current = null; dataset.current = null;
      setState(s => ({ ...s, phase: 'cancelled', result: null, progress: '' })); },
    onReset() { ++epoch.current; engine.current.cancel(); scientific.current = null; dataset.current = null; selectedExample.current = null;
      setState(s => ({ ...s, phase: 'idle', result: null, error: null, progress: '' })); },
    async onIntent(intent: PredictionIntent) {
      const token = ++epoch.current; engine.current.cancel();
      setState(s => ({ ...s, intent, error: null }));
      if (!scientific.current) return;
      try {
        if (selectedExample.current === 'tablet-saved') {
          const source = await loadPublicSaved(intent);
          if (token !== epoch.current) return;
          scientific.current = source; setState(s => ({ ...s, result: savedView(source) })); return;
        }
        if (!dataset.current) {
          setState(s => ({ ...s, error: { code: 'SAVED_DECLARATION_ONLY', message: 'The new intention is recorded as a user declaration. Imported original companions remain unchanged; regenerate them through the qualified Domains API to obtain another saved reading.' } })); return;
        }
        const report = scientific.current as BrowserReport;
        const reading = await engine.current.request<BrowserReading>('interpret', { report, intent });
        if (token !== epoch.current) return;
        const updated = { ...report, interpretation: reading };
        scientific.current = updated;
        setState(s => ({ ...s, result: liveView(updated, dataset.current!) }));
      } catch (error) { failed(token, error); }
    },
    onDeclaration(key, value) { setState(s => ({ ...s, declarations: { ...s.declarations!, [key]: value } })); },
    onExport(format, locale) {
      if (!state.result || !scientific.current) return;
      downloadReport(reportModel(state.result, scientific.current, state.intent, locale, state.declarations), format);
    },
  };
  return <App state={state} callbacks={callbacks} />;
}

createRoot(document.getElementById('root')!).render(<Controller />);
