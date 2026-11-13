import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { App } from '../App';
import { Workspace } from '../Workspace';
import { Landing } from '../Landing';
import { translator } from '../i18n';
import type { Locale, UiCallbacks, UiResult, UiState } from '../ui-types';

const callbacks: UiCallbacks = {
  onImport: vi.fn(), onExample: vi.fn(), onCancel: vi.fn(), onReset: vi.fn(),
  onIntent: vi.fn(), onExport: vi.fn(), onDeclaration: vi.fn(),
};
const result: UiResult = {
  mode: 'saved', protocol: 'saved.test.v1', summary: 'Saved evidence only.',
  dataset: { name: '<script>alert(1)</script>', id: 'test', source: 'public fixture', contentHash: 'abc',
    observations: 4, variables: null, axisUnit: '', axis: [], spectra: [], metadata: [],
    identity: 'Unknown physical identity', provenance: 'Test evidence', license: 'Test fixture' },
  findings: [{ id: 'contradicted', title: 'Contradictory evidence', status: 'contradicted',
    observation: 'A frozen observation.', hypothesis: 'An unverified explanation.', relevance: 'Only if this use applies.',
    verification: 'A check that has not been executed.', limitation: 'No independent validation.', confidence: 'unknown', evidenceIds: ['missing'] }],
  evidence: [{ id: 'missing', method: 'Unsupported provider', status: 'unavailable', reason: 'PROVIDER_NOT_AVAILABLE',
    value: null, scope: 'X only', provider: 'not configured' }],
  pca: null, geometryReason: 'No score coordinates transported.', limitations: ['No calibration was fitted.'], provenance: { mode: 'saved' },
};
const renderWorkspace = (locale: Locale) => renderToStaticMarkup(<Workspace result={result} intent="new_context" declarations={{ population: 'Target <population>', prediction_unit: 'specimen', new_context: 'new study' }} callbacks={callbacks} locale={locale} t={translator(locale)}/>);
const idleState: UiState = { phase: 'idle', progress: '', error: null, result: null, examples: [], intent: 'unknown', importHint: 'CSV / TSV' };

describe('Domains presentation contracts', () => {
  it('keeps saved, unavailable and contradicted evidence explicit without numerical substitutes', () => {
    const html = renderWorkspace('en');
    expect(html).toContain('Saved evidence · no new calculation');
    expect(html).toContain('status-contradicted');
    expect(html).toContain('status-unavailable');
    expect(html).toContain('PROVIDER_NOT_AVAILABLE');
    expect(html).toContain('No score coordinates transported.');
    expect(html).toContain('Not carried</strong> Variables');
    expect(html).not.toContain('>0</strong> Variables');
  });

  it('preserves observation, hypothesis, conditional check and execution limits separately', () => {
    const html = renderWorkspace('en');
    expect(html).toContain('A frozen observation.');
    expect(html).toContain('An unverified explanation.');
    expect(html).toContain('Only if this use applies.');
    expect(html).toContain('A check that has not been executed.');
    expect(html).toContain('No independent validation.');
    expect(html).toContain('It does not change measurements, fit a model or evaluate a validation split.');
    expect(html).toContain('Optional user declarations, not verified evidence.');
  });

  it('localizes guidance and status labels without rewriting canonical source evidence', () => {
    const html = renderWorkspace('fr');
    expect(html).toContain('Preuves enregistrées · aucun nouveau calcul');
    expect(html).toContain('Non transporté</strong> Variables');
    expect(html).toContain('Contredit');
    expect(html).toContain('Indisponible');
    expect(html).toContain('Population cible');
    expect(html).toContain('Unité de prédiction');
    expect(html).toContain('Nouveau contexte d’acquisition ou d’étude');
    expect(html).toContain('A frozen observation.');
  });

  it('escapes source and declaration text and exposes evidence anchor navigation', () => {
    const html = renderWorkspace('en');
    expect(html).toContain('&lt;script&gt;alert(1)&lt;/script&gt;');
    expect(html).not.toContain('<script>alert(1)</script>');
    expect(html).toContain('Target &lt;population&gt;');
    expect(html).toContain('href="#evidence-missing"');
    expect(html).toContain('id="evidence-missing"');
  });

  it('renders a keyboard reachable local import and labels the hero as illustration', () => {
    const html = renderToStaticMarkup(<Landing state={idleState} callbacks={callbacks} t={translator('en')} busy={false}/>);
    expect(html).toContain('Drop your files here, or choose files');
    expect(html).toContain('Spectral illustration — not measured data');
    expect(html).toContain('Your data are not uploaded.');
    expect(html).not.toContain('.zip');
    expect(html).not.toContain('.xlsx');
    expect(html).not.toContain('.npy');
  });

  it('announces cancellation and import errors accessibly without a result', () => {
    const html = renderToStaticMarkup(<App callbacks={callbacks} state={{ ...idleState, phase: 'cancelled', error: { code: 'INPUT_REFUSED', message: '<unsafe>' } }}/>);
    expect(html).toContain('role="status"');
    expect(html).toContain('role="alert"');
    expect(html).toContain('Analysis cancelled. No superseded result is displayed.');
    expect(html).toContain('&lt;unsafe&gt;');
    expect(html).not.toContain('workspace-summary');
  });
});
