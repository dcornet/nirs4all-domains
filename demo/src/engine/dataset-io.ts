/** Transport only: the published IO/Formats parsers own decoding, roles and joins. */
import type { BrowserInput, InputFile, LocalDataset } from './types';

export const MAX_IMPORT_BYTES = 8 * 1024 * 1024;
export const MAX_IMPORT_FILES = 32;
export const MAX_CELLS = 1_000_000;
interface Matrix { n_rows: number; n_cols: number; data: ArrayLike<number> }
interface Block {
  n_samples: number; source_ids: string[]; x: Matrix[]; feature_headers: string[][];
  header_units: string[]; metadata?: { columns: { name: string; values: (string | number | null)[] }[] };
}
interface Assembled {
  assembled_schema_version: number; name: string; blocks: Record<string, Block>;
  identity?: { provenance?: { observation_id?: string; sample_id?: string; group_id?: string } };
}
export async function sha256(bytes: Uint8Array): Promise<string> {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes.slice().buffer))].map(v => v.toString(16).padStart(2, '0')).join('');
}
export function checkFiles(files: InputFile[]) {
  if (!files.length || files.length > MAX_IMPORT_FILES || new Set(files.map(f => f.name)).size !== files.length)
    throw new Error('AMBIGUOUS_OR_EMPTY_FILE_SET');
  if (files.reduce((n, f) => n + f.bytes.byteLength, 0) > MAX_IMPORT_BYTES)
    throw new Error('IMPORT_BYTE_BUDGET_EXCEEDED');
  if (files.some(f => /(^|[\\/])\.\.([\\/]|$)/.test(f.name))) throw new Error('UNSAFE_RELATIVE_FILE_NAME');
  if (files.some(f => !/\.(csv|tsv|txt|json|spc|jdx|dx)$/i.test(f.name)))
    throw new Error('FORMAT_NOT_QUALIFIED_FOR_THIS_BOUNDED_BROWSER_IMPORT');
}

/** Preserve each original partition. No split generation, source fusion or silent row deletion. */
export async function adaptAssembled(full: Assembled, files: InputFile[], spec: unknown, warnings: string[]): Promise<LocalDataset> {
  if (full.assembled_schema_version !== 2) throw new Error('IO_ASSEMBLED_SCHEMA_V2_REQUIRED');
  const blocks = Object.entries(full.blocks).filter(([, b]) => b.n_samples > 0);
  if (!blocks.length) throw new Error('NO_SPECTRAL_POPULATION');
  if (blocks.some(([, b]) => b.x.length !== 1)) throw new Error('MULTISOURCE_SELECTION_REQUIRED_NO_IMPLICIT_FUSION');
  const first = blocks[0][1];
  const headers = first.feature_headers[0];
  const width = first.x[0].n_cols;
  if (!width || headers.length !== width) throw new Error('AXIS_WIDTH_MISMATCH');
  const values = headers.map(Number);
  const numeric = headers.every(h => h.trim() && Number.isFinite(Number(h))) &&
    (values.every((v, i) => !i || v > values[i - 1]) || values.every((v, i) => !i || v < values[i - 1]));
  const axis = numeric ? values : Array.from({ length: width }, (_, i) => i);
  const unit = numeric ? first.header_units[0] || 'unknown' : 'index';
  const sourceId = first.source_ids[0];
  if (blocks.some(([, b]) => b.source_ids[0] !== sourceId || JSON.stringify(b.feature_headers[0]) !== JSON.stringify(headers) || (numeric && (b.header_units[0] || 'unknown') !== unit)))
    throw new Error('INCOMPATIBLE_DECLARED_SOURCE_AXES');
  const count = blocks.reduce((n, [, b]) => n + b.n_samples, 0);
  if (count > 2_000 || count * width > MAX_CELLS) throw new Error('FULL_POPULATION_BROWSER_BUDGET_EXCEEDED');
  const ids: string[] = [], spectra: number[][] = [], partitions: LocalDataset['partitions'] = [];
  const columns = new Map<string, (string | number | null)[]>();
  const declaredId = full.identity?.provenance?.observation_id;
  let offset = 0;
  for (const [partition, b] of blocks) {
    const matrix = b.x[0];
    if (matrix.n_rows !== b.n_samples || matrix.n_cols !== width || matrix.data.length !== b.n_samples * width)
      throw new Error('MISALIGNED_IO_MATRIX');
    const observationIds = b.metadata?.columns.find(c => c.name === declaredId)?.values;
    const blockIds: string[] = [];
    for (let row = 0; row < b.n_samples; row++) {
      // A row coordinate names an observation only; it never invents a physical specimen.
      const id = observationIds?.[row] === null || observationIds?.[row] === undefined ? JSON.stringify([sourceId, partition, row]) : String(observationIds[row]);
      blockIds.push(id); ids.push(id);
      const cells = Array.from({ length: width }, (_, j) => matrix.data[row * width + j]);
      if (cells.some(v => !Number.isFinite(v))) throw new Error('NONFINITE_X_NO_IMPLICIT_IMPUTATION');
      spectra.push(cells);
    }
    for (const existing of columns.values()) existing.push(...Array(b.n_samples).fill(null));
    for (const column of b.metadata?.columns ?? []) {
      if (column.values.length !== b.n_samples) throw new Error('MISALIGNED_IO_METADATA');
      if (!columns.has(column.name)) columns.set(column.name, Array(offset + b.n_samples).fill(null));
      const destination = columns.get(column.name)!;
      column.values.forEach((value, i) => { destination[offset + i] = value; });
    }
    partitions.push({ name: partition, observation_ids: blockIds }); offset += b.n_samples;
  }
  if (new Set(ids).size !== ids.length) throw new Error('DUPLICATE_OBSERVATION_ID_REQUIRES_IO_DECLARATION');
  // Bind exact file bytes/names in order; none are placed in reports.
  const fileBindings = await Promise.all(files.map(async file => ({ name: file.name, sha256: await sha256(file.bytes) })));
  const contentHash = await sha256(new TextEncoder().encode(JSON.stringify(fileBindings)));
  const input: BrowserInput = {
    schema_version: 1, dataset_id: full.name || 'Imported dataset', source_id: sourceId,
    content_sha256: contentHash, observation_ids: ids, axis, axis_unit: unit, spectra,
  };
  const groupName = full.identity?.provenance?.group_id;
  if (groupName && columns.has(groupName)) {
    const groups = columns.get(groupName)!;
    if (groups.every(v => v !== null && String(v).trim())) input.group_ids = groups.map(String);
    else warnings.push('Declared group column is incomplete; group exclusions are unavailable, not fabricated.');
  }
  return { input, metadata: [...columns].map(([name, values]) => ({ name, values })),
    partitions, headers, warnings: [...warnings,
      'IO-inferred roles are declarations to review; target values are not passed to Domains.',
      ...(numeric ? [] : ['Non-numeric original headers retained; the display axis is explicitly a logical band index.']),
      ...(partitions.length > 1 ? ['All declared partitions are retained in a descriptive full-X fit. This is transductive, not train-fitted support.'] : [])],
    importSpec: spec, identityOrigin: declaredId ? 'IO-declared observation identities; physical/reference evidence unverified' : 'Original source/partition/row coordinates; observation identities only',
    license: 'User-supplied data; no redistribution permission inferred', mode: 'user_computed_live' };
}

