/** IO owns parsing, inference, keyed joins and assembly; UI owns role review. */
import { buildExportConfig, type DatasetExportConfig, type DatasetRole, type DatasetSource } from 'nirs4all-ui/datasetBuilder';
import type { AssembledDataset, DatasetPlan, DatasetSpec, RecordSet, SourceSpec } from '@nirs4all/io-wasm/types';
import { checkFiles, MAX_CELLS, sha256 } from './dataset-io';
import type { ImportedMetadata, ImportedRow, ImportedTarget, ImportedValue, InputFile, LocalDataset, MetadataRole, PartitionRole } from './types';

export interface IoRuntime {
  inferDataset: typeof import('@nirs4all/io-wasm').inferDataset;
  assembleDataset: typeof import('@nirs4all/io-wasm').assembleDataset;
  validate: typeof import('@nirs4all/io-wasm').validate;
}
export interface FormatsRuntime { openWithSidecars: typeof import('@nirs4all/formats-wasm').openWithSidecars }
/** Plain structured-cloneable data; runtime handles never cross the worker seam. */
export interface DatasetDraft {
  files: InputFile[]; records: RecordSet[]; spec: DatasetSpec; sources: DatasetSource[];
  warnings: string[]; taskType: string | null;
}
export interface ReviewedImport { draft: DatasetDraft; config: DatasetExportConfig; sources: DatasetSource[] }
export interface MetadataDeclaration { role: MetadataRole; derived_from_target: boolean | 'unknown'; unit?: string }
export interface ReviewedDatasetConfig extends DatasetExportConfig { metadata_declarations?: Record<string, MetadataDeclaration> }

let ioRuntime: Promise<IoRuntime> | undefined;
let formatsRuntime: Promise<FormatsRuntime> | undefined;
let importObserver:(phase:string,component:string)=>void=()=>{};
export function setImportRuntimeObserver(observer:typeof importObserver){importObserver=observer;}
export async function loadImportRuntime(needsFormats = false): Promise<{ io: IoRuntime; formats: FormatsRuntime }> {
  importObserver('IO_RUNTIME_LOADING','io');
  const io = await (ioRuntime ??= import('virtual:nirs4all-io').then(async io => {
    await io.init(); return io;
  }).catch(error => { ioRuntime = undefined; throw error; }));
  importObserver('IO_RUNTIME_READY','io');
  // Tables are parsed by IO. Assembly consumes already decoded records and must
  // not initialize Formats in its separate worker merely to reassemble them.
  if(needsFormats)importObserver('FORMATS_RUNTIME_LOADING','formats');
  const formats = needsFormats ? await (formatsRuntime ??= import('virtual:nirs4all-formats').then(async formats => {
    await formats.init(); return formats;
  }).catch(error => { formatsRuntime = undefined; throw error; })) : {
    openWithSidecars() { throw new Error('FORMATS_NOT_INITIALIZED_FOR_THIS_TABLE_ONLY_IMPORT'); },
  };
  if(needsFormats)importObserver('FORMATS_RUNTIME_READY','formats');
  return { io, formats };
}

function diagnosticSpec(input: DatasetSpec): DatasetSpec {
  const spec = structuredClone(input);
  if (spec.aggregate || spec.repetition) throw new Error('AGGREGATION_NOT_ADMITTED_IN_OBSERVATION_DIAGNOSTIC');
  spec.params = { ...spec.params, na: { policy: 'ignore' } };
  spec.sources = spec.sources.map(source => ({ ...source, params: { ...source.params, na: { policy: 'ignore' } } }));
  return spec;
}
const roles: Record<string, DatasetRole> = { features: 'x', targets: 'y', metadata: 'metadata', id: 'id', ignore: 'ignored' };
type ColumnPlan = { ref: string; column_roles: { col: string; role: string }[] };
const namesOf = (source: SourceSpec): string[] => Array.isArray(source.input) ? source.input as string[] : [source.input];
const rawFiles = (files: InputFile[], records: RecordSet[]) => files.filter(file => !records.some(record => record.source === file.name));
const canonical = (value: unknown): unknown => Array.isArray(value) ? value.map(canonical)
  : value && typeof value === 'object' ? Object.fromEntries(Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([key, item]) => [key, canonical(item)])) : value;

