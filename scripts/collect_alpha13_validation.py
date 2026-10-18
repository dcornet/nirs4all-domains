"""Executed gates, isolated wheel parity and final bounded source/storage evidence."""
import json
from importlib.metadata import version
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile
from alpha13_common import ROOT,PUBLIC,STATE,policy
from check_alpha13_results import check
from nirs4all_domains.storage import atomic_json,digest,tree_bytes


def main():
    checks=json.loads((ROOT/'validation/checks.json').read_text());latest={v['check']:v for v in checks}
    assert len(latest)==19 and all(v['exit_code']==0 for v in latest.values())
    assert all(digest(v['log'])==v['log_sha256'] for v in checks)
    python_log=Path(latest['python']['log']).read_text(encoding='utf-8');assert re.search(r'Ran 244 tests in [\d.]+s\s+OK',python_log)
    rust=sum(sum(map(int,re.findall(r'test result: ok\. (\d+) passed',Path(latest[k]['log']).read_text(encoding='utf-8')))) for k in ['workspace','native']);assert rust==35
    wheel,=list((ROOT/'validation/wheel').glob('*0.1.0a13*.whl'));matched={}
    with ZipFile(wheel) as archive:
        for path in Path('bridges/python/nirs4all_domains').glob('*'):
            if path.suffix in ['.py','.json']:
                assert archive.read('nirs4all_domains/'+path.name)==path.read_bytes();matched[path.name]=digest(path)
    smoke=ROOT/'wheel-smoke';log=ROOT/'validation/wheel-smoke.log'
    if not smoke.exists():
        with log.open('w',encoding='utf-8') as out:
            subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-index','--target',str(smoke),str(wheel)],check=True,stdout=out,stderr=subprocess.STDOUT)
            env=os.environ.copy();env.update(PYTHONPATH=str(smoke.resolve()),PYTHONDONTWRITEBYTECODE='1')
            code="from pathlib import Path;import nirs4all_domains;from nirs4all_domains import stability_power,power_checkpoint,native_profile_stream,falsification,x_admission,keyed_source_x;root=Path(nirs4all_domains.__file__).resolve().parent;assert 'wheel-smoke' in str(root);assert (root/'x-source-admission.v1.schema.json').is_file();print('isolated alpha13 wheel imports and schemas passed')"
            subprocess.run([sys.executable,'-c',code],env=env,check=True,stdout=out,stderr=subprocess.STDOUT)
    assert 'isolated alpha13 wheel imports and schemas passed' in log.read_text(encoding='utf-8')
    executed=json.loads((PUBLIC/'execution-contracts.json').read_text())
    for sha,path in executed['source_bindings'].items():assert digest(path)==sha,('EXECUTED_SOURCE_PARITY_CHANGED',path)
    integrity=check(True);assert integrity['scientific_evidence_complete']
    journal=json.loads((STATE/'journal.json').read_text());limits=policy();local=json.loads((ROOT/'input-locators.json').read_text());paths=[Path(v['matrix']) for v in local.values()]
    used=tree_bytes([Path.cwd()]);combined=tree_bytes([Path.cwd(),*paths]);assert combined<limits['workspace_max_bytes']
    assert journal['reserved_campaign_bytes']<=limits['campaign_bytes'] and journal['reserved_campaign_bytes']-427393916<=96*1024*1024
    task_bytes={}
    for record in journal['runs'].values():
        if record['status']=='computed' and (ROOT/'evidence'/record['artifact']).is_file():
            task_bytes[record['task_id']]=task_bytes.get(record['task_id'],0)+record['bytes']
    assert max(task_bytes.values())<=limits['evidence_bytes'] and max(journal['task_reserved_bytes'].values())<=limits['per_task_bytes']
    storage={'measurement_scope':'After full local validation and isolated wheel import, before Git publication. Final Git/CI metadata gets another guard.',
        'workspace_unique_bytes':used,'workspace_plus_selected_existing_x_bytes':combined,'policy':limits,
        'campaign_reserved_bytes':journal['reserved_campaign_bytes'],'alpha13_additional_reserved_bytes':journal['reserved_campaign_bytes']-427393916,
        'maximum_new_task_persistent_evidence_bytes':max(task_bytes.values()),'C_free_bytes':shutil.disk_usage('C:/').free,'D_free_bytes':shutil.disk_usage('D:/').free,
        'source_matrix_copies_per_draw':0,'historical_files_deleted_or_migrated':False,'upstream_modified':False}
    atomic_json('docs/audit/alpha13-storage.json',storage)
    value={'protocol':'domains.alpha13.release_validation.v0.1','rust_tests':rust,'python_tests':244,'total_tests':rust+244,
        'baseline_tests_retained':225,'release_checks_passed':19,'check_attempts':checks,'scientific_integrity':integrity,
        'provider_versions':{p:version(p) for p in ['nirs4all-methods','dag-ml','nirs4all-datasets','nirs4all-domains-bridge']},
        'wheel':{'name':wheel.name,'sha256':digest(wheel),'bytes':wheel.stat().st_size,'packaged_source_hashes':matched,
            'isolated_import_passed':True,'isolated_import_log_sha256':digest(log)},
        'executed_source_bindings_verified':executed['source_bindings'],'executed_stream_binary_sha256':digest(ROOT/'executed-alpha13-cli.exe'),
        'original_executed_alpha12_binary_sha256':digest(ROOT/'executed-alpha12-cli.exe'),
        'native_library_sha256':digest('.venv/Lib/site-packages/n4m/lib/n4m.dll'),
        'scientific_metadata_at_execution':'Editable alpha12 metadata with exact alpha13 source files; subsequent wheel parity is not retroactive wheel execution.',
        'hosted_ci':'Pending push and completed-job evidence; local success does not assert hosted CI.'}
    atomic_json('docs/audit/alpha13-validation.json',value)
    print(json.dumps({'tests':rust+244,'checks':19,'wheel_bytes':wheel.stat().st_size,'source_files_matched':len(matched),'workspace_plus_cached_x':combined,'ceiling':limits['workspace_max_bytes']}))


if __name__=='__main__':main()
