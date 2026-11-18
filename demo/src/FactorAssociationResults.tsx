import { useId, type ReactNode } from 'react';
import type { Locale } from './ui-types';

export interface FactorAssociationResultsProps {
  result: unknown;
  locale: Locale;
}

const copy = {
  en: {
    title: 'Factor association results', population: 'Population', observation: 'Observation', hypotheses: 'Possible explanations', limits: 'Limits', checks: 'Checks to consider',
    association: 'Association with each resolved PCA component', component: 'PC', measure: 'Measure', estimate: 'Estimate', descriptive: 'Descriptive status', inference: 'Inference status', p: 'Exact p-value', holm: 'Holm-adjusted p-value',
    factor: 'Factor', kind: 'Type', origin: 'Origin', evidence: 'Provenance evidence', unit: 'Unit', nUsed: 'Pairs used', missing: 'Missing pairs', nLevels: 'Observed levels', levels: 'Observed level counts', level: 'Level', count: 'Count',
    noFactors: 'No factor results were carried.', unavailable: 'Unavailable', computed: 'Computed', conditional: 'Conditionally admissible', descriptiveOnly: 'Descriptive only', unqualified: 'Unqualified', reason: 'Reason',
    depTitle: 'Declared dependencies and context', depName: 'Field', role: 'Role', rows: 'Rows', distinct: 'Distinct values', repeated: 'Repeated rows beyond first', uniqueUnits: 'Declared unique units',
    pairwise: 'Pairwise context tables', left: 'Left field', right: 'Right field', complete: 'Complete pairs', missingPairs: 'Missing pairs', combo: 'Observed level combination', absent: 'Absent combinations', totalConfounding: 'Literal total confounding of observed labels', leftNested: 'Left labels nested in right', rightNested: 'Right labels nested in left', enumeration: 'Absent-combination enumeration',
    noCausal: 'These descriptive results do not establish causality, leakage, calibration risk, or a global structural risk.', noTotalX: 'A component statistic concerns that recorded PC score; it is not association with total X variance.', unknownFactor: 'An absent or unavailable factor does not show that structure or confounding is absent.',
    hypothesisText: 'Observed associations can be consistent with several explanations, including shared acquisition context or dependence. The metadata alone cannot distinguish them.',
    checkText: 'Review the factor definitions, physical/reference/repetition dependencies, missingness, the intended prediction population, and any external design record before making a stronger interpretation.',
    conditionalText: 'Any reported p-value is conditional on the supplied external exchangeability record; Domains does not independently authenticate that record or establish physical independence.',
    literal: 'Literal metadata combinations only; they do not identify a causal mechanism or prove that all relevant factors were supplied.',
  },
  fr: {
    title: 'Résultats d’association des facteurs', population: 'Population', observation: 'Observation', hypotheses: 'Explications possibles', limits: 'Limites', checks: 'Vérifications à envisager',
    association: 'Association avec chaque composante ACP résolue', component: 'CP', measure: 'Mesure', estimate: 'Estimation', descriptive: 'Statut descriptif', inference: 'Statut inférentiel', p: 'Valeur p exacte', holm: 'Valeur p ajustée de Holm',
    factor: 'Facteur', kind: 'Type', origin: 'Origine', evidence: 'Élément de provenance', unit: 'Unité', nUsed: 'Paires utilisées', missing: 'Paires manquantes', nLevels: 'Niveaux observés', levels: 'Effectifs des niveaux observés', level: 'Niveau', count: 'Effectif',
    noFactors: 'Aucun résultat de facteur n’a été fourni.', unavailable: 'Indisponible', computed: 'Calculé', conditional: 'Admissible sous condition', descriptiveOnly: 'Descriptif uniquement', unqualified: 'Non qualifié', reason: 'Raison',
    depTitle: 'Dépendances déclarées et contexte', depName: 'Champ', role: 'Rôle', rows: 'Lignes', distinct: 'Valeurs distinctes', repeated: 'Lignes répétées au-delà de la première', uniqueUnits: 'Unités uniques déclarées',
    pairwise: 'Tableaux contextuels par paire', left: 'Champ gauche', right: 'Champ droit', complete: 'Paires complètes', missingPairs: 'Paires manquantes', combo: 'Combinaison de niveaux observée', absent: 'Combinaisons absentes', totalConfounding: 'Confusion totale littérale des étiquettes observées', leftNested: 'Étiquettes gauches imbriquées dans les droites', rightNested: 'Étiquettes droites imbriquées dans les gauches', enumeration: 'Énumération des combinaisons absentes',
    noCausal: 'Ces résultats descriptifs n’établissent ni causalité, ni fuite, ni risque de calibration, ni risque structurel global.', noTotalX: 'Une statistique de composante concerne le score ACP enregistré ; elle ne mesure pas l’association avec la variance totale de X.', unknownFactor: 'Un facteur absent ou indisponible ne montre pas que la structure ou la confusion est absente.',
    hypothesisText: 'Les associations observées peuvent être compatibles avec plusieurs explications, notamment un contexte d’acquisition partagé ou des dépendances. Les seules métadonnées ne permettent pas de les distinguer.',
    checkText: 'Vérifiez les définitions des facteurs, les dépendances physiques/de référence/de répétition, les valeurs manquantes, la population de prédiction visée et tout dossier de plan externe avant une interprétation plus forte.',
    conditionalText: 'Toute valeur p rapportée dépend du dossier externe d’échangeabilité fourni ; Domains ne l’authentifie pas de façon indépendante et n’établit pas l’indépendance physique.',
    literal: 'Combinaisons littérales de métadonnées uniquement ; elles n’identifient aucun mécanisme causal et ne prouvent pas que tous les facteurs pertinents ont été fournis.',
  },
} as const;

