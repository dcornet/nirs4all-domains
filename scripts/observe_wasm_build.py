"""Observe the existing locked WASM build; no source/provider substitution."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import psutil

npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
node = shutil.which("node")
assert npm and node
cli = Path(npm).parent / "node_modules/npm/bin/npm-cli.js" if os.name == "nt" else Path(npm).resolve()
assert cli.is_file()
free_before = shutil.disk_usage(".").free
start = time.monotonic()
process = subprocess.Popen([node, str(cli), "run", "build:native", "--prefix", "bindings/wasm"])
peak = 0
while process.poll() is None:
    try:
        members = [psutil.Process(process.pid), *psutil.Process(process.pid).children(recursive=True)]
        total = 0
        for member in members:
            try:
                total += member.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        peak = max(peak, total)
    except psutil.NoSuchProcess:
        pass
    time.sleep(0.05)
exit_code = process.wait()
result = {"protocol": "domains.wasm_build_resources.v1", "exit_code": exit_code,
          "seconds": time.monotonic() - start, "observed_process_tree_rss_peak_bytes": peak,
          "volume_free_before_bytes": free_before, "volume_free_after_bytes": shutil.disk_usage(".").free,
          "generated_binding_bytes": sum(p.stat().st_size for p in Path("bindings/wasm/native").rglob("*") if p.is_file()),
          "scope": "Existing locked build, 50 ms process-tree RSS observation including compiler children; shared pages may be counted more than once. No allocation-quota or before/after compiler-speed claim."}
out = Path("demo/test-results/wasm-build.resources.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
raise SystemExit(exit_code)
