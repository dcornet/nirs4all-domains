"""Deterministic TEST DATA ONLY; no fitting, clustering, metric or numerical backend.

Expectations were frozen in docs/CLUSTERING_STABILITY_PROTOCOL.md before execution.
Existing fixture files are never replaced.
"""
import json
from pathlib import Path
import random


def fixture(kind):
    rng = random.Random(651)
    sizes = [24, 24, 24] if kind not in ('density', 'continuum', 'diffuse', 'small', 'duplicates') else {
        'density': [44, 20, 12], 'continuum': [80], 'diffuse': [80], 'small': [12], 'duplicates': [64]}[kind]
    rows = []
    for g, count in enumerate(sizes):
        for j in range(count):
            i = len(rows)
            cx, cy = [(-8, -4), (8, -4), (0, 8)][g]
            spread = [.05, .25, .8][g] if kind == 'density' else .12
            x = [cx+rng.gauss(0, spread), cy+rng.gauss(0, spread)] + [rng.gauss(0, spread/2) for _ in range(4)]
            if kind in ('continuum', 'small'):
                x = [(i-count/2)*(.1+.02*k) for k in range(6)]
            elif kind == 'diffuse':
                x = [rng.gauss(0, 1) for _ in range(6)]
            elif kind == 'duplicates':
                x = [10.] * 6
            rows.append({'observation_id': f'o{i:03}', 'sample_id': f'p{i:03}', 'physical_sample_id': f'p{i:03}',
                'independence_group': f'block:{i//2:03}', 'partition': 'train', 'x': x, 'y': rng.gauss(0, 1),
                'reference_id': f'ref:{i:03}', 'reference_status': 'exact', 'reference_unit': 'test_units',
                'repetition_type': 'rescan', 'metadata': {'instrument': f'instrument:{g}' if kind == 'nuisance' else 'instrument:0',
                    'campaign': 'synthetic', 'generating_group': str(g)}})
    for i in range(12):
        rows.append({'observation_id': f'held:o{i}', 'sample_id': f'held:p{i}', 'physical_sample_id': f'held:p{i}',
            'independence_group': f'held:block:{i//2}', 'partition': 'test', 'x': [999.] * 6, 'y': 1e30,
            'metadata': {'instrument': 'instrument:0', 'campaign': 'synthetic'}})
    return {'schema_version': 1, 'context': {'dataset_id': 'controlled_structure_'+kind, 'content_version': '1',
        'source_id': 'X', 'target_id': 'y', 'split_id': 'frozen_component_split'}, 'data_origin': 'synthetic',
        'axis': list(range(1000, 1006)), 'axis_unit': 'nm', 'signal_unit': 'controlled_units', 'target_unit': 'test_units',
        'policy': {'independence_unit': 'group', 'representation': 'technical_mean', 'seed': 17,
            'pca_max_components': 20, 'pca_variance_fraction': .95}, 'observations': rows,
        'provenance': {'purpose': 'Frozen alpha.5 controlled structural input; no target-reliance inference'}}


if __name__ == '__main__':
    root = Path('tests/fixtures/structure')
    root.mkdir(parents=True, exist_ok=True)
    for name in ['separated', 'density', 'continuum', 'diffuse', 'small', 'nuisance', 'duplicates', 'independent_y']:
        with (root/(name+'.json')).open('x', encoding='utf-8') as f:
            json.dump(fixture(name), f, indent=2, allow_nan=False)
            f.write('\n')
