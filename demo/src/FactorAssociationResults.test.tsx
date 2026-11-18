import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { FactorAssociationResults } from './FactorAssociationResults';

const result = (
  inference: unknown = { status: 'unavailable', reason: 'DESCRIPTIVE_ONLY_NO_INFERENCE_REQUESTED', value: null },
  descriptive: unknown = { status: 'computed', reason: null, value: { measure: 'eta_squared', estimate: 0.5 } },
) => ({
  protocol_version: 'domains.browser_factor_association_result.v1', status: 'computed', reason: null,
  value: {
    population: 'train',
    inference: { level: 'descriptive_only', reason: 'DESCRIPTIVE_ONLY_NO_INFERENCE_REQUESTED' },
    factors: [{
      factor_id: 'batch', kind: 'categorical', role: 'factor', unit: null, origin: 'declared-M', evidence: 'import declaration',
      n_fit_observations: 6, n_used: 6, n_missing: 0, n_levels: 2,
      level_counts: [{ level_id: 'level-1', value: 'A', label: 'A', count: 3 }, { level_id: 'level-2', value: 'B', label: 'B', count: 3 }],
      components: [{
        component: 1, n_used: 6,
        descriptive,
        inference,
      }],
    }],
    dependency_audit: {
      fields: [{ name: 'specimen', role: 'specimen', n_rows: 6, n_missing: 0, n_distinct_nonmissing: 3, n_repeated_rows_beyond_first: 3, declared_unique_unit_count: 3 }],
      pairwise_context_tables: [{
        left: 'batch', right: 'instrument', n_complete_pairs: 6, n_missing_pairs: 0,
        literal_total_confounding: true, left_nested_in_right: true, right_nested_in_left: true,
        absent_combination_count: 0, absent_combinations: [], absence_enumeration_reason: null,
        observed_combinations: [{ left_level: 'level-1', right_level: 'level-1', count: 3 }, { left_level: 'level-2', right_level: 'level-2', count: 3 }],
      }],
      qualification: 'Literal metadata only; missing factors do not establish absence of confounding.',
    },
  },
  limitations: ['Repeated observations are retained with acquisition weighting; no automatic pseudoreplication correction.'],
  action: 'Review declared units and acquisition design.',
});

describe('factor association results', () => {
  it('renders per-PC descriptive results, level counts, repeats, confounding and the four interpretation sections', () => {
    const html = renderToStaticMarkup(<FactorAssociationResults result={result()} locale="en" />);
    for (const text of [
      'Factor association results', 'Association with each resolved PCA component', 'eta_squared', '0.5',
      'Observed level counts', 'A', 'Repeated rows beyond first', '3', 'Literal total confounding of observed labels',
      'Possible explanations', 'Limits', 'Checks to consider', 'do not establish causality', 'not association with total X variance',
      'An absent or unavailable factor does not show that structure or confounding is absent.',
    ]) expect(html).toContain(text);
    expect(html).toContain('DESCRIPTIVE_ONLY_NO_INFERENCE_REQUESTED');
    expect(html).not.toContain('significant');
  });

  it('distinguishes conditional exact p-values and Holm values from descriptive-only results', () => {
    const conditional = result({
      status: 'computed', reason: null,
      value: { qualification: 'conditional_on_supplied_external_exchangeability_record', owner_exact: { p_value: 0.0833333333333 }, holm_adjusted_p: 0.1, family_size: 2, external_evidence: { uri: 'synthetic record' } },
    });
    const html = renderToStaticMarkup(<FactorAssociationResults result={conditional} locale="en" />);
    expect(html).toContain('Conditionally admissible');
    expect(html).toContain('0.08333333');
    expect(html).toContain('0.1');
    expect(html).toContain('Any reported p-value is conditional on the supplied external exchangeability record');

    const descriptive = renderToStaticMarkup(<FactorAssociationResults result={result()} locale="fr" />);
    expect(descriptive).toContain('Descriptif uniquement');
    expect(descriptive).toContain('DESCRIPTIVE_ONLY_NO_INFERENCE_REQUESTED');
  });

  it('renders unavailable and absent evidence without inventing values or implying no structure', () => {
    const perComponent = result(undefined, { status: 'unavailable', reason: 'PCA_COMPONENT_NOT_RESOLVED', value: null });
    const perPcHtml = renderToStaticMarkup(<FactorAssociationResults result={perComponent} locale="en" />);
    expect(perPcHtml).toContain('PCA_COMPONENT_NOT_RESOLVED');
    expect(perPcHtml).toContain('Unavailable · PCA_COMPONENT_NOT_RESOLVED');
    expect(perPcHtml).not.toContain('<td>0.5</td>');

    const html = renderToStaticMarkup(<FactorAssociationResults result={{ status: 'unavailable', reason: 'NO_QUALIFIED_PCA', value: null }} locale="fr" />);
    expect(html).toContain('NO_QUALIFIED_PCA');
    expect(html).toContain('Aucun résultat de facteur n’a été fourni.');
    expect(html).toContain('Un facteur absent ou indisponible ne montre pas que la structure ou la confusion est absente.');
  });

  it('keeps accessible section IDs unique when multiple factor result panels are rendered', () => {
    const html = renderToStaticMarkup(<><FactorAssociationResults result={result()} locale="en" /><FactorAssociationResults result={result()} locale="en" /></>);
    const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
    expect(ids.length).toBeGreaterThan(10);
    expect(new Set(ids).size).toBe(ids.length);
    expect(html).toContain('aria-labelledby="factor-association-results-');
  });
});
