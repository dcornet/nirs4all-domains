"""Consolidate executed local gates, wheel parity, preservation and unique bytes."""
import json
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

from nirs4all_domains.bank import schema_check
from nirs4all_domains.storage import atomic_json,digest,fingerprint,tree_bytes


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--reuse-import',action='store_true');args=parser.parse_args()
    root=Path('.audit/alpha11');public=Path('docs/benchmarks/alpha11');validation=root/'validation'
    checks=json.loads((validation/'checks.json').read_text());assert len(checks)==18 and all(r['exit_code']==0 for r in checks)
    assert all(digest(validation/(r['check']+'.log'))==r['log_sha256'] for r in checks)
    log=(validation/'python.log').read_text(encoding='utf-8');assert re.search(r'Ran 138 tests in [\d.]+s\s+OK',log)
    rust=sum(sum(map(int,re.findall(r'test result: ok\. (\d+) passed', (validation/(n+'.log')).read_text()))) for n in ['workspace','native'])
    assert rust==35
    wheel,=list((validation/'wheel').glob('*0.1.0a11*.whl'));matched={}
    with ZipFile(wheel) as z:
        for p in Path('bridges/python/nirs4all_domains').glob('*'):
            if p.suffix in ['.py','.json']:
                assert z.read('nirs4all_domains/'+p.name)==p.read_bytes();matched[p.name]=digest(p)
    target=root/'wheel-smoke';smoke=validation/'wheel-smoke.log'
    if args.reuse_import:
        previous=json.loads(Path('docs/audit/alpha11-validation.json').read_text())
        assert previous['wheel']['sha256']==digest(wheel) and previous['wheel']['isolated_import_log_sha256']==digest(smoke)
    else:
        with smoke.open('w',encoding='utf-8') as stream:
            subprocess.run([sys.executable,'-m','pip','install','--no-deps','--target',str(target),str(wheel)],check=True,stdout=stream,stderr=subprocess.STDOUT)
            env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(target.resolve()),str(Path('.audit/alpha10/runtime').resolve())])
            code="import json,pathlib,nirs4all_domains; from nirs4all_domains import adaptive,repeated; from nirs4all.operators.models import FastAOMPLSRidge,FastAOMConfig; p=pathlib.Path(nirs4all_domains.__file__).resolve(); assert 'wheel-smoke' in str(p); assert (p.parent/'adaptive-coverage.v1.schema.json').exists(); print('isolated alpha11 wheel and qualified optional provider import passed')"
            subprocess.run([sys.executable,'-c',code],check=True,env=env,stdout=stream,stderr=subprocess.STDOUT)
    protected=json.loads(Path('docs/audit/alpha11-frozen-output-hashes.json').read_text());assert len(protected)==224
    assert all(Path(p).exists() and digest(p)==h for p,h in protected.items())
    runtime=json.loads((root/'qualified-model-runtime.json').read_text())
    assert all(digest(p)==h for p,h in runtime['scientific_sources'].items())
    assert digest(runtime['executed_runner_archive'])==runtime['executed_runner_sha256']
    sources={p.as_posix():digest(p) for p in [Path('bridges/python/nirs4all_domains/adaptive.py'),Path('bridges/python/nirs4all_domains/repeated.py'),Path('crates/nirs4all-domains/src/x_structure.rs')]}
    journal=json.loads(Path('results/alpha9-perten-keyed/state/journal.json').read_text());policy=json.loads(Path('configs/bank/storage-policy-alpha11.json').read_text())
    before=json.loads((root/'budget-approval.json').read_text())
    source_bytes=sum(f['bytes'] for name in ['crops','litter'] for f in json.loads((root/(name+'-origin.json')).read_text())['files'])
    assert source_bytes==17143168
    # All new compact stage/public evidence together is a conservative bound for
    # any single task. Hardlink identity accounting preserves shared export bytes.
    essential=tree_bytes([public,root/'evidence'])
    assert essential<policy['evidence_bytes']
    occupied=tree_bytes([Path.cwd()]);assert occupied<policy['workspace_max_bytes']
    volumes={name:{'free_bytes':shutil.disk_usage(name+':/').free} for name in ['C','D']}
    assert all(v['free_bytes']>=policy['reserve_free_bytes'] for v in volumes.values())
    assert journal['reserved_campaign_bytes']<=policy['campaign_bytes']
    assert all(v<=policy['per_task_bytes'] for v in journal['task_reserved_bytes'].values())
    storage={'workspace_unique_bytes':occupied,'workspace_ceiling':policy['workspace_max_bytes'],
        'initial_workspace_unique_bytes':12656201578,'workspace_growth_bytes':occupied-12656201578,'source_acquisition_bytes':source_bytes,
        'combined_new_stage_and_portable_essential_unique_bytes':essential,'evidence_cap_per_task':policy['evidence_bytes'],
        'cumulative_campaign_reserved_bytes':journal['reserved_campaign_bytes'],'campaign_cap':policy['campaign_bytes'],
        'per_task_cap':policy['per_task_bytes'],'volumes':volumes,'approval':before,'historical_deleted_bytes':0,'historical_migrated_bytes':0,
        'shared_new_exports':json.loads((root/'new-evidence-sharing.json').read_text()),
        'scope':'Snapshot after local gates and wheel import; tooling/build growth is separate from scientific source bytes.'}
    atomic_json('docs/audit/alpha11-storage.json',storage)
    manifest={'schema_version':1,'protocol_version':'domains.storage.v0.1','execution_id':fingerprint(sources),
        'artifacts':[{'path':p.relative_to(public).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size,'retention':'essential_evidence'} for p in sorted(public.rglob('*')) if p.is_file() and p.name!='storage.json'],
        'cache_dependencies':[{'content_sha256':f['sha256'],'bytes':f['bytes'],'provider':'Datasets 0.3.11 original public source cache','access':'public','local_locator_key':'original:'+f['sha256']} for name in ['crops','litter'] for f in json.loads((root/(name+'-origin.json')).read_text())['files']],
        'replay_grade':'reconstructed_from_cache','measured_bytes':tree_bytes([public]),'optional_archives':[],
        'limitations':['Requires exact source caches, protocols and numerical providers for refitting; compact GitHub evidence contains no full X.',
                       'Source metadata/PDF/controller audit archives remain separately content-pinned in local audit storage; no complete source bundle claim.']}
    schema_check(manifest,'storage-manifest');atomic_json(public/'storage.json',manifest)
    result={'baseline_commit':'ece7788459204b33945c83f054f05353391cbe77','rust_tests':35,'python_tests':138,'total_tests':173,
        'checks':checks,'protected_files_verified':224,'wheel':{'sha256':digest(wheel),'bytes':wheel.stat().st_size,'matched_members':matched,'isolated_import_log_sha256':digest(smoke)},
        'actual_executed_numerical_source_attestation':runtime,'new_source_hashes':sources,
        'source_isolation':json.loads((public/'source-isolation.json').read_text()),
        'guarded_checkpoint_reuse':json.loads((root/'guarded-model-cache-hit.json').read_text()),
        'fresh_replay':json.loads((public/'replay.json').read_text()),'tabpfn_source_audit':json.loads((root/'tabpfn-source-audit.json').read_text()),
        'storage_snapshot_ref':'docs/audit/alpha11-storage.json','ci_status':'Pending actual pushed-source Windows/Ubuntu execution; recorded separately.'}
    atomic_json('docs/audit/alpha11-validation.json',result)
    print(json.dumps({'tests':173,'protected':224,'essential_unique_bytes':essential,'workspace_unique_bytes':occupied,
        'campaign_reserved':journal['reserved_campaign_bytes'],'wheel_bytes':wheel.stat().st_size,'isolated_import':True}))


if __name__=='__main__':main()
