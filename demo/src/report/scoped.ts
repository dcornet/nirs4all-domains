/** Safe presentation projection for operation-scoped browser evidence.
 * This module counts and labels imported fields; it does not analyze values.
 */
import type { LocalDataset } from '../engine/types';
import type { UiEvidence, UiFinding,UiResult } from '../ui-types';
import type { ScopedResult } from '../../../bindings/wasm/scoped';

const safeCount = (values: readonly unknown[] | undefined): number => values?.length ?? 0;

/** Counts and declarations only: never returns X/Y values or arbitrary metadata values. */
export function scopedInventory(data: LocalDataset) {
  const rows = data.rowManifest ?? [];
  const partitions = new Map<string, number>();
  for (const row of rows) partitions.set(row.partition, (partitions.get(row.partition) ?? 0) + 1);
  const fields = data.metadata.map(field => ({
    name: field.name,
    role: field.role ?? 'unknown',
    unit:field.unit??null,
    kind: field.type ?? 'unknown',
    origin: field.origin ?? 'unknown',
    derived_from_target: field.derived_from_target ?? 'unknown',
    evidence: field.evidence ?? 'unknown',
    rows: safeCount(field.values),
    missing: field.values.reduce<number>((n, value) => n + (value === null ? 1 : 0), 0),
  }));
  const targets = (data.targets ?? []).map(target => ({
    name: target.name, unit: target.unit ?? null, type: target.type ?? 'unknown',
    rows: safeCount(target.values), missing: target.values.reduce<number>((n, _value, i) =>
      n + (target.mask[i] === true ? 0 : 1), 0),
  }));
  const xRows = data.rawX?.length ?? data.input.spectra.length;
  return {
    protocol_version: 'domains.browser_scoped_inventory.v1' as const,
    dataset_id: data.input.dataset_id, source_id: data.input.source_id,
    content_version: null,
    content_sha256: data.input.content_sha256,
    source_binding:data.importProvenance?{protocol:data.importProvenance.protocol,
      files:data.importProvenance.files.map(file=>({name:file.name,sha256:file.sha256})),
      file_content_sha256:data.importProvenance.file_content_sha256??null,
      reviewed_spec_sha256:data.importProvenance.reviewed_spec_sha256??null,
      original_source_ids:data.importProvenance.original_source_ids,
      roles_reviewed:data.importProvenance.roles_reviewed,identity_independence:data.importProvenance.identity_independence}:null,
    loaded: {
      x: { rows: xRows, variables: data.rawX?.[0]?.length ?? data.input.axis.length, present: xRows > 0 },
      y: targets.map(target => ({ name: target.name, unit: target.unit, type: target.type, rows: target.rows, missing: target.missing })),
      metadata: fields,
      partitions: [...partitions].map(([name, rows]) => ({ name, rows })),
      manifest_rows: rows.length,
    },
    access_boundary: 'Inventory reports declarations and counts only. Raw X, Y and metadata values are omitted.',
  };
}

const operationEvidence = (result: ScopedResult, index: number): UiEvidence => {
  const receipt = result.receipt as Record<string, unknown>;
  const population=(value:unknown)=>{
    if(!value||typeof value!=='object')return 'not carried';
    const p=value as {role?:unknown;row_keys?:unknown};
    return `${String(p.role??'unknown')} (${Array.isArray(p.row_keys)?p.row_keys.length:'unknown'} observations)`;
  };
  const scope = `${result.operation}; reference ${population(receipt.reference_population)}; query ${population(receipt.query_population)}; requested fit ${String(receipt.fit??'not carried')}; fit completed ${String(receipt.fit_executed??'not carried')}`;
  return {
    id: `scoped-${index}-${result.operation}${result.diagnostic ? `-${result.diagnostic}` : ''}`,
    method: result.diagnostic ? `${result.operation} / ${result.diagnostic}` : result.operation,
    status: result.status, reason: result.reason, value: {
      receipt: result.receipt, result: result.value, supported_claims: result.supported_claims,
      limitations: result.limitations, action: result.action,
    },
    scope, provider: 'Domains browser scoped operation; see exact receipt',
    representation: 'raw', pointer: `/scoped_operations/${index}`,
  };
};

