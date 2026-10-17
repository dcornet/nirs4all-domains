"""Record completed Windows/Ubuntu jobs and actual 138-test logs at an exact SHA."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from nirs4all_domains.storage import atomic_json,digest


def gh(*args):return subprocess.check_output(['gh',*args],text=True,encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('run_id');parser.add_argument('--expected-sha',required=True)
    parser.add_argument('--out',type=Path,default=Path('docs/audit/github-ci-alpha11.json'));args=parser.parse_args()
    info=json.loads(gh('run','view',args.run_id,'--repo','dcornet/nirs4all-domains','--json','headSha,status,conclusion,jobs,url,createdAt,updatedAt'))
    if info['headSha']!=args.expected_sha or info['status']!='completed' or info['conclusion']!='success':raise ValueError('EXPECTED_SOURCE_CI_NOT_COMPLETED_SUCCESSFULLY')
    if {j['name'] for j in info['jobs']}!={'audit (ubuntu-latest)','audit (windows-latest)'}:raise ValueError('BOTH_PLATFORM_JOBS_REQUIRED')
    for job in info['jobs']:
        if job['status']!='completed' or job['conclusion']!='success':raise ValueError('PLATFORM_EXECUTION_NOT_COMPLETED_SUCCESSFULLY')
        log=gh('run','view',args.run_id,'--repo','dcornet/nirs4all-domains','--job',str(job['databaseId']),'--log')
        path=Path('.audit/alpha11')/(args.run_id+'-'+str(job['databaseId'])+'.log');path.write_text(log,encoding='utf-8')
        found=re.findall(r'Ran (\d+) tests in ([\d.]+)s',log)
        if not found or any(int(n)!=138 for n,s in found):raise ValueError('ACTUAL_138_TEST_EXECUTION_LOG_REQUIRED')
        rust=sum(map(int,re.findall(r'test result: ok\. (\d+) passed',log)))
        if rust!=35:raise ValueError('ACTUAL_35_RUST_TEST_EXECUTION_LOG_REQUIRED')
        job.update(actual_python_test_runs=[{'count':int(n),'seconds':float(s)} for n,s in found],actual_rust_tests=rust,total_tests=173,log_sha256=digest(path))
    atomic_json(args.out,{'repository':'dcornet/nirs4all-domains','run_id':int(args.run_id),**info,
        'proof':'Both completed platform jobs/steps and actual native/138-Python-test logs; no real-data acquisition or TabPFN fit in CI.'})
    print(json.dumps({'headSha':info['headSha'],'conclusion':info['conclusion'],'jobs':[j['name'] for j in info['jobs']]}))


if __name__=='__main__':main()
