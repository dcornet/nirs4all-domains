import type { UiExample } from '../ui-types';
import type { LocalDataset } from '../engine/types';
import { sha256 } from '../engine/dataset-io';

export const examples: UiExample[] = [
  { id: 'separated', name: 'Two spectral populations', description: 'Synthetic separation with declared group exclusions. Mathematical groups are not biological families.', mode: 'live', dimensions: '48 spectra × 24 bands', license: 'Project synthetic fixture · dual license' },
  { id: 'continuum', name: 'A continuous gradient', description: 'Synthetic X without specimen metadata. A continuous shape need not produce meaningful discrete clusters.', mode: 'live', dimensions: '40 spectra × 24 bands', license: 'Project synthetic fixture · dual license' },
  { id: 'small', name: 'A justified unavailable result', description: 'Five observations: PCA can run, while the fixed density setting has insufficient observations.', mode: 'live', dimensions: '5 spectra × 12 bands', license: 'Project synthetic fixture · dual license' },
  { id: 'tablet-saved', name: 'Tablets: a qualified saved report', description: 'Public source-permitted D1–D6.1 report reading, with unknown physical independence. No browser refit.', mode: 'saved', dimensions: '310 recorded observations · X view raw', license: 'Published aggregate example · see source attribution' },
];

/** Synthetic data generation is an example fixture, never a runtime numerical backend. */
export async function synthetic(id: string): Promise<LocalDataset> {
  const n = id === 'small' ? 5 : id === 'continuum' ? 40 : 48;
  const p = id === 'small' ? 12 : 24;
  const axis = Array.from({ length: p }, (_, j) => 1000 + 20 * j);
  const spectra = Array.from({ length: n }, (_, i) => axis.map((_, j) => {
    const gradient = (i - (n - 1) / 2) / n;
    const population = id === 'separated' && i >= n / 2 ? 1.2 : 0;
    return 0.5 + Math.exp(-(((j - 8) / 4) ** 2)) * (1 + gradient + population) +
      Math.exp(-(((j - 18) / 3) ** 2)) * (0.7 - gradient / 2) + 0.015 * Math.sin(i * 7 + j * 3);
  }));
  const bytes = new TextEncoder().encode(JSON.stringify({ axis, spectra }));
  const observationIds = spectra.map((_, i) => `synthetic-${id}-${i + 1}`);
  return { input: { schema_version: 1, dataset_id: `synthetic-${id}`, source_id: 'X',
    content_sha256: await sha256(bytes), observation_ids: observationIds, axis, axis_unit: 'nm', spectra,
    ...(id === 'separated' ? { group_ids: observationIds.map((_, i) => `declared-block-${Math.floor(i / 4)}`) } : {}) },
    metadata: [], partitions: [{ name: 'descriptive', observation_ids: observationIds }],
    headers: axis.map(String), warnings: ['Synthetic illustration; no real chemistry, causal mechanism, specimen independence or prediction performance is claimed.'],
    importSpec: { generator: 'domains.synthetic_examples.v1', seed: 'deterministic formulas; no stochastic selection', source: 'demo/src/examples/index.ts' },
    identityOrigin: 'Synthetic observation coordinates; declared groups are not independent physical units',
    license: 'CECILL-2.1 OR AGPL-3.0-or-later', mode: 'synthetic_computed_live' };
}