/** A failed preliminary join remains reviewable; never invent a positional alignment. */
export function prepareDataset(files: InputFile[], io: IoRuntime, formats: FormatsRuntime): DatasetDraft {
  checkFiles(files);
  const configFile = files.find(file => file.name.endsWith('.nirs4all.json'));
  const dataFiles = files.filter(file => file !== configFile);
  const sidecars = Object.fromEntries(files.map(file => [file.name, file.bytes]));
  const records: RecordSet[] = [];
  for (const file of dataFiles) {
    if (/\.(csv|tsv|txt)$/i.test(file.name)) continue;
    const decoded = formats.openWithSidecars(file.name, file.bytes, sidecars) as unknown[];
    if (decoded?.length) records.push({ source: file.name, records: decoded });
  }
  const plan = io.inferDataset(dataFiles, records, {}) as DatasetPlan;
  const spec = diagnosticSpec(configFile ? JSON.parse(new TextDecoder().decode(configFile.bytes)) as DatasetSpec : plan.resolved_spec);
  if (!spec?.sources?.length) throw new Error('IO_DATASET_CONFIGURATION_REQUIRED');
  const declaredNames = spec.sources.flatMap(namesOf);
  if (dataFiles.some(file => /\.(csv|tsv|txt)$/i.test(file.name) && !declaredNames.includes(file.name)) || records.some(record => !declaredNames.includes(record.source)))
    throw new Error('IO_UNASSIGNED_INPUT_REQUIRES_EXPLICIT_CONFIGURATION');
  const warnings = [...(plan.warnings ?? [])];
  let preview: AssembledDataset | undefined;
  try { preview = io.assembleDataset(rawFiles(dataFiles, records), records, JSON.stringify(spec)) as AssembledDataset; }
  catch { warnings.push('Preliminary assembly is unresolved. Review column roles and declared join keys; IO will validate the final assembly.'); }
  const sources = spec.sources.map((source): DatasetSource => {
    const names = namesOf(source);
    const blocks = Object.entries(preview?.blocks ?? {}).filter(([partition]) => !source.partition || partition === source.partition).map(([, block]) => block);
    const block = blocks[0];
    const spectral = block?.source_ids.indexOf(source.id) ?? -1;
    const columns = new Map<string, DatasetRole>();
    let inferred = (plan.columns as ColumnPlan[]).find(column => names.includes(column.ref));
    // File conventions can omit column decisions. Ask the public IO inferencer
    // for that table's columns, using neutral naming solely for this preview.
    if (!inferred && names.length === 1 && /\.(csv|tsv|txt)$/i.test(names[0])) {
      const file = dataFiles.find(candidate => candidate.name === names[0]);
      if (file) {
        try {
          const local = io.inferDataset([{ ...file, name: `preview.${file.name.split('.').pop()}` }], [], {}) as DatasetPlan;
          inferred = (local.columns as ColumnPlan[])[0];
        } catch { /* Final native validation explains unsupported input. */ }
      }
    }
    for (const column of inferred?.column_roles ?? []) {
      const role = roles[column.role] ?? 'metadata';
      columns.set(column.col, role === 'id' ? role : source.role === 'targets' ? 'y' : source.role === 'metadata' ? 'metadata' : role);
    }
    const selectors = source.columns;
    if (Array.isArray(selectors)) for (const selector of selectors as { role: string; select: unknown }[]) {
      if (Array.isArray(selector.select)) for (const name of selector.select as string[]) columns.set(name, roles[selector.role] ?? 'metadata');
    }
    else if (selectors && typeof selectors === 'object') for (const [role, names] of Object.entries(selectors)) {
      if (Array.isArray(names)) for (const name of names as string[]) columns.set(name, roles[role] ?? 'metadata');
    }
    if (spectral >= 0) for (const name of block.feature_headers[spectral]) columns.set(name, 'x');
    if (source.role === 'targets' || source.role === 'mixed') for (const name of block?.y_headers ?? []) columns.set(name, columns.get(name) ?? 'y');
    if (source.role === 'metadata' || source.role === 'mixed') for (const column of block?.metadata?.columns ?? []) {
      const owner = spec.sources.find(other => column.name.startsWith(`${other.id}__`));
      if (owner && owner.id !== source.id) continue;
      if (!owner && inferred && !columns.has(column.name)) continue;
      const name = owner ? column.name.slice(owner.id.length + 2) : column.name;
      columns.set(name, columns.get(name) ?? 'metadata');
    }
    if (typeof source.key === 'string') columns.set(source.key, 'id');
    const params = source.params ?? {};
    return { id: source.id, name: names.join(', '), kind: 'file', fileType: names[0]?.split('.').pop() ?? 'unknown',
      signalType: spectral >= 0 || source.role === 'features' ? 'spectra' : source.role === 'targets' ? 'target' : 'metadata',
      status: preview ? 'parsed' : 'warning', rowCount: blocks.reduce((count, block) => count + block.n_samples, 0), columnCount: columns.size,
      sizeBytes: dataFiles.filter(file => names.includes(file.name)).reduce((count, file) => count + file.bytes.byteLength, 0),
      parsing: { ...(typeof params.delimiter === 'string' ? { separator: params.delimiter } : {}),
        headerMode: params.has_header === false ? 'none' : 'horizontal', decimal: params.decimal_separator === ',' ? ',' : '.' },
      usage: { useAs: source.partition === 'predict' ? 'auxiliary' : source.role === 'targets' ? source.partition === 'test' ? 'y_test' : 'y_train'
        : source.role === 'metadata' ? 'metadata' : source.partition === 'test' ? 'x_test' : source.partition === 'train' ? 'x_train' : 'x_train_test' },
      columns: [...columns].map(([name, assignedRole], index) => {
        const metadata = block?.metadata?.columns.find(column => column.name === name || column.name === `${source.id}__${name}`)?.values[0];
        const x = block?.feature_headers[spectral]?.indexOf(name) ?? -1;
        const y = block?.y_headers.indexOf(name) ?? -1;
        const raw = metadata ?? (x >= 0 ? block?.x[spectral].data[x] : y >= 0 ? block?.y?.data[y] : null);
        const categories = block?.y_categorical[name]?.categories;
        const value = categories && typeof raw === 'number' ? categories[raw] ?? null : raw;
        return { id: `${source.id}:${index}`, name, assignedRole, manual: false,
          detectedType: typeof value === 'number' && Number.isFinite(value) ? 'float' : typeof value === 'string' ? 'text' : typeof value === 'boolean' ? 'boolean' : 'unknown',
          previewValue: typeof value === 'boolean' ? String(value) : typeof value === 'number' && !Number.isFinite(value) ? null : value,
          ...(categories ? { semanticType: 'classification' as const } : {}) };
      }) };
  });
  return { files, records, spec, sources, warnings, taskType: plan.task_type?.value ?? null };
}

