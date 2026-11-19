import {describe,it,expect,vi} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {TechnicalDiagnostic,copyTechnicalDiagnostic} from './TechnicalDiagnostic';
import {makeWorkerDiagnostic} from '../engine/runtime-diagnostic';
describe('Local explicit diagnostic UX',()=>{
 it('localizes controls, distinguishes unknown cause, and only offers reload for an explicit reload remediation',()=>{
  const d=makeWorkerDiagnostic({operation:'prepare_import',phase:'BOOTSTRAP_STARTED',lastConfirmedPhase:'WORKER_CREATED',code:'WORKER_STARTUP_CAUSE_UNAVAILABLE'}),retry=vi.fn(),reload=vi.fn();
  const en=renderToStaticMarkup(<TechnicalDiagnostic diagnostic={d} locale="en" error onRetryImport={retry} onReload={reload}/>),fr=renderToStaticMarkup(<TechnicalDiagnostic diagnostic={d} locale="fr" error/>);
  expect(en).toContain('Last confirmed phase');expect(en).toContain('did not reveal');expect(en).toContain('Copy technical diagnostic');expect(en).not.toContain('Reload application');expect(fr).toContain('Copier le diagnostic technique');expect(retry).not.toHaveBeenCalled();expect(reload).not.toHaveBeenCalled();
  const missing=makeWorkerDiagnostic({operation:'prepare_import',phase:'IO_RUNTIME_LOADING',lastConfirmedPhase:'BOOTSTRAP_READY',code:'WASM_ASSET_UNAVAILABLE'});expect(renderToStaticMarkup(<TechnicalDiagnostic diagnostic={missing} locale="en" error/>)).toContain('Reload application');
 });
 it('does not label confirmed loading progress as a runtime refusal',()=>{const d=makeWorkerDiagnostic({operation:'prepare_import',phase:'BOOTSTRAP_READY',lastConfirmedPhase:'BOOTSTRAP_READY',code:'WORKER_BOOTSTRAP_READY'});expect(renderToStaticMarkup(<TechnicalDiagnostic diagnostic={d} locale="en"/>)).not.toContain('Run refused');});
 it('copies only reprojected public diagnostic JSON in an explicit local action',async()=>{
  const d=makeWorkerDiagnostic({operation:'prepare_import',phase:'IO_RUNTIME_LOADING',lastConfirmedPhase:'BOOTSTRAP_READY',code:'IO_INITIALIZATION_FAILED',originalMessage:'PRIVATE_X_Y_M'}),write=vi.fn().mockResolvedValue(undefined);
  expect(write).not.toHaveBeenCalled();await copyTechnicalDiagnostic({...d,raw:'PRIVATE_X_Y_M'} as any,write);expect(write).toHaveBeenCalledTimes(1);expect(write.mock.calls[0][0]).not.toContain('PRIVATE_X_Y_M');expect(JSON.parse(write.mock.calls[0][0]).protocol_version).toBe('domains.worker_diagnostic.v1');
 });
});
