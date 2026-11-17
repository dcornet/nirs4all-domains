import { describe, expect, it } from 'vitest';
import type { BrowserInput } from '../engine/types';
import type { LocalDataset } from '../engine/types';
import type { UiResult } from '../ui-types';
import type { ScopedOperation, ScopedResult } from '../../../bindings/wasm/scoped';
import { reportModel } from './model';
import { serializeReport } from './export';
import { presentation } from './presentation';
import { scopedInventory, scopedView } from './scoped';

const X_SENTINEL = 987654321.125;
const Y_SENTINEL = 'PRIVATE_TARGET_SENTINEL';
const M_SENTINEL = 'PRIVATE_METADATA_SENTINEL';

function dataset(): LocalDataset {
  const input: BrowserInput = {
    schema_version: 1, dataset_id: 'F4 fixture', source_id: 'source-fixture', content_sha256: 'content-hash',
    observation_ids: ['obs-a', 'obs-b'], axis: [1000, 1010], axis_unit: 'nm',
    spectra: [[X_SENTINEL, 1], [2, 3]],
  };
  return {
    input, metadata: [
      { name: 'batch', role: 'group', type: 'categorical', origin: 'declared', derived_from_target: false, evidence: 'declared', values: ['B', null] },
      { name: 'possibly-derived', role: 'factor', type: 'categorical', origin: 'unknown', derived_from_target: 'unknown', evidence: 'unknown', values: ['unknown-level', 'ok'] },
      { name: 'unselected-private-field', role: 'unknown', type: 'unknown', values: [M_SENTINEL, null] },
      { name: 'target-key', role: 'factor', type: 'categorical', derived_from_target: true, values: ['a', 'b'] },
    ],
    partitions: [{ name: 'train', observation_ids: ['obs-a'] }, { name: 'test', observation_ids: ['obs-b'] }],
    headers: ['1000', '1010'], warnings: [], importSpec: {}, identityOrigin: 'fixture IDs', license: 'test',
    mode: 'user_computed_live', rawX: [[X_SENTINEL, 1], [2, 3]], missingX: [[false, false], [false, false]],
    targets: [{ name: 'y', type: 'categorical', unit: null, values: [Y_SENTINEL, null], mask: [true, false], origin: 'declared' }],
    rowManifest: [
      { key: 'row-train-a', observation_id: 'obs-a', partition: 'train', original_partition: 'Train', source_id: 'source-fixture' },
      { key: 'row-test-b', observation_id: 'obs-b', partition: 'test', original_partition: 'Test', source_id: 'source-fixture' },
    ],
  };
}

function baseView(): UiResult {
  return {
    mode: 'live', protocol: 'domains.browser_x.v1',
    dataset: { name: 'F4 fixture', id: 'fixture', source: 'source-fixture', contentHash: 'content-hash',
      observations: 2, variables: 2, axisUnit: 'nm', axis: [1000, 1010], spectra: [], metadata: ['batch'],
      identity: 'fixture', provenance: 'fixture', license: 'test', representation: 'raw' },
    summary: 'fixture', findings: [], evidence: [{ id: 'pca', method: 'PCA', status: 'computed', reason: null,
      value: { immutable: true }, scope: 'train', provider: 'fixture' }],
    pca: { points: [{ id: 'row-train-a', x: 4.5, y: -2 }, { id: 'row-test-b', x: 8, y: 3 }],
      eigenvalues: [7, 2], totalVariance: 10, xLabel: 'PC1', yLabel: 'PC2' },
    geometryReason: null, limitations: [], provenance: { original: 'kept', evidence_sha256: 'matching-hash' },
  };
}

function operation(kind: ScopedOperation = 'metadata_factor_audit'): ScopedResult {
  return { protocol_version: 'domains.browser_scoped_result.v1', operation: kind, diagnostic: null,
    status: 'computed', reason: null, value: (kind === 'train_structure' || kind === 'global_descriptive_transductive'
      ? { structure: { evidence_sha256: 'matching-hash' } } : { evidence: 'provider-only' }) as never,
    receipt: { fit_population: 'train', reference_population: null, query_population: null, y_access: false },
    supported_claims: ['train X structure'], limitations: ['Descriptive only'], action: 'Review unit of analysis' };
}

