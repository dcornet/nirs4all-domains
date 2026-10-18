"""Cross-source protocol assembly; published Methods owns every numeric kernel."""
from itertools import combinations
import ctypes
import math

from .adaptive import association
from .dependence import state
from .falsification import require_pre_outcome
from .predictive import native_summary
from .storage import fingerprint
from .unsupervised import RADII

PROTOCOL = 'domains.synthesis.v0.1'
THRESHOLDS = (.5, .8, .95)
PRIMARY = ('pc1_fraction', 'pc5_fraction', 'retained_variance_fraction', 'effective_dimension',
    'clusters_8', 'noise_8', 'nn_median', 'neighbor_cv', 'proximity_0.01', 'raw_snv_ari', 'raw_snv_overlap')


def validate_states(value):
    """Check scientific result states throughout nested comparative evidence."""
    if isinstance(value, dict):
        if 'status' in value:
            if not {'value', 'reason'} <= set(value):
                raise ValueError('EXPLICIT_STATUS_REASON_VALUE_REQUIRED')
            if value['status'] not in ['computed', 'unavailable', 'failed', 'insufficient_data',
                    'insufficient_information', 'not_identifiable', 'inconclusive']:
                raise ValueError('UNKNOWN_SCIENTIFIC_RESULT_STATUS')
            if value['status'] == 'computed':
                if value['reason'] is not None or value['value'] is None:
                    raise ValueError('COMPUTED_STATE_INVARIANT')
            elif value['value'] is not None or not isinstance(value['reason'], str) or not value['reason']:
                raise ValueError('NONCOMPUTED_STATE_INVARIANT')
        for item in value.values(): validate_states(item)
    elif isinstance(value, list):
        for item in value: validate_states(item)
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError('NONFINITE_SCIENTIFIC_RESULT')


def scalar(value, reason='SOURCE_DESCRIPTOR_UNAVAILABLE'):
    if isinstance(value, dict) and set(['status', 'reason', 'value']) <= set(value):
        if value['status'] != 'computed':
            return state(reason=value['reason'] or reason, status=value['status'])
        value = value['value']
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return state(reason=reason)
    return state(float(value))


def unwrap(value):
    if isinstance(value, dict) and 'status' in value:
        return value.get('value') if value['status'] == 'computed' else None
    return value


def describe(view_id, representation, profile, agreement, *, family, modality, population=None):
    """Accept one existing complete-source compact profile, never X or Y arrays."""
    require_pre_outcome([profile, agreement])
    if representation not in ['raw', 'snv']:
        raise ValueError('FROZEN_RAW_SNV_REPRESENTATION_REQUIRED')
    pca = profile.get('pca', {})
    metrics = {k: scalar(pca.get(k)) for k in ['pc1_fraction', 'pc5_fraction', 'retained_variance_fraction']}
    metrics['effective_dimension'] = scalar(profile.get('effective_dimension'), 'EXACT_FULL_MOMENTS_UNAVAILABLE')
    clusters = profile.get('cluster_settings', [])
    for index, size in enumerate([8, 12]):
        item = unwrap(clusters[index]) if index < len(clusters) else None
        if item is not None and item.get('min_cluster_size') != size:
            raise ValueError('FROZEN_CLUSTER_PARAMETER_BINDING_REQUIRED')
        missing = clusters[index] if index < len(clusters) else None
        metrics['clusters_'+str(size)] = scalar(item.get('n_clusters') if item else missing)
        metrics['noise_'+str(size)] = scalar(item.get('noise_fraction') if item else missing)
    neighbors = unwrap(profile.get('neighborhoods')) or {}
    full = neighbors.get('full_axis', {})
    summary = full.get('normalized_nearest_summary', {})
    for key in ['median', 'q25', 'q75', 'mean', 'sd']:
        metrics['nn_'+key] = scalar(summary.get(key))
    metrics['neighbor_cv'] = scalar(full.get('neighbor_distance_dispersion', {}).get('coefficient_of_variation'))
    proximity = {r['radius']: r for r in full.get('relative_proximity', [])}
    for radius in RADII:
        metrics['proximity_'+str(radius)] = scalar(proximity.get(radius, {}).get('fraction'))
    agree = unwrap(agreement) or {}
    partitions = agree.get('partitions', [])
    primary = unwrap(partitions[0]) if partitions else None
    metrics['raw_snv_ari'] = scalar((primary or {}).get('ari_including_noise'))
    neighbor_agreement = unwrap(agree.get('full_axis_neighbors')) or {}
    candidates = [v for v in neighbor_agreement.get('metrics', []) if v.get('k') == 8]
    metrics['raw_snv_overlap'] = scalar(candidates[0].get('set_overlap', {}).get('mean') if len(candidates) == 1 else None)
    design = profile.get('query_design', {})
    return {'view_id': view_id, 'representation': representation, 'family': family, 'modality': modality,
        'verified_population_id': population, 'n_observations': profile['n_observations'], 'n_bands': profile['n_bands'],
        'neighbor_support': {'mode': full.get('mode', design.get('mode', 'unavailable')),
            'n_query': full.get('n_query', design.get('n_query')), 'n_reference': full.get('n_reference', profile['n_observations'])},
        'metrics': metrics, 'metadata_agreement': profile.get('metadata_agreement', state(reason='NO_KEYED_METADATA_EVIDENCE'))}


