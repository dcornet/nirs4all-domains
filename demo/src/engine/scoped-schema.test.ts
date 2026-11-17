import Ajv2020 from 'ajv/dist/2020';
import { describe, expect, it } from 'vitest';
import inputSchema from '../../../bindings/wasm/scoped-input.schema.json';
import resultSchema from '../../../bindings/wasm/scoped-result.schema.json';
import type { ScopedResult } from '../../../bindings/wasm/scoped';
import { scopedRequest } from './scoped';
import type { LocalDataset } from './types';

const ajv = new Ajv2020({ strict: false, strictNumbers: true, allErrors: true });
ajv.addSchema(inputSchema);
const validateInput = ajv.compile(inputSchema);
const validateResult = ajv.compile(resultSchema);
const hash = 'a'.repeat(64);

function imported(): LocalDataset {
  const rows = ['row-a', 'row-b', 'row-c'];
  return {
    input: {
      schema_version: 1, dataset_id: 'schema fixture', source_id: 'source-a',
      content_sha256: hash, observation_ids: rows, axis: [1000, 1010], axis_unit: 'nm', spectra: [],
    },
    rawX: [[1, 2], [null, 4], [5, 6]], missingX: [[false, false], [true, false], [false, false]],
    metadata: [{ name: 'batch', role: 'group', type: 'categorical', origin: 'declared',
      derived_from_target: false, evidence: 'declared', values: ['A', 'A', 'B'] }],
    targets: [], rowManifest: rows.map((key, index) => ({ key, observation_id: `obs-${index}`,
      partition: 'train' as const, original_partition: 'train', source_id: 'source-a' })),
    partitions: [{ name: 'train', observation_ids: rows }], headers: ['1000', '1010'], warnings: [],
    importSpec: { content_version: 'fixture-v1' }, identityOrigin: 'declared observation IDs',
    license: 'synthetic fixture', mode: 'user_computed_live',
  };
}

function computedResult(): ScopedResult {
  return {
    protocol_version: 'domains.browser_scoped_result.v1', operation: 'train_structure', diagnostic: null,
    status: 'computed', reason: null, value: { structure: {} as never },
    receipt: {
      protocol_version: 'domains.browser_scoped_analysis.v1', operation: 'train_structure', diagnostic: null,
      dataset: { dataset_id: 'schema fixture', source_id: 'source-a', content_version: 'fixture-v1', content_sha256: hash },
      request_sha256: hash, manifest_sha256: hash, reference_keys: ['row-a', 'row-b', 'row-c'],
      query_keys: [], fit_keys: ['row-a', 'row-b', 'row-c'],
      reference_population: { role: 'train', row_keys: ['row-a', 'row-b', 'row-c'] },
      query_population: { role: 'test', row_keys: [] }, fit: 'train', representation: 'raw',
      parameters: { preset: 'f4_fixed_raw_v1' }, selection_context: 'unspecified', explicit_transductive: false,
      exclusion_field: 'batch',
      fields_read: {
        x: { row_keys: ['row-a', 'row-b', 'row-c'], matrix: { shape: [3, 2], sha256: hash }, axis_sha256: hash, axis_unit: 'nm' },
        m: [{ name: 'batch', role: 'group', kind: 'categorical', origin: 'declared', evidence: 'declared', derived_from_target: null,
          row_keys: ['row-a', 'row-b', 'row-c'], shape: [3], sha256: hash }], y: [],
      },
      provider_calls: [], test_x_accessed: false, y_accessed: false, physical_independence: 'unverified',
      physical_id_encoding: 'type-preserving JSON scalar; identity not verified', receipt_sha256: hash,
    },
    supported_claims: ['Exact receipt population'], limitations: ['Descriptive only'], action: 'Review provenance',
  };
}

describe('scoped wire schemas', () => {
  it('accepts a request projected from the imported dataset builder model, including nullable X', () => {
    const request = scopedRequest(imported(), 'train_structure');
    expect(validateInput(request), JSON.stringify(validateInput.errors)).toBe(true);
    const unknownDerivation = structuredClone(request);
    unknownDerivation.metadata[0]!.derived_from_target = null;
    expect(validateInput(unknownDerivation)).toBe(true);
  });

  it('rejects Y grants, unsupported protocol versions, and non-finite X', () => {
    const request = scopedRequest(imported(), 'train_structure');
    expect(validateInput({ ...request, access: { ...request.access, y_fields: ['target'] } })).toBe(false);
    expect(validateInput({ ...request, schema_version: 2 })).toBe(false);
    const nonfinite = structuredClone(request);
    nonfinite.x!.matrix[0]![0] = Number.NaN;
    expect(validateInput(nonfinite)).toBe(false);
  });

  it('accepts computed and rejects status/reason/value contradictions', () => {
    const result = computedResult();
    expect(validateResult(result), JSON.stringify(validateResult.errors)).toBe(true);
    expect(validateResult({ ...result, reason: 'unexpected' })).toBe(false);
    expect(validateResult({ ...result, status: 'unavailable', reason: 'NOT_AVAILABLE', value: {} })).toBe(false);
    expect(validateResult({ ...result, status: 'unavailable', reason: null, value: null })).toBe(false);
  });
});