export async function prepareImport(files: InputFile[]): Promise<DatasetDraft> {
  checkFiles(files);
  const needsFormats = files.some(file => !file.name.endsWith('.nirs4all.json') && !/\.(csv|tsv|txt)$/i.test(file.name));
  const { io, formats } = await loadImportRuntime(needsFormats);
  importObserver('IMPORT_RUNNING','io');
  const draft=prepareDataset(files,io,formats);
  importObserver('IMPORT_COMPLETE','io');return draft;
}

function sourcePartition(source: DatasetSource, original: SourceSpec): string | undefined {
  if (source.columns.some(column => column.assignedRole === 'partition')) return undefined;
  const use = source.usage.useAs;
  if (use === 'x_test' || use === 'y_test') return 'test';
  if (use === 'x_train' || use === 'y_train') return 'train';
  return original.partition;
}

/** Translate reviewed declarations only. Native IO validates cardinality and joins. */
export function builderSpec(draft: DatasetDraft, config: DatasetExportConfig, sources: DatasetSource[]): DatasetSpec {
  const spec = diagnosticSpec(draft.spec);
  if (config.replicates && config.replicates.strategy !== 'keep') throw new Error('AGGREGATION_NOT_ADMITTED_IN_OBSERVATION_DIAGNOSTIC');
  if (config.partition?.type === 'random') throw new Error('IMPLICIT_PARTITION_GENERATION_NOT_ADMITTED');
  if (sources.length !== draft.spec.sources.length || new Set(sources.map(source => source.id)).size !== sources.length) throw new Error('SOURCE_REMOVAL_NOT_ADMITTED');
  spec.name = config.name;
  spec.target_tasks = Object.fromEntries(config.targets.map(target => [target.column, target.task]));
  if ((config as ReviewedDatasetConfig).metadata_declarations) spec.metadata_declarations = (config as ReviewedDatasetConfig).metadata_declarations;
  const nativeRoles: Record<DatasetRole, string> = { x: 'features', y: 'targets', metadata: 'metadata', id: 'metadata',
    partition: 'metadata', replicate: 'metadata', group: 'metadata', ignored: 'ignore' };
  const identity: Record<string, unknown> = { ...(spec.sample_index as object ?? {}) };
  const spectralJoinKeys = new Set<string>();
  spec.sources = sources.map(source => {
    const original = draft.spec.sources.find(candidate => candidate.id === source.id);
    if (!original) throw new Error('UNKNOWN_IMPORT_SOURCE');
    const explicitTargets=draft.files.some(file=>file.name.endsWith('.nirs4all.json'))&&
      (original.role==='targets'||original.columns&&typeof original.columns==='object'&&'targets' in original.columns);
    if(explicitTargets){
      const declared=draft.sources.find(candidate=>candidate.id===source.id)?.columns.filter(column=>column.assignedRole==='y')??[];
      if(declared.some(column=>source.columns.some(next=>next.name===column.name&&!['y','ignored'].includes(next.assignedRole))))
        throw new Error('DECLARED_TARGET_CANNOT_BECOME_PRIMARY_METADATA');
    }
    if (source.parsing.headerMode === 'vertical' || ['image', 'hyperspectral', 'timeseries'].includes(source.signalType)) throw new Error('TWO_DIMENSIONAL_SPECTRAL_SOURCE_REQUIRED');
    const columns: Record<string, string[]> = {};
    for (const column of source.columns) (columns[nativeRoles[column.assignedRole]] ??= []).push(column.name);
    if (!source.columns.length) throw new Error('SOURCE_COLUMNS_REQUIRE_EXPLICIT_IO_CONFIGURATION');
    const next: SourceSpec = { ...original, role: 'mixed', columns,
      params: { ...original.params, na: { policy: 'ignore' }, ...(source.parsing.separator ? { delimiter: source.parsing.separator } : {}),
        has_header: source.parsing.headerMode !== 'none', decimal_separator: source.parsing.decimal ?? '.' } };
    const partition = sourcePartition(source, original);
    if (partition) next.partition = partition; else delete next.partition;
    const id = source.columns.find(column => column.assignedRole === 'id' && column.name === original.key)
      ?? source.columns.find(column => column.assignedRole === 'id');
    if (id) {
      next.key = id.name;
      if (source.columns.some(column => column.assignedRole === 'x')) {
        spectralJoinKeys.add(id.name);
        if (spectralJoinKeys.size > 1) throw new Error('INCOMPATIBLE_DECLARED_SPECTRAL_JOIN_KEYS');
        identity.by = 'id'; identity.key = id.name;
        identity.observation_id ??= id.name;
      }
    }
    else delete next.key;
    const group = source.columns.find(column => column.assignedRole === 'group');
    if (group) identity.group_id = group.name;
    const repeat = source.columns.find(column => column.assignedRole === 'replicate');
    if (repeat) identity.repetition_id = repeat.name;
    const partitionColumn = source.columns.find(column => column.assignedRole === 'partition');
    if (partitionColumn) spec.partitions = { by: 'column', column: partitionColumn.name,
      train_values: ['train', 'calibration', 'cal', 'val', 'validation', 'dev', 'development'],
      test_values: ['test', 'retained_test'], predict_values: ['predict', 'prediction'], unknown_policy: 'error' };
    return next;
  });
  for (const source of spec.sources) {
    const reviewed = sources.find(candidate => candidate.id === source.id)!;
    const hasX = reviewed.columns.some(column => column.assignedRole === 'x');
    const anchors = spec.sources.filter(candidate => candidate.id !== source.id && candidate.partition === source.partition &&
      sources.find(item => item.id === candidate.id)!.columns.some(column => column.assignedRole === 'x'));
    if (hasX) { delete source.join; continue; }
    if (!anchors.length) throw new Error('DECLARED_PARTITION_SPECTRAL_ANCHOR_REQUIRED');
    const oldAnchor = (source.join as { right?: string } | undefined)?.right;
    const declared = config.joins.find(join => join.right === reviewed.name);
    const anchor = anchors.find(candidate => candidate.id === oldAnchor) ?? anchors.find(candidate => sources.find(item => item.id === candidate.id)?.name === declared?.left) ?? (anchors.length === 1 ? anchors[0] : undefined);
    if (!anchor || typeof source.key !== 'string' || typeof anchor.key !== 'string') throw new Error('DECLARED_KEY_JOIN_REQUIRED_NO_POSITIONAL_ALIGNMENT');
    if (declared && !['strict', 'allow_missing', 'left'].includes(declared.strategy)) throw new Error('ROW_DELETING_JOIN_NOT_ADMITTED');
    // In published IO's materializer, left_on addresses the assembled X frame
    // and right_on addresses this attached table, including differently named keys.
    source.join = { left: anchor.id, right: anchor.id, left_on: anchor.key, right_on: source.key,
      cardinality: '1:1', coverage: declared?.strategy === 'allow_missing' || declared?.strategy === 'left' ? 'warn' : 'complete' };
  }
  if (Object.keys(identity).length) spec.sample_index = identity; else delete spec.sample_index;
  return spec;
}

