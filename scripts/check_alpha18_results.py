"""Portable bank accounting and explicit scientific-state invariants."""
import argparse
import json
from pathlib import Path
from pathlib import PureWindowsPath,PurePosixPath
import jsonschema
from nirs4all_domains.synthesis import validate_states
from nirs4all_domains.storage import fingerprint


def read(name):return json.loads(Path(name).read_text(encoding='utf-8'))


def portable_paths(value):
    if isinstance(value,dict):
        for key,item in value.items():portable_paths(key);portable_paths(item)
    elif isinstance(value,list):
        for item in value:portable_paths(item)
    elif isinstance(value,str):
        assert not PureWindowsPath(value).is_absolute() and not PurePosixPath(value).is_absolute(),'ABSOLUTE_DEVELOPMENT_PATH_IN_PUBLIC_MANIFEST'


def main():
    p=argparse.ArgumentParser();p.add_argument('--require-local',action='store_true');a=p.parse_args()
    root=Path('docs/campaign');inventory=read(root/'bank-inventory.json')
    x=read(root/'structural-matrix.json');experiment=read(root/'experiment-matrix.json');confrontation=read(root/'confrontation.json');status=read(root/'status.json')
    assert len(inventory['entries'])==164 and len(inventory['source_views'])==len(x['sources'])==171
    assert len({r['dataset_id'] for r in inventory['entries']})==164
    assert {r['view_id'] for r in x['sources']}=={r['view_id'] for r in inventory['source_views']}
    assert sum(x['counts'].values())==171
    assert len(experiment['tasks'])==len({t['task_id'] for t in experiment['tasks']})==2054
    assert sum(experiment['counts'].values())==2054
    assert status['source_execution_counts']==x['counts'] and status['reference_task_counts']==experiment['counts']
    assert experiment['descriptor_freeze_id']==x['descriptor_freeze_id']
    assert not x['target_used_for_descriptors'] and not experiment['independent_generalization_validated'] and not confrontation['independent_confirmation']
    for s in x['sources']:
        if s['aggregates']['status']=='computed':
            assert s['aggregate_permission'] in ['allowed','allowed_noncommercial']
            assert all(r['view_id']==s['view_id'] and r['n_observations']==s['n_observations'] and r['n_bands']==s['n_bands'] for r in s['aggregates']['value'])
    permitted={s['view_id'] for s in x['sources'] if s['aggregate_permission'] in ['allowed','allowed_noncommercial']}
    for t in experiment['tasks']:
        assert not t['retained_target_decoded'] and not t['independent_generalization']
        if t['aggregates']['status']=='computed':
            assert t['view_id'] in permitted
            v=t['aggregates']['value'];assert 0<v['n_evaluated']<=v['n_development']
            for family in v['families'].values():
                if family['pooled']['status']=='computed':
                    assert sum(f['n_evaluation'] for f in family['folds'])==v['n_evaluated']
                    for f in family['folds']:assert f['n_train']+f['n_evaluation']==v['n_evaluated']
    for t in confrontation['stress_tasks']+confrontation['SNV_stress_tasks']:
        if t['result']['status']=='computed':
            assert t['view_id'] in permitted
            v=t['result']['value'];assert v['matched_evaluation'] and v['matched_training_size']
            assert v['regimes']['size_control']['n_train']==v['regimes']['context_excluded']['n_train']
    for r in confrontation['representation_interactions']:
        if r['result']['status']=='computed':
            assert r['result']['value']['matched_memberships_verified']
            assert r['result']['value']['common_null_denominator_verified']
    for r in confrontation['declared_plot_sensitivity']:
        if r['result']['status']=='computed':
            for pair in r['result']['value']['paired_comparison'].values():
                if pair['status']=='computed':assert pair['value']['n_common_evaluation']>0
            assert all('oof' not in fam for fam in r['result']['value']['grouped_reference']['families'].values())
    for path in root.glob('*.json'):
        value=read(path);validate_states(value);portable_paths(value)
    jsonschema.validate(read('configs/bank/study-evidence.json'),read('schemas/study-evidence.v1.schema.json'))
    schema=read('schemas/full-bank-matrix.v1.schema.json')
    for matrix in [x,experiment,confrontation]:jsonschema.validate(matrix,schema)
    if a.require_local:
        from alpha18_common import Context
        from nirs4all_domains.storage import digest
        c=Context();f=c.load('campaign-freeze.json')
        assert f['target_numeric_cells_decoded']==f['model_fits']==0
        for path,sha in f['controller_sha256'].items():
            if Path(path).as_posix()=='bridges/python/nirs4all_domains/full_bank.py':
                continuation=c.load('group-explicit-fold-code-continuation.json')
                assert digest('.audit/alpha18-full-bank-primary-first.py')==sha==continuation['primary_core_sha256']
                delivery=c.load('delivery-adapter-code-continuation.json')
                assert digest('.audit/alpha18-full-bank-grouped-first.py')==continuation['current_core_sha256']==delivery['prior_grouped_core_sha256']
                assert digest(path)==delivery['packaged_core_sha256']
            else:assert digest(path)==sha
        for s in f['sources']:
            if s.get('input_sha256'):assert digest(s['matrix'])==s['input_sha256']
        for name in ['X-progress.json','reference-progress.json','stress-progress.json','SNV-stress-progress.json','null-progress.json','group-sensitivity-progress.json']:
            if not (c.root/name).exists():continue
            for r in c.load(name):
                if r.get('artifact_path'):assert digest(r['artifact_path'])==r['artifact_sha256']
        assert c.approval['workspace_ceiling_increase']+c.approval['campaign_ceiling_increase']<=5000000000
        c.preservation()
    print('ALPHA18_FULL_BANK_ACCOUNTING_STATES_AND_ALIGNMENT_VERIFIED')

if __name__=='__main__':main()
