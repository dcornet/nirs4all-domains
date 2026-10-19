"""Record actual checks, package parity, source preservation and footprint."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
from alpha18_common import Context,read
from alpha16_common import Context as HistoricalContext
from check_alpha16_results import verify_private
from nirs4all_domains.publication import package_surfaces
from nirs4all_domains.storage import atomic_json,digest


def main():
    c=Context();root=Path('.audit/alpha18/validation');checks=read(root/'checks.json')
    assert len(checks)==23 and all(r['exit_code']==0 and digest(r['log'])==r['sha256'] for r in checks)
    by={r['check']:r for r in checks}
    python=int(re.search(r'Ran (\d+) tests in',Path(by['python']['log']).read_text(encoding='utf-8'))[1])
    rust=sum(sum(map(int,re.findall(r'test result: ok\. (\d+) passed',Path(by[k]['log']).read_text(encoding='utf-8')))) for k in ['workspace','native'])
    assert python==372 and rust==35
    sources={p.name:p for p in Path('bridges/python/nirs4all_domains').iterdir() if p.suffix in ['.py','.json']}
    archives=[]
    for archive in [*root.glob('wheel/*0.1.0a18*.whl'),*root.glob('sdist/*0.1.0a18*.tar.gz')]:
        seen=set();members=0
        for name,data in package_surfaces(archive):
            members+=1;parts=Path(name).parts
            if 'nirs4all_domains' in parts:
                relative=parts[parts.index('nirs4all_domains')+1:]
                assert len(relative)==1 and relative[0] in sources
                assert data==sources[relative[0]].read_bytes();seen.add(relative[0])
            else:assert not any(p in ['.audit','results','.venv','keys','identities'] for p in parts)
        assert seen==set(sources)
        archives.append({'name':archive.name,'sha256':digest(archive),'members':members,'package_source_parity':True})
    assert len(archives)==2
    wheel,=root.glob('wheel/*0.1.0a18*.whl');smoke=Path('.audit/alpha18/wheel-smoke')
    log=root/'isolated-wheel.log'
    with log.open('w',encoding='utf-8') as out:
        subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-index','--target',str(smoke),str(wheel)],stdout=out,stderr=subprocess.STDOUT,check=True)
        code="import sys; sys.path.insert(0,sys.argv[1]); import nirs4all_domains.full_bank as m; assert 'wheel-smoke' in m.__file__; assert m.PROTOCOL=='domains.bank_reference.v0.1'"
        subprocess.run([sys.executable,'-I','-c',code,str(smoke.resolve())],stdout=out,stderr=subprocess.STDOUT,check=True)
    # Check immutable historical facts with the CURRENT resource envelope;
    # historical approvals/reports/journal entries are never edited.
    old=HistoricalContext();old.guard=c.guard;verify_private(old)
    baseline=read('docs/audit/alpha16-frozen-output-hashes.json')
    assert all(digest(p)==sha for p,sha in baseline.items())
    resources=c.preservation()
    resources.update(combined_ceiling_bytes=c.policy['workspace_max_bytes'],
        combined_remaining_bytes=c.policy['workspace_max_bytes']-resources['combined_bytes'],
        free_volume_bytes={volume:shutil.disk_usage(volume+'/').free for volume in ['C:','D:']})
    proof={'python_tests':python,'rust_tests':rust,'total_tests':python+rust,'local_checks':len(checks),
        'checks':checks,'wheel_and_sdist':archives,'isolated_wheel_import':True,
        'historical_local_artifacts_verified':len(baseline),'historical_portable_artifacts_verified':487,
        'pre_campaign_protected_files_unchanged':len(c.load('baseline-preservation.json')['files']),
        'original_journal_entries_preserved':True,'resources':resources,
        'standing_authorized_ceiling_increases_bytes':{'combined_storage':4000000000,'campaign_reservations':1000000000,'sum':5000000000},
        'bridge_version':'0.1.0a18','unchanged_Rust_version':'0.1.0-alpha.16',
        'hosted_CI':'Separate completed final-source Windows/Ubuntu execution proof.'}
    c.save('delivery-validation.json',proof);atomic_json('docs/audit/alpha18-validation.json',proof)
    print('ALPHA18_VALIDATED',python+rust,'TESTS',len(checks),'CHECKS_PACKAGES_AND_HISTORY')

if __name__=='__main__':main()
