"""Preserve completed raw stress, correct the OS watchdog's ctypes race."""
from concurrent.futures import ThreadPoolExecutor
from alpha18_common import Context,read
from alpha18_memory import peak_memory
from nirs4all_domains.storage import digest,atomic_json

c=Context();old=c.load('SNV-stress-extension-freeze-v2.json')
assert digest('.audit/alpha18-stress-controller-before-memory.py')==old['controller_sha256']
with ThreadPoolExecutor(max_workers=4) as pool:
    values=list(pool.map(lambda _:peak_memory(),range(400)))
assert all(0<v<2147483648 for v in values)
raw=c.load('stress-progress.json');assert len(raw)==5
actual=max(read(r['artifact_path'])['peak_resident_bytes'] for r in raw)
assert actual<2147483648
v={'prior_stress_controller_sha256':digest('.audit/alpha18-stress-controller-before-memory.py'),
   'current_stress_controller_sha256':digest('scripts/run_alpha18_stress.py'),
   'memory_monitor_sha256':digest('scripts/alpha18_memory.py'),
   'prior_worker_entry_sha256':digest('.audit/alpha18-worker-entry-first.py'),
   'current_worker_entry_sha256':digest('scripts/alpha18_worker_entry.py'),
   'qualification':'400 concurrent native OS peak reads across four threads; no prototype mutation or error.',
   'cause':'Historical per-call ctypes structure classes mutate a cached function prototype; watchdog/main threads can race.',
   'completed_raw_stress_preserved':True,'completed_raw_process_lifetime_peak_bytes':actual,
   'actual_memory_cap_respected':True,'continuous_watchdog_fault_recorded':True,
   'numerical_protocol_changed':False,'numerical_rerun':False}
c.save('memory-watchdog-continuation.json',v);atomic_json('docs/campaign/memory-watchdog-continuation.json',v)
print('THREAD_SAFE_OS_WATCHDOG_QUALIFIED; RAW_NUMERICAL_RESULTS_PRESERVED')
