import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { FactorAssociationControls, type FactorAssociationControlsProps } from './FactorAssociationControls';

const factors: FactorAssociationControlsProps['factors'] = [
  { id: 'batch', label: 'Batch', kind: 'categorical', unit: null, origin: 'declared', derivedFromTarget: false },
  { id: 'moisture', label: 'Moisture', kind: 'continuous', unit: '%', origin: 'declared', derivedFromTarget: false },
  { id: 'unknown', label: 'Unknown field', kind: 'unknown', unit: null, origin: 'unknown', derivedFromTarget: 'unknown' },
  { id: 'target-derived', label: 'Target-derived', kind: 'categorical', unit: null, origin: 'declared', derivedFromTarget: true },
];

function markup(overrides: Partial<FactorAssociationControlsProps> = {}) {
  const props: FactorAssociationControlsProps = {
    datasetKey: 'dataset-a', factors,
    populations: [
      { id: 'train', label: 'Train', ready: false, reason: 'No executed train PCA' },
      { id: 'unpartitioned', label: 'Unpartitioned source', ready: true },
      { id: 'global_transductive', label: 'Global train + test', ready: true },
    ],
    busy: false, inferenceRecordAvailable: false, onRun: vi.fn(), onColor: vi.fn(),
    exportColorAuthorized: false, onAuthorizeColorExport: vi.fn(), locale: 'en', ...overrides,
  };
  return renderToStaticMarkup(<FactorAssociationControls {...props} />);
}

describe('factor association controls', () => {
  it('uses a factor placeholder, prefers train then unpartitioned, and excludes unsupported or Y-derived choices', () => {
    const html = markup();
    expect(html).toContain('Which factors are associated with spectral structure?');
    expect(html).toContain('<option value="" selected="">Select a factor</option>');
    expect(html).toContain('<option value="train" disabled="" selected="">Train · Unavailable</option>');
    expect(html).toContain('value="batch"');
    expect(html).toContain('value="moisture"');
    expect(html).not.toContain('value="unknown"');
    expect(html).not.toContain('value="target-derived"');
    expect(html).toContain('Y-derived fields are excluded from factor choices.');
    expect(html).toContain('disabled="">Run factor association</button>');
    expect(html).not.toContain('I explicitly authorize a separate descriptive analysis');

    const fallback = markup({ populations: [{ id: 'unpartitioned', label: 'Unpartitioned source', ready: true }] });
    expect(fallback).toContain('<option value="unpartitioned" selected="">Unpartitioned source</option>');
    expect(fallback).not.toContain('value="global_transductive" selected');
  });

  it('shows continuous measure defaults, unavailable PCA reason, and conditional inference state', () => {
    const html = markup({
      populations: [{ id: 'train', label: 'Train', ready: false, reason: 'PCA not executed' }],
      unavailablePcaReason: 'PCA not executed', inferenceRecordAvailable: true,
    });
    expect(html).toContain('Pearson (linear; default)');
    expect(html).toContain('Spearman (monotone rank)');
    expect(html).toContain('Descriptive only (default)');
    expect(html).toContain('Request exact inference if qualified');
    expect(html).toContain('Inference is conditional on an external design record and has not been independently verified.');
    expect(html).toContain('PCA is unavailable for this population: PCA not executed');
  });

  it('offers external plan file attachment only when a loader is supplied and warns it does not qualify or execute', () => {
    const ordinary = markup();
    expect(ordinary).not.toContain('type="file"');
    const withLoader = markup({ onLoadInferencePlan: vi.fn() });
    expect(withLoader).toContain('type="file"');
    expect(withLoader).toContain('accept=".json,application/json"');
    expect(withLoader).toContain('Attach an external design record (JSON)');
    expect(withLoader).toContain('selecting the file grants no independence or execution');
    expect(withLoader).toContain('Rust checks coherence only when you explicitly run the analysis.');
    const french = markup({ locale: 'fr', onLoadInferencePlan: vi.fn() });
    expect(french).toContain('Joindre un dossier de plan externe (JSON)');
    expect(french).toContain('ne lance pas une execution');
  });

  it('localizes controls in French and explains export color authorization separately', () => {
    const html = markup({ locale: 'fr' });
    expect(html).toContain('Quels facteurs sont associés à la structure spectrale ?');
    expect(html).toContain('Sélectionner un facteur');
    expect(html).toContain('Aucun dossier externe de qualification ; l’inférence ne peut pas être demandée.');
    expect(html).toContain('Tout sélectionner dans le rapport ne donne pas cette autorisation.');
  });
});
