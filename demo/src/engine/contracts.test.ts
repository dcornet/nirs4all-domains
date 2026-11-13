import { describe, expect, it } from 'vitest';
import { adaptAssembled, checkFiles } from './dataset-io';

const files = [{ name: 'x.csv', bytes: new TextEncoder().encode('2000,1000\n1,2\n2,3\n3,4') }];
function assembled() {
  return { assembled_schema_version: 2, name: 'Fixture', blocks: { train: {
    n_samples: 3, source_ids: ['X'], x: [{ n_rows: 3, n_cols: 2, data: new Float64Array([1,2,2,3,3,4]) }],
    feature_headers: [['2000','1000']], header_units: ['nm'], metadata: { columns: [{ name: 'acquisition', values: ['a','b','c'] }] },
  } }, identity: { provenance: { observation_id: 'acquisition' } } };
}
describe('IO transport integrity, with original owner data already materialized', () => {
  it('preserves descending axes, original order and observation identity without physical inference', async () => {
    const data = await adaptAssembled(assembled(), files, {}, []);
    expect(data.input.axis).toEqual([2000,1000]);
    expect(data.input.observation_ids).toEqual(['a','b','c']);
    expect(data.input.spectra).toEqual([[1,2],[2,3],[3,4]]);
    expect(data.input).not.toHaveProperty('physical_sample_ids');
    expect(data.input.content_sha256).toMatch(/^[0-9a-f]{64}$/);
  });
  it('refuses missing/nonfinite cells rather than changing the population', async () => {
    const value = assembled(); value.blocks.train.x[0].data[2] = NaN;
    await expect(adaptAssembled(value, files, {}, [])).rejects.toThrow('NONFINITE_X_NO_IMPLICIT_IMPUTATION');
  });
  it('refuses retained test/prediction populations before a full-source numerical request', async () => {
    const source = assembled();
    for (const partition of ['test','retained_test','predict']) {
      await expect(adaptAssembled({ ...source, blocks: { train: source.blocks.train, [partition]: source.blocks.train } }, files, {}, []))
        .rejects.toThrow('PARTITIONED_IMPORT_REQUIRES_TRAIN_FITTED_BROWSER_PROTOCOL');
    }
  });
  it('refuses duplicate observation keys and implicit multisource fusion', async () => {
    const duplicates = assembled(); duplicates.blocks.train.metadata.columns[0].values[1] = 'a';
    await expect(adaptAssembled(duplicates, files, {}, [])).rejects.toThrow('DUPLICATE_OBSERVATION_ID');
    const multiple = assembled(); multiple.blocks.train.x.push(multiple.blocks.train.x[0]);
    await expect(adaptAssembled(multiple, files, {}, [])).rejects.toThrow('MULTISOURCE_SELECTION_REQUIRED');
  });
  it('retains nonnumeric original headers and labels the logical axis instead of sorting bands', async () => {
    const value = assembled(); value.blocks.train.feature_headers[0] = ['b','a'];
    const data = await adaptAssembled(value, files, {}, []);
    expect(data.headers).toEqual(['b','a']); expect(data.input.axis).toEqual([0,1]);
    expect(data.input.axis_unit).toBe('index'); expect(data.input.spectra[0]).toEqual([1,2]);
  });
  it('admits no empty, duplicate-name or excessive file set', () => {
    expect(() => checkFiles([])).toThrow(); expect(() => checkFiles([...files,...files])).toThrow();
    expect(() => checkFiles([{ name: 'big.csv', bytes: new Uint8Array(8 * 1024 * 1024 + 1) }])).toThrow('IMPORT_BYTE_BUDGET');
    expect(() => checkFiles([{ name: '../private.csv', bytes: new Uint8Array() }])).toThrow('UNSAFE_RELATIVE');
  });
});
