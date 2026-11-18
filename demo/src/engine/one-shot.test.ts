import { describe, expect, it } from 'vitest';
import * as io from '@nirs4all/io-wasm';
import { oneShotFixtureCases, filesForOneShotCase } from '../../scripts/one-shot-fixtures.mjs';
import { autoImportDataset, defaultImportConfig, resolveDatasetDraft } from './one-shot';
import { prepareDataset } from './import-draft';
import type { InputFile, LocalDataset } from './types';

const formats = { openWithSidecars() { throw new Error('CSV fixture must stay on the published IO table route'); } };
const fileSet = (id: string) => filesForOneShotCase(id) as InputFile[];
const importCase = (id: string) => autoImportDataset(fileSet(id), io, formats);
const textFile = (name: string, text: string): InputFile => ({ name, bytes: new TextEncoder().encode(text) });
const loaded = (value: Awaited<ReturnType<typeof autoImportDataset>>): LocalDataset => {
  if (value.status !== 'loaded') throw new Error(`EXPECTED_LOADED:${value.session.issues.map(issue => issue.code).join(',')}`);
  return value.dataset;
};

describe('one-shot import fixtures through published IO 0.2.14', () => {
  it('refuses explicit random partition generation before native assembly',async()=>{
    let assemblies=0;
    const files:InputFile[]=[{name:'X.csv',bytes:new TextEncoder().encode('1000\n1\n2\n3\n')},{name:'random.nirs4all.json',bytes:new TextEncoder().encode(JSON.stringify({schema_version:1,sources:[{id:'X',input:'X.csv',role:'features',params:{has_header:true}}],partitions:{by:'random',test_size:0.25}}))}];
    const owner={...io,assembleDataset:(...args:Parameters<typeof io.assembleDataset>)=>{assemblies++;return io.assembleDataset(...args);}};
    await expect(autoImportDataset(files,owner,formats)).rejects.toThrow('IMPLICIT_PARTITION_GENERATION_NOT_ADMITTED');
    expect(assemblies).toBe(0);
  });
  it('keeps the 26-case inventory plus the inference regression explicit', () => {
    expect(oneShotFixtureCases).toHaveLength(27);
    expect(oneShotFixtureCases.map(fixture => fixture.id)).toContain('unassociated-y-no-key');
  });

  it.each(oneShotFixtureCases.map(fixture => [fixture.id, fixture.expected] as const))(
    '%s resolves as %s', async (id, expected) => {
      const outcome = await importCase(id);
      expect(outcome.status).toBe(expected);
    },
  );

  it('assembles reordered keyed X/Y/M by native identity and preserves train/test populations', async () => {
    const dataset = loaded(await importCase('keyed-train-test'));
    expect(dataset.rowManifest?.filter(row => row.partition === 'train').map(row => row.observation_id)).toEqual(['a', 'b', 'c']);
    expect(dataset.rowManifest?.filter(row => row.partition === 'test').map(row => row.observation_id)).toEqual(['d', 'e']);
    expect(dataset.targets?.find(target => target.name === 'yield')?.values).toEqual([40, 50, 10, 20, 30]);
    expect(dataset.rowManifest).toHaveLength(5);
  });

  it('retains all-missing Y/M declarations and masks without dropping rows', async () => {
    const y = loaded(await importCase('all-missing-y'));
    expect(y.rowManifest).toHaveLength(2);
    expect(y.targets?.find(target => target.name === 'yield')?.values).toEqual([null, null]);
    expect(y.targets?.find(target => target.name === 'yield')?.mask).toEqual([false, false]);
    const m = loaded(await importCase('all-missing-m'));
    expect(m.rowManifest).toHaveLength(3);
    expect(m.metadata.find(column => column.name === 'batch')?.values).toEqual([null, null, null]);
  });

  it('preserves source-declared missing tokens instead of translating strings in Domains', async () => {
    const blank = loaded(await importCase('na-empty'));
    expect(blank.missingX?.[1]).toEqual([true, false]);
    expect(blank.targets?.find(target => target.name === 'yield')?.mask).toEqual([true, false, true]);
    const literal = loaded(await importCase('na-missing'));
    const target = literal.targets?.find(item => item.name === 'yield');
    expect(target?.mask[1]).toBe(true);
    expect(target?.values[1]).toBe('missing');
  });

  it('keeps an unassociated Y source in the review session while loading only independently assembled X', async () => {
    const outcome = await importCase('unassociated-y-no-key');
    expect(outcome.status).toBe('loaded');
    if (outcome.status !== 'loaded') return;
    expect(outcome.dataset.rawX).toHaveLength(2);
    expect(outcome.dataset.targets).toEqual([]);
    expect(outcome.session.draft.files.map(file => file.name)).toContain('train_y.csv');
    expect(outcome.session.draft.spec.sources.map(source => source.id)).toContain('train_y');
    expect(outcome.session.issues.some(issue => issue.kind === 'join_key' && !issue.blocking)).toBe(true);
  });

  it('keeps an unassociated M source in the review session without presenting it as aligned metadata', async () => {
    const outcome = await importCase('unassociated-m-no-key');
    expect(outcome.status).toBe('loaded');
    if (outcome.status !== 'loaded') return;
    expect(outcome.dataset.rawX).toHaveLength(3);
    expect(outcome.dataset.metadata.some(column => column.name === 'campaign')).toBe(false);
    expect(outcome.session.draft.files.map(file => file.name)).toContain('train_m.csv');
    expect(outcome.session.issues.some(issue => issue.kind === 'join_key' && !issue.blocking)).toBe(true);
  });

  it('does not implicitly combine two X sources or infer a row-order Y join', async () => {
    const spectral = await importCase('two-x-same-axis');
    expect(spectral.status).toBe('needs_input');
    const pairing = await importCase('ambiguous-row-order-pairing');
    expect(pairing.status).toBe('needs_input');
    if (pairing.status === 'needs_input') {
      expect(pairing.dataset?.rawX).toHaveLength(2);
      expect(pairing.dataset?.targets).toEqual([]);
      expect(pairing.session.issues.some(issue => issue.blocking && issue.kind === 'join_key')).toBe(true);
    }
  });

  it('keeps X available while a duplicate-key M attachment remains blocked', async () => {
    const outcome = await importCase('duplicate-m-keys');
    expect(outcome.status).toBe('needs_input');
    if (outcome.status === 'needs_input') {
      expect(outcome.dataset?.rawX).toHaveLength(3);
      expect(outcome.dataset?.metadata.some(column => column.name === 'batch')).toBe(false);
      expect(outcome.session.issues.some(issue => issue.blocking && issue.kind === 'join_key')).toBe(true);
    }
  });

  it('preserves both original X bands when inferred assembly fails on duplicate Y keys', async () => {
    const outcome = await importCase('inferred-duplicate-y-keys-preserve-x-axis');
    expect(outcome.status).toBe('needs_input');
    if (outcome.status === 'needs_input') {
      expect(outcome.dataset?.input.axis).toEqual([2000, 1000]);
      expect(outcome.dataset?.rawX).toEqual([[1, 2], [3, 4]]);
      expect(outcome.dataset?.targets).toEqual([]);
      expect(outcome.session.issues.some(issue => issue.blocking && issue.kind === 'join_key')).toBe(true);
    }
  });

  it('applies a corrected explicit separator through IO and binds reviewed replacement provenance', async () => {
    const draft = prepareDataset(fileSet('explicit-delimiter-correction'), io, formats);
    const originalSpec = JSON.stringify(draft.spec);
    const originalSources = JSON.stringify(draft.sources);
    const originalSeparator = draft.sources.find(source => source.id === 'X')?.parsing.separator;
    const config = defaultImportConfig(draft);
    const originalConfig = JSON.stringify(config);
    const invalidAttempt = await resolveDatasetDraft(draft, config, draft.sources, io, 'user_configured');
    expect(invalidAttempt.status).toBe('needs_input');
    expect(JSON.stringify(draft.spec)).toBe(originalSpec);
    expect(JSON.stringify(draft.sources)).toBe(originalSources);
    expect(JSON.stringify(config)).toBe(originalConfig);
    const reviewedSources = structuredClone(draft.sources);
    const spectral = reviewedSources.find(source => source.id === 'X');
    if (!spectral) throw new Error('MISSING_SYNTHETIC_X_SOURCE');
    spectral.parsing.separator = ';';

    const outcome = await resolveDatasetDraft(draft, config, reviewedSources, io, 'user_configured');
    expect(outcome.status, JSON.stringify(outcome.session.issues)).toBe('loaded');
    if (outcome.status !== 'loaded') return;
    expect(outcome.dataset.rawX).toEqual([[1, 2], [3, 4], [5, 6]]);
    expect(outcome.dataset.input.axis).toEqual([2000, 1000]);
    expect(outcome.dataset.rowManifest?.map(row => row.observation_id)).toEqual(['a', 'b', 'c']);
    expect(outcome.dataset.importProvenance?.roles_reviewed).toBe(true);
    expect(outcome.dataset.importProvenance?.reviewed_spec_sha256).toMatch(/^[a-f0-9]{64}$/);
    expect(outcome.dataset.importProvenance?.file_content_sha256).toMatch(/^[a-f0-9]{64}$/);
    expect(outcome.dataset.input.content_sha256).toMatch(/^[a-f0-9]{64}$/);
    expect(outcome.dataset.input.content_sha256).not.toBe(outcome.dataset.importProvenance?.file_content_sha256);
    expect(JSON.stringify(draft.spec)).toBe(originalSpec);
    expect(JSON.stringify(draft.sources)).toBe(originalSources);
    expect(JSON.stringify(config)).toBe(originalConfig);
    expect(draft.sources.find(source => source.id === 'X')?.parsing.separator).toBe(originalSeparator);

    const automatic = loaded(await importCase('x-only'));
    expect(automatic.importProvenance?.roles_reviewed).toBe(false);
  });

  it('left-fills inferred partial M while preserving full X and null metadata', async () => {
    const draft = prepareDataset(fileSet('partial-m-inferred-allow-missing'), io, formats);
    const originalSpec = JSON.stringify(draft.spec);
    const originalSources = JSON.stringify(draft.sources);
    const outcome = await resolveDatasetDraft(draft, defaultImportConfig(draft), draft.sources, io);
    expect(outcome.status).toBe('loaded');
    if (outcome.status !== 'loaded') return;
    expect(outcome.dataset.rawX).toHaveLength(3);
    expect(outcome.dataset.rowManifest?.map(row => row.observation_id)).toEqual(['a', 'b', 'c']);
    expect(outcome.dataset.metadata.find(column => column.name === 'batch')?.values).toEqual(['A', null, 'C']);
    expect(outcome.session.issues).toEqual([]);
    expect(JSON.stringify(draft.spec)).toBe(originalSpec);
    expect(JSON.stringify(draft.sources)).toBe(originalSources);
  });

  it('keeps explicit complete-coverage policy strict and retains independently assembled X', async () => {
    const files = [
      textFile('train_x.csv', 'id,2000,1000\na,1,2\nb,3,4\nc,5,6'),
      textFile('train_m.csv', 'id,batch\na,A\nc,C'),
      textFile('explicit.nirs4all.json', JSON.stringify({ schema_version: 1,
        sample_index: { by: 'id', key: 'id', observation_id: 'id' },
        sources: [
          { id: 'X', input: 'train_x.csv', role: 'features', key: 'id', partition: 'train', params: { delimiter: ',', has_header: true } },
          { id: 'M', input: 'train_m.csv', role: 'metadata', key: 'id', partition: 'train',
            join: { left: 'M', right: 'X', left_on: 'id', right_on: 'id', cardinality: '1:1', coverage: 'complete' },
            params: { delimiter: ',', has_header: true } },
        ],
      })),
    ];
    const draft = prepareDataset(files, io, formats);
    const originalSpec = JSON.stringify(draft.spec);
    const config = defaultImportConfig(draft);
    const originalConfig = JSON.stringify(config);
    const outcome = await resolveDatasetDraft(draft, config, draft.sources, io);
    expect(outcome.status, JSON.stringify(outcome.session.issues)).toBe('needs_input');
    const dataset = outcome.status === 'needs_input' ? outcome.dataset : undefined;
    expect(dataset, JSON.stringify(outcome.session.issues)).toBeDefined();
    expect(dataset?.rawX).toEqual([[1, 2], [3, 4], [5, 6]]);
    expect(dataset?.rowManifest?.map(row => row.observation_id)).toEqual(['a', 'b', 'c']);
    expect(dataset?.metadata.some(column => column.name === 'batch')).toBe(false);
    expect(JSON.stringify(draft.spec)).toBe(originalSpec);
    expect(JSON.stringify(config)).toBe(originalConfig);
    expect(outcome.session.config.joins.some(join => join.strategy === 'strict')).toBe(true);
    expect(outcome.session.issues.some(issue => issue.kind === 'join_key' && issue.blocking)).toBe(true);
  });

  it('retains an all-missing spectral band, its axis coordinate, and every row', async () => {
    const outcome = await autoImportDataset([textFile('train_x.csv', 'id,2000,1000\na,1,\nb,3,\nc,5,')], io, formats);
    expect(outcome.status).toBe('loaded');
    if (outcome.status !== 'loaded') return;
    expect(outcome.dataset.input.axis).toEqual([2000, 1000]);
    expect(outcome.dataset.rawX).toEqual([[1, null], [3, null], [5, null]]);
    expect(outcome.dataset.missingX).toEqual([[false, true], [false, true], [false, true]]);
    expect(outcome.dataset.rowManifest).toHaveLength(3);
  });
});
