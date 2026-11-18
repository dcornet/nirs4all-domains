import type { Locale, UiEvidence, UiFinding, UiResult } from '../ui-types';
import type { FactorResult } from '@nirs4all/domains';

type Row = unknown[];
export interface FactorAssociationTable {
  id: string; title: string; columns: string[]; rows: Row[]; note: string;
}

const record = (v: unknown): Record<string, any> => v !== null && typeof v === 'object' && !Array.isArray(v) ? v as Record<string, any> : {};
const status = (v: unknown): UiEvidence['status'] =>
  ['observed','available','computed','unavailable','unsupported','error','conditional','contradicted','not_qualified','not_tested','supported'].includes(String(v))
    ? v as UiEvidence['status'] : 'unavailable';
const display = (v: unknown, fallback: unknown = null): unknown => v === undefined ? fallback : v;
const slotValue = (slot: unknown): unknown => record(slot).value ?? null;

/** Build practical documentary tables from the owner's aggregate result. No statistics are calculated here. */
export function factorAssociationTables(input: unknown, locale: Locale = 'en'): FactorAssociationTable[] {
  const value = record(record(input).value);
  const factors = Array.isArray(value.factors) ? value.factors.map(record) : [];
  const fr = locale === 'fr';
  const descriptiveRows: Row[] = [], factorRows: Row[] = [], inferenceRows: Row[] = [], fRows: Row[] = [];
  for (const factor of factors) {
    const components = Array.isArray(factor.components) ? factor.components.map(record) : [];
    factorRows.push([factor.factor_id, factor.kind, factor.unit ?? null, factor.n_missing ?? null,
      factor.n_levels ?? null, factor.origin ?? null, factor.n_fit_observations ?? null]);
    for (const component of components) {
      const desc = record(component.descriptive), statistic = record(slotValue(desc));
      const inference = record(component.inference), inferValue = record(slotValue(inference));
      const n = display(component.n_used, factor.n_used);
      const measure = statistic.measure;
      descriptiveRows.push([factor.factor_id, `PC${String(component.component ?? '?')}`, measure ?? null,
        statistic.estimate ?? null, n, desc.status ?? 'unavailable', desc.reason ?? null]);
      const exact = record(inferValue.owner_exact);
      const conditional = inference.status === 'computed'
        ? (fr ? 'Conditionnelle au dossier externe fourni' : 'Conditional on supplied external design record')
        : (inference.reason ?? (fr ? 'Non admissible' : 'Not admissible'));
      inferenceRows.push([factor.factor_id, `PC${String(component.component ?? '?')}`, exact.p_value ?? null,
        inferValue.holm_adjusted_p ?? null, inference.status ?? 'unavailable', inference.reason ?? null, conditional]);
      const owner = record(statistic.owner_output);
      if (measure === 'eta_squared') fRows.push([factor.factor_id, `PC${String(component.component ?? '?')}`,
        owner.f_statistic ?? null, owner.df1 ?? null, owner.df2 ?? null]);
    }
  }
  const tables: FactorAssociationTable[] = [
    { id:'factor-association-components', title:fr?'Associations descriptives par composante':'Descriptive associations by component',
      columns:fr?['Facteur','PC','Mesure','Estimation','Paires utilisées','Statut','Raison']:['Factor','PC','Measure','Estimate','Pairs used','Status','Reason'],
      rows:descriptiveRows,
      note:fr?'Eta² concerne le score PC indiqué, pas la variance spectrale totale. Les coefficients signés suivent l’orientation enregistrée de la PC.'
        :'Eta-squared concerns the listed PC score, not total spectral variance. Signed coefficients follow the recorded PC orientation.' },
    { id:'factor-association-summary', title:fr?'Résumé des facteurs':'Factor summary',
      columns:fr?['Facteur','Type','Unité','Manquants','Niveaux','Origine','Observations ajustées']:['Factor','Type','Unit','Missing','Levels','Origin','Fit observations'],
      rows:factorRows, note:fr?'Les comptes restent pondérés par acquisition ; les niveaux de facteur ne sont pas des unités physiques.'
        :'Counts remain acquisition weighted; factor levels are not physical units.' },
    { id:'factor-association-inference', title:fr?'Inférence conditionnelle':'Conditional inference',
      columns:fr?['Facteur','PC','p exacte','p ajustée de Holm','Statut','Raison','Qualification']:['Factor','PC','Exact p','Holm adjusted p','Status','Reason','Qualification'],
      rows:inferenceRows, note:fr?'Toute p-value exige un plan externe qualifié ; Domains ne certifie ni indépendance ni échangeabilité.'
        :'Any p-value requires an externally qualified design; Domains certifies neither independence nor exchangeability.' }
  ];
  if (fRows.length) tables.push({ id:'factor-association-anova', title:fr?'Statistique F et degrés de liberté':'F statistic and degrees of freedom',
    columns:fr?['Facteur','PC','F','ddl facteur','ddl résiduels']:['Factor','PC','F','Factor df','Residual df'], rows:fRows,
    note:fr?'F peut être indisponible pour un contraste dégénéré même si eta² est défini.'
      :'F can be unavailable for a degenerate contrast while eta-squared remains defined.' });
  const levels: Row[] = [];
  for (const factor of factors) for (const level of (Array.isArray(factor.level_counts) ? factor.level_counts : [])) {
    const l = record(level); levels.push([factor.factor_id, l.label ?? l.level_id ?? null, l.count ?? null]);
  }
  if (levels.length) tables.push({ id:'factor-association-levels', title:fr?'Effectifs des niveaux':'Factor level counts',
    columns:fr?['Facteur','Niveau','Effectif']:['Factor','Level','Count'], rows:levels,
    note:fr?'Effectifs littéraux des valeurs observées, sans interprétation causale.':'Literal counts of observed values; no causal interpretation.' });
  const audit = record(value.dependency_audit);
  const dependencies = Array.isArray(audit.fields) ? audit.fields.map(record) : [];
  const dependencyRows: Row[] = dependencies.map(d => [d.name ?? d.field_id ?? null, d.role ?? null, d.kind ?? null,
    d.n_missing ?? d.missing_count ?? null, d.n_distinct_nonmissing ?? d.n_levels ?? d.cardinality ?? null,
    d.n_repeated_rows_beyond_first ?? d.repeated_units ?? d.repeated_count ?? null,
    d.declared_unique_unit_count ?? null, d.independent_units_established ?? null, d.qualification ?? null]);
  if (dependencyRows.length) tables.push({ id:'factor-association-dependencies', title:fr?'Dépendances déclarées':'Declared dependencies',
    columns:fr?['Champ','Rôle','Type','Manquants','Niveaux','Répétitions au-delà du premier','Unités déclarées','Indépendance établie','Qualification']
      :['Field','Role','Type','Missing','Levels','Repeated rows beyond first','Declared units','Independence established','Qualification'],
    rows:dependencyRows, note:fr?'Les répétitions d’acquisitions ne certifient pas les unités physiques indépendantes.':'Repeated acquisitions do not certify independent physical units.' });
  const crossings = Array.isArray(audit.pairwise_context_tables) ? audit.pairwise_context_tables.map(record) : [];
  const crossingRows: Row[] = crossings.map(c => [c.left ?? c.field_a ?? c.first ?? null, c.right ?? c.field_b ?? c.second ?? null,
    c.n_complete_pairs ?? c.n_observations ?? null, c.observed_combinations ?? c.table ?? null,
    c.literal_total_confounding ?? c.confounded ?? null,
    { absent_combination_count:c.absent_combination_count ?? null, absent_combinations:c.absent_combinations ?? null,
      left_nested_in_right:c.left_nested_in_right ?? null, right_nested_in_left:c.right_nested_in_left ?? null,
      n_missing_pairs:c.n_missing_pairs ?? null, qualification:c.qualification ?? null }]);
  if (crossingRows.length) tables.push({ id:'factor-association-crossings', title:fr?'Croisements des facteurs':'Factor crossings',
    columns:fr?['Champ A','Champ B','Observations','Combinaisons','Confusion 1:1','Tableau observé']:['Field A','Field B','Observations','Combinations','One-to-one confounding','Observed table'],
    rows:crossingRows, note:fr?'Les tableaux décrivent les combinaisons observées et absentes; ils ne démontrent pas de mécanisme causal.':'Tables describe observed and absent combinations; they do not establish a causal mechanism.' });
  return tables;
}

