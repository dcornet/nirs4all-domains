"""Offline finite/schema/identity/fold/preservation checks; no acquisition or fit."""
import json
import math
from pathlib import Path
from nirs4all_domains.bank import schema_check
from nirs4all_domains.registry import verify_evidence,verify_storage
from nirs4all_domains.storage import digest,fingerprint

ROOT=Path('docs/benchmarks/alpha11')


def finite(value):
    if isinstance(value,float) and not math.isfinite(value):raise ValueError('NONFINITE_SCIENTIFIC_VALUE')
    if isinstance(value,dict):
        if {'status','reason','value'}<=set(value):
            if value['status'] in ['computed','exploratory']:
                if value['reason'] is not None or value['value'] is None:raise ValueError('INVALID_COMPUTED_STATE')
            elif value['value'] is not None or not value['reason']:raise ValueError('INVALID_UNAVAILABLE_STATE')
        for v in value.values():finite(v)
    elif isinstance(value,list):
        for v in value:finite(v)


def main():
    inventory=json.loads(Path('docs/audit/catalog-inventory-alpha8.json').read_text())
    cohort={r['dataset_id'] for r in inventory['datasets'] if r['tier']=='public'}
    coverage=json.loads((ROOT/'public-coverage.json').read_text())
    assert len(cohort)==42 and {r['dataset_id'] for r in coverage['entries']}==cohort
    assert len(coverage['entries'])==42
    for r in coverage['entries']:
        schema_check(r,'adaptive-coverage');assert r['record_id']==fingerprint({k:v for k,v in r.items() if k!='record_id'})
        p=Path(r['profile_ref']['path']);assert digest(p)==r['profile_ref']['sha256']
    for p in (ROOT/'public').glob('*.json'):schema_check(json.loads(p.read_text()),'adaptive-coverage')
    assert coverage['counts']['X0']['computed']==37 and coverage['metadata_profiles']==35
    assert coverage['counts']['MODEL']['computed']==2 # one historical public task, one new conditional task
    frozen=json.loads((ROOT/'litter-evaluation.json').read_text())
    assert frozen['evaluation_id']==fingerprint({k:v for k,v in frozen.items() if k!='evaluation_id'})
    result=json.loads((ROOT/'litter-model-results.json').read_text());schema_check(result,'repeated-design-result')
    assert result['evaluation_id']==frozen['evaluation_id'] and not result['test_target_accessed']
    actual_fits=0
    for model in result['models'].values():
        assert len(model['designs'])==3
        for d in model['designs']:
            assert d['status']=='computed';v=d['value'];rows=v['oof'];assert len(rows)==298
            assert len({r['physical_sample_id'] for r in rows})==298
            assert len(v['transfer_evaluation_ids'])==297
            folds=frozen['designs'][v['design_id']]['outer'];by_id={r['physical_sample_id']:r for r in rows}
            for fold in folds['folds']:
                assert not set(fold['train_sample_ids'])&set(fold['validation_sample_ids'])
                a={by_id[s]['component_id'] for s in fold['train_sample_ids']};b={by_id[s]['component_id'] for s in fold['validation_sample_ids']}
                assert not a&b
            actual_fits+=sum(3*l['candidate_count']+1 for l in v['lineage'])
        assert model['refit_variation']['value']['n_unique_physical_units']==298
    assert actual_fits==324
    for name in ['litter-evidence','litter-transfer-evidence']:
        record=json.loads((ROOT/(name+'.json')).read_text());schema_check(record,'qualification-evidence');verify_evidence(record)
        assert record['qualifications']['independent_support']['status']=='unavailable'
    for p in ROOT.glob('*-suite.json'):
        if p.name=='tabpfn-future-suite.json':continue
        value=json.loads(p.read_text());schema_check(value,'benchmark-suite')
        assert value['suite_id']==fingerprint({k:v for k,v in value.items() if k!='suite_id'})
    assert not json.loads((ROOT/'low-dependence-candidate-suite.json').read_text())['tasks']
    assert len(json.loads((ROOT/'transfer-suite.json').read_text())['tasks'])==1
    correction=json.loads((ROOT/'source-isolation.json').read_text())
    assert correction['original_source_audit_numeric_retained_access'] and correction['retained_numeric_mutations']==24
    assert correction['sanitized_task_exact'] and correction['transfer_development_exact']
    assert json.loads((ROOT/'transfer-geometry.json').read_text())['same_training_fit_exact']
    plan=json.loads((ROOT/'tabpfn-future-suite.json').read_text())
    assert plan['suite_id']==fingerprint({k:v for k,v in plan.items() if k!='suite_id'})
    assert not plan['tabpfn_installed'] and not plan['tabpfn_fitted'] and not plan['checkpoint_acquired']
    checked=0
    for path,sha in json.loads(Path('docs/audit/alpha11-frozen-output-hashes.json').read_text()).items():
        p=Path(path)
        if p.exists():assert digest(p)==sha;checked+=1
        elif not path.startswith('results/'):raise ValueError('MISSING_PORTABLE_PROTECTED_ARTIFACT:'+path)
    for p in ROOT.rglob('*.json'):
        d=json.loads(p.read_text());finite(d)
        if '\\VS projects\\' in p.read_text() or 'D:/' in p.read_text():raise ValueError('ABSOLUTE_DEVELOPMENT_PATH_IN_PORTABLE_EVIDENCE')
    manifest=ROOT/'storage.json'
    if manifest.exists():schema_check(json.loads(manifest.read_text()),'storage-manifest');verify_storage(json.loads(manifest.read_text()),ROOT)
    print(json.dumps({'public_entries':42,'x0_computed':37,'new_primary_model_fits':actual_fits,'protected_files_present_verified':checked,'finite_schema_identity_checks':True}))


if __name__=='__main__':main()
