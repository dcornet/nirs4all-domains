"""Public/private transport schemas; no data, results or native implementation."""
from pathlib import Path
from nirs4all_domains.storage import atomic_json


def state_schema():
    return {'type': 'object', 'required': ['status', 'reason', 'value'],
        'properties': {'status': {'enum': ['computed', 'unavailable', 'failed', 'insufficient_data',
            'insufficient_information', 'not_identifiable', 'inconclusive']},
            'reason': {'type': ['string', 'null']}, 'value': {}},
        'allOf': [{'if': {'properties': {'status': {'const': 'computed'}}},
            'then': {'properties': {'reason': {'type': 'null'}, 'value': {'not': {'type': 'null'}}}},
            'else': {'properties': {'reason': {'type': 'string', 'minLength': 1}, 'value': {'type': 'null'}}}}]}


def main():
    metric = {'allOf': [{'$ref': '#/$defs/state'},
        {'if': {'properties': {'status': {'const': 'computed'}}}, 'then': {'properties': {'value': {'type': 'number'}}}}]}
    row = {'type': 'object', 'required': ['view_id', 'representation', 'family', 'modality', 'verified_population_id',
        'n_observations', 'n_bands', 'neighbor_support', 'metrics', 'metadata_agreement'],
        'properties': {'view_id': {'type': 'string', 'minLength': 1}, 'representation': {'enum': ['raw', 'snv']},
            'family': {'type': 'string'}, 'modality': {'type': 'string'}, 'verified_population_id': {'type': ['string', 'null']},
            'n_observations': {'type': 'integer', 'minimum': 2}, 'n_bands': {'type': 'integer', 'minimum': 1},
            'neighbor_support': {'type': 'object', 'required': ['mode', 'n_query', 'n_reference'],
                'properties': {'mode': {'type': 'string'}, 'n_query': {'type': ['integer', 'null']},
                    'n_reference': {'type': 'integer', 'minimum': 2}}, 'additionalProperties': False},
            'metrics': {'type': 'object', 'additionalProperties': metric},
            'metadata_agreement': {'$ref': '#/$defs/state'}}, 'additionalProperties': False}
    schema = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
        'title': 'Confidential cross-dataset synthesis; not a public-disclosure schema',
        'type': 'object', 'required': ['protocol', 'visibility', 'cohort_id', 'rows', 'distributions', 'relationships',
            'family_associations', 'paired_representation_changes', 'new_PCA_HDBSCAN_B60_fits', 'new_supervised_model_fits',
            'study_level_inference', 'H1_H5_changed', 'universal_risk_score', 'synthesis_id'],
        'properties': {'protocol': {'const': 'domains.synthesis.v0.1'}, 'visibility': {'const': 'local_private'},
            'cohort_id': {'type': 'string', 'minLength': 1}, 'rows': {'type': 'array', 'items': row},
            **{key: {'type': 'array', 'items': {'type': 'object'}} for key in
                ['distributions', 'relationships', 'family_associations', 'paired_representation_changes']},
            'new_PCA_HDBSCAN_B60_fits': {'const': 0}, 'new_supervised_model_fits': {'const': 0},
            'study_level_inference': {'$ref': '#/$defs/state'}, 'H1_H5_changed': {'const': False},
            'universal_risk_score': {'type': 'null'}, 'synthesis_id': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}},
        '$defs': {'state': state_schema()}, 'additionalProperties': False}
    for root in [Path('schemas'), Path('bridges/python/nirs4all_domains')]:
        atomic_json(root/'cross-dataset-synthesis.v1.schema.json', schema)


if __name__ == '__main__': main()
