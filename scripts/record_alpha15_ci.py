"""Record completed public/synthetic CI jobs; no private inputs or proof upload."""
import argparse
import json
from pathlib import Path
import re
import subprocess

from nirs4all_domains.storage import atomic_json,digest


def gh(*args):return subprocess.run(['gh',*args],check=True,capture_output=True).stdout


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run_id')
    p.add_argument('--out',default='docs/audit/github-ci-alpha15.json');a=p.parse_args()
    repo='dcornet/nirs4all-domains'
    proof=json.loads(gh('run','view',a.run_id,'--repo',repo,'--json','status,conclusion,headSha,url,jobs,createdAt,updatedAt'))
    assert proof['status']=='completed' and proof['conclusion']=='success'
    assert {j['name'] for j in proof['jobs']}=={'audit (windows-latest)','audit (ubuntu-latest)'}
    root=Path('.audit/alpha15/ci')/a.run_id;root.mkdir(parents=True,exist_ok=True)
    for job in proof['jobs']:
        assert job['status']=='completed' and job['conclusion']=='success'
        data=gh('run','view',a.run_id,'--repo',repo,'--job',str(job['databaseId']),'--log')
        path=root/(str(job['databaseId'])+'.log');path.write_bytes(data);text=data.decode('utf-8')
        runs=[{'count':int(n),'seconds':float(t)} for n,t in re.findall(r'Ran (\d+) tests in ([\d.]+)s',text)]
        rust=sum(map(int,re.findall(r'test result: ok\. (\d+) passed',text)))
        assert len(runs)==1 and runs[0]['count']==333 and rust==35
        assert '"protected_repository_files": 471' in text
        assert '"private_taint_registry_checked": false' in text
        assert '"private_verification": "not_accessed_in_portable_verification"' in text
        job.update(actual_python_test_runs=runs,actual_rust_tests=rust,log_sha256=digest(path),
            protected_portable_files_verified=471,public_source_provenance_checked=True,
            real_private_source_data_used=False,private_numerical_verification_claimed=False)
    proof.update(repository=repo,run_id=a.run_id,tests_per_platform=368,
        qualification_scope='Both completed Windows/Ubuntu jobs: actual 333 Python/35 Rust tests, 471 protected repository artifacts and public source/provenance checks. Public/synthetic inputs only; no private keys, maps, source matrices, targets or private numerical verification.')
    atomic_json(a.out,proof)
    print(json.dumps({'source':proof['headSha'],'run_id':a.run_id,'platforms':2,'tests_per_platform':368,'status':'success'}))


if __name__=='__main__':main()
