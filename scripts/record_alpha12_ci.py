"""Record only completed hosted jobs and their actual numerical test logs."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from nirs4all_domains.storage import atomic_json,digest


def gh(*args):
    return subprocess.run(['gh',*args],check=True,capture_output=True).stdout


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('run_id',type=int)
    parser.add_argument('--out',type=Path,default=Path('docs/audit/github-ci-alpha12.json'));args=parser.parse_args()
    repo='dcornet/nirs4all-domains'
    proof=json.loads(gh('run','view',str(args.run_id),'--repo',repo,'--json','status,conclusion,headSha,url,jobs,createdAt,updatedAt'))
    assert proof['status']=='completed' and proof['conclusion']=='success'
    assert {j['name'] for j in proof['jobs']}=={'audit (windows-latest)','audit (ubuntu-latest)'}
    folder=Path('.audit/alpha12/ci')/str(args.run_id);folder.mkdir(parents=True,exist_ok=True)
    for job in proof['jobs']:
        assert job['status']=='completed' and job['conclusion']=='success'
        raw=gh('run','view',str(args.run_id),'--repo',repo,'--job',str(job['databaseId']),'--log')
        log=folder/(str(job['databaseId'])+'.log');log.write_bytes(raw);data=raw.decode('utf-8')
        runs=[{'count':int(a),'seconds':float(b)} for a,b in re.findall(r'Ran (\d+) tests in ([\d.]+)s',data)]
        rust=sum(map(int,re.findall(r'test result: ok\. (\d+) passed',data)))
        assert len(runs)==1 and runs[0]['count']==190 and rust==35
        assert '"protected_present_verified": 207' in data and '"manifest_verified": true' in data
        job.update(actual_python_test_runs=runs,actual_rust_tests=rust,log_sha256=digest(log),
            portable_manifest_and_executed_source_verified=True,protected_portable_files_verified=207)
    proof.update(repository=repo,run_id=args.run_id,
        proof='Both completed platform jobs/steps and actual 190-Python/35-Rust-test logs; portable manifest, executed sources and 207 historical repository files checked. No real spectral acquisition or TabPFN fitting in CI.')
    atomic_json(args.out,proof);print(json.dumps({'run_id':args.run_id,'source':proof['headSha'],'status':'success','platforms':2,'tests_per_platform':225}))


if __name__=='__main__':main()
