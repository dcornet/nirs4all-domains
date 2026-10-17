"""Observe phase wall time, logs and Python-worker OS peak counters; no numeric fits."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from nirs4all_domains.storage import atomic_json,digest,tree_bytes


def windows_peak(process):
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(k,ctypes.c_size_t) for k in (
            'PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
            'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    value=Counters();value.cb=ctypes.sizeof(value)
    read=ctypes.windll.psapi.GetProcessMemoryInfo
    read.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    return value.PeakWorkingSetSize if read(wintypes.HANDLE(int(process._handle)),ctypes.byref(value),value.cb) else 0


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase');parser.add_argument('script');parser.add_argument('arguments',nargs=argparse.REMAINDER);args=parser.parse_args()
    root=Path('.audit/alpha12/phases');root.mkdir(parents=True,exist_ok=True)
    log=root/(args.phase+'.log');proof=root/(args.phase+'.json')
    if proof.exists():raise ValueError('PHASE_OBSERVATION_ALREADY_EXISTS; CHOOSE_DISTINCT_ATTEMPT_NAME')
    start=time.perf_counter();peak=0
    env=os.environ.copy();worker_proof=root/(args.phase+'.worker.json')
    env['N4DOMAINS_PHASE_MEASUREMENT_PATH']=str(worker_proof.resolve())
    with log.open('w',encoding='utf-8') as stream:
        child=subprocess.Popen([sys.executable,'scripts/alpha12_worker_entry.py',args.script,*args.arguments],stdout=stream,stderr=subprocess.STDOUT,env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        while child.poll() is None:
            if os.name=='nt':peak=max(peak,windows_peak(child))
            time.sleep(.25)
        if os.name=='nt':peak=max(peak,windows_peak(child))
    result={'command':['python',args.script,*args.arguments],'exit_code':child.returncode,'wall_seconds':time.perf_counter()-start,
        'log_sha256':digest(log),'observed_venv_launcher_peak_resident_bytes':peak or None,
        'worker_memory':json.loads(worker_proof.read_text()) if worker_proof.exists() else {'worker_peak_resident_bytes':None,'reason':'ACTUAL_WORKER_MEASUREMENT_UNAVAILABLE'},
        'peak_scope':'Launcher and actual Python worker are separate; neither includes the separate Rust process peak.',
        'native_child_peak':{'status':'unavailable','reason':'SEPARATE_NATIVE_CHILD_PEAK_NOT_MEASURED','value':None},
        'workspace_unique_bytes_after':tree_bytes([Path.cwd()])}
    atomic_json(proof,result);print(json.dumps(result))
    if child.returncode:print(log.read_text(encoding='utf-8')[-7000:])
    sys.exit(child.returncode)


if __name__=='__main__':main()
