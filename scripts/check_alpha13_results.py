"""Read-only integrity checks; partial execution never becomes a release pass."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re

from nirs4all_domains.bank import schema_check
from nirs4all_domains.storage import digest,fingerprint
from nirs4all_domains.x_admission import authorize_x_source

ROOT=Path('docs/benchmarks/alpha13')


def read(path):
    def invalid(token):raise ValueError('NONFINITE_JSON_CONSTANT: '+token)
    return json.loads(Path(path).read_text(encoding='utf-8'),parse_constant=invalid)


def portable(value):
    if isinstance(value,dict):
        if {'status','reason','value'}<=set(value):
            if value['status'] in ['computed','exploratory']:
                assert value['reason'] is None and value['value'] is not None,'INVALID_COMPUTED_STATE'
            elif value['value'] is None:
                assert isinstance(value['reason'],str) and value['reason'],'MISSING_UNAVAILABLE_REASON'
        for key,item in value.items():
            assert key not in {'spectra','transport_only_scores','loadings','Y_test','y_test','Y','y'},'RAW_X_SCORE_OR_TARGET_PAYLOAD'
            portable(item)
    elif isinstance(value,list):
        for item in value:portable(item)
    elif isinstance(value,float):assert math.isfinite(value),'NONFINITE_JSON_VALUE'
    elif isinstance(value,str):
        assert not re.search(r'(?<![A-Za-z0-9:/])[A-Za-z]:[\\/]',value),'ABSOLUTE_DEVELOPMENT_PATH'


def check(strict_local=False):
    local=read('docs/audit/alpha13-frozen-output-hashes.json')
    assert len(local)==511
    preservation=read('docs/audit/alpha13-portable-preservation.json');absent=[];verified=0
    for path,sha in local.items():
        if not Path(path).is_file():
            assert path not in preservation['repository_blobs'],('MISSING_PORTABLE_HISTORICAL_FILE',path)
            absent.append(path);continue
        actual=digest(path)
        if actual!=sha:
            assert path in preservation['newline_only_variants'] and actual==preservation['repository_blobs'][path],('HISTORICAL_LOCAL_BYTES_CHANGED',path)
        verified+=1
    if strict_local:assert not absent,'LOCAL_ONLY_HISTORICAL_CACHE_FILES_REQUIRED'
    previous=read('docs/audit/alpha12-frozen-output-hashes.json')
    assert len(previous)==371 and all(local[p]==sha for p,sha in previous.items())
    assert len(preservation['repository_blobs'])==347
    for path,sha in preservation['repository_blobs'].items():
        data=Path(path).read_bytes()
        if digest(path)!=sha:
            assert path in preservation['newline_only_variants']
            import hashlib
            assert hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()==sha,('HISTORICAL_REPOSITORY_BYTES_CHANGED',path)
    for path in ROOT.rglob('*.json'):portable(read(path))
    design=read(ROOT/'design-power.json');freeze=read(ROOT/'calibration-freeze.json')
    assert design['selected_draw_count']==freeze['draw_count']==60
    assert freeze['design_power_sha256']==digest(ROOT/'design-power.json')
    for key,path in [('protocol_sha256','docs/ALPHA13_STABILITY_POWER_PROTOCOL.md'),
                     ('power_bridge_sha256','bridges/python/nirs4all_domains/stability_power.py'),
                     ('generator_sha256','scripts/generate_unsupervised_fixtures.py')]:
        assert freeze[key]==digest(path),('FROZEN_CALIBRATION_SOURCE_CHANGED',path)
    identity=freeze.pop('freeze_id');assert fingerprint(freeze)==identity
    schema_check(read(ROOT/'falsification-contract.json'),'falsification-contract')
    contract=read(ROOT/'falsification-contract.json');identity=contract.pop('contract_id')
    assert fingerprint(contract)==identity
    for key in ['hypothesis_register_ref','future_outcome_ref','operational_preregistration_ref']:
        assert digest(contract[key]['path'])==contract[key]['sha256']
    assert [h['hypothesis_id'] for h in contract['descriptor_bindings']]==['H1','H2','H3','H4','H5']
    assert not contract['test_target_accessed'] and not contract['model_performance_used']
    inventory=read(ROOT/'source-diversity-inventory.json');entries=inventory['entries']
    assert len(entries)==164 and len({r['dataset_id'] for r in entries})==164
    assert Counter(r['catalog_tier'] for r in entries)=={'public':42,'private':122}
    assert not inventory['target_accessed'] and inventory['spectral_bytes_acquired']==0
    assert all(not r['scientific_selection_uses_model_scores'] for r in entries)
    oracle=read(ROOT/'oracle-calibration.json')
    assert oracle['new_pca_fits']==oracle['new_hdbscan_fits']==0
    parity=read(ROOT/'native-stream-parity.json')
    assert parity['all_exact'] and len(parity['cases'])==33 and parity['real_data_fits']==0
    for key,path in [('native_characterization_source_sha256','crates/nirs4all-domains/src/unsupervised.rs'),
                     ('native_adapter_source_sha256','crates/nirs4all-domains/src/methods.rs'),
                     ('stream_bridge_sha256','bridges/python/nirs4all_domains/native_profile_stream.py')]:
        assert parity['contract'][key]==digest(path),('QUALIFIED_NATIVE_TRANSPORT_SOURCE_CHANGED',path)
    controls=[read(p) for p in (ROOT/'controls').glob('*.json')]
    completed_pca=sum(v['pca_fits'] for v in controls)
    expected=freeze['native_reference_pca_fits']+freeze['native_draw_pca_fits']
    missing=[str(ROOT/name) for name in ['controlled-calibration.json','revised-design-freeze.json','real-stability.json','source-admissions.json','x-only-extension.json','validation-feasibility.json','storage.json'] if not (ROOT/name).is_file()]
    if (ROOT/'controlled-calibration.json').exists():
        full=read(ROOT/'controlled-calibration.json');assert full['native_pca_fits']==completed_pca==6498
        assert full['native_hdbscan_attempts']==sum(v['hdbscan_attempts'] for v in controls)==12996
        assert sum(full['native_classifications'].values())==216
        qualification=read(ROOT/'controlled-qualification.json')
        assert qualification['actual_unique_pca_fits_verified']==6498 and qualification['failed_draws']==0
        assert not full['target_accessed'] and full['model_fits']==0
    if (ROOT/'source-admissions.json').exists():
        admissions=read(ROOT/'source-admissions.json');assert len(admissions['admissions'])==2
        for record in admissions['admissions']:
            schema_check(record,'x-source-admission');assert authorize_x_source(record['specification'])==record
            assert record['supervised_admission']['status']=='unavailable'
        assert admissions['admitted_confirmation_studies']==0
    if (ROOT/'x-only-extension.json').exists():
        extension=read(ROOT/'x-only-extension.json');assert len(extension['records'])==2 and extension['new_pca_fits']==4
        assert extension['hdbscan_attempts']==8 and not extension['target_accessed'] and extension['supervised_fits']==0
        for source in extension['records']:
            for rep,ref in source['profiles'].items():
                assert digest(ref['path'])==ref['sha256'];profile=read(ref['path'])
                assert profile['status']=='computed';v=profile['value'];dims=source['source_dimensions']
                assert v['n_observations']==dims['n_observations'] and v['n_bands']==dims['n_variables']
                assert v['query_design']['mode']=='complete_source' and not v['test_target_accessed']
                assert v['neighborhoods']['value']['full_axis']['n_reference']==dims['n_observations']
    if (ROOT/'real-stability.json').exists():
        real=read(ROOT/'real-stability.json');assert len(real['reports'])==3
        real_inputs=read(ROOT/'real-input-freeze.json');by_name={e['dataset_id']:e for e in real_inputs['entries']}
        exposure=read(ROOT/'real-exposure-freeze.json');plans={e['dataset_id']:e['conditions'] for e in exposure['entries']}
        actual_pca=0;actual_hdb=0;observed_classes=Counter()
        for ref in real['reports']:
            assert digest(ref['path'])==ref['sha256'];result=read(ref['path']);schema_check(result,'stability-power-result')
            record_id=result.pop('record_id');assert fingerprint(result)==record_id
            entry=by_name[result['dataset_id']];assert result['source_content_sha256']==entry['input_csv_sha256']
            assert result['resampling_design']['n_resampling_units']==entry['n_resampling_units']
            assert not result['resampling_design']['biological_sampling_uncertainty']
            assert len(result['resampling_design']['per_setting_classifications'])==8
            observed_classes.update(result['resampling_design']['per_setting_classifications'])
            for condition,summary in result['conditions'].items():
                planned=plans[result['dataset_id']][condition]
                if not any(planned['planned_feasible_settings']):
                    assert summary['status']=='insufficient_information' and summary['value'] is None;continue
                assert summary['status']=='computed'
                batch_path=ROOT/'stability-batches'/(result['dataset_id']+'.'+condition+'.json');batch=read(batch_path)
                assert len(batch['records'])==60 and batch['pca_fits']==sum(r['pca_fits'] for r in batch['records'])
                assert fingerprint(batch['panels'])==planned['panel_sha256']
                actual_pca+=batch['pca_fits'];actual_hdb+=batch['hdbscan_attempts']
                for setting in summary['value']['settings']:
                    if setting['status']=='computed':
                        assert setting['value']['pair_panel_ref']['sha256']==digest(batch_path)
                        if setting['value']['classification']=='robust_structure':assert all(setting['value']['gates'].values())
            if result['overall_classification'].get('value')=='robust_structure':
                assert result['resampling_design']['per_setting_classifications']==['robust_structure']*8
                assert all(v['status']=='computed' and v['value']>=.8 for v in result['resampling_design']['parameter_ari'])
        assert real['pca_refits']==actual_pca and real['hdbscan_attempts']==actual_hdb
        assert real['classifications']==dict(observed_classes) and sum(observed_classes.values())==24
        assert actual_pca==60*sum(any(p['planned_feasible_settings']) for e in plans.values() for p in e.values())
        assert not real['target_accessed'] and real['supervised_fits']==0
    if (ROOT/'validation-feasibility.json').exists():
        feasibility=read(ROOT/'validation-feasibility.json')
        assert feasibility['independent_confirmation_studies']==0 and feasibility['supervised_model_fits']==0
        assert feasibility['pilot']['status']=='unavailable' and feasibility['confirmatory_power']['status']=='insufficient_information'
        assert not feasibility['target_accessed'] and not feasibility['model_performance_used']
    if (ROOT/'storage.json').exists():
        from nirs4all_domains.registry import verify_storage
        manifest=read(ROOT/'storage.json');schema_check(manifest,'storage-manifest');verify_storage(manifest,ROOT)
    return {'integrity':'passed','scientific_evidence_complete':not missing,'historical_protected_local_files':len(local),
        'historical_present_files_verified':verified,'historical_local_only_files_absent':len(absent),
        'historical_repository_files':len(preservation['repository_blobs']),'catalog_metadata_entries':len(entries),
        'controlled_unique_pca_completed':completed_pca,'controlled_unique_pca_planned':expected,
        'controlled_hdbscan_attempts_completed':sum(v['hdbscan_attempts'] for v in controls),
        'missing_release_evidence':missing,'scope':'Portable scientific evidence integrity; local test/package and completed hosted CI qualification are separate.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--require-complete',action='store_true');p.add_argument('--require-local-preservation',action='store_true');args=p.parse_args()
    value=check(args.require_local_preservation);print(json.dumps(value))
    if args.require_complete and not value['scientific_evidence_complete']:raise SystemExit('ALPHA13_SCIENTIFIC_EVIDENCE_INCOMPLETE')


if __name__=='__main__':main()