function roleOf(name: string, spec: DatasetSpec): PartitionRole {
  // IO defaults an unpartitioned source to a train block; retain its original declaration.
  const explicit = Boolean(spec.partitions) || spec.sources.some(source => source.partition);
  if (!explicit) return 'unpartitioned';
  if (['train', 'calibration', 'cal', 'val', 'validation', 'dev', 'development'].includes(name)) return 'train';
  if (['test', 'retained_test'].includes(name)) return 'test';
  if (['predict', 'prediction'].includes(name)) return 'predict';
  throw new Error('UNKNOWN_DECLARED_PARTITION_ROLE');
}
type IoIdentity = { observation_id?: string; sample_id?: string; group_id?: string; repetition_id?: string };
export type ImportedAssembled = AssembledDataset & { assembled_schema_version: number; identity?: { provenance?: IoIdentity } };
const cell = (value: unknown): ImportedValue => {
  if (value === null || value === undefined || typeof value === 'number' && !Number.isFinite(value)) return null;
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return value;
  throw new Error('UNSUPPORTED_METADATA_CELL_TYPE');
};
function declaredMetadata(name: string, sources: DatasetSource[], spec: DatasetSpec, identity: IoIdentity): Partial<ImportedMetadata> {
  const owner = spec.sources.find(source => name.startsWith(`${source.id}__`));
  const plain = owner ? name.slice(owner.id.length + 2) : name;
  const candidates = sources.filter(source => !owner || source.id === owner.id).flatMap(source => source.columns.filter(column => column.name === plain).map(column => ({ source, column })));
  const declaration = candidates.length === 1 ? candidates[0] : undefined;
  const role: MetadataRole = name === identity.observation_id ? 'observation_id' : name === identity.group_id ? 'group'
    : name === identity.repetition_id ? 'repetition' : name === identity.sample_id ? 'specimen'
    : declaration?.column.assignedRole === 'group' ? 'group' : declaration?.column.assignedRole === 'replicate' ? 'repetition'
    : declaration?.column.assignedRole === 'partition' ? 'partition' : declaration ? 'factor' : 'unknown';
  // Optional content declarations can document target derivation and units. Absence stays unknown.
  const declarations = spec.metadata_declarations as Record<string, Partial<MetadataDeclaration>> | undefined;
  // IO can merge an identically named M field across partition-specific tables.
  // Reuse their source-bound declarations only when every candidate agrees;
  // never choose one partition's identity declaration arbitrarily.
  const extras = candidates.map(candidate => declarations?.[`${candidate.source.id}__${plain}`]);
  const agreed = extras.length > 0 && extras.every(extra => JSON.stringify(canonical(extra ?? null)) === JSON.stringify(canonical(extras[0] ?? null)));
  const extra = declarations?.[name] ?? (agreed ? extras[0] : undefined);
  const derived = extra?.derived_from_target === true || extras.some(value => value?.derived_from_target === true)
    ? true : extra?.derived_from_target ?? 'unknown';
  const origins = [...new Set(candidates.map(candidate => candidate.source.id))];
  return { role: extra?.role ?? role, unit: extra?.unit ?? null,
    origin: owner?.id ?? declaration?.source.id ?? (origins.length ? JSON.stringify(origins) : 'IO assembled metadata'),
    derived_from_target: derived, evidence: declaration || extra ? 'declared' : 'unknown' };
}

