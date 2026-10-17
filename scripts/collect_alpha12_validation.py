"""Collect actual gates, executed source parity, storage and portable manifests."""
import argparse
from collections import Counter,defaultdict
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile
from nirs4all_domains.bank import schema_check
from nirs4all_domains.storage import atomic_json,digest,fingerprint,tree_bytes

ROOT=Path('.audit/alpha12');PUBLIC=Path('docs/benchmarks/alpha12')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--reuse-import',action='store_true');args=parser.parse_args()
    validation=ROOT/'validation';attempts=json.loads((validation/'checks.json').read_text());latest={r['check']:r for r in attempts}
    assert len(latest)==18 and all(r['exit_code']==0 for r in latest.values())
    assert all(digest(r['log'])==r['log_sha256'] for r in attempts)
    assert re.search(r'Ran 190 tests in [\d.]+s\s+OK',Path(latest['python']['log']).read_text(encoding='utf-8'))
    rust=sum(sum(map(int,re.findall(r'test result: ok\. (\d+) passed',Path(latest[n]['log']).read_text()))) for n in ['workspace','native'])
    assert rust==35
    wheel,=list((validation/'wheel').glob('*0.1.0a12*.whl'));matched={}
    with ZipFile(wheel) as z:
        for p in Path('bridges/python/nirs4all_domains').glob('*'):
            if p.suffix in ['.py','.json']:
                assert z.read('nirs4all_domains/'+p.name)==p.read_bytes();matched[p.name]=digest(p)
    target=ROOT/'wheel-smoke';smoke=validation/'wheel-smoke.log'
    if args.reuse_import:
        previous=json.loads(Path('docs/audit/alpha12-validation.json').read_text())
        assert previous['wheel']['sha256']==digest(wheel) and previous['wheel']['isolated_import_log_sha256']==digest(smoke)
    else:
        assert not target.exists(),'USE_REUSE_IMPORT_FOR_COMPLETED_SMOKE'
        with smoke.open('w',encoding='utf-8') as stream:
            subprocess.run([sys.executable,'-m','pip','install','--no-deps','--target',str(target),str(wheel)],check=True,stdout=stream,stderr=subprocess.STDOUT)
            env=os.environ.copy();env['PYTHONPATH']=str(target.resolve())
            code="import pathlib,nirs4all_domains;from nirs4all_domains import unsupervised,paired_x,unsupervised_sources,unsupervised_checkpoint;p=pathlib.Path(nirs4all_domains.__file__).resolve();assert 'wheel-smoke' in str(p);assert (p.parent/'unsupervised-evidence.v1.schema.json').exists();print('isolated alpha12 wheel import passed')"
            subprocess.run([sys.executable,'-c',code],check=True,env=env,stdout=stream,stderr=subprocess.STDOUT)
    protected=json.loads(Path('docs/audit/alpha12-frozen-output-hashes.json').read_text());assert len(protected)==371
    assert all(Path(p).exists() and digest(p)==h for p,h in protected.items())
    old=json.loads(Path('.audit/alpha11/qualified-model-runtime.json').read_text())
    assert all(digest(p)==h for p,h in old['scientific_sources'].items())
    frozen=json.loads((PUBLIC/'input-freeze.json').read_text());paired=json.loads((PUBLIC/'paired-x-freeze.json').read_text())
    assert digest('docs/ALPHA12_UNSUPERVISED_PROTOCOL.md')==frozen['protocol_sha256']
    assert digest('docs/ALPHA12_HYPOTHESIS_REGISTER.md')==frozen['hypotheses_sha256']
    assert digest('docs/ALPHA12_PAIRED_X_PROTOCOL.md')==paired['protocol_sha256']
    journal=json.loads(Path('results/alpha9-perten-keyed/state/journal.json').read_text())
    bridge=digest('bridges/python/nirs4all_domains/unsupervised.py')
    records=[r for r in journal['runs'].values() if r['contract'].get('bridge_sha256')==bridge]
    assert records and all(r['status']=='computed' for r in records)
    path_hashes={}
    names={'bridge_sha256':'bridges/python/nirs4all_domains/unsupervised.py',
        'binary_sha256':'target/debug/n4domains.exe','library_sha256':'.venv/Lib/site-packages/n4m/lib/n4m.dll',
        'generator_sha256':'scripts/generate_unsupervised_fixtures.py','checkpoint_sha256':'bridges/python/nirs4all_domains/unsupervised_checkpoint.py',
        'adapter_sha256':'bridges/python/nirs4all_domains/paired_x.py','writer_sha256':'scripts/publish_alpha12_results.py'}
    runners={digest(p):p.as_posix() for p in Path('scripts').glob('*alpha12*.py')}
    task_artifacts=defaultdict(dict);phase_cost=defaultdict(float);phase_counts=Counter();receipts=[]
    for record in records:
        contract=record['contract'];phase=contract.get('phase','controlled-mechanisms')
        for key,path in names.items():
            if key in contract:assert digest(path)==contract[key];path_hashes[path]=contract[key]
        if 'runner_sha256' in contract:
            path=runners[contract['runner_sha256']];assert digest(path)==contract['runner_sha256'];path_hashes[path]=contract['runner_sha256']
        artifact=ROOT/'evidence'/record['artifact'];assert digest(artifact)==record['sha256']
        task_artifacts[record['task_id']][record['sha256']]=record['bytes']
        phase_cost[phase]+=record['duration_seconds'];phase_counts[phase]+=1
        receipts.append({'execution_id':record['execution_id'],'task_id':record['task_id'],'phase':phase,
            'sha256':record['sha256'],'bytes':record['bytes'],'contract':contract})
    assert phase_counts['representation-reference']==78 and phase_counts['structural-resampling']==160
    assert phase_counts['structural-resampling-batch']==20 and phase_counts['paired-x-view']==4
    sources={k:v for k,v in path_hashes.items() if not k.startswith(('target/','.venv/'))}
    atomic_json(PUBLIC/'execution-contracts.json',{'records':sorted(receipts,key=lambda r:r['execution_id']),
        'source_hashes':sources,'phase_record_counts':dict(phase_counts),'real_pca_fits':642,'real_hdbscan_attempts':1284,
        'controlled_pca_fits':57,'controlled_hdbscan_attempts':114,'real_supervised_model_fits':0,'target_accessed':False,
        'scientific_source_metadata_at_execution':json.loads((ROOT/'scientific-environment-observed.json').read_text()),
        'scope':'Exact executed source/contracts, not retroactive released-wheel execution. Later local wheel matches these packaged sources.'})
    phases={p.stem:json.loads(p.read_text()) for p in (ROOT/'phases').glob('*.json') if not p.stem.endswith('worker')}
    sentinel=json.loads((ROOT/'sentinel-cost-review.json').read_text())
    resources={'phase_observations':phases,'sentinel_cost_review':sentinel,'stage_callback_seconds':dict(phase_cost),
        'primary_callback_seconds':sum(json.loads(p.read_text())['value']['elapsed_seconds'] for p in (PUBLIC/'profiles').glob('*.json')),
        'scope':'Stage callback durations exclude admission/inventory. Phase wall observations exclude each other; sentinel admission span is not full launch duration.',
        'combined_native_memory_estimate_bytes':1610612736,'estimate_is_os_quota':False,'separate_native_peak_measured':False,
        'source_acquisition_spectral_bytes':0,'real_supervised_model_fits':0}
    atomic_json(PUBLIC/'resources.json',resources)
    policy=json.loads(Path('configs/bank/storage-policy-alpha12.json').read_text())
    task_bytes={t:sum(v.values()) for t,v in task_artifacts.items()}
    # Matrix tables/figure/contracts/resource proofs belong to the P4 publication
    # task in addition to its immutable matrix. Other exported bytes hardlink
    # already counted stages; no source matrix is copied into public evidence.
    auxiliary=['execution-contracts.json','resources.json','structural-matrix.csv','COVERAGE.md','figures/representation-sensitivity.svg','findings.json']
    matrix_receipt=json.loads((ROOT/'matrix-receipt.json').read_text())
    task_bytes[matrix_receipt['task_id']]+=sum((PUBLIC/p).stat().st_size for p in auxiliary if (PUBLIC/p).exists())
    assert max(task_bytes.values())<=policy['evidence_bytes']
    assert journal['reserved_campaign_bytes']<=policy['campaign_bytes']
    assert all(v<=policy['per_task_bytes'] for v in journal['task_reserved_bytes'].values())
    occupied=tree_bytes([Path.cwd()]);assert occupied<policy['workspace_max_bytes']
    volumes={n:{'free_bytes':shutil.disk_usage(n+':/').free} for n in ['C','D']}
    assert all(v['free_bytes']>=policy['reserve_free_bytes'] for v in volumes.values())
    atomic_json('docs/audit/alpha12-storage.json',{'workspace_unique_bytes':occupied,'workspace_ceiling':policy['workspace_max_bytes'],
        'initial_workspace_bytes':13175068062,'cumulative_campaign_reserved_bytes':journal['reserved_campaign_bytes'],
        'policy':policy,'task_essential_bytes':task_bytes,'max_task_essential_bytes':max(task_bytes.values()),'volumes':volumes,
        'new_stage_and_public_unique_bytes':tree_bytes([PUBLIC,ROOT/'evidence']),
        'source_acquisition_spectral_bytes':0,'historical_deleted_bytes':0,'historical_migrated_bytes':0,
        'owner_approval':json.loads((ROOT/'budget-approval.json').read_text()),'scope':'Snapshot after local checks/import; final Git/CI metadata receives another guard.'})
    deps=[]
    locators=json.loads((ROOT/'input-locators.json').read_text())
    for e in frozen['entries']:
        if e['status']=='computed':
            for key,sha in [('matrix','input_csv_sha256'),('metadata','metadata_sha256')]:
                p=Path(locators[e['dataset_id']][key]);assert digest(p)==e[sha]
                deps.append({'content_sha256':e[sha],'bytes':p.stat().st_size,'provider':'Datasets 0.3.11 existing standardized public source cache',
                    'access':'public','local_locator_key':e['dataset_id']+':'+key})
    deps.extend({'content_sha256':f['sha256'],'bytes':f['bytes'],'provider':'Datasets 0.3.11 original litter cache','access':'public','local_locator_key':f['name']} for f in paired['files'])
    artifacts=[{'path':p.relative_to(PUBLIC).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size,'retention':'essential_evidence'} for p in sorted(PUBLIC.rglob('*')) if p.is_file() and p.name!='storage.json']
    manifest={'schema_version':1,'protocol_version':'domains.storage.v0.1','execution_id':fingerprint(sources),'artifacts':artifacts,
        'cache_dependencies':deps,'replay_grade':'reconstructed_from_cache','measured_bytes':sum(a['bytes'] for a in artifacts),'optional_archives':[],
        'limitations':['Exact authorized source caches/providers required for new numerical reconstruction; public evidence contains no X or scores.',
            'Original metadata/controller archives remain separately content-pinned; this is not a complete raw source bundle.']}
    schema_check(manifest,'storage-manifest');atomic_json(PUBLIC/'storage.json',manifest)
    result={'baseline_commit':frozen['baseline'],'rust_tests':35,'python_tests':190,'total_tests':225,'checks':list(latest.values()),
        'all_check_attempts':attempts,'protected_files_verified':371,'original_protected_count':224,
        'wheel':{'sha256':digest(wheel),'bytes':wheel.stat().st_size,'matched_members':matched,'isolated_import_log_sha256':digest(smoke)},
        'executed_source_hashes':sources,'guarded_historical_cache_reuse':json.loads(Path('.audit/alpha11/guarded-model-cache-hit.json').read_text()),
        'storage_ref':'docs/audit/alpha12-storage.json','ci_status':'Pending actual Windows/Ubuntu execution; separate hosted proof required.'}
    atomic_json('docs/audit/alpha12-validation.json',result)
    print(json.dumps({'tests':225,'protected':371,'max_task_evidence_bytes':max(task_bytes.values()),'workspace_bytes':occupied,
        'campaign_reserved_bytes':journal['reserved_campaign_bytes'],'wheel_bytes':wheel.stat().st_size,'contracts_verified':len(receipts)}))


if __name__=='__main__':main()