describe('F4 scoped report projection', () => {
  it('exports only safe inventory declarations, counts and missingness', () => {
    const data = dataset(), inventory = scopedInventory(data), text = JSON.stringify(inventory);
    expect(inventory.loaded.x).toMatchObject({ rows: 2, variables: 2 });
    expect(inventory.loaded.y).toEqual([{ name: 'y', unit: null, type: 'categorical', rows: 2, missing: 1 }]);
    expect(inventory.loaded.metadata[1]!.derived_from_target).toBe('unknown');
    expect(text).not.toContain(String(X_SENTINEL));
    expect(text).not.toContain(Y_SENTINEL);
    expect(text).not.toContain(M_SENTINEL);
  });

  it('colors by exact technical row key without changing coordinates or scientific evidence', () => {
    const base = baseView(), beforePoints = structuredClone(base.pca!.points), beforeEvidence = structuredClone(base.evidence);
    const view = scopedView(base, dataset(), [operation()], 'batch');
    expect(view.pca!.points.map(({ x, y }) => ({ x, y }))).toEqual(beforePoints.map(({ x, y }) => ({ x, y })));
    expect(view.pca!.points.map(point => point.group)).toEqual(['B', 'Missing metadata']);
    expect(view.evidence[0]!.status).toBe(beforeEvidence[0]!.status);
    expect(view.evidence[0]!.value).toMatchObject({ immutable: true });
    expect(base.evidence).toEqual(beforeEvidence);
    expect(view.provenance.display_color_status).toBe('MAPPED_BY_TECHNICAL_ROW_KEY');
  });

  it('blocks explicitly target-derived color and refuses incomplete key mapping', () => {
    const noCoordinates=scopedView(undefined,dataset(),[],'batch');
    expect(noCoordinates.pca).toBeNull();expect(noCoordinates.provenance.display_color_status).toBe('PCA_COORDINATES_NOT_CARRIED');
    const derived = scopedView(baseView(), dataset(), [], 'target-key');
    expect(derived.pca!.points.every(point => point.group === undefined)).toBe(true);
    expect(derived.provenance.display_color_status).toBe('TARGET_DERIVED_METADATA_NOT_ELIGIBLE_FOR_COLORING');
    const unmapped = baseView(); unmapped.pca!.points[1]!.id = 'unknown-row';
    const result = scopedView(unmapped, dataset(), [], 'batch');
    expect(result.pca!.points.every(point => point.group === undefined)).toBe(true);
    expect(result.provenance.display_color_status).toBe('PCA_POINT_TO_METADATA_KEY_MAPPING_INCOMPLETE');
  });

  it('labels train-only and explicitly global structure without mutating the source report', () => {
    const source = baseView(), original = structuredClone(source);
    const train = scopedView(source, dataset(), [operation('train_structure')]);
    expect(train.dataset.population).toContain('train population only');
    expect(train.provenance.scoped_structure_scope).toBe('train_only');
    expect(train.evidence[0]!.scope).toContain('train population only');
    expect((train.evidence[0]!.value as { scope: string }).scope).toContain('train only');
    expect(presentation(train, 'en', 'unknown').brief[0]).toContain('Train-only');
    expect(presentation(train, 'en', 'unknown').figures[0]!.population).toContain('Train-only');
    expect(source).toEqual(original);

    const global = scopedView(baseView(), dataset(), [operation('global_descriptive_transductive')]);
    expect(global.dataset.population).toContain('Explicitly selected train and test');
    expect(global.provenance.scoped_structure_scope).toBe('global_transductive');
    expect(presentation(global, 'en', 'unknown').brief[0]).toContain('Explicit global descriptive/transductive');
    expect(presentation(global, 'en', 'unknown').figures[0]!.population).toContain('Explicit global descriptive/transductive');
  });

  it('does not describe an unmatched structure as complete-source descriptive analysis', () => {
    const stale=baseView();stale.provenance.evidence_sha256='different-population';
    expect(scopedView(stale,dataset(),[operation('train_structure')]).provenance.scoped_structure_scope).toBe('unknown');
    const view = scopedView(baseView(), dataset(), []);
    expect(view.provenance.scoped_structure_scope).toBe('unknown');
    expect(presentation(view, 'en', 'unknown').brief[0]).toContain('could not be matched');
    expect(presentation(baseView(), 'en', 'unknown').brief[0]).toContain('Complete imported X');
  });

  it('reads exact-pair counts literally and keeps owner policy refusals distinct from model leakage',()=>{
    const audit=operation('integrity_audit');audit.diagnostic='exact_spectra';
    audit.receipt.reference_keys=['a','b'];audit.receipt.query_keys=['c'];
    audit.value={metrics:[{metric_id:'integrity.cross_partition_exact_duplicate_pairs',status:'computed',value:0}]};
    const reading=scopedView(undefined,dataset(),[audit]).findings[0];
    expect(reading.observation).toContain('reports 0 pairs');expect(reading.observation).toContain('2 reference and 1 query');
    expect(reading.hypothesis).toContain('does not identify a causal mechanism');
    const refused={...audit,status:'error' as const,reason:'PREFLIGHT_INPUT_VALIDATION_FAILED',value:null};
    const failed=scopedView(undefined,dataset(),[refused]).findings[0];
    expect(failed.status).toBe('error');expect(failed.limitation).toContain('does not establish leakage in a predictive model');
    expect(failed.limitation).toContain('repeated-acquisition objective');
  });
  it('keeps unknown derivation explicit and excludes X/Y and unselected metadata from all report exports', () => {
    const data = dataset(),base=baseView();
    base.provenance.import_spec={unconsumed_extension:{raw_targets:[Y_SENTINEL],raw_spectra:[[X_SENTINEL]]}};
    const view = scopedView(base, data, [operation()], 'possibly-derived');
    expect(view.provenance).not.toHaveProperty('import_spec');
    expect(view.provenance.display_color_status).toBe('MAPPED_BY_TECHNICAL_ROW_KEY_TARGET_DERIVATION_UNKNOWN');
    const report = reportModel(view, { protocol_version: 'domains.browser_scoped_report.v1' }, 'unknown', 'en');
    for (const format of ['json', 'markdown', 'html'] as const) {
      const serialized = serializeReport(report, format);
      expect(serialized).not.toContain(String(X_SENTINEL));
      expect(serialized).not.toContain(Y_SENTINEL);
      expect(serialized).not.toContain(M_SENTINEL);
    }
  });
});
