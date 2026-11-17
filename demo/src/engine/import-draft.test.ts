import { describe, expect, it } from 'vitest';
import * as io from '@nirs4all/io-wasm';
import { buildExportConfig } from 'nirs4all-ui/datasetBuilder';
import { adaptImported, assembleDatasetDraft, builderSpec, prepareDataset, type FormatsRuntime, type ImportedAssembled, type ReviewedDatasetConfig } from './import-draft';
import { importFiles } from './dataset-io';
import type { InputFile } from './types';

const formats: FormatsRuntime = { openWithSidecars() { throw new Error('CSV tests must use native IO parsing'); } };
const file = (name: string, contents: string): InputFile => ({ name, bytes: new TextEncoder().encode(contents) });
const x = 'id,2000,1000\na,1,2\nb,3,4\nc,5,6';
async function imported(files: InputFile[]) {
  const draft = prepareDataset(files, io, formats);
  return assembleDatasetDraft(draft, buildExportConfig('Fixture', draft.sources), draft.sources, io);
}

describe('F4 import transport through published IO 0.2.14 and public shared builder', () => {
  it.each([
    ['X', []], ['X/Y', [file('train_y.csv', 'id,sugar,class\nc,30,C\na,10,A\nb,20,B')]],
    ['X/M', [file('train_m.csv', 'id,instrument,batch\nc,I3,c\na,I1,a\nb,I2,b')]],
    ['X/Y/M', [file('train_y.csv', 'id,sugar,class\nc,30,C\na,10,A\nb,20,B'), file('train_m.csv', 'id,instrument\nb,I2\nc,I3\na,I1')]],
  ] as [string, InputFile[]][])('retains %s with native keyed ordering and no numerical payload', async (_topology, extra) => {
    const dataset = await imported([file('train_x.csv', x), ...extra]);
    expect(dataset.rawX).toEqual([[1,2], [3,4], [5,6]]);
    expect(dataset.input.axis).toEqual([2000,1000]);
    expect(dataset.input.spectra).toEqual([]);
    expect(dataset.rowManifest?.map(row => row.observation_id)).toEqual(['a','b','c']);
    expect(dataset.importProvenance?.roles_reviewed).toBe(true);
    expect(dataset.input).not.toHaveProperty('targets');
    if (extra.some(item => item.name.includes('_y'))) {
      expect(dataset.targets?.find(target => target.name === 'sugar')?.values).toEqual([10,20,30]);
      expect(dataset.targets?.find(target => target.name === 'class')?.values).toEqual(['A','B','C']);
      expect(dataset.targets?.find(target => target.name === 'class')?.type).toBe('categorical');
    }
    if (extra.some(item => item.name.includes('_m'))) expect(dataset.metadata.find(column => column.name === 'instrument')?.values).toEqual(['I1','I2','I3']);
  });
  it('retains train/test/predict and repeated source identities with distinct technical keys', async () => {
    const files = [file('train_x.csv', x), file('test_x.csv', 'id,2000,1000\na,7,8\nd,9,10'), file('predict_x.csv', 'id,2000,1000\na,11,12')];
    files.push(file('fixture.nirs4all.json', JSON.stringify({ schema_version: 1, sample_index: { by:'id', key:'id', observation_id:'id' }, sources: ['train','test','predict'].map(partition => ({ id:`${partition}_x`, input:`${partition}_x.csv`, role:'features', key:'id', partition, params:{has_header:true, delimiter:','} })) })));
    const dataset = await imported(files);
    expect(dataset.rowManifest?.map(row => row.partition)).toEqual(['predict','test','test','train','train','train']);
    expect(dataset.rowManifest?.filter(row => row.observation_id === 'a')).toHaveLength(3);
    expect(new Set(dataset.rowManifest?.map(row => row.key)).size).toBe(6);
    expect(dataset.rawX).toHaveLength(6);
    expect(dataset.targets).toEqual([]);
  });
  it('preserves unpartitioned combined source and requires reviewed roles', async () => {
    const files = [file('measurements.csv', 'id,2000,1000,target,batch\na,1,2,10,A\nb,3,4,20,B\nc,5,6,30,C')];
    const draft = prepareDataset(files, io, formats);
    const sources = draft.sources.map(source => ({ ...source, columns: source.columns.map(column => column.name === 'target' ? { ...column, assignedRole: 'y' as const } : column) }));
    const dataset = await assembleDatasetDraft(draft, buildExportConfig('Combined', sources), sources, io);
    expect(dataset.targets?.[0].values).toEqual([10,20,30]);
    expect(dataset.rowManifest?.every(row => row.partition === 'unpartitioned')).toBe(true);
    expect(dataset.metadata.find(column => column.name === 'batch')?.values).toEqual(['A','B','C']);
    await expect(importFiles(files)).rejects.toThrow('IMPORT_ROLE_REVIEW_REQUIRED');
  });
  it('keeps missing X and target cells as null with explicit masks', async () => {
    const dataset = await imported([file('train_x.csv', 'id,2000,1000\na,1,2\nb,,4\nc,5,6'), file('train_y.csv', 'id,sugar\na,10\nb,\nc,30')]);
    expect(dataset.rawX).toEqual([[1,2], [null,4], [5,6]]);
    expect(dataset.missingX).toEqual([[false,false], [true,false], [false,false]]);
    expect(dataset.targets?.[0].values).toEqual([10,null,30]);
    expect(dataset.targets?.[0].mask).toEqual([true,false,true]);
    expect(dataset.rowManifest).toHaveLength(3);
    expect(JSON.stringify(dataset)).not.toContain('NaN');
  });
  it('retains multiple metadata tables and explicit target-derived declarations', async () => {
    const draft = prepareDataset([file('train_x.csv', x), file('train_m.csv', 'id,instrument\nc,I3\na,I1\nb,I2'), file('train_metadata.csv', 'id,target_bucket\nb,high\na,low\nc,high')], io, formats);
    const config: ReviewedDatasetConfig = { ...buildExportConfig('Factors', draft.sources), metadata_declarations: { target_bucket: { role: 'factor', derived_from_target: true } } };
    const dataset = await assembleDatasetDraft(draft, config, draft.sources, io);
    expect(dataset.metadata.find(column => column.name === 'target_bucket')).toMatchObject({ values: ['low','high','high'], derived_from_target: true, evidence: 'declared' });
    expect(dataset.metadata.find(column => column.name === 'instrument')?.derived_from_target).toBe('unknown');
  });
  it('keeps partial keyed metadata only with an explicit allow-missing join', async () => {
    const draft = prepareDataset([file('train_x.csv', x), file('train_m.csv', 'id,batch\nc,C\na,A')], io, formats);
    const config = buildExportConfig('Partial', draft.sources);
    config.joins = config.joins.map(join => ({ ...join, strategy: 'allow_missing' }));
    const dataset = await assembleDatasetDraft(draft, config, draft.sources, io);
    expect(dataset.metadata.find(column => column.name === 'batch')?.values).toEqual(['A',null,'C']);
    expect(dataset.rowManifest).toHaveLength(3);
  });
  it('refuses duplicate join keys without replacing the review draft', async () => {
    const draft = prepareDataset([file('train_x.csv', x), file('train_m.csv', 'id,batch\na,A\na,B\nc,C')], io, formats);
    expect(draft.sources).toHaveLength(2);
    await expect(assembleDatasetDraft(draft, buildExportConfig('Duplicate', draft.sources), draft.sources, io)).rejects.toThrow();
  });
  it('refuses separate positional X/Y alignment and source deletion', () => {
    const draft = prepareDataset([file('train_x.csv', '2000,1000\n1,2\n3,4'), file('train_y.csv', 'sugar\n10\n20')], io, formats);
    expect(() => builderSpec(draft, buildExportConfig('No keys', draft.sources), draft.sources)).toThrow('DECLARED_KEY_JOIN_REQUIRED');
    expect(() => builderSpec(draft, buildExportConfig('Drop source', draft.sources.slice(0,1)), draft.sources.slice(0,1))).toThrow('SOURCE_REMOVAL');
  });
  it('retains metadata-only missingness, original target units and categorical dictionaries per block', async () => {
    const full = io.assembleDataset([file('train_x.csv', x)], [], JSON.stringify({ schema_version: 1, sources: [{ id: 'X', input: 'train_x.csv', role: 'features', key: 'id', partition: 'train' }] })) as ImportedAssembled;
    const block = full.blocks.train;
    block.metadata = { n_rows:3, columns:[{ name: 'reference', values: ['r',null,'s'] }] };
    block.y = { n_rows: 3, n_cols: 1, data: new Float64Array([4,5,NaN]) }; block.y_headers = ['concentration'];
    const dataset = await adaptImported(full, [file('train_x.csv', x)], { schema_version: 1, sources: [{ id:'X', role:'features', input:'train_x.csv', partition:'train' }], target_units: { concentration: 'mg/L' }, metadata_declarations: { reference: { role:'reference', derived_from_target:false } } });
    expect(dataset.targets?.[0]).toMatchObject({ unit:'mg/L', values:[4,5,null], mask:[true,true,false] });
    expect(dataset.metadata.find(column => column.name === 'reference')).toMatchObject({ role:'reference', values:['r',null,'s'] });
  });
  it('binds reviewed roles and declarations while keeping file hashes exact', async () => {
    const draft = prepareDataset([file('train_x.csv', x), file('train_m.csv', 'id,batch\na,A\nb,B\nc,C')], io, formats);
    const config = buildExportConfig('Binding', draft.sources);
    const first = await assembleDatasetDraft(draft, config, draft.sources, io);
    const changed: ReviewedDatasetConfig = { ...config, metadata_declarations: { batch: { role:'factor', derived_from_target:true } } };
    const second = await assembleDatasetDraft(draft, changed, draft.sources, io);
    expect(second.input.content_sha256).not.toBe(first.input.content_sha256);
    expect(second.importProvenance?.files).toEqual(first.importProvenance?.files);
    const reordered = { ...changed, metadata_declarations: { batch: { derived_from_target:true, role:'factor' as const } } };
    const third = await assembleDatasetDraft(draft, reordered, draft.sources, io);
    expect(third.input.content_sha256).toBe(second.input.content_sha256);
  });
  it('refuses unassigned tables instead of silently omitting prediction rows', () => {
    expect(() => prepareDataset([file('train_x.csv', x), file('predict_x.csv', x)], io, formats)).toThrow('IO_UNASSIGNED_INPUT');
  });
  it('does not reclassify an explicitly configured target as primary metadata',()=>{
    const config={schema_version:1,sources:[
      {id:'X',role:'features',input:'X.csv',partition:'train',key:'id'},
      {id:'Y',role:'targets',input:'Y.csv',partition:'train',key:'id',join:{left:'Y',right:'X',left_on:'id',right_on:'id',cardinality:'1:1',coverage:'complete'}}]};
    const draft=prepareDataset([file('X.csv',x),file('Y.csv','id,yield\na,1\nb,2\nc,3'),file('explicit.nirs4all.json',JSON.stringify(config))],io,formats);
    const sources=structuredClone(draft.sources);
    sources.find(source=>source.id==='Y')!.columns.find(column=>column.name==='yield')!.assignedRole='metadata';
    expect(()=>builderSpec(draft,buildExportConfig('Fixture',sources),sources)).toThrow('DECLARED_TARGET_CANNOT_BECOME_PRIMARY_METADATA');
  });
});
