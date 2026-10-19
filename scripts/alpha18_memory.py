"""Thread-safe OS lifetime peak counters; no shared mutable ctypes prototypes."""
import os

if os.name=='nt':
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(name,ctypes.c_size_t) for name in (
            'PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
            'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    # Independent function objects, initialized once. Historical helpers create
    # a new structure class and rewrite windll's cached argtypes on each call;
    # concurrent watchdog/main calls can then reject each other's pointers.
    _psapi=ctypes.WinDLL('psapi',use_last_error=True)
    _read=_psapi.GetProcessMemoryInfo
    _read.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    _read.restype=wintypes.BOOL
    _kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    _self=_kernel.GetCurrentProcess;_self.restype=wintypes.HANDLE

    def _peak(handle):
        value=Counters();value.cb=ctypes.sizeof(value)
        if not _read(handle,ctypes.byref(value),value.cb):raise OSError(ctypes.get_last_error(),'PROCESS_MEMORY_COUNTER_FAILED')
        return int(value.PeakWorkingSetSize)

    def peak_memory():return _peak(_self())
    def windows_peak(process):return _peak(wintypes.HANDLE(int(process._handle)))
else:
    def peak_memory():
        import resource
        import sys
        value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(value if sys.platform=='darwin' else value*1024)

    def windows_peak(process):raise RuntimeError('WINDOWS_CHILD_MEMORY_COUNTER_REQUIRED')
