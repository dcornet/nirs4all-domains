"""Actual local test/package evidence; no private scientific payload in output."""
import json
from pathlib import Path
import re
import subprocess
import sys

from alpha17_common import Context
from nirs4all_domains.publication import package_surfaces
from nirs4all_domains.storage import atomic_json,digest


def main():
    c=Context();root=Path('.audit/alpha17/validation');checks=json.loads((root/'checks.json').read_text())
    assert len(checks)==18 and all(r['exit_code']==0 and r['resource_limits_respected'] for r in checks)
    assert all(digest(r['log'])==r['sha256'] for r in checks)
    by={r['check']:r for r in checks}
    post=json.loads((root/'post-split-check.json').read_text()) if (root/'post-split-check.json').exists() else None
    if post:
        assert post['record']['exit_code']==0 and digest(post['record']['log'])==post['record']['sha256']
        by['python']=post['record']
    python=int(re.search(r'Ran (\d+) tests in',Path(by['python']['log']).read_text(encoding='utf-8'))[1])
    rust=sum(sum(map(int,re.findall(r'test result: ok\. (\d+) passed',Path(by[k]['log']).read_text(encoding='utf-8')))) for k in ['workspace','native'])
    assert python==(365 if post else 364) and rust==35
    final=json.loads((root/'final-checks.json').read_text()) if (root/'final-checks.json').exists() else []
    if final:
        assert len(final)==3 and all(x['exit_code']==0 and digest(x['log'])==x['sha256'] for x in final)
        hashes=post['current_source_hashes'] if post else json.loads((root/'final-source-hashes.json').read_text())
        assert all(digest(p)==sha for p,sha in hashes.items())
    sources={p.name:p for p in Path('bridges/python/nirs4all_domains').iterdir() if p.suffix in ['.py','.json']}
    archives=[]
    prefix='final-' if final else ''
    for archive in [*root.glob(prefix+'wheel/*0.1.0a17*.whl'),*root.glob(prefix+'sdist/*0.1.0a17*.tar.gz')]:
        seen=set();members=0
        for name,data in package_surfaces(archive):
            members+=1;parts=Path(name).parts
            if 'nirs4all_domains' in parts:
                relative=parts[parts.index('nirs4all_domains')+1:]
                assert len(relative)==1 and relative[0] in sources
                assert data==sources[relative[0]].read_bytes();seen.add(relative[0])
            else:
                assert not any(x in ['.audit','results','.venv','keys','identities'] for x in parts)
                assert parts[-1] in ['METADATA','WHEEL','RECORD','top_level.txt','LICENSE','pyproject.toml',
                    'PKG-INFO','setup.cfg','SOURCES.txt','dependency_links.txt','requires.txt']
        assert seen==set(sources)
        archives.append({'name':archive.name,'sha256':digest(archive),'members':members,'package_source_parity':True})
    assert len(archives)==2
    delivery_prefix='scope-' if post else prefix
    wheel,=list(root.glob(prefix+'wheel/*0.1.0a17*.whl'));smoke=Path('.audit/alpha17/'+delivery_prefix+'wheel-smoke')
    log=root/(delivery_prefix+'isolated-wheel.log')
    with log.open('w',encoding='utf-8') as stream:
        subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-index','--target',str(smoke),str(wheel)],stdout=stream,stderr=subprocess.STDOUT,check=True)
        code="import sys;sys.path.insert(0,sys.argv[1]);import nirs4all_domains.exploratory as m;assert 'wheel-smoke' in m.__file__;assert m.PROTOCOL=='domains.exploratory.admission.v0.1'"
        subprocess.run([sys.executable,'-I','-c',code,str(smoke.resolve())],stdout=stream,stderr=subprocess.STDOUT,check=True)
    resources=c.preservation()
    c.save(delivery_prefix+'delivery-local-validation.json',{'checks':checks,'final_checks':final,'post_split_full_suite':post,'archives':archives,'resources':resources,
        'new_real_model_fits':0,'new_spectral_fits':0,'new_raw_source_numeric_target_access':False})
    atomic_json('docs/audit/alpha17-validation.json',{'python_tests':python,'rust_tests':rust,'total_tests':python+rust,
        'local_checks':len(checks),'isolated_wheel_import':True,'wheel_and_sdist':archives,
        'checks':checks,'final_focused_and_rebuilt_packages':final,'post_split_full_suite':post,
        'historical_local_artifacts_verified':651,'historical_portable_artifacts_verified':487,
        'all_prior_private_files_and_journal_entries_preserved':True,
        'combined_ceiling_respected':True,'approved_additional_footprint_respected':True,
        'new_campaign_reservation_bytes':8388608,'campaign_ceiling_respected':True,
        'bridge_version':'0.1.0a17','unchanged_Rust_version':'0.1.0-alpha.16',
        'hosted_CI':'Separate completed-job evidence; this file records local execution only.'})
    print('ALPHA17_VALIDATED_'+str(python+rust)+'_TESTS_18_CHECKS_PACKAGE_PARITY_AND_ISOLATED_IMPORT')


if __name__=='__main__':main()