/** Literal reading of carried results, without a magnitude threshold or new risk rule. */
function operationFinding(result:ScopedResult,index:number):UiFinding{
  const reference=Array.isArray(result.receipt.reference_keys)?result.receipt.reference_keys.length:'not carried';
  const query=Array.isArray(result.receipt.query_keys)?result.receipt.query_keys.length:'not carried';
  const value=result.value as Record<string,any>|null;
  let observation=`${result.operation}: ${result.status}${result.reason?'; '+result.reason:''}.`;
  if(result.status==='computed'){
    if(result.operation==='integrity_audit'&&result.diagnostic==='exact_spectra'){
      const metric=value?.metrics?.find((m:{metric_id:string})=>m.metric_id==='integrity.cross_partition_exact_duplicate_pairs');
      observation=metric?.status==='computed'?`Preflight integrity.cross_partition_exact_duplicate_pairs reports ${metric.value} pairs, with ${reference} reference and ${query} query observations. Its declared physical-identity policy applies.`:'The original exact-pair metric is not computed; inspect its owner status and reason.';
    }else if(result.operation==='train_structure'||result.operation==='global_descriptive_transductive'){
      const pca=value?.structure?.metrics?.pca;
      observation=`${result.operation}: ${reference} reference and ${query} query observations; requested fit ${String(result.receipt.fit)}, fit completed ${String(result.receipt.fit_executed)}. PCA status: ${String(pca?.status??'not carried')}.`;
    }else if(result.operation==='train_reference_test_query'){
      observation=`Raw-space train-reference/test-query comparison: ${reference} reference and ${query} query observations; neighbor status ${String(value?.raw_neighbors?.status??'not carried')}. No test PCA refit or domain threshold is inferred.`;
    }else{
      const columns=Array.isArray(value?.columns)?value.columns:[];
      observation=`${columns.length} documentary metadata fields; ${reference} reference and ${query} query observations. `+columns.map((column:Record<string,any>)=>`${String(column.name)}: reference missing ${String(column.reference?.missing_count??'not carried')}, cardinality ${String(column.reference?.cardinality??'not carried')}; query missing ${String(column.query?.missing_count??'not carried')}, cardinality ${String(column.query?.cardinality??'not carried')}; shared nonmissing values ${String(column.literal_shared_nonmissing_value_count??'not carried')}.`).join(' ');
    }
  }
  const limitation=[...result.limitations,
    ...(result.reason==='PREFLIGHT_INPUT_VALIDATION_FAILED'?['The owner input-policy refusal does not establish leakage in a predictive model. Shared declared identities can be expected for a repeated-acquisition objective; interpret them against the stated prediction setting.']:[])].join(' ');
  return {id:`operation-reading-${index}`,title:result.operation.replaceAll('_',' '),status:result.status==='computed'?'observed':result.status,
    observation,hypothesis:'Any relevance to repeated units, reference dependencies or context remains conditional; the audit does not identify a causal mechanism.',
    relevance:'Match the reported populations and declared dependencies to the intended prediction unit and context.',verification:result.action,
    limitation,confidence:'Source-scoped recorded evidence; no calibrated probability or independence certificate',
    evidenceIds:[`scoped-${index}-${result.operation}${result.diagnostic?`-${result.diagnostic}`:''}`],
    prerequisites:['Declared identity meaning, source permissions and the intended prediction population remain necessary for stronger claims.']};
}

