import type { BrowserReport, LocalDataset } from '../engine/types';
import type { PredictionIntent, UiResult, UiFinding, EvidenceStatus, UiDeclarations } from '../ui-types';

const status = (value: string): EvidenceStatus => (['computed', 'unavailable', 'conditional', 'contradicted', 'not_qualified', 'not_tested', 'supported'].includes(value) ? value : 'unavailable') as EvidenceStatus;
export function liveView(report: BrowserReport, data: LocalDataset): UiResult {
  const pca = report.metrics.pca.value;
  return {
    mode: 'live', protocol: report.protocol_version,
    dataset: { name: data.input.dataset_id, id: data.input.dataset_id, source: data.input.source_id,
      contentHash: data.input.content_sha256, observations: data.input.spectra.length,
      variables: data.input.axis.length, axisUnit: data.input.axis_unit, axis: data.input.axis,
      spectra: data.input.spectra.map((values, i) => ({ id: data.input.observation_ids[i], values, group: data.input.group_ids?.[i] })),
      metadata: data.metadata.map(c => c.name), identity: data.identityOrigin, provenance: data.mode, license: data.license },
    summary: report.interpretation.consequence,
    findings: [
      ...report.findings.map((f, i): UiFinding => ({ id: `observation-${i}`, title: f.observation, status: 'conditional',
        observation: f.observation, hypothesis: f.consequence, relevance: report.interpretation.observation,
        verification: f.action, limitation: 'A descriptive X observation is not evidence of harmful shortcuts or independent transfer.', confidence: f.confidence, evidenceIds: [] })),
      { id: 'intended-use', title: report.interpretation.observation, status: 'conditional', observation: report.interpretation.consequence,
        hypothesis: 'The relevance of dependencies depends on the intended prediction unit and context.', relevance: report.interpretation.observation,
        verification: report.interpretation.action, limitation: report.interpretation.qualification,
        confidence: report.interpretation.confidence, evidenceIds: [report.evidence_sha256] },
    ],
    evidence: Object.entries(report.metrics).map(([id, evidence]) => ({ id,
      method: id === 'pca' ? 'Methods PCA via the public Preflight provider' : `Methods / Domains ${id}`,
      status: status(evidence.status), reason: evidence.reason, value: evidence.value,
      scope: String(report.scope.population), provider: 'Methods 1.3.13 · ABI 2.20 · Domains Rust/WASM' })),
    pca: pca ? { points: pca.scores.map((row, i) => ({ id: data.input.observation_ids[i], x: row[0], y: row[1] ?? 0,
      group: data.input.group_ids?.[i] })), eigenvalues: pca.eigenvalues, totalVariance: pca.full_moments[0],
      xLabel: 'PC1', yLabel: pca.n_components_resolved >= 2 ? 'PC2' : 'PC2 unavailable · displayed at zero' } : null,
    geometryReason: report.metrics.pca.reason,
    limitations: [...report.limitations, ...data.warnings],
    provenance: { source_mode: data.mode, engine_version: report.engine_version,
      input_sha256: report.input_sha256, evidence_sha256: report.evidence_sha256,
      imported_partitions: data.partitions, original_headers: data.headers, import_spec: data.importSpec,
      metadata_scope: 'Carried by this import; absence here does not establish absence in the original database.',
      physical_independence: 'unknown', independent_original_study_count: null, prediction_evaluation: 'not_executed',
      verification_inputs: 'unknown', verification_protocol: 'not_qualified', verification_authorization: 'not_declared',
      verification_execution: 'not_executed', scientific_reading_scope: report.interpretation.qualification },
  };
}

