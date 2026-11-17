import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import type { UiResult } from './ui-types';
import { ScopeControls } from './ScopeControls';

function result(inventory?: unknown): UiResult {
  return {
    mode: 'live', protocol: 'test', summary: '', dataset: { name: 'fixture', id: 'fixture', source: 'fixture', contentHash: 'hash',
      observations: null, variables: null, axisUnit: '', axis: [], spectra: [], metadata: [], identity: '', provenance: '', license: '' },
    findings: [], evidence: [], pca: null, geometryReason: null, limitations: [],
    provenance: inventory === undefined ? {} : { scoped_inventory: inventory },
  };
}

const loaded = {
  protocol_version: 'domains.browser_scoped_inventory.v1',
  loaded: {
    x: { rows: 5, variables: 2, present: true },
    y: [{ name: 'yield', unit: 'kg', type: 'numeric', rows: 3, missing: 1 }],
    metadata: [
      { name: 'batch', role: 'group', kind: 'categorical', origin: 'declared', derived_from_target: false, evidence: 'declared', rows: 5, missing: 0 },
      { name: 'unknown-field', role: 'factor', kind: 'unknown', origin: 'unknown', derived_from_target: 'unknown', evidence: 'unknown', rows: 5, missing: 1 },
      { name: 'derived', role: 'factor', kind: 'categorical', origin: 'declared', derived_from_target: true, evidence: 'declared', rows: 5, missing: 0 },
    ],
    partitions: [{ name: 'train', rows: 3 }, { name: 'test', rows: 2 }],
  },
};

describe('operation scoped controls', () => {
  it('is absent until a loaded scoped inventory is present', () => {
    expect(renderToStaticMarkup(<ScopeControls result={result()} locale="en" busy={false} onOperation={vi.fn()} />)).toBe('');
    expect(renderToStaticMarkup(<ScopeControls result={result({ loaded: {} })} locale="en" busy={false} onOperation={vi.fn()} />)).toBe('');
  });

  it('shows count-only inventory, scoped actions, consent gate, and display-only factor choices', () => {
    const html = renderToStaticMarkup(<ScopeControls result={result(loaded)} locale="en" busy={false} onOperation={vi.fn()} onColor={vi.fn()} />);
    for (const text of ['X: 5 rows, 2 variables', 'Y target fields: 1 (3 rows)', 'M metadata fields: 3 (15 rows)', 'train: 3 rows', 'test: 2 rows',
      'Train structure', 'Exact spectra train/test audit', 'Identity audit (no X)', 'Train M factors', 'Cross-partition M audit', 'Raw support: train reference → test query',
      'Unspecified', 'Test X can be audited', 'Inspecting test X can influence decisions even when no Y values are used.', 'Unknown origin limits interpretation.']) expect(html).toContain(text);
    expect(html).toContain('value="unknown-field"');
    expect(html).toContain('value="batch"');
    expect(html).not.toContain('value="derived"');
    expect(html).toMatch(/button[^>]*disabled=""[^>]*>Global descriptive analysis/);
  });

  it('localizes inventory and controls in French and disables operations while busy', () => {
    const html = renderToStaticMarkup(<ScopeControls result={result(loaded)} locale="fr" busy onOperation={vi.fn()} />);
    for (const text of ['Analyse à périmètre défini', 'Inventaire chargé', 'Champs cibles Y', 'Structure de train', 'Non précisé', 'Consulter X de test peut influencer les décisions même sans utiliser Y.']) expect(html).toContain(text);
    expect(html.match(/<button[^>]*disabled=""/g)?.length).toBe(7);
    expect(html).toContain('disabled=""');
  });
});