/** Adds operation receipts to a train/global base view, retaining loaded inventory separately. */
export function scopedView(base: UiResult | undefined, data: LocalDataset, operations: ScopedResult[], colorField?: string): UiResult {
  const inventory = scopedInventory(data);
  const structureOperations = operations.filter(operation =>
    (operation.operation === 'train_structure' || operation.operation === 'global_descriptive_transductive')
      && !!(operation.value as { structure?: unknown } | null)?.structure);
  const baseHash = base?.provenance.evidence_sha256;
  const matchingStructure = [...structureOperations].reverse().find(operation => {
    const value = operation.value as { structure?: { evidence_sha256?: unknown } } | null;
    return typeof baseHash === 'string' && value?.structure?.evidence_sha256 === baseHash;
  });
  const structureOperation = matchingStructure;
  const active = structureOperation ?? operations.at(-1);
  const unpartitionedBase=!!base&&!!data.rowManifest?.length&&data.rowManifest.every(row=>row.partition==='unpartitioned')&&base.dataset.observations===data.rowManifest.length
    &&base.dataset.id===data.input.dataset_id&&base.dataset.source===data.input.source_id&&base.dataset.contentHash===data.input.content_sha256;
  const fallback: UiResult = {
    mode: 'live', protocol: 'domains.browser_scoped_report.v1',
    dataset: {
      name: data.input.dataset_id, id: data.input.dataset_id, source: data.input.source_id,
      contentHash: data.input.content_sha256, observations: null, variables: data.input.axis.length,
      axisUnit: data.input.axis_unit, axis: data.input.axis, spectra: [], metadata: (data.metadata ?? []).map(f => f.name),
      identity: data.identityOrigin, provenance: data.mode, license: data.license, representation: 'raw',
      population: 'No numerical structure base supplied; coordinates and scores are unavailable.',
    },
    summary: 'Operation-scoped evidence; no numerical structure result was supplied.',
    findings: [], evidence: [], pca: null, geometryReason: 'SCOPED_STRUCTURE_BASE_NOT_SUPPLIED',
    limitations: ['No numerical coordinates or scores are reconstructed by the report adapter.'], provenance: {source_mode:data.mode},
  };
  const structureScope = structureOperation?.operation === 'train_structure' ? 'train_only'
    : structureOperation?.operation === 'global_descriptive_transductive' ? 'global_transductive'
    : null;
  let view: UiResult = base ? {
    ...base,
    dataset: { ...base.dataset, population: structureScope === 'train_only'
      ? 'Declared train population only; other partitions were not used for this fit.'
      : structureScope === 'global_transductive'
        ? 'Explicitly selected train and test population; global descriptive/transductive fit.'
        : 'Numerical structure scope is not matched to a scoped fit receipt.' },
    summary: structureScope === 'train_only'
      ? 'Train-only descriptive structure; no other partition was used for this fit.'
      : structureScope === 'global_transductive'
        ? 'Explicit global descriptive/transductive structure over the selected train and test population.'
        : 'Numerical structure is present, but its scoped fit receipt could not be matched.',
    evidence: base.evidence.map(evidence => {
      const value = evidence.value && typeof evidence.value === 'object' && !Array.isArray(evidence.value)
        ? { ...(evidence.value as Record<string, unknown>) } : evidence.value;
      if (evidence.id === 'pca' && value && typeof value === 'object')
        (value as Record<string, unknown>).scope = structureScope === 'train_only' ? 'Declared train only; no test rows fitted.'
          : structureScope === 'global_transductive' ? 'Explicitly selected train and test; transductive fit.'
          : 'Scoped fit receipt not matched.';
      return { ...evidence, scope: structureScope === 'train_only' ? 'Declared train population only'
        : structureScope === 'global_transductive' ? 'Explicitly selected train and test population; transductive'
        : 'Scoped fit receipt not matched', value };
    }),
  } : fallback;
  if(unpartitionedBase&&base)view={...base,dataset:{...base.dataset,population:'Unpartitioned source; complete descriptive full-X fit, no predictive evaluation.'}};
  let colorStatus: string | null = colorField&&!base?.pca?'PCA_COORDINATES_NOT_CARRIED':null;
  if (base?.pca && colorField) {
    const field = data.metadata.find(column => column.name === colorField);
    const manifest = data.rowManifest ?? [];
    if (!field) colorStatus = 'COLOR_FIELD_NOT_CARRIED';
    else if (field.derived_from_target === true) colorStatus = 'TARGET_DERIVED_METADATA_NOT_ELIGIBLE_FOR_COLORING';
    else if (field.values.length !== manifest.length) colorStatus = 'METADATA_ROW_KEY_MAPPING_UNAVAILABLE';
    else {
      const knownKeys = new Set(manifest.map(row => row.key));
      const positions = new Map(manifest.map((row, i) => [row.key, i]));
      if (knownKeys.size !== manifest.length || base.pca.points.some(point => !knownKeys.has(point.id)))
        colorStatus = 'PCA_POINT_TO_METADATA_KEY_MAPPING_INCOMPLETE';
      else {
        view = { ...view, pca: { ...base.pca, points: base.pca.points.map(point => {
          const value = field.values[positions.get(point.id)!];
          return { ...point, group: value === null ? 'Missing metadata' : String(value) };
        }) } };
        if (field.derived_from_target === 'unknown') colorStatus = 'MAPPED_BY_TECHNICAL_ROW_KEY_TARGET_DERIVATION_UNKNOWN';
      }
    }
  }
  const scoped = operations.map(operationEvidence);
  // The reviewed IO spec remains local: arbitrary transport extensions may carry
  // values. Scientific parameters and immutable configuration fingerprints belong
  // in the report, rather than the unprojected import configuration.
  const {import_spec:_localImportSpec,...safeProvenance}=view.provenance;
  return {
    ...view,
    protocol: 'domains.browser_scoped_report.v1',
    findings:[...view.findings,...operations.map(operationFinding)],
    evidence: [...view.evidence, ...scoped],
    limitations: [...view.limitations, ...operations.flatMap(op => op.limitations)],
    provenance: {
      ...safeProvenance,
      scoped_inventory: inventory,
      scoped_operations: operations.map((operation, index) => ({
        operation: operation.operation, diagnostic: operation.diagnostic, status: operation.status,
        reason: operation.reason, receipt: operation.receipt,
        supported_claims: operation.supported_claims, limitations: operation.limitations,
        action: operation.action, evidence_pointer: `/scoped_operations/${index}`,
      })),
      analyzed_population: active ? {
        operation: active.operation,
        fit_keys: active.receipt.fit_keys ?? null,
        fit_executed: active.receipt.fit_executed ?? null,
        reference_population: active.receipt.reference_population ?? null,
        query_population: active.receipt.query_population ?? null,
      } : null,
      raw_X_Y_exported: false,
      scoped_structure_scope:structureScope??(unpartitionedBase?'unpartitioned_descriptive':'unknown'),
      ...(colorField ? { display_color_field: colorField, display_color_status: colorStatus ?? 'MAPPED_BY_TECHNICAL_ROW_KEY' } : {}),
    },
  };
}