// Saved companion prose is already qualified by the original Python interpreter.
// This adapter only projects fields for display, without deriving scientific rules.
export function savedView(source: unknown): UiResult {
  const report = source as Record<string, any>;
  if (report.protocol_version !== 'domains.standalone_report.v1' || !Array.isArray(report.cases) || report.cases.length !== 1)
    throw new Error('ONE_QUALIFIED_STANDALONE_CASE_REQUIRED');
  const row = report.cases[0], identity = row.identity?.value ?? {};
  const d1 = row.companions?.d1?.value;
  if (!row.companions || typeof row.companions !== 'object') throw new Error('VALIDATED_COMPANION_SLOTS_REQUIRED');
  const reading = row.decision_summary ?? {};
  const prose = (value: unknown): string => typeof value === 'string' ? value : Array.isArray(value) ? value.map(prose).join(' ') : JSON.stringify(value ?? 'Unknown');
  return { mode: 'saved', protocol: report.protocol_version,
    dataset: { name: String(identity.dataset_id ?? row.label), id: String(identity.dataset_id ?? 'unknown'),
      source: String(identity.source_id ?? 'unknown'), contentHash: String(row.source_reports?.reference?.sha256 ?? 'unknown'),
      observations: identity.n_observations ?? 0, variables: null, axisUnit: 'not carried', axis: [], spectra: [], metadata: [],
      identity: 'Original qualified report scope; physical/reference independence remains unknown',
      provenance: 'saved_qualified_report · no browser refit', license: 'Already-published aggregate example; source restrictions remain applicable' },
    summary: prose(reading.observed ?? report.title),
    findings: (d1?.warnings ?? []).map((w: Record<string, any>): UiFinding => ({ id: w.warning_id,
      title: w.warning_id.replaceAll('_', ' '), status: status(w.value?.assessment ?? w.status),
      observation: prose(w.observation?.value ?? w.observation?.reason), hypothesis: prose(w.risk_hypothesis),
      relevance: prose(w.conditions), verification: prose(w.recommended_checks), limitation: prose(w.limitations),
      confidence: 'Original qualified conditional interpretation', evidenceIds: [w.warning_id] })),
    evidence: Object.entries({ ...row.companions, native_preflight: row.native_preflight }).filter(([, value]) => value !== undefined).map(([id, value]) => {
      const slot = value as Record<string, any>;
      return { id, method: slot.protocol_version ?? id, status: status(slot.status), reason: slot.reason ?? null,
        value: slot.value, scope: prose(identity), provider: 'Original published Domains Python consumer; saved only' };
    }),
    pca: null, geometryReason: 'RAW_SPECTRA_AND_PCA_COORDINATES_NOT_REDISTRIBUTED_WITH_THIS_AGGREGATE_REPORT',
    limitations: report.limitations ?? [], provenance: { source_mode: 'saved_qualified_report',
      identity, source_reports: row.source_reports, decision_summary: reading, coverage: report.coverage,
      independent_original_study_count: null, browser_numerical_execution: false,
      original_annotations_unchanged: true, original_source_ref: row.source_ref },
  };
}

export interface DemoReport {
  protocol_version: 'domains.browser_demo_report.v1'; generated_at_utc: string;
  language: 'en' | 'fr'; source_mode: string; intended_use: PredictionIntent;
  user_declarations: { population: string | null; prediction_unit: string | null; new_context: string | null };
  dataset: Omit<UiResult['dataset'], 'spectra'>; summary: string; findings: UiFinding[];
  evidence: UiResult['evidence']; pca: UiResult['pca']; limitations: string[];
  provenance: Record<string, unknown>; scientific_report: unknown;
  raw_x_included: false; numerical_evidence_recomputed_for_export: false;
}
export function reportModel(view: UiResult, scientific: unknown, intent: PredictionIntent, language: 'en' | 'fr', declarations?: UiDeclarations): DemoReport {
  const { spectra: _privateDisplayOnly, ...dataset } = view.dataset;
  return { protocol_version: 'domains.browser_demo_report.v1', generated_at_utc: new Date().toISOString(), language,
    source_mode: String(view.provenance.source_mode), intended_use: intent,
    user_declarations: { population: declarations?.population || null, prediction_unit: declarations?.prediction_unit || null, new_context: declarations?.new_context || null },
    dataset, summary: view.summary, findings: view.findings, evidence: view.evidence,
    pca: view.pca, limitations: view.limitations, provenance: view.provenance, scientific_report: scientific,
    raw_x_included: false, numerical_evidence_recomputed_for_export: false };
}
