"""Ordinary aggregate invariants and preserved history; no recurring owner review."""
import argparse
import json
from pathlib import Path
import subprocess

import jsonschema
from nirs4all_domains.disclosure import scan_bytes
from nirs4all_domains.publication import git_surfaces
from nirs4all_domains.storage import digest
from nirs4all_domains.synthesis import validate_states


def main():
    p=argparse.ArgumentParser();p.add_argument('--require-local',action='store_true');p.add_argument('--staged',action='store_true');a=p.parse_args()
    path=Path('docs/benchmarks/alpha17/structural-summary.json')
    value=json.loads(path.read_text());jsonschema.validate(value,json.loads(Path('schemas/structural-summary.v1.schema.json').read_text()))
    validate_states(value)
    for d in value['comparison']['distributions']:
        assert d['total_views']==value['coverage']['aggregate_permission_covered_views']
        assert 0<=d['computed_views']<=d['total_views']
        if d['summary']['status']=='computed':assert d['summary']['value']['count']==d['computed_views']
        assert sum(d['missing_reasons'].values())+d['computed_views']==d['total_views']
    historic=json.loads(Path('docs/benchmarks/alpha17/retrospective-anchors.json').read_text())
    assert digest(historic['source_report'])==historic['source_report_sha256']
    validate_states(historic)
    assert historic['new_model_fits']==0 and historic['original_population_count']==1
    assert all(r.get('retained_target_accessed') is False for r in historic['rows'] if 'rmse' in r)
    # Existing sensitive-path exclusion stays active for actual Git/index blobs.
    surfaces=list(git_surfaces(Path.cwd(),staged=a.staged))
    if not a.staged:
        names=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z']).decode().split('\0')
        surfaces.extend((n,Path(n).read_bytes()) for n in names if n)
    if a.require_local:
        from alpha17_common import Context
        c=Context();c.preservation()
        science=c.load('science.json');result=json.loads(Path(science['artifact_path']).read_text())
        assert digest(path)==result['public_candidate']['sha256'], 'AGGREGATE_OUTPUT_CHANGED'
        audit=c.auth(c.store.root/'screening-rights-reviewed.json','audit')
        cohort=c.phase('cohort-v2');entries={e['dataset_id']:e for e in audit['entries']};views={v['view_id']:v for v in cohort['views']}
        assert all(entries[views[k]['catalog_id']]['permissions']['publish_aggregates']['status']=='allowed'
            for k in result['public_contributing_views']), 'SOURCE_AGGREGATE_PERMISSION_REQUIRED'
        # Reuse literal protection for actual secrets/locations; catalog tier and
        # ordinary numeric statistics are not sensitive canaries by themselves.
        sensitive=[(c.store.keys/'scope.key').read_bytes(),str(c.store.root)]
        for name,data in surfaces:scan_bytes(name.encode()+b'\n'+data,sensitive_literals=sensitive)
    print('ALPHA17_AGGREGATE_SCHEMA_STATES_AND_HISTORY_VERIFIED; NO_PRIVATE_INPUTS_IN_PORTABLE_CHECK')


if __name__=='__main__':
    try:main()
    except Exception:
        print('ALPHA17_CHECK_REFUSED');raise SystemExit(2) from None