def summarize(values):
    return state(native_summary(values)) if values else state(reason='NO_ELIGIBLE_SOURCE_VALUES')


def threshold_association(left, right, identities):
    """Fixed native abs-Pearson screens; no locally implemented correlation."""
    if len(left) != len(right) or len(left) != len(identities) or len(set(identities)) != len(identities):
        raise ValueError('MATCHED_UNIQUE_SOURCE_IDENTITIES_REQUIRED')
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in left+right):
        raise ValueError('FINITE_SOURCE_DESCRIPTOR_PAIRS_REQUIRED')
    if len(left) < 3:
        return state(reason='FEWER_THAN_THREE_MATCHED_SOURCE_VALUES', status='insufficient_data')
    if native_summary(left)['sd'] == 0 or native_summary(right)['sd'] == 0:
        return state(reason='CONSTANT_DESCRIPTOR_NOT_EVIDENCE_OF_LOW_ASSOCIATION')
    from n4m import lib, MatrixView
    x = (ctypes.c_double * len(left))(*left)
    y = (ctypes.c_double * len(right))(*right)
    view = MatrixView(ctypes.cast(x, ctypes.c_void_p), len(left), 1, 1, 1, 1, 0)
    decisions = []
    for threshold in THRESHOLDS:
        handle, count = ctypes.c_void_p(), ctypes.c_int64()
        status = lib.n4m_feature_selection_correlation_create(ctypes.byref(handle), threshold, -1)
        if status:
            raise ValueError('NATIVE_CORRELATION_CREATE_FAILED')
        try:
            status = lib.n4m_feature_selection_correlation_fit(handle, view, y, len(right))
            if not status:
                status = lib.n4m_feature_selection_correlation_output_cols(handle, ctypes.byref(count))
            if status or count.value not in [0, 1]:
                raise ValueError('NATIVE_CORRELATION_SELECTION_CONTRACT_FAILED')
            decisions.append({'strict_abs_pearson_threshold': threshold, 'exceeds': count.value == 1})
        finally:
            lib.n4m_feature_selection_correlation_destroy(handle)
    return state({'screens': decisions, 'n_source_views': len(left), 'source_view_ids': identities,
        'exact_coefficient': state(reason='PUBLIC_FILTER_EXPOSES_SELECTION_NOT_COEFFICIENT'),
        'provider': 'Methods1.3.6 public correlation fit/output_cols ABI',
        'inference': 'Descriptive pairwise source-view screen; no independent-study p-value or sign supplied.'})


