"""Generate the optional D1 sidecar contract; historical schemas are untouched."""
import json
from pathlib import Path


def record(properties):
    return {'type': 'object', 'additionalProperties': False,
            'properties': properties, 'required': list(properties)}


def state(value):
    return {'oneOf': [record({'status': {'const': 'computed'}, 'reason': {'type': 'null'}, 'value': value}),
                      record({'status': {'enum': ['unavailable', 'not_applicable']},
                              'reason': {'type': 'string', 'minLength': 1}, 'value': {'type': 'null'}})]}


def schema():
    text = {'type': 'string', 'minLength': 1}
    count = {'type': 'integer', 'minimum': 0}
    fraction = {'type': 'number', 'minimum': 0, 'maximum': 1}
    nullable_number = {'type': ['number', 'null']}
    summary = record({key: nullable_number for key in ('count', 'min', 'max', 'mean', 'sd', 'q25', 'median', 'q75')})
    missing = record({'status': {'const': 'unavailable'}, 'reason': text, 'value': {'type': 'null'}})
    cluster = record({'label': count, 'n_observations': {'type': 'integer', 'minimum': 1},
                      'fraction_of_fitted_population': fraction,
                      'persistence': state({'type': 'number', 'minimum': 0}),
                      'hierarchy_node_index': state(count), 'independent_unit_support': missing})
    value = record({'n_observations': {'type': 'integer', 'minimum': 1}, 'support_unit': text,
                    'n_selected_clusters': count, 'n_noise': count, 'noise_fraction': fraction,
                    'clusters': {'type': 'array', 'items': cluster},
                    'persistence_distribution': state(summary), 'observation_support_distribution': state(summary),
                    'distribution_weighting': {'const': 'one vote per selected cluster; no noise-cluster vote'},
                    'persistence_convention': {'enum': ['unknown', 'global_infinite_lambda_fallback_one',
                        'global_zero_lambda_fallback_one', 'finite_or_unknown_global_lambda']},
                    'discrete_structure': {'enum': ['no_selected_clusters', 'single_selected_cluster', 'multiple_selected_clusters']}})
    root = record({'schema_version': {'const': 1},
                   'protocol_version': {'const': 'domains.selected_branch_persistence.v1'},
                   'source': record({'content_sha256': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'},
                       'protocol_version': {'enum': ['domains.structure.v0.1', 'domains.unsupervised.v0.1']},
                       'setting_index': count, 'native_pointer': {'type': 'string', 'pattern': '^/'}}),
                   'configuration': record({'min_cluster_size': {'type': ['integer', 'null'], 'minimum': 2},
                       'min_samples': {'type': ['integer', 'null'], 'minimum': 1},
                       'selection_method': {'enum': ['eom', 'leaf']}, 'allow_single_cluster': {'type': 'boolean'}}),
                   'representation': record({'name': text, 'partition': text, 'pca': {'type': ['object', 'null']}}),
                   'provider': {'type': 'object'},
                   'summary_provider': state(record({'name': {'const': 'Methods summary ABI'}, 'version': text,
                       'binary_sha256': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}})),
                   'selected_structure': state(value),
                   'hierarchy': state(record({'pointer': {'type': 'string', 'pattern': '^/'}, 'n_nodes': count})),
                   'resampling_stability': missing,
                   'separate_resampling_evidence_pointer': {'type': ['string', 'null']},
                   'finding': record({'observation': text, 'confidence': {'const': 'descriptive_within_fit'},
                                      'consequence': text, 'action': text}),
                   'limitations': {'type': 'array', 'minItems': 8, 'items': text}})
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema',
            '$id': 'https://nirs4all.org/domains/selected-branch-persistence.v1.schema.json', **root}


if __name__ == '__main__':
    output = json.dumps(schema(), indent=2, sort_keys=True) + '\n'
    for folder in ('schemas', 'bridges/python/nirs4all_domains'):
        (Path(folder) / 'selected-branch-persistence.v1.schema.json').write_text(output, encoding='utf-8')
