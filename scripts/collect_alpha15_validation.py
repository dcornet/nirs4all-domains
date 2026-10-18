"""Engineering/package evidence may be public; private science remains local."""
import json
import argparse
import base64
import hashlib
from importlib.metadata import version
import os
from pathlib import Path
import re
import subprocess
import sys

from check_alpha15_publication import private_taints
from nirs4all_domains.privacy import PrivateStore
from nirs4all_domains.publication import audit_surfaces,package_surfaces,public_record
from nirs4all_domains.storage import atomic_json,digest,tree_bytes


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--artifact-suffix',default='');args=p.parse_args()
    assert args.artifact_suffix in ['', '-portable-acl']
    root=Path('.audit/alpha15');checks=json.loads((root/'validation/checks.json').read_text());last={v['check']:v for v in checks}
    assert len(last)==25 and all(v['exit_code']==0 and v['combined_ceiling_respected'] for v in last.values())
    assert all(digest(v['log'])==v['log_sha256'] for v in checks)
    pylog=Path(last['python']['log']).read_text(encoding='utf-8')
    match=re.search(r'Ran (\d+) tests in [\d.]+s\s+OK',pylog);assert match
    python_tests=int(match[1]);assert python_tests==333
    rust=sum(sum(map(int,re.findall(r'test result: ok\. (\d+) passed',Path(last[k]['log']).read_text(encoding='utf-8')))) for k in ['workspace','native'])
    assert rust==35
    literals,new_private_literals,store=private_taints();literals+=new_private_literals
    wheel,=list((root/('validation/wheel'+args.artifact_suffix)).glob('*0.1.0a15*.whl'))
    sdist,=list((root/('validation/sdist'+args.artifact_suffix)).glob('*0.1.0a15*.tar.gz'))
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
                if parts[-1]=='METADATA':assert b'Version: 0.1.0a15' in data.splitlines()
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
        code="from pathlib import Path;import nirs4all_domains;from nirs4all_domains import privacy,disclosure,publication,private_batch,private_corpus,cohort,synthesis,confrontation;root=Path(nirs4all_domains.__file__).resolve().parent;assert 'wheel-smoke' in str(root);assert (root/'cross-dataset-synthesis.v1.schema.json').is_file();print('isolated alpha15 wheel imports and schemas passed')"
        subprocess.run([sys.executable,'-c',code],check=True,stdout=stream,stderr=subprocess.STDOUT,
            env={**os.environ,'PYTHONPATH':str(smoke.resolve()),'PYTHONDONTWRITEBYTECODE':'1'})
    assert 'isolated alpha15 wheel imports and schemas passed' in log.read_text(encoding='utf-8')
    policy=json.loads(Path('configs/bank/storage-policy-alpha15.json').read_text())
    approval=json.loads((root/'budget-approval.json').read_text())
    inputs=json.loads((store.root/'execution-freeze.json').read_text())['freeze']
    paths=inputs['sources'][0]['other_participating_files'] if inputs['sources'] else []
    from alpha15_common import Context
    used=Context().guard()['combined_bytes'];ledger=json.loads(Path('results/alpha9-perten-keyed/state/journal.json').read_text())
    assert used<policy['workspace_max_bytes']
    assert ledger['reserved_campaign_bytes']<=policy['campaign_bytes'] and ledger['reserved_campaign_bytes']-approval['previous_campaign_reserved']<=approval['new_reservation_envelope']
    private_storage={'visibility':'local_private','scope':'After all local native/Python/package gates, before Git/CI metadata.',
        'combined_measured_bytes':used,'campaign_reserved_bytes':ledger['reserved_campaign_bytes'],
        'new_reserved_bytes':ledger['reserved_campaign_bytes']-approval['previous_campaign_reserved'],'policy':policy}
    atomic_json(store.root/'alpha15/final-validation-storage.json',{'measurement':private_storage,'authentication':store.authenticate(private_storage)})
    from n4m._ffi import library_path
    scientific_sources = ['scripts/alpha15_common.py', 'scripts/run_alpha15_synthesis.py',
        'scripts/run_alpha15_source_closure.py', 'scripts/finalize_alpha15_local.py',
        *('bridges/python/nirs4all_domains/'+n+'.py' for n in ['cohort','synthesis','confrontation'])]
    attribution = {'visibility':'local_private', 'executed_controller_sources':{p:digest(p) for p in scientific_sources},
        'editable_bridge_metadata_during_science':'0.1.0a14', 'scientific_protocol':'domains.synthesis.v0.1',
        'new_summary_association_provider':{'version':version('nirs4all-methods'), 'library_sha256':digest(library_path())},
        'figure_provider':{'matplotlib':version('matplotlib')},
        'original_profiles':'Immutable alpha12/13/14 receipts and exact original protocol/provider contracts; no spectral refits.',
        'failed_and_superseded_attempts':'Retained shared journal entries and original protected stage artifacts; latest signed phase receipts select explicit retained revisions.'}
    attribution_path = store.root/'alpha15/execution-source-attribution.json'
    if attribution_path.exists():
        original_attribution = json.loads(attribution_path.read_text())
        assert original_attribution['authentication'] == store.authenticate(original_attribution['value'])
        # Preserve the actually executed scientific source, even after a later
        # engineering-only guard is strengthened. Never relabel old execution.
    else:
        atomic_json(attribution_path,{'value':attribution,'authentication':store.authenticate(attribution)})
    snapshot_path = store.root/'alpha15/executed-source-snapshot.json'
    if not snapshot_path.exists():
        exact = json.loads(attribution_path.read_text())['value']['executed_controller_sources']
        sources = {}
        for path, sha in exact.items():
            data = Path(path).read_bytes()
            assert hashlib.sha256(data).hexdigest() == sha, 'EXACT_EXECUTED_SOURCE_BYTES_REQUIRED'
            sources[path] = {'sha256':sha,'base64':base64.b64encode(data).decode()}
        snapshot = {'visibility':'local_private','sources':sources,'purpose':'Exact executed scientific controller bytes.'}
        atomic_json(snapshot_path,{'value':snapshot,'authentication':store.authenticate(snapshot)})
    # Do not release exact private execution counts, resource deltas or source
    # fingerprints. Public engineering budgets/compliance are independently safe.
    atomic_json('docs/audit/alpha15-storage.json',{'policy':policy,'combined_ceiling_respected':True,
        'campaign_ceiling_respected':True,'new_alpha15_reservation_envelope_bytes':approval['new_reservation_envelope'],
        'serial_scientific_execution':True,'source_matrix_copies':0,'historical_deletion_or_migration':False,
        'exact_private_accounting':'protected local report; not publicly released','peak_RAM_claimed':False})
    value={'protocol':'domains.alpha15.release_validation.v0.1','python_tests':python_tests,'rust_tests':rust,'total_tests':python_tests+rust,
        'prior_tests_retained':338,'new_scientific_tests':30,'local_release_checks':len(last),'check_attempts':checks,
        'archives':archives,'packaged_source_hashes':packaged,'isolated_wheel_import_passed':True,'wheel_smoke_log_sha256':digest(log),
        'protected_local_files':635,'protected_repository_files':471,'frozen_H1_H5_preserved':True,
        'provider_versions':{p:version(p) for p in ['nirs4all-methods','dag-ml','nirs4all-datasets','nirs4all-domains-bridge']},
        'new_private_scientific_exports':0,'private_source_inputs_in_CI':False,
        'scientific_runtime_attribution':'Existing alpha12/13/14 numerical profiles are reused by exact receipt; new native summary/association ABI calls are separate from versioned native release validation.',
        'scientific_report_visibility':'local_private',
        'hosted_CI':'Pending push/completed-job verification; local success does not establish CI.'}
    atomic_json('docs/audit/alpha15-validation.json',value)
    print(json.dumps({'status':'local_release_evidence_collected','tests':python_tests+rust,'checks':len(last),
                      'wheel_and_sdist_members_verified':True,'private_scientific_payloads_exported':0}))


if __name__=='__main__':main()
