"""End only the owned calibration worker at a durable idle boundary on Windows."""
import argparse
import ctypes
from ctypes import wintypes as w
import json
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace
from measure_alpha12_phase import windows_peak
from nirs4all_domains.storage import atomic_json,digest


def children(pid):
    class Entry(ctypes.Structure):
        _fields_=[('dwSize',w.DWORD),('cntUsage',w.DWORD),('th32ProcessID',w.DWORD),('th32DefaultHeapID',ctypes.c_size_t),
            ('th32ModuleID',w.DWORD),('cntThreads',w.DWORD),('th32ParentProcessID',w.DWORD),('pcPriClassBase',w.LONG),('dwFlags',w.DWORD),('szExeFile',w.WCHAR*260)]
    kernel=ctypes.windll.kernel32;create=kernel.CreateToolhelp32Snapshot;create.argtypes=[w.DWORD,w.DWORD];create.restype=w.HANDLE
    snapshot=create(2,0);entry=Entry();entry.dwSize=ctypes.sizeof(entry);result=[]
    first=kernel.Process32FirstW;first.argtypes=[w.HANDLE,ctypes.POINTER(Entry)]
    advance=kernel.Process32NextW;advance.argtypes=first.argtypes
    try:
        success=first(snapshot,ctypes.byref(entry))
        while success:
            if entry.th32ParentProcessID==pid:result.append({'pid':entry.th32ProcessID,'name':entry.szExeFile})
            success=advance(snapshot,ctypes.byref(entry))
    finally:
        close=kernel.CloseHandle;close.argtypes=[w.HANDLE];close(snapshot)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('pid',type=int);args=parser.parse_args()
    # Bind the PID to our exact experiment, never a process found by name alone.
    command=['powershell','-NoProfile','-Command',f'Get-CimInstance Win32_Process -Filter "ProcessId={args.pid}" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress']
    owner=json.loads(subprocess.check_output(command).decode('utf-8-sig'))
    assert owner['ProcessId']==args.pid and 'alpha12_worker_entry.py' in owner['CommandLine'] and 'scripts/run_alpha13_calibration.py run' in owner['CommandLine']
    freeze=json.loads(Path('docs/benchmarks/alpha13/calibration-freeze.json').read_text())['freeze_id']
    kernel=ctypes.windll.kernel32;opening=kernel.OpenProcess;opening.argtypes=[w.DWORD,w.BOOL,w.DWORD];opening.restype=w.HANDLE
    handle=opening(0x0800|0x0001|0x0400|0x0010|0x100000,False,args.pid)
    if not handle:raise OSError('OWNED_WORKER_HANDLE_UNAVAILABLE')
    suspend=ctypes.windll.ntdll.NtSuspendProcess;resume=ctypes.windll.ntdll.NtResumeProcess
    suspend.argtypes=[w.HANDLE];resume.argtypes=[w.HANDLE]
    terminate=kernel.TerminateProcess;terminate.argtypes=[w.HANDLE,w.UINT]
    suspended=False;stopped=False;start=time.monotonic()
    try:
        while time.monotonic()-start<180:
            if suspend(handle)!=0:raise OSError('CANNOT_SUSPEND_OWNED_WORKER')
            suspended=True
            active=children(args.pid)
            journal=json.loads(Path('results/alpha9-perten-keyed/state/journal.json').read_text())
            running=[r for r in journal['runs'].values() if r['contract'].get('freeze_id')==freeze and r['status']=='running']
            if not active and not running:
                proof={'pid':args.pid,'owned_command':owner['CommandLine'],'freeze_id':freeze,'active_native_children':active,'running_scientific_stages':len(running),
                    'actual_python_worker_peak_resident_bytes':windows_peak(SimpleNamespace(_handle=int(handle))),
                    'completed_stage_count':sum(r['contract'].get('freeze_id')==freeze and r['status']=='computed' for r in journal['runs'].values()),
                    'reason':'COST_BASED_TRANSPORT_SWITCH_AT_DURABLE_STAGE_BOUNDARY','native_fit_canceled':False,
                    'source_controller_sha256':digest('scripts/run_alpha13_calibration.py'),'exit_code':77}
                if not terminate(handle,77):raise OSError('OWNED_WORKER_TERMINATION_FAILED')
                stopped=True;suspended=False;atomic_json('.audit/alpha13/transport-boundary-stop.json',proof)
                print(json.dumps(proof));return
            resume(handle);suspended=False;time.sleep(.2)
        raise TimeoutError('NO_SAFE_DURABLE_BOUNDARY_OBSERVED; WORKER_LEFT_RUNNING')
    finally:
        if suspended and not stopped:resume(handle)
        close=kernel.CloseHandle;close.argtypes=[w.HANDLE];close(handle)


if __name__=='__main__':main()
