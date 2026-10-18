"""Completed hosted jobs, actual test logs and portable scientific checks."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from nirs4all_domains.storage import atomic_json,digest

def gh(*args):return subprocess.run(['gh',*args],check=True,capture_output=True).stdout

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run_id');p.add_argument('--out',default='docs/audit/github-ci-alpha13.json');args=p.parse_args()
    repo='dcornet/nirs4all-domains';proof=json.loads(gh('run','view',args.run_id,'--repo',repo,'--json','status,conclusion,headSha,url,jobs,createdAt,updatedAt'))
    assert proof['status']=='completed' and proof['conclusion']=='success'
    assert {j['name'] for j in proof['jobs']}=={'audit (windows-latest)','audit (ubuntu-latest)'}
    root=Path('.audit/alpha13/ci')/args.run_id;root.mkdir(parents=True,exist_ok=True)
    for job in proof['jobs']:
        assert job['status']=='completed' and job['conclusion']=='success'
        data=gh('run','view',args.run_id,'--repo',repo,'--job',str(job['databaseId']),'--log');log=root/(str(job['databaseId'])+'.log');log.write_bytes(data);text=data.decode('utf-8')
        runs=[{'count':int(a),'seconds':float(b)} for a,b in re.findall(r'Ran (\d+) tests in ([\d.]+)s',text)]
        rust=sum(map(int,re.findall(r'test result: ok\. (\d+) passed',text)))
        assert len(runs)==1 and runs[0]['count']==244 and rust==35
        assert '"scientific_evidence_complete": true' in text and '"historical_repository_files": 347' in text
        job.update(actual_python_test_runs=runs,actual_rust_tests=rust,log_sha256=digest(log),protected_portable_files_verified=347,portable_scientific_manifest_verified=True)
    proof.update(repository=repo,run_id=args.run_id,tests_per_platform=279,
        qualification_scope='Both completed platform jobs: actual 244 Python/35 Rust tests, scientific manifests, 347 historical repository artifacts; no real-bank reacquisition or TabPFN fitting.')
    atomic_json(args.out,proof);print(json.dumps({'source':proof['headSha'],'run_id':args.run_id,'platforms':2,'tests_per_platform':279,'status':'success'}))

if __name__=='__main__':main()