type ObjectValue = Record<string, unknown>;
const object = (value: unknown): value is ObjectValue => typeof value === 'object' && value !== null && !Array.isArray(value);
const list = (value: unknown): unknown[] => Array.isArray(value) ? value : [];
const field = (value: ObjectValue, key: string): unknown => value[key];
const display = (value: unknown, fallback = '—'): string => {
  if (typeof value === 'string') return value || fallback;
  if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  return fallback;
};
const number = (value: unknown, locale: Locale): string => typeof value === 'number' && Number.isFinite(value) ? new Intl.NumberFormat(locale, { maximumSignificantDigits: 8 }).format(value) : '—';
const slotStatus = (value: unknown, locale: Locale): string => {
  const status = object(value) ? value.status : undefined;
  if (status === 'computed') return copy[locale].computed;
  if (status === 'unavailable') return copy[locale].unavailable;
  return display(status, copy[locale].unavailable);
};

function Table({ headers, rows }: { headers: string[]; rows: ReactNode[][] }) {
  return <div className="table-scroll"><table><thead><tr>{headers.map((header, index) => <th scope="col" key={`${header}-${index}`}>{header}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{row.map((cell, col) => col === 0 ? <th scope="row" key={col}>{cell}</th> : <td key={col}>{cell}</td>)}</tr>)}</tbody></table></div>;
}

function Fact({ label, value }: { label: string; value: ReactNode }) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>;
}

function FactorCard({ factor, population, locale }: { factor: ObjectValue; population: string; locale: Locale }) {
  const t = copy[locale];
  const components = list(factor.components).filter(object);
  const categorical = factor.kind === 'categorical';
  const levels = list(factor.level_counts).filter(object);
  const levelRows = levels.map(level => [display(level.label ?? level.value), number(level.count, locale)]);
  const componentRows = components.map(component => {
    const descriptive = component.descriptive;
    const descValue = object(descriptive) && object(descriptive.value) ? descriptive.value : {};
    const inference = component.inference;
    const inferValue = object(inference) && object(inference.value) ? inference.value : {};
    const exact = object(inferValue.owner_exact) ? inferValue.owner_exact : {};
    const status = object(inference) && inference.status === 'computed' ? t.conditional
      : object(inference) && inference.reason === 'DESCRIPTIVE_ONLY_NO_INFERENCE_REQUESTED' ? t.descriptiveOnly
      : slotStatus(inference, locale);
    const pValue = field(exact, 'p_value');
    return [
      `${t.component}${display(component.component)}`,
      display(descValue.measure),
      number(descValue.estimate, locale),
      `${slotStatus(descriptive, locale)}${object(descriptive) && descriptive.reason ? ` · ${display(descriptive.reason)}` : ''}`,
      `${status}${object(inference) && inference.reason && inference.status !== 'computed' ? ` · ${display(inference.reason)}` : ''}`,
      number(pValue, locale),
      number(inferValue.holm_adjusted_p, locale),
    ];
  });

  return <article className="factor-association-result">
    <h4>{display(factor.factor_id, t.factor)}</h4>
    <dl className="factor-association-facts">
      <Fact label={t.kind} value={display(factor.kind)} />
      <Fact label={t.origin} value={display(factor.origin)} />
      <Fact label={t.evidence} value={display(factor.evidence)} />
      <Fact label={t.unit} value={display(factor.unit)} />
      <Fact label={t.population} value={population} />
      <Fact label={t.nUsed} value={number(factor.n_used, locale)} />
      <Fact label={t.missing} value={number(factor.n_missing, locale)} />
      <Fact label={t.nLevels} value={number(factor.n_levels, locale)} />
    </dl>
    <h5>{t.association}</h5>
    <Table headers={[t.component, t.measure, t.estimate, t.descriptive, t.inference, t.p, t.holm]} rows={componentRows} />
    {componentRows.some(row => String(row[4]).startsWith(t.conditional)) && <p>{t.conditionalText}</p>}
    {categorical && levels.length > 0 && <>
      <h5>{t.levels}</h5>
      <Table headers={[t.level, t.count]} rows={levelRows} />
    </>}
  </article>;
}

