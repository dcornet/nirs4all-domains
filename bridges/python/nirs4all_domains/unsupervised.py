"""X-only population/identity protocols; native providers own every numeric kernel."""
from __future__ import annotations

from collections import Counter
import copy
import json
import math
import random
import subprocess

from .adaptive import partition_agreement
from .dependence import state
from .predictive import native_summary
from .storage import fingerprint

PROTOCOL = 'domains.unsupervised.v0.1'
RADII = (1e-6, .001, .01, .05, .1, .25, .5)
TOTAL_PRODUCTS = 750_000_000


def query_design(observation_ids, n_bands, seed=12017):
    """An observation SRS changes queries only, never the reference population."""
    n = len(observation_ids)
    if len(set(observation_ids)) != n or not n or n_bands < 1:
        raise ValueError('UNIQUE_COMPLETE_SOURCE_IDENTITIES_REQUIRED')
    if n*n*n_bands <= TOTAL_PRODUCTS:
        return {'mode': 'complete_source', 'ids': list(observation_ids), 'seed': None,
                'n_source': n, 'n_query': n, 'sampling': 'census'}
    q = min(128, n, TOTAL_PRODUCTS//(n*n_bands))
    if q < 32:
        raise ValueError('QUERY_SUBSET_WORK_BUDGET_EXCEEDED')
    chosen = set(random.Random(seed).sample(sorted(observation_ids), q))
    return {'mode': 'query_subset', 'ids': [s for s in observation_ids if s in chosen],
            'seed': seed, 'n_source': n, 'n_query': q,
            'sampling': 'simple random observation sample without replacement; entire reference retained'}


def represent(spectral, representation):
    """Public Methods SNV, with NumPy used solely as native binding transport."""
    if representation not in ('raw', 'snv'):
        raise ValueError('FROZEN_REPRESENTATIONS_REQUIRED')
    result = copy.deepcopy(spectral)
    if representation == 'snv':
        from n4m.roles import SNV
        import numpy as np
        if any(len(set(row)) < 2 for row in spectral['spectra']):
            raise ValueError('CONSTANT_SPECTRUM_PREVENTS_FULL_POPULATION_SNV')
        result['spectra'] = SNV(with_mean=True, with_std=True, ddof=0).fit_transform(
            np.asarray(spectral['spectra'], dtype=np.float64)).tolist()
    if any(not math.isfinite(v) for row in result['spectra'] for v in row):
        raise ValueError('NONFINITE_FULL_REPRESENTATION')
    return result


def native_profile(spectral, representation, binary, library, design=None):
    payload = {'spectral': spectral, 'representation': representation,
               'query_ids': design['ids'] if design else [], 'include_neighbors': design is not None}
    result = subprocess.run([str(binary), 'x-profile', '--methods-library', str(library)],
        input=json.dumps(payload, allow_nan=False, separators=(',', ':')),
        capture_output=True, text=True, timeout=600)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    value = json.loads(result.stdout)
    if value['test_target_accessed'] or value['protocol_version'] != PROTOCOL:
        raise ValueError('X_ONLY_SCOPE_VIOLATION')
    if value['n_observations'] != len(spectral['observation_ids']):
        raise ValueError('FULL_SOURCE_POPULATION_CHANGED')
    return value


def compact_profile(profile, design):
    """Assemble dimensionless within-source evidence; never persist PCA scores."""
    result = {k: v for k, v in profile.items() if k != 'transport_only_scores'}
    result['query_design'] = design
    scale = math.sqrt(result['pca']['full_trace'])
    eigenvalues = result['pca']['eigenvalues']
    result['pca']['pc1_fraction'] = eigenvalues[0]/result['pca']['full_trace']
    result['pca']['pc5_fraction'] = sum(eigenvalues[:5])/result['pca']['full_trace']
    for space, neighbors in result['neighborhoods']['value'].items():
        distances = [r[0]/scale for r in neighbors['distances']]
        neighbors['normalized_nearest_summary'] = native_summary(distances)
        s = neighbors['normalized_nearest_summary']
        neighbors['neighbor_distance_dispersion'] = {
            'q75_over_q25':state(s['q75']/s['q25']) if s['q25'] else state(reason='ZERO_LOWER_DISTANCE_QUARTILE'),
            'coefficient_of_variation':state(s['sd']/s['mean']) if s['mean'] and s['sd'] is not None else state(reason='ZERO_OR_INSUFFICIENT_DISTANCE_MEAN'),
            'upper_tukey_fence_fraction':sum(d>s['q75']+1.5*(s['q75']-s['q25']) for d in distances)/len(distances),
            'scope':'Within-source neighbor-distance heterogeneity and heuristic isolation; not a physical density or calibrated outlier probability.'}
        neighbors['normalization'] = 'sqrt(full representation covariance trace); within source only'
        neighbors['relative_proximity'] = [
            {'radius': t, 'n_query_with_neighbor': sum(d <= t for d in distances),
             'n_query': len(distances), 'fraction': sum(d <= t for d in distances)/len(distances)}
            for t in RADII]
        gaps = [r[-1]/r[0] for r in neighbors['distances'] if r[0] > 0]
        neighbors['rank_last_over_first_distance'] = state(native_summary(gaps)) if gaps else state(reason='ALL_NEAREST_DISTANCES_ZERO')
        neighbors['zero_nearest_distances'] = sum(r[0] == 0 for r in neighbors['distances'])
        neighbors['physical_duplicate_inference'] = state(reason='SPECTRAL_PROXIMITY_DOES_NOT_ESTABLISH_PHYSICAL_IDENTITY')
        if design['mode'] == 'query_subset':
            draws = [[] for _ in RADII]
            rng = random.Random(12019)
            for _ in range(100):
                selected = [distances[rng.randrange(len(distances))] for _ in distances]
                for values, t in zip(draws, RADII, strict=True):
                    values.append(sum(d <= t for d in selected)/len(selected))
            neighbors['query_sensitivity'] = {
                'scope': '100 conditional query-bootstrap draws; not finite-population coverage or biological uncertainty',
                'radius_fraction_summaries': [native_summary(v) for v in draws],
                'quantile_sampling_intervals': state(reason='NOT_QUALIFIED_FOR_PARTIAL_QUERY_SAMPLE')}
        else:
            neighbors['query_sensitivity'] = {'scope': 'full source census; no query sampling uncertainty'}
    return result


def neighborhood_agreement(a, b):
    """Exact identity/rank comparisons on the same prespecified query support."""
    if a['query_ids'] != b['query_ids'] or a['n_reference'] != b['n_reference'] or a['k'] != b['k']:
        raise ValueError('MATCHED_NEIGHBOR_SUPPORT_REQUIRED')
    metrics = []
    for k in (1, 4, 8):
        if k > a['k']:
            continue
        overlaps, ranks = [], []
        for left, right in zip(a['reference_indices'], b['reference_indices'], strict=True):
            overlaps.append(len(set(left[:k]) & set(right[:k]))/k)
            ranks.append(sum(i == j for i, j in zip(left[:k], right[:k], strict=True))/k)
        metrics.append({'k': k, 'set_overlap': native_summary(overlaps),
                        'exact_rank_persistence': native_summary(ranks)})
    return {'n_query': len(a['query_ids']), 'metrics': metrics,
            'scope': a['mode'], 'not_a_correlation_coefficient': True}


def component_draw(ids, components, fraction, draw, seed=12031):
    if not .5 <= fraction <= .9 or set(ids) != set(components):
        raise ValueError('COMPLETE_DECLARED_COMPONENT_MAP_REQUIRED')
    units = sorted(set(components.values()))
    rng = random.Random(fingerprint([seed, fraction, draw]))
    selected = set(rng.sample(units, math.ceil(fraction*len(units))))
    indices = [i for i, s in enumerate(ids) if components[s] in selected]
    return {'selected_units': sorted(selected), 'indices': indices,
            'observation_ids': [ids[i] for i in indices], 'n_source_units': len(units)}


def compare_partition(ids, labels, sub_ids, sub_labels):
    if len(ids) != len(labels) or len(sub_ids) != len(sub_labels) or len(set(sub_ids)) != len(sub_ids):
        raise ValueError('MATCHED_UNIQUE_PARTITION_IDENTITIES_REQUIRED')
    by_id = dict(zip(ids, labels, strict=True))
    if not set(sub_ids) <= set(ids):
        raise ValueError('SUBSAMPLE_IDS_OUTSIDE_REFERENCE')
    left, right = [by_id[s] for s in sub_ids], sub_labels
    eligible = len(left) >= 20 and len(left) >= .5*len(ids)
    def ari(a, b):
        if not eligible or len(a) < 20 or any(len(set(v)) < 2 or len(set(v)) == len(v) for v in [a,b]):
            return state(reason='INSUFFICIENT_SHARED_NONTRIVIAL_PARTITION_SUPPORT')
        return partition_agreement(a,b)
    common = [(a,b) for a,b in zip(left,right,strict=True) if a >= 0 and b >= 0]
    return {'n_common': len(left), 'reference_fraction':len(left)/len(ids),
            'ari_including_noise':ari(left,right),
            'ari_excluding_noise':ari([v[0] for v in common],[v[1] for v in common]),
            'n_jointly_clustered':len(common),
            'noise_status_agreement':sum((a<0)==(b<0) for a,b in zip(left,right,strict=True))/len(left),
            'n_reference_clusters_on_shared_support':len({v for v in left if v>=0}),
            'n_draw_clusters':len({v for v in right if v>=0})}


def pair_panel(labels, seed=12037):
    """Bounded prespecified within/between pair panel, not all-pair stability."""
    rng = random.Random(seed)
    within, between = set(), set()
    candidates = [i for i,v in enumerate(labels) if v >= 0]
    if len(candidates) < 2:
        return {'within': [], 'between': []}
    for _ in range(20000):
        i,j = sorted(rng.sample(candidates,2))
        target = within if labels[i] == labels[j] else between
        if len(target) < 128:
            target.add((i,j))
        if len(within) == len(between) == 128:
            break
    return {'within': [list(p) for p in sorted(within)], 'between': [list(p) for p in sorted(between)]}


def factor_profile(labels, scores, factor_by_id, ids, provenance):
    """Metadata transport and native association; no target table is an input."""
    from .adaptive import association
    present = [i for i,s in enumerate(ids) if s in factor_by_id and factor_by_id[s] is not None]
    factor = [str(factor_by_id[ids[i]]) for i in present]
    counts = Counter(factor)
    if not present:
        return state(reason='NO_NONMISSING_KEYED_FACTOR_VALUES')
    associations = [association(factor,[scores[i][pc] for i in present]) for pc in range(min(3,len(scores[0])))]
    for a in associations:
        if a['status']=='computed':
            a['value']['scope']='Descriptive full-source acquisition factor-PC association; not out-of-fold prediction or target association.'
    return state({'provenance':provenance, 'missing':len(ids)-len(present),
        'n_levels':len(counts), 'level_support':dict(sorted(counts.items())),
        'high_cardinality':len(counts) > .1*len(present),
        'ari_including_noise':partition_agreement(factor,[labels[i] for i in present]),
        'pc_associations':associations,
        'weighting':'one vote per acquisition; repeated acquisitions are not independent biological units',
        'noise_treatment':'noise is a category for ARI, never an invented metadata level',
        'limitation':'Low ARI does not establish absence from continuous X; high cardinality and repeated acquisition weight can affect agreement.'})


def stability_summary(reference, draws, ids, n_units, unit_scope):
    """Task-level shared-support, noise and sampled co-membership bookkeeping."""
    settings = []
    for setting, ref in enumerate(reference['cluster_settings']):
        if ref['status'] != 'computed':
            settings.append(state(reason='REFERENCE_PARTITION_UNAVAILABLE'))
            continue
        labels = ref['value']['labels']; panel = pair_panel(labels)
        counts = {tuple(p):[0,0] for kind in panel.values() for p in kind}
        records = []
        successes = 0
        for draw in draws:
            if draw['status'] != 'computed' or draw['value']['cluster_settings'][setting]['status'] != 'computed':
                records.append({'draw':draw['draw'],'status':'failed','reason':draw.get('reason') or 'DRAW_PARTITION_UNAVAILABLE'})
                continue
            value = draw['value']; sub_ids = [ids[i] for i in draw['selected_indices']]
            sub_labels = value['cluster_settings'][setting]['value']['labels']
            comparison = compare_partition(ids,labels,sub_ids,sub_labels)
            mapping = dict(zip(draw['selected_indices'],sub_labels,strict=True))
            for (i,j), exposure in counts.items():
                if i in mapping and j in mapping:
                    exposure[0] += 1
                    exposure[1] += int(mapping[i] >= 0 and mapping[i] == mapping[j])
            records.append({'draw':draw['draw'],'status':'computed','reason':None,
                'n_units':draw['n_selected_units'],'comparison':comparison,
                'membership_summary':value['cluster_settings'][setting]['value']['membership_summary'],
                'noise_fraction':value['cluster_settings'][setting]['value']['noise_fraction']})
            successes += 1
        valid = [d for d in records if d['status']=='computed']
        aris = [d['comparison']['ari_including_noise']['value'] for d in valid if d['comparison']['ari_including_noise']['status']=='computed']
        noises = [d['comparison']['noise_status_agreement'] for d in valid]
        pair_records = {kind:[{'indices':p,'exposures':counts[tuple(p)][0],
            'same_nonnoise_cluster':counts[tuple(p)][1],
            'support':counts[tuple(p)][1]/counts[tuple(p)][0] if counts[tuple(p)][0] else None,
            'support_reason':None if counts[tuple(p)][0] else 'NO_JOINT_PAIR_EXPOSURES'}
            for p in pairs] for kind,pairs in panel.items()}
        cluster_support = []
        for label in sorted({v for v in labels if v>=0}):
            values = [d['support'] for d in pair_records['within'] if labels[d['indices'][0]]==label and d['exposures']>=10]
            cluster_support.append({'reference_label':label,'n_reference_observations':labels.count(label),
                'n_pairs_exposed_at_least_10':len(values),
                'support_summary':state(native_summary(values)) if values else state(reason='NO_ADEQUATELY_EXPOSED_PAIR_PANEL')})
        def p10(values):
            return sorted(values)[max(0,math.ceil(.1*len(values))-1)] if values else None
        execution = (len(ids)>=30 and n_units>=20 and len(draws)>=20 and successes>=.9*len(draws))
        eligible = len(aris)>=.9*len(draws)
        pair_eligible = bool(cluster_support) and all(c['n_pairs_exposed_at_least_10']>=10 for c in cluster_support)
        quality = (eligible and native_summary(aris)['median']>=.9 and p10(aris)>=.8
            and noises and p10(noises)>=.9 and ref['value']['noise_fraction']<=.4
            and ref['value']['n_clusters']>=2 and pair_eligible
            and all(c['support_summary']['value']['median']>=.8 for c in cluster_support))
        classification = 'robust_structure' if execution and quality else (
            'fragile_structure' if execution and eligible and pair_eligible else 'insufficient_information')
        settings.append(state({'min_cluster_size':ref['value']['min_cluster_size'],
            'attempted_draws':len(draws),'successful_draws':successes,'eligible_ari_draws':len(aris),
            'ari_summary':state(native_summary(aris)) if aris else state(reason='NO_ELIGIBLE_SHARED_PARTITIONS'),
            'ari_p10':p10(aris),'noise_agreement_summary':state(native_summary(noises)) if noises else state(reason='NO_SUCCESSFUL_DRAWS'),
            'noise_agreement_p10':p10(noises),'draws':records,'pair_panel':pair_records,
            'cluster_pair_support':cluster_support,'classification':classification,
            'gates':{'execution_support':execution,'eligible_ari_support':eligible,'pair_support':pair_eligible,'quality':bool(quality)},
            'scope':unit_scope,'biological_sampling_uncertainty':False,
            'continuum_classification':state(reason='REGULAR_ONE_DIMENSIONAL_ALPHA5_GATE_NOT_QUALIFIED_ON_THIS_POPULATION')}))
    return {'settings':settings,'n_reference_observations':len(ids),'n_declared_resampling_units':n_units,
            'unit_scope':unit_scope,'pair_scope':'prespecified sampled pair panel; not all observation pairs',
            'biologically_independent_unit_count':state(reason='NOT_ESTIMATED_BY_ALGORITHMIC_RESAMPLING')}
