"""Check separate structural JSON schema, availability and exact-population invariants."""
import json
from pathlib import Path
import sys
import jsonschema

ROOT = Path(__file__).resolve().parents[1]


def check(report):
    jsonschema.validate(report, json.loads((ROOT/'schemas/structure-report.v1.schema.json').read_text()))
    assert report['test_target_accessed'] is False
    assert (report['reason'] is None) == (report['status'] == 'computed')
    assert report['held_out_assignment']['status'] == 'unavailable'
    assert report['held_out_assignment']['value'] is None and report['held_out_assignment']['reason']
    for setting in report['settings']:
        assert (setting['reference'] is not None) == (setting['status'] == 'computed')
        assert len(setting['replicates']) == report['configuration']['replicates']
        for record in [setting, *setting['replicates']]:
            fit = record.get('fit', record.get('reference'))
            assert (fit is not None) == (record['status'] == 'computed')
            assert (record['reason'] is None) == (record['status'] == 'computed')
            if fit:
                assert fit['pca']['fit_partition'] == 'train'
                assert len(fit['physical_sample_ids']) == len(fit['scores']) == len(fit['hdbscan']['labels'])
        for comparison in [setting['comparison_to_primary'], *[r['comparison'] for r in setting['replicates']]]:
            if comparison:
                for name in ['ari_including_noise', 'ari_excluding_noise']:
                    e = comparison[name]
                    assert (e['value'] is not None and e['reason'] is None) if e['status'] == 'computed' else (e['value'] is None and e['reason'])
                    assert set(e['physical_sample_ids']) <= set(comparison['common_physical_sample_ids'])


if __name__ == '__main__':
    report = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'), parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
    check(report)
    print('Structural schema, availability and population invariants valid')
