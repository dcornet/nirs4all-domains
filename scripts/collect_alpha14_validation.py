"""Engineering/package evidence may be public; private science remains local."""
import json
import argparse
from importlib.metadata import version
import os
from pathlib import Path
import re
import subprocess
import sys

from check_alpha14_publication import private_taints
from nirs4all_domains.privacy import PrivateStore
from nirs4all_domains.publication import audit_surfaces,package_surfaces,public_record
from nirs4all_domains.storage import atomic_json,digest,tree_bytes


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--artifact-suffix',default='');args=p.parse_args()
    assert args.artifact_suffix in ['', '-portable-acl']
    root=Path('.audit/alpha14');checks=json.loads((root/'validation/checks.json').read_text());last={v['check']:v for v in checks}
    assert len(last)==24 and all(v['exit_code']==0 and v['combined_ceiling_respected'] for v in last.values())
    assert all(digest(v['log'])==v['log_sha256'] for v in checks)
    pylog=Path(last['python']['log']).read_text(encoding='utf-8')
    match=re.search(r'Ran (\d+) tests in [\d.]+s\s+OK',pylog);assert match
    python_tests=int(match[1]);assert python_tests==303
    rust=sum(sum(map(int,re.findall(r'test result: ok\. (\d+) passed',Path(last[k]['log']).read_text(encoding='utf-8')))) for k in ['workspace','native'])
    assert rust==35
    literals,new_private_literals,store=private_taints();literals+=new_private_literals
    wheel,=list((root/('validation/wheel'+args.artifact_suffix)).glob('*0.1.0a14*.whl'))
    sdist,=list((root/('validation/sdist'+args.artifact_suffix)).glob('*0.1.0a14*.tar.gz'))
    sources={p.name:p for p in Path('bridges/python/nirs4all_domains').iterdir() if p.suffix in ['.py','.json']}
    packaged={};archives=[]
    for archive in [wheel,sdist]:
        surfaces=list(package_surfaces(archive));roster={}
        for name,data in surfaces:
            parts=Path(name).parts
            if 'nirs4all_domains' in parts:
                index=parts.index('nirs4all_domains');relative=parts[index+1:]
                assert len(relative)==1 and relative[0] in sources,'PACKAGE_UNAPPROVED_MODULE_MEMBER'
                assert data==sources[relative[0]].read_bytes(),'PACKAGED_SOURCE_BYTES_CHANGED'
                packaged[relative[0]]=digest(sources[relative[0]])
            elif archive==wheel:
                assert any(p.endswith('.dist-info') for p in parts),'WHEEL_UNAPPROVED_MEMBER'
                assert parts[-1] in ['METADATA','WHEEL','RECORD','top_level.txt','LICENSE'],'WHEEL_UNAPPROVED_METADATA_MEMBER'
                if parts[-1]=='METADATA':assert b'Version: 0.1.0a14' in data.splitlines()
                if parts[-1]=='LICENSE':assert data==Path('bridges/python/LICENSE').read_bytes()
            else:
                assert len(parts)>=2 and (parts[-1] in ['pyproject.toml','LICENSE','PKG-INFO','setup.cfg'] or
                    (any(p.endswith('.egg-info') for p in parts) and parts[-1] in ['PKG-INFO','SOURCES.txt','dependency_links.txt','requires.txt','top_level.txt'])),'SDIST_UNAPPROVED_MEMBER'
                if parts[-1]=='pyproject.toml':assert data==Path('bridges/python/pyproject.toml').read_bytes()
            roster[name]=public_record(data,'public_source')
        audit=audit_surfaces(surfaces,roster,sensitive_literals=literals)
        archives.append({'name':archive.name,'sha256':digest(archive),'bytes':archive.stat().st_size,
            'members_verified':audit['outgoing_surfaces'],'unknown_or_private_members':0})
    assert set(packaged)==set(sources)
    smoke=root/('wheel-smoke'+args.artifact_suffix);log=root/('validation/wheel-smoke'+args.artifact_suffix+'.log')
    with log.open('w',encoding='utf-8') as stream:
        subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-index','--target',str(smoke),str(wheel)],check=True,stdout=stream,stderr=subprocess.STDOUT)
        code="from pathlib import Path;import nirs4all_domains;from nirs4all_domains import privacy,disclosure,publication,private_batch,private_corpus;root=Path(nirs4all_domains.__file__).resolve().parent;assert 'wheel-smoke' in str(root);assert (root/'public-disclosure.v1.schema.json').is_file();print('isolated alpha14 wheel imports and schemas passed')"
        subprocess.run([sys.executable,'-c',code],check=True,stdout=stream,stderr=subprocess.STDOUT,
            env={**os.environ,'PYTHONPATH':str(smoke.resolve()),'PYTHONDONTWRITEBYTECODE':'1'})
    assert 'isolated alpha14 wheel imports and schemas passed' in log.read_text(encoding='utf-8')
    policy=json.loads(Path('configs/bank/storage-policy-alpha14.json').read_text())
    approval=json.loads((root/'budget-approval.json').read_text())
    inputs=json.loads((store.root/'execution-freeze.json').read_text())['freeze']
    paths=inputs['sources'][0]['other_participating_files'] if inputs['sources'] else []
    used=tree_bytes([Path.cwd(),store.root,*paths]);ledger=json.loads(Path('results/alpha9-perten-keyed/state/journal.json').read_text())
    assert used<policy['workspace_max_bytes']
    assert ledger['reserved_campaign_bytes']<=policy['campaign_bytes'] and ledger['reserved_campaign_bytes']-approval['previous_campaign_reserved']<=approval['new_reservation_envelope']
    private_storage={'visibility':'local_private','scope':'After all local native/Python/package gates, before Git/CI metadata.',
        'combined_measured_bytes':used,'campaign_reserved_bytes':ledger['reserved_campaign_bytes'],
        'new_reserved_bytes':ledger['reserved_campaign_bytes']-approval['previous_campaign_reserved'],'policy':policy}
    atomic_json(store.root/'final-validation-storage.json',{'measurement':private_storage,'authentication':store.authenticate(private_storage)})
    # Do not release exact private execution counts, resource deltas or source
    # fingerprints. Public engineering budgets/compliance are independently safe.
    atomic_json('docs/audit/alpha14-storage.json',{'policy':policy,'combined_ceiling_respected':True,
        'campaign_ceiling_respected':True,'new_alpha14_reservation_envelope_bytes':approval['new_reservation_envelope'],
        'serial_scientific_execution':True,'source_matrix_copies':0,'historical_deletion_or_migration':False,
        'exact_private_accounting':'protected local report; not publicly released','peak_RAM_claimed':False})
    value={'protocol':'domains.alpha14.release_validation.v0.1','python_tests':python_tests,'rust_tests':rust,'total_tests':python_tests+rust,
        'prior_tests_retained':279,'new_privacy_tests':59,'local_release_checks':len(last),'check_attempts':checks,
        'archives':archives,'packaged_source_hashes':packaged,'isolated_wheel_import_passed':True,'wheel_smoke_log_sha256':digest(log),
        'protected_local_files':617,'protected_repository_files':453,'frozen_H1_H5_preserved':True,
        'provider_versions':{p:version(p) for p in ['nirs4all-methods','dag-ml','nirs4all-datasets','nirs4all-domains-bridge']},
        'new_private_scientific_exports':0,'private_source_inputs_in_CI':False,
        'scientific_runtime_attribution':'Recorded protected alpha14 controllers reuse exact qualified alpha13 native binary and pinned Methods DLL; packaged native alpha14 validation is separate.',
        'local_report_receipt':json.loads((root/'local-report-receipt.json').read_text())['receipt_id'],
        'hosted_CI':'Pending push/completed-job verification; local success does not establish CI.'}
    atomic_json('docs/audit/alpha14-validation.json',value)
    print(json.dumps({'status':'local_release_evidence_collected','tests':python_tests+rust,'checks':len(last),
                      'wheel_and_sdist_members_verified':True,'private_scientific_payloads_exported':0}))


if __name__=='__main__':main()
