"""Resource watchdog in the actual Python worker, including native DLL calls."""
import os
from pathlib import Path
import runpy
import sys
import threading
import time

from alpha18_memory import peak_memory
from nirs4all_domains import full_bank
from nirs4all_domains.storage import atomic_json

active={'start':None,'task':None};original=full_bank.reference_task


def bounded(*args,**kwargs):
    active.update(start=time.monotonic(),task=args[3]['task_id'])
    try:return original(*args,**kwargs)
    finally:active.update(start=None,task=None)


full_bank.reference_task=bounded


def watch():
    while True:
        current=dict(active);peak=peak_memory()
        fault='ACTUAL_WORKER_RAM_LIMIT' if peak>2147483648 else 'REFERENCE_TASK_180_SECOND_LIMIT' if current['start'] is not None and time.monotonic()-current['start']>180 else None
        if fault:
            # The current StageStore entry stays interrupted, never successful.
            # Earlier task artifacts and the cumulative reservation remain.
            Path('.audit/alpha18').mkdir(exist_ok=True)
            atomic_json('.audit/alpha18/worker-resource-stop.json',{'reason':fault,'peak_bytes':peak,'task_receipt':current['task']})
            os._exit(86)
        time.sleep(.1)


threading.Thread(target=watch,daemon=True).start()
script=sys.argv[1];sys.argv=sys.argv[1:];sys.path.insert(0,str(Path(script).resolve().parent))
runpy.run_path(script,run_name='__main__')
