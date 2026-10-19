"""Record real completed Windows/Ubuntu CI, optionally requiring current HEAD."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from nirs4all_domains.storage import atomic_json,digest


def gh(*args):return subprocess.run(['gh',*args],check=True,capture_output=True).stdout


def main():
    p=argparse.ArgumentParser();p.add_argument('run_id');p.add_argument('--out',default='docs/audit/github-ci-alpha18.json');p.add_argument('--require-head',action='store_true');a=p.parse_args()
    repo='dcornet/nirs4all-domains';proof=json.loads(gh('run','view',a.run_id,'--repo',repo,'--json','status,conclusion,headSha,url,jobs,createdAt,updatedAt'))
    assert proof['status']=='completed' and proof['conclusion']=='success'
    if a.require_head:assert proof['headSha']==subprocess.check_output(['git','rev-parse','HEAD']).decode().strip()
    assert {j['name'] for j in proof['jobs']}=={'audit (windows-latest)','audit (ubuntu-latest)'}
    root=Path('.audit/alpha18/ci')/a.run_id;root.mkdir(parents=True,exist_ok=True)
    for job in proof['jobs']:
        assert job['status']=='completed' and job['conclusion']=='success'
        data=gh('run','view',a.run_id,'--repo',repo,'--job',str(job['databaseId']),'--log');path=root/(str(job['databaseId'])+'.log');path.write_bytes(data);text=data.decode('utf-8')
        runs=[int(n) for n in re.findall(r'Ran (\d+) tests in',text)]
        rust=sum(map(int,re.findall(r'test result: ok\. (\d+) passed',text)))
        assert runs==[372] and rust==35
        assert '"protected_repository_files": 487' in text
        assert 'ALPHA18_FULL_BANK_ACCOUNTING_STATES_AND_ALIGNMENT_VERIFIED' in text
        job.update(actual_python_tests=372,actual_rust_tests=35,log_sha256=digest(path),protected_portable_files_verified=487,private_source_inputs_used=False)
    proof.update(repository=repo,run_id=a.run_id,tests_per_platform=407,
        scope='Completed public/synthetic Windows/Ubuntu jobs; no private matrices, keys, rosters or local OOF.')
    atomic_json(a.out,proof);print(json.dumps({'head':proof['headSha'],'url':proof['url'],'tests_per_platform':407,'platforms':2,'status':'success'}))

if __name__=='__main__':main()
