"""Resource-only entry wrapper, executed inside the actual Python worker."""
import atexit
import ctypes
import os
from pathlib import Path
import runpy
import sys


def record_peak():
    from nirs4all_domains.storage import atomic_json
    from ctypes import wintypes
    path=os.environ.get('N4DOMAINS_PHASE_MEASUREMENT_PATH')
    if not path:return
    if os.name!='nt':
        atomic_json(path,{'worker_peak_resident_bytes':None,'reason':'WINDOWS_WORKER_COUNTER_NOT_AVAILABLE'})
        return
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(k,ctypes.c_size_t) for k in (
            'PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
            'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    value=Counters();value.cb=ctypes.sizeof(value)
    process=ctypes.windll.kernel32.GetCurrentProcess;process.restype=wintypes.HANDLE
    read=ctypes.windll.psapi.GetProcessMemoryInfo;read.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    success=bool(read(process(),ctypes.byref(value),value.cb))
    atomic_json(path,{'worker_peak_resident_bytes':value.PeakWorkingSetSize if success else None,
        'reason':None if success else 'WORKER_MEMORY_COUNTER_FAILED','pid':os.getpid(),
        'scope':'Actual Python worker lifetime OS peak; includes in-process SNV/metadata kernels, excludes separate Rust children.'})


if __name__=='__main__':
    script=sys.argv[1];sys.argv=sys.argv[1:];sys.path.insert(0,str(Path(script).resolve().parent))
    atexit.register(record_peak)
    runpy.run_path(script,run_name='__main__')
