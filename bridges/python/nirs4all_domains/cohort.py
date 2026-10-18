"""Identity/receipt accounting, not an estimator of independent sample size."""
from collections import Counter
import re

from .dependence import state
from .falsification import require_pre_outcome
from .storage import fingerprint

PROTOCOL = 'domains.research_cohort.v0.1'
SHA = re.compile(r'[0-9a-f]{64}')


def unique(records, key):
    values = [r[key] for r in records]
    if any(not isinstance(v, str) or not v for v in values) or len(set(values)) != len(values):
        raise ValueError('UNIQUE_DECLARED_IDENTITIES_REQUIRED')
    return dict(zip(values, records, strict=True))


def reconcile(entries, views, executions, relations):
    """All inputs are metadata; source values and outcomes cannot enter this API."""
    require_pre_outcome([entries, views, executions, relations])
    catalog = unique(entries, 'catalog_id')
    sources = unique(views, 'view_id')
    receipts = unique(executions, 'execution_id')
    observed = {}
    for view in views:
        if view['catalog_id'] not in catalog:
            raise ValueError('SOURCE_VIEW_OUTSIDE_CATALOG')
        for kind in ['study', 'population']:
            identity = view.get(kind, {})
            if identity.get('verified') is True and (not identity.get('id') or not SHA.fullmatch(identity.get('evidence_sha256') or '')):
                raise ValueError('VERIFIED_UNIT_REQUIRES_IDENTITY_AND_EVIDENCE')
    for execution in receipts.values():
        key = execution['view_id']
        if key not in sources or execution['content_sha256'] != sources[key].get('content_sha256'):
            raise ValueError('EXECUTION_SOURCE_CONTENT_IDENTITY_MISMATCH')
        if execution['status'] not in ['computed', 'partial', 'failed', 'unavailable', 'not_executed']:
            raise ValueError('UNKNOWN_EXECUTION_STATUS')
        if execution['status'] in ['computed', 'partial'] and (execution.get('receipt_verified') is not True or
                not SHA.fullmatch(execution.get('artifact_sha256') or '')):
            raise ValueError('ACTUAL_VERIFIED_EXECUTION_RECEIPT_REQUIRED')
        if key in observed:
            raise ValueError('ONE_PRESPECIFIED_EXECUTION_PER_SOURCE_VIEW_REQUIRED')
        observed[key] = execution
    pairs = set()
    relation_by_pair = {}
    shared, unknown = [], []
    for relation in relations:
        pair = relation['view_ids']
        if len(pair) != 2 or pair[0] == pair[1] or any(p not in sources for p in pair) or frozenset(pair) in pairs:
            raise ValueError('UNIQUE_DECLARED_SOURCE_RELATION_REQUIRED')
        pairs.add(frozenset(pair))
        relation_by_pair[frozenset(pair)] = relation
        if relation['status'] not in ['verified_shared', 'verified_disjoint', 'unknown_possible']:
            raise ValueError('UNKNOWN_POPULATION_RELATION')
        if relation['status'] != 'unknown_possible' and not SHA.fullmatch(relation.get('evidence_sha256') or ''):
            raise ValueError('POPULATION_RELATION_REQUIRES_ORIGINAL_EVIDENCE')
        a, b = [sources[p].get('population', {}) for p in pair]
        same = a.get('verified') is True and b.get('verified') is True and a['id'] == b['id']
        if relation['status'] == 'verified_disjoint' and same:
            raise ValueError('CONTRADICTORY_SAME_POPULATION_DISJOINTNESS')
        if relation['status'] == 'verified_shared':
            if not same:
                raise ValueError('SHARED_POPULATION_REQUIRES_ONE_VERIFIED_NAMESPACE')
            shared.append(relation)
        if relation['status'] == 'unknown_possible':
            unknown.append(relation)
    computed = [v for v in views if observed.get(v['view_id'], {}).get('status') == 'computed']
    if any(not catalog[sources[v['view_id']]['catalog_id']]['local_analysis_allowed'] for v in executions if v['status'] in ['computed', 'partial']):
        raise ValueError('COMPUTED_SOURCE_WITHOUT_ANALYSIS_AUTHORIZATION')
    verified_studies = {v['study']['id'] for v in views if v.get('study', {}).get('verified') is True}
    verified_populations = {v['population']['id'] for v in views if v.get('population', {}).get('verified') is True}
    incomplete_units = [v['view_id'] for v in views if not all(v.get(k, {}).get('verified') is True for k in ['study', 'population'])]
    unknown_pairs = 0
    for i, left in enumerate(views):
        for right in views[i+1:]:
            a, b = [v.get('population', {}) for v in [left, right]]
            same = a.get('verified') is True and b.get('verified') is True and a['id'] == b['id']
            relation = relation_by_pair.get(frozenset([left['view_id'], right['view_id']]), {})
            if not same and relation.get('status') != 'verified_disjoint':
                unknown_pairs += 1
    closed_xy = [v for v in views if catalog[v['catalog_id']]['local_analysis_allowed'] and
        v.get('xy_mapping_verified') is True and v.get('target_unit_verified') is True]
    supervised = [v for v in closed_xy if all(v.get(k) is True for k in [
        'physical_reference_closure_verified', 'exact_folds_frozen', 'retained_isolation_verified', 'supervised_budget_admitted'])]
    counts = {
        'catalog_entries': len(catalog), 'spectral_source_views': len(views),
        'authorized_local_catalog_entries': sum(e['local_analysis_allowed'] is True for e in entries),
        'available_complete_X_views': sum(v.get('complete_X_available') is True and catalog[v['catalog_id']]['local_analysis_allowed'] for v in views),
        'calculated_X_views': len(computed),
        'partial_X_views': sum(v['status'] == 'partial' for v in executions),
        'incomplete_or_unexecuted_views': len(views) - len(computed),
        'verified_original_studies': len(verified_studies), 'verified_physical_populations': len(verified_populations),
        'views_with_unresolved_study_or_population': len(incomplete_units),
        'XY_descriptive_eligible_views': len(closed_xy), 'leakage_safe_supervised_eligible_views': len(supervised),
        'approved_public_disclosure_views': sum(v.get('exact_publication_approved') is True for v in views)}
    value = {'protocol': PROTOCOL, 'visibility': 'local_private', 'denominators': counts,
        'entries': entries, 'views': views, 'executions': executions, 'relations': relations,
        'known_shared_population_relations': shared, 'explicit_unknown_overlap_relations': unknown,
        'unknown_or_unproven_disjoint_source_pairs': unknown_pairs,
        'unresolved_unit_views': incomplete_units,
        'independent_study_denominator': state(reason='UNKNOWN_OVERLAP_OR_UNIT_CLOSURE_PREVENTS_STUDY_LEVEL_INFERENCE', status='not_identifiable')
            if incomplete_units or unknown or unknown_pairs else state({'verified_studies': len(verified_studies),
                'scope': 'Verified identities alone do not establish random study sampling or confirmatory power.'}),
        'material_family_views': dict(Counter(v.get('family', 'unresolved') for v in views)),
        'modality_views': dict(Counter(v.get('modality', 'unresolved') for v in views)),
        'scientific_scope': 'Source-view descriptions; unknown scientific units are not unique new studies.'}
    value['cohort_id'] = fingerprint(value)
    return value
