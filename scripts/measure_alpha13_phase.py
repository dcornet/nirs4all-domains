"""Resource observation in the actual Python worker; native child peak separate."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from measure_alpha12_phase import windows_peak
from nirs4all_domains.storage import atomic_json,digest,tree_bytes


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase');p.add_argument('script');p.add_argument('arguments',nargs=argparse.REMAINDER);args=p.parse_args()
    root=Path('.audit/alpha13/phases');root.mkdir(parents=True,exist_ok=True)
    proof=root/(args.phase+'.json');log=root/(args.phase+'.log');worker=root/(args.phase+'.worker.json')
    if proof.exists():raise ValueError('PHASE_PROOF_EXISTS; USE_A_DISTINCT_ATTEMPT_NAME')
    env=os.environ.copy();env['N4DOMAINS_PHASE_MEASUREMENT_PATH']=str(worker.resolve());begin=time.perf_counter();peak=0
    with log.open('w',encoding='utf-8') as stream:
        process=subprocess.Popen([sys.executable,'scripts/alpha12_worker_entry.py',args.script,*args.arguments],stdout=stream,stderr=subprocess.STDOUT,
            env=env,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        while process.poll() is None:
            if os.name=='nt':peak=max(peak,windows_peak(process))
            time.sleep(.25)
    value={'command':['python',args.script,*args.arguments],'exit_code':process.returncode,'wall_seconds':time.perf_counter()-begin,
        'log_sha256':digest(log),'observed_venv_launcher_peak_resident_bytes':peak or None,
        'worker_memory':json.loads(worker.read_text()) if worker.exists() else {'worker_peak_resident_bytes':None,'reason':'WORKER_COUNTER_UNAVAILABLE'},
        'separate_native_child_peak':{'status':'unavailable','reason':'SEPARATE_NATIVE_CHILD_PEAK_NOT_MEASURED','value':None},
        'workspace_unique_bytes_after':tree_bytes([Path.cwd()]),'scope':'Actual Python lifetime peak excludes separate native child; launcher counter is separate.'}
    atomic_json(proof,value);print(json.dumps(value))
    if process.returncode:print(log.read_text(encoding='utf-8')[-5000:])
    raise SystemExit(process.returncode)


if __name__=='__main__':main()