/** Import retains nullable X/Y/M; it produces no numerical request and performs no fit. */
export async function adaptImported(full: ImportedAssembled, files: InputFile[], spec: DatasetSpec, warnings: string[] = [], sources: DatasetSource[] = [], rolesReviewed = false): Promise<LocalDataset> {
  if (full.assembled_schema_version !== 2) throw new Error('IO_ASSEMBLED_SCHEMA_V2_REQUIRED');
  const blocks = Object.entries(full.blocks).filter(([, block]) => block.n_samples > 0);
  if (!blocks.length) throw new Error('NO_SPECTRAL_POPULATION');
  if (blocks.some(([, block]) => block.x.length !== 1)) throw new Error('MULTISOURCE_SELECTION_REQUIRED_NO_IMPLICIT_FUSION');
  const first = blocks[0][1];
  const headers = first.feature_headers[0];
  const width = first.x[0].n_cols;
  if (!width || headers.length !== width) throw new Error('AXIS_WIDTH_MISMATCH');
  if (blocks.some(([, block]) => block.x[0].n_cols !== width || JSON.stringify(block.feature_headers[0]) !== JSON.stringify(headers) || block.header_units[0] !== first.header_units[0])) throw new Error('INCOMPATIBLE_DECLARED_SOURCE_AXES');
  const n = blocks.reduce((count, [, block]) => count + block.n_samples, 0);
  if (n > 2_000 || n * width > MAX_CELLS) throw new Error('FULL_POPULATION_BROWSER_BUDGET_EXCEEDED');
  const values = headers.map(Number);
  const numeric = headers.every(header => header.trim() && Number.isFinite(Number(header))) &&
    (values.every((value, index) => !index || value > values[index - 1]) || values.every((value, index) => !index || value < values[index - 1]));
  const rawX: (number | null)[][] = [], missingX: boolean[][] = [], rowManifest: ImportedRow[] = [], partitions: LocalDataset['partitions'] = [];
  const columns = new Map<string, ImportedValue[]>(), targets = new Map<string, ImportedTarget>();
  const identity = full.identity?.provenance ?? {};
  let offset = 0;
  for (const [partition, block] of blocks) {
    const role = roleOf(partition, spec), x = block.x[0];
    if (x.n_rows !== block.n_samples || x.data.length !== block.n_samples * width) throw new Error('MISALIGNED_IO_MATRIX');
    const ids: string[] = [];
    const sourceSpec = spec.sources.find(source => source.id === block.source_ids[0]);
    const observed = block.metadata?.columns.find(column => column.name === identity.observation_id)?.values
      ?? block.metadata?.columns.find(column => column.name === sourceSpec?.key)?.values;
    const partitionColumn = (spec.partitions as { column?: string } | undefined)?.column;
    const originalPartitions = block.metadata?.columns.find(column => column.name === partitionColumn)?.values;
    for (let row = 0; row < block.n_samples; row++) {
      const key = JSON.stringify([block.source_ids[0], partition, row]); ids.push(key);
      rowManifest.push({ key, observation_id: observed?.[row] === null || observed?.[row] === undefined ? null : String(observed[row]),
        partition: role, original_partition: originalPartitions?.[row] === null || originalPartitions?.[row] === undefined ? partition : String(originalPartitions[row]), source_id: block.source_ids[0] });
      const cells = Array.from({ length: width }, (_, column) => cell(x.data[row * width + column]) as number | null);
      rawX.push(cells); missingX.push(cells.map(value => value === null));
    }
    for (const values of columns.values()) values.push(...Array(block.n_samples).fill(null));
    for (const column of block.metadata?.columns ?? []) {
      if (column.values.length !== block.n_samples) throw new Error('MISALIGNED_IO_METADATA');
      if (!columns.has(column.name)) columns.set(column.name, Array(offset + block.n_samples).fill(null));
      column.values.forEach((value, row) => { columns.get(column.name)![offset + row] = cell(value); });
    }
    for (const target of targets.values()) { target.values.push(...Array(block.n_samples).fill(null)); target.mask.push(...Array(block.n_samples).fill(false)); }
    if (block.y) {
      if (block.y.n_rows !== block.n_samples || block.y.n_cols !== block.y_headers.length || block.y.data.length !== block.n_samples * block.y.n_cols) throw new Error('MISALIGNED_IO_TARGETS');
      for (let column = 0; column < block.y_headers.length; column++) {
        const name = block.y_headers[column], categories = block.y_categorical[name]?.categories;
        const task = (spec.target_tasks as Record<string, string> | undefined)?.[name];
        const type = categories || ['classification', 'multiclass', 'multilabel', 'ordinal'].includes(task ?? '') ? 'categorical' : 'numeric';
        if (targets.has(name) && targets.get(name)!.type !== type) throw new Error('INCOMPATIBLE_DECLARED_TARGET_TYPES');
        if (!targets.has(name)) targets.set(name, { name, type, unit: null, values: Array(offset + block.n_samples).fill(null), mask: Array(offset + block.n_samples).fill(false), origin: 'IO assembled target' });
        const target = targets.get(name)!;
        const units = spec.target_units as Record<string, string> | undefined;
        target.unit = units?.[name] ?? null;
        for (let row = 0; row < block.n_samples; row++) {
          const value = block.y.data[row * block.y.n_cols + column];
          const present = Number.isFinite(value);
          if (categories && present && (!Number.isInteger(value) || categories[value] === undefined)) throw new Error('INVALID_IO_CATEGORICAL_CODE');
          target.values[offset + row] = present ? categories ? categories[value] : type === 'categorical' ? String(value) : value : null;
          target.mask[offset + row] = present;
        }
      }
    }
    partitions.push({ name: partition, observation_ids: ids }); offset += block.n_samples;
  }
  const bindings = await Promise.all(files.map(async file => ({ name: file.name, sha256: await sha256(file.bytes) })));
  // Review changes alter execution meaning, even when source bytes stay identical.
  const contentHash = await sha256(new TextEncoder().encode(JSON.stringify(canonical({ files: bindings, reviewed_spec: spec }))));
  const fileContentHash = await sha256(new TextEncoder().encode(JSON.stringify(bindings)));
  const reviewedSpecHash = await sha256(new TextEncoder().encode(JSON.stringify(canonical(spec))));
  const sourceIds = [...new Set(blocks.flatMap(([, block]) => block.source_ids))];
  const metadata = [...columns].map(([name, values]): ImportedMetadata => ({ name, values, ...declaredMetadata(name, sources, spec, identity),
    type: values.every(value => value === null) ? 'unknown' : values.every(value => value === null || typeof value === 'number') ? 'numeric'
      : values.every(value => value === null || typeof value === 'boolean') ? 'boolean' : 'categorical' }));
  return { input: { schema_version: 1, dataset_id: full.name || 'Imported dataset', source_id: sourceIds.length === 1 ? sourceIds[0] : JSON.stringify(sourceIds),
    content_sha256: contentHash, observation_ids: rowManifest.map(row => row.key), axis: numeric ? values : headers.map((_, index) => index),
    axis_unit: numeric ? first.header_units[0] || 'unknown' : 'index', spectra: [] }, rawX, missingX, targets: [...targets.values()], rowManifest,
    metadata, partitions, headers, importSpec: spec, identityOrigin: identity.observation_id ? 'IO-declared observation identities; physical/reference independence unknown' : 'Technical source/partition/row coordinates; source observation identity unavailable',
    license: 'User-supplied data; no redistribution permission inferred', mode: 'user_computed_live',
    importProvenance: { protocol: 'domains.import_xy_m.v1', files: bindings, file_content_sha256: fileContentHash, reviewed_spec_sha256: reviewedSpecHash,
      original_source_ids: sourceIds, roles_reviewed: rolesReviewed, identity_independence: 'unknown' },
    warnings: [...warnings, ...(full.warnings ?? []), 'Import preserves X/Y/M locally. Each scientific operation must request its own authorized population and fields; no Y values are admitted.',
      'Pinned IO 0.2.14 materializes X/Y at float32 precision before Float64 transport. Source hashes bind original bytes; exact preservation of their numeric decimal precision is not claimed.',
      ...(!numeric ? ['Original headers retained; the display axis is a logical band index.'] : []),
      ...(missingX.some(row => row.some(Boolean)) ? ['Missing X cells retained without imputation or row deletion; operations needing complete X may be unavailable.'] : [])] };
}

export async function assembleDatasetDraft(draft: DatasetDraft, config: DatasetExportConfig, sources: DatasetSource[], io: IoRuntime): Promise<LocalDataset> {
  checkFiles(draft.files);
  const spec = builderSpec(draft, config, sources); io.validate(JSON.stringify(spec));
  const dataFiles = draft.files.filter(file => !file.name.endsWith('.nirs4all.json'));
  const assembled = io.assembleDataset(rawFiles(dataFiles, draft.records), draft.records, JSON.stringify(spec)) as ImportedAssembled;
  return adaptImported(assembled, draft.files, spec, draft.warnings, sources, true);
}
export async function assembleImport(draft: DatasetDraft, config: DatasetExportConfig, sources: DatasetSource[]): Promise<LocalDataset> {
  const { io } = await loadImportRuntime();importObserver('IMPORT_RUNNING','io');
  const dataset=await assembleDatasetDraft(draft,config,sources,io);
  importObserver('IMPORT_COMPLETE','io');return dataset;
}
/** Explicit programmatic review seam; UI consumers must use the DatasetBuilder first. */
export const reviewedConfig = (name: string, sources: DatasetSource[]) => buildExportConfig(name, sources);