function observation(result: FactorResult, factor: Record<string, any>, locale: Locale): string {
  const fr = locale === 'fr', comps = Array.isArray(factor.components) ? factor.components : [];
  const computed = comps.filter((c: any) => record(c.descriptive).status === 'computed').length;
  return fr
    ? `${String(factor.factor_id)} : ${String(factor.n_used ?? '—')} paires utilisées, ${String(factor.n_missing ?? '—')} manquantes, ${computed}/${comps.length} associations descriptives calculées. Population ${String(record(result.value).population ?? 'non transportée')}.`
    : `${String(factor.factor_id)}: ${String(factor.n_used ?? '—')} pairs used, ${String(factor.n_missing ?? '—')} missing, ${computed}/${comps.length} descriptive associations computed. Population: ${String(record(result.value).population ?? 'not carried')}.`;
}

/** Append aggregate factor/PCA evidence without changing any existing scientific object. */
export function appendFactorAssociations(view: UiResult, results: readonly FactorResult[], locale: Locale = 'en'): UiResult {
  const additions = results.map((raw, index) => {
    const result = raw, value = record(result.value), factors = Array.isArray(value.factors) ? value.factors.map(record) : [];
    const id = `factor-association-${index + 1}`;
    const evidence: UiEvidence = { id, method: String(result.protocol_version ?? 'domains.browser_factor_association_result.v1'),
      status: status(result.status), reason: typeof result.reason === 'string' ? result.reason : null, value: result,
      scope: String(value.population ?? 'Population not carried'), provider: 'Domains browser factor association; Methods owner statistics',
      representation: String(value.representation ?? 'recorded raw-PCA scores'), pointer: `/factor_associations/${index}` };
    const findings: UiFinding[] = factors.map((factor, factorIndex) => {
      const categorical = factor.kind === 'categorical';
      const warnings = Array.isArray(factor.warnings) ? factor.warnings.join('; ') : '';
      const dep = record(value.dependency_audit), inference = record(value.inference);
      const fr = locale === 'fr';
      const inferenceLimit = inference.level === 'conditionally_admissible'
        ? (fr ? 'Toute inférence est conditionnelle au dossier de plan externe fourni; Domains ne l’authentifie pas.' : 'Any inference is conditional on the supplied external design record; Domains does not authenticate it.')
        : inference.level === 'descriptive_only'
          ? (fr ? 'Aucune inférence demandée; seuls les descriptifs sont rapportés.' : 'No inference was requested; descriptive results only.')
          : `${fr ? 'Inférence non qualifiée' : 'Inference unqualified'}${inference.reason ? ` (${String(inference.reason)})` : '.'}`;
      return { id:`${id}-factor-${factorIndex + 1}`, title:String(factor.factor_id ?? (fr?'Facteur':'Factor')),
        status: status(result.status === 'computed' ? 'observed' : result.status), observation:observation(result,factor,locale),
        hypothesis: fr ? 'Une correspondance observée peut motiver une vérification de facteurs concomitants; elle ne démontre aucune cause.' : 'An observed correspondence can motivate checks of concomitant factors; it does not establish a cause.',
        relevance: fr ? 'La correspondance est descriptive pour chaque score PC et la population indiquée.' : 'The correspondence is descriptive for each PC score and the stated population.',
        verification: String(result.action ?? (fr?'Examiner le plan d’acquisition, les unités physiques et les croisements déclarés.':'Review acquisition design, physical units, and declared factor crossings.')),
        limitation: [categorical ? (fr?'Eta² mesure la séparation entre niveaux du score PC, pas la variance spectrale totale.':'Eta² measures between-level separation of a PC score, not total spectral variance.') : (fr?'La corrélation signée dépend de l’orientation enregistrée de la PC.':'Signed correlation depends on the recorded PC orientation.'),
          inferenceLimit, String(dep.qualification ?? ''), warnings,
          ...(Array.isArray(result.limitations) ? result.limitations.map(String) : [])].filter(Boolean).join(' '),
        confidence: inference.level === 'conditionally_admissible'
          ? (fr ? '\u00c9ligibilit\u00e9 conditionnelle selon le dossier externe fourni; aucune probabilit\u00e9 calibr\u00e9e.' : 'Conditionally admissible under the supplied external record; no calibrated probability.')
          : fr ? 'Association descriptive enregistr\u00e9e par le fournisseur; aucune probabilit\u00e9 calibr\u00e9e.' : 'Provider-recorded descriptive association; no calibrated probability.', evidenceIds:[id],
        prerequisites:[fr?'Les unités indépendantes et les hypothèses d’échangeabilité restent à qualifier extérieurement.':'Independent units and exchangeability assumptions require external qualification.'] };
    });
    return { evidence, findings };
  });
  return { ...view, evidence:[...view.evidence,...additions.map(a=>a.evidence)], findings:[...view.findings,...additions.flatMap(a=>a.findings)],
    limitations:[...view.limitations,...results.flatMap(r=>Array.isArray(record(r).limitations)?record(r).limitations.map(String):[])],
    provenance:{...view.provenance, factor_association_evidence_ids:additions.map((_,i)=>`factor-association-${i+1}`)} };
}
