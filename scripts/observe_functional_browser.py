"""Measure actual owned browser qualification processes with finite engineering guards."""
import json
import os
from pathlib import Path
import subprocess
import time

import psutil

root = Path(__file__).resolve().parents[1]
output = Path(os.environ.get('DOMAINS_BROWSER_RESULTS', root / 'demo/test-results/browser'))
output.mkdir(parents=True, exist_ok=True)
start = time.monotonic()
peak, samples, stopped = 0, 0, None
with (output / 'functional-browser.log').open('xb') as log:
    process = subprocess.Popen(['node', 'demo/scripts/browser.mjs'], cwd=root, stdout=log, stderr=subprocess.STDOUT)
    while process.poll() is None:
        try:
            parent = psutil.Process(process.pid)
            members = [parent, *parent.children(recursive=True)]
            current = 0
            for member in members:
                try:
                    current += member.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            peak = max(peak, current)
            samples += 1
            if current > 4 * 1024**3 or time.monotonic() - start > 900:
                stopped = 'OBSERVED_RSS_GUARD' if current > 4 * 1024**3 else 'WALL_GUARD'
                for member in reversed(members):
                    try:
                        member.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
        except psutil.NoSuchProcess:
            pass
        time.sleep(.1)
receipt = {'protocol_version': 'domains.functional_browser_resources.v1', 'exit_code': process.wait(),
           'observed_process_tree_rss_peak_bytes': peak, 'samples': samples,
           'seconds': time.monotonic() - start, 'stop_reason': stopped,
           'guard_bytes': 4 * 1024**3, 'guard_seconds': 900,
           'scope': '100 ms sampled RSS of owned Node/browser tree; shared pages may be counted repeatedly. Sampling guard, not strict allocation containment.'}
(output / 'functional-browser-resources.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt))
raise SystemExit(receipt['exit_code'] or (1 if stopped else 0))