export async function importFiles(files: InputFile[]): Promise<LocalDataset> {
  checkFiles(files);
  const [io, formats] = await Promise.all([import('virtual:nirs4all-io'), import('virtual:nirs4all-formats')]);
  await Promise.all([io.init(), formats.init()]);
  const records: { source: string; records: unknown[] }[] = [];
  const sidecars = Object.fromEntries(files.map(f => [f.name, f.bytes]));
  const config = files.find(f => f.name.endsWith('.nirs4all.json'));
  const raw = files.filter(f => f !== config);
  for (const file of raw) {
    if (/\.(csv|tsv|txt)$/i.test(file.name)) continue;
    const decoded = formats.openWithSidecars(file.name, file.bytes, sidecars) as unknown[];
    if (decoded?.length) records.push({ source: file.name, records: decoded });
  }
  const plan = config ? null : io.inferDataset(raw, records as never, {}) as { resolved_spec?: Record<string, unknown>; warnings?: string[] };
  const spec = config ? JSON.parse(new TextDecoder().decode(config.bytes)) as Record<string, unknown> : structuredClone(plan?.resolved_spec);
  if (!spec || !Array.isArray(spec.sources) || !spec.sources.length) throw new Error('IO_DATASET_CONFIGURATION_REQUIRED');
  if (spec.aggregate || spec.repetition) throw new Error('AGGREGATION_NOT_ADMITTED_IN_OBSERVATION_DIAGNOSTIC');
  // Preserve missing cells for an explicit refusal instead of IO's default row-drop policy.
  spec.params = { ...(spec.params as object), na: { policy: 'ignore' } };
  spec.sources = (spec.sources as Record<string, unknown>[]).map(s => ({ ...s, params: { ...(s.params as object), na: { policy: 'ignore' } } }));
  io.validate(JSON.stringify(spec));
  const decoded = new Set(records.map(r => r.source));
  const full = io.assembleDataset(raw.filter(f => !decoded.has(f.name)), records as never, JSON.stringify(spec)) as Assembled;
  return adaptAssembled(full, files, spec, plan?.warnings ?? []);
}