def compare(rows, cohort_id):
    require_pre_outcome(rows)
    keys = [(r['view_id'], r['representation']) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError('DUPLICATE_SOURCE_REPRESENTATION_IN_SYNTHESIS')
    if any(r['representation'] not in ['raw', 'snv'] for r in rows):
        raise ValueError('FROZEN_RAW_SNV_REPRESENTATION_REQUIRED')
    by_key = dict(zip(keys, rows, strict=True))
    distributions, relationships, family_effects = [], [], []
    all_metrics = sorted({k for r in rows for k in r['metrics']})
    for representation in ['raw', 'snv']:
        current = sorted([r for r in rows if r['representation'] == representation], key=lambda r: r['view_id'])
        for metric in all_metrics:
            eligible = [r for r in current if r['metrics'].get(metric, {}).get('status') == 'computed']
            vals = [r['metrics'][metric]['value'] for r in eligible]
            distributions.append({'representation': representation, 'metric': metric, 'n_source_views': len(current),
                'eligible_source_view_ids': [r['view_id'] for r in eligible], 'summary': summarize(vals),
                'missing_reasons': {r['view_id']: r['metrics'].get(metric, state(reason='MISSING_DESCRIPTOR_COLUMN'))['reason']
                    for r in current if r not in eligible}})
            if metric in PRIMARY:
                family_effects.append({'representation': representation, 'metric': metric,
                    'source_view_ids': [r['view_id'] for r in eligible],
                    'association': association([r['family'] for r in eligible], vals) if vals else state(reason='NO_ELIGIBLE_SOURCE_VALUES'),
                    'scope': 'Declared material-family view association; n/p and study overlap remain unadjusted.'})
        columns = list(PRIMARY) + ['n_observations', 'n_bands']
        for left, right in combinations(columns, 2):
            if left in ['n_observations', 'n_bands'] and right in ['n_observations', 'n_bands']:
                continue
            def cell(row, key):
                return scalar(row[key]) if key in ['n_observations', 'n_bands'] else row['metrics'].get(key, state(reason='MISSING_DESCRIPTOR_COLUMN'))
            eligible = [r for r in current if cell(r, left)['status'] == cell(r, right)['status'] == 'computed']
            relationships.append({'representation': representation, 'left': left, 'right': right,
                'association': threshold_association([cell(r, left)['value'] for r in eligible],
                    [cell(r, right)['value'] for r in eligible], [r['view_id'] for r in eligible])})
    paired = []
    for metric in all_metrics:
        common = sorted({key[0] for key in keys if all((key[0], rep) in by_key and
            by_key[key[0], rep]['metrics'].get(metric, {}).get('status') == 'computed' for rep in ['raw', 'snv'])})
        changes = [{'view_id': key, 'raw': by_key[key, 'raw']['metrics'][metric]['value'],
            'snv': by_key[key, 'snv']['metrics'][metric]['value'],
            'snv_minus_raw': by_key[key, 'snv']['metrics'][metric]['value'] - by_key[key, 'raw']['metrics'][metric]['value']} for key in common]
        paired.append({'metric': metric, 'matched_views': changes, 'change_summary': summarize([r['snv_minus_raw'] for r in changes]),
            'scope': 'Paired within-source difference; observation weighting and numerical support unchanged.'})
    result = {'protocol': PROTOCOL, 'visibility': 'local_private', 'cohort_id': cohort_id, 'rows': rows,
        'distributions': distributions, 'relationships': relationships, 'family_associations': family_effects,
        'paired_representation_changes': paired, 'new_PCA_HDBSCAN_B60_fits': 0, 'new_supervised_model_fits': 0,
        'study_level_inference': state(reason='DESCRIPTIVE_SOURCE_VIEWS_WITH_UNRESOLVED_POPULATION_OVERLAP', status='not_identifiable'),
        'H1_H5_changed': False, 'universal_risk_score': None}
    result['synthesis_id'] = fingerprint(result)
    validate_states(result)
    return result