function DependencyAudit({ audit, locale }: { audit: ObjectValue; locale: Locale }) {
  const t = copy[locale];
  const fields = list(audit.fields).filter(object);
  const fieldRows = fields.map(item => [
    display(item.name), display(item.role), number(item.n_rows, locale), number(item.n_missing, locale),
    number(item.n_distinct_nonmissing, locale), number(item.n_repeated_rows_beyond_first, locale), number(item.declared_unique_unit_count, locale),
  ]);
  const tables = list(audit.pairwise_context_tables).filter(object);
  return <section className="factor-dependency-audit">
    <h3>{t.depTitle}</h3>
    {fields.length > 0 && <Table headers={[t.depName, t.role, t.rows, t.missing, t.distinct, t.repeated, t.uniqueUnits]} rows={fieldRows} />}
    {tables.map((table, index) => {
      const combinations = list(table.observed_combinations).filter(object);
      const absentValues = list(table.absent_combinations).filter(object);
      return <article className="factor-context-table" key={`${display(table.left)}-${display(table.right)}-${index}`}>
        <h4>{t.pairwise}: {display(table.left)} · {display(table.right)}</h4>
        <dl>
          <Fact label={t.complete} value={number(table.n_complete_pairs, locale)} />
          <Fact label={t.missingPairs} value={number(table.n_missing_pairs, locale)} />
          <Fact label={t.totalConfounding} value={display(table.literal_total_confounding)} />
          <Fact label={t.leftNested} value={display(table.left_nested_in_right)} />
          <Fact label={t.rightNested} value={display(table.right_nested_in_left)} />
          <Fact label={t.absent} value={number(table.absent_combination_count, locale)} />
          <Fact label={t.enumeration} value={display(table.absence_enumeration_reason, locale === 'fr' ? 'Complète' : 'Complete')} />
        </dl>
        {combinations.length > 0 && <Table headers={[t.combo, t.count]} rows={combinations.map(combo => [`${display(combo.left_level)} × ${display(combo.right_level)}`, number(combo.count, locale)])} />}
        {absentValues.length > 0 && <Table headers={[t.absent, t.left, t.right]} rows={absentValues.map(combo => [t.absent, display(combo.left_level), display(combo.right_level)])} />}
        <p>{t.literal}</p>
      </article>;
    })}
  </section>;
}

export function FactorAssociationResults({ result, locale }: FactorAssociationResultsProps) {
  const reactId = useId().replace(/[^A-Za-z0-9_-]/g, '');
  const ids = {
    title: `factor-association-results-${reactId}-title`,
    observation: `factor-association-results-${reactId}-observation`,
    hypotheses: `factor-association-results-${reactId}-hypotheses`,
    dependencies: `factor-association-results-${reactId}-dependencies`,
    limits: `factor-association-results-${reactId}-limits`,
    checks: `factor-association-results-${reactId}-checks`,
  };
  const t = copy[locale];
  const wrapper = object(result) ? result : {};
  const value = object(wrapper.value) ? wrapper.value : wrapper;
  const factors = list(value.factors).filter(object);
  const population = display(value.population);
  const audit = object(value.dependency_audit) ? value.dependency_audit : {};
  const reason = display(wrapper.reason, '');
  const status = display(wrapper.status, 'computed');
  const limitations = list(wrapper.limitations).filter((item): item is string => typeof item === 'string');
  const action = display(wrapper.action, '');

  return <section className="factor-association-results" aria-labelledby={ids.title}>
    <h3 id={ids.title}>{t.title}</h3>
    {status !== 'computed' && <p className="status status-unavailable">{status} · {reason || t.unavailable}</p>}
    <section aria-labelledby={ids.observation}><h4 id={ids.observation}>{t.observation}</h4>
      <p>{t.noCausal} {t.noTotalX}</p><p>{t.unknownFactor}</p>
      {factors.length ? factors.map(factor => <FactorCard key={display(factor.factor_id)} factor={factor} population={population} locale={locale} />) : <p>{t.noFactors}{reason ? ` ${reason}` : ''}</p>}
    </section>
    <section aria-labelledby={ids.hypotheses}><h4 id={ids.hypotheses}>{t.hypotheses}</h4><p>{t.hypothesisText}</p></section>
    <section aria-labelledby={ids.dependencies}><h4 id={ids.dependencies}>{t.depTitle}</h4>
      {list(audit.fields).length || list(audit.pairwise_context_tables).length ? <DependencyAudit audit={audit} locale={locale} /> : <p>{t.unknownFactor}</p>}
      {typeof audit.qualification === 'string' && <p>{audit.qualification}</p>}
    </section>
    <section aria-labelledby={ids.limits}><h4 id={ids.limits}>{t.limits}</h4>
      <ul>{limitations.map((limitation, index) => <li key={index}>{limitation}</li>)}</ul>
      <p>{t.noCausal} {t.noTotalX} {t.unknownFactor}</p>
    </section>
    <section aria-labelledby={ids.checks}><h4 id={ids.checks}>{t.checks}</h4><p>{t.checkText}</p>{action && <p>{action}</p>}</section>
  </section>;
}
