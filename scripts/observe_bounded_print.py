"""Experimental Windows Job admission/containment probe; not qualified for printing.

The child must wait for ADMITTED on stdin before starting browsers or allocating
the print workload. This closes the process-assignment race. Unsupported hosts
fail closed; there is no uncontained fallback. Job committed-memory accounting
is distinct from renderer working set/shared memory. A successful child alone
does not establish an aggregate physical-memory bound.
"""
import argparse
import ctypes
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


class BasicLimits(ctypes.Structure):
    _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                ("flags", w.DWORD), ("min_working_set", ctypes.c_size_t),
                ("max_working_set", ctypes.c_size_t), ("active_process_limit", w.DWORD),
                ("affinity", ctypes.c_size_t), ("priority", w.DWORD), ("scheduling", w.DWORD)]


class IOCounts(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in
                ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [("basic", BasicLimits), ("io", IOCounts),
                ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]


def run(args):
    receipt = {"protocol_version": "domains.bounded_print_process.v1", "status": "unavailable",
               "memory_limit_bytes": args.memory_bytes, "deadline_seconds": args.timeout_seconds,
               "containment": "Windows aggregate Job memory plus kill-on-close; child waits for assignment",
               "scope": "Engineering containment only; no scientific qualification", "new_scientific_reservations": 0}
    if os.name != "nt":
        receipt["reason"] = "AGGREGATE_PRINT_CONTAINMENT_NOT_IMPLEMENTED_ON_THIS_HOST"
        args.out.write_text(json.dumps(receipt, indent=2) + "\n")
        return 2
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
    kernel.CreateJobObjectW.restype = w.HANDLE
    kernel.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    kernel.SetInformationJobObject.restype = w.BOOL
    kernel.QueryInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p]
    kernel.QueryInformationJobObject.restype = w.BOOL
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    kernel.OpenProcess.restype = w.HANDLE
    kernel.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
    kernel.AssignProcessToJobObject.restype = w.BOOL
    kernel.TerminateJobObject.argtypes = [w.HANDLE, w.UINT]
    kernel.TerminateJobObject.restype = w.BOOL
    kernel.CloseHandle.argtypes = [w.HANDLE]
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    limits = ExtendedLimits()
    limits.basic.flags = 0x2000 | 0x0200  # KILL_ON_JOB_CLOSE | JOB_MEMORY
    limits.job_memory = args.memory_bytes
    process = None
    start = time.monotonic()
    try:
        if not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise ctypes.WinError(ctypes.get_last_error())
        with args.log.open("xb") as log:
            process = subprocess.Popen(args.command, stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT)
            handle = kernel.OpenProcess(0x0100 | 0x0001, False, process.pid)  # SET_QUOTA | TERMINATE
            if not handle:
                raise ctypes.WinError(ctypes.get_last_error())
            try:
                if not kernel.AssignProcessToJobObject(job, handle):
                    raise ctypes.WinError(ctypes.get_last_error())
            finally:
                kernel.CloseHandle(handle)
            initial = ExtendedLimits()
            if not kernel.QueryInformationJobObject(job, 9, ctypes.byref(initial), ctypes.sizeof(initial), None):
                raise ctypes.WinError(ctypes.get_last_error())
            receipt["initial_job_committed_peak_bytes"] = initial.peak_job_memory
            if initial.peak_job_memory > args.memory_bytes:
                raise RuntimeError("CHILD_STARTUP_ALREADY_EXCEEDS_JOB_LIMIT")
            receipt["assigned_before_workload"] = True
            process.stdin.write(b"ADMITTED\n")
            process.stdin.close()
            try:
                code = process.wait(timeout=args.timeout_seconds)
                receipt.update(status="passed" if code == 0 else "child_failed", child_exit=code)
            except subprocess.TimeoutExpired:
                kernel.TerminateJobObject(job, 124)
                process.wait(timeout=10)
                receipt.update(status="deadline_terminated", child_exit=124)
        measured = ExtendedLimits()
        if not kernel.QueryInformationJobObject(job, 9, ctypes.byref(measured), ctypes.sizeof(measured), None):
            raise ctypes.WinError(ctypes.get_last_error())
        receipt["peak_job_committed_bytes"] = measured.peak_job_memory
        receipt["aggregate_limit_respected"] = measured.peak_job_memory <= args.memory_bytes
        receipt["physical_memory_containment"] = "unqualified; job commit is not renderer RSS"
        if not receipt["aggregate_limit_respected"]:
            receipt["status"] = "memory_limit_not_qualified"
    finally:
        kernel.CloseHandle(job)  # All assigned descendants are terminated, including on failure.
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        receipt["elapsed_seconds"] = round(time.monotonic() - start, 3)
        receipt["owned_job_closed"] = True
        if args.log.exists():
            receipt["log_sha256"] = hashlib.sha256(args.log.read_bytes()).hexdigest()
        args.out.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(json.dumps(receipt))
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory-bytes", type=int, default=2_147_483_648)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    options = parser.parse_args()
    if options.command[:1] == ["--"]:
        options.command.pop(0)
    assert 32_000_000 <= options.memory_bytes <= 2_147_483_648
    assert 1 <= options.timeout_seconds <= 900 and options.command
    assert not options.out.exists() and not options.log.exists(), "Retain previous evidence"
    raise SystemExit(run(options))
