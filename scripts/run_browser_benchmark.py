"""Observe a bounded Node/browser process tree. No numeric dataset processing."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

import psutil

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, "DOMAINS_BENCH_DIST": str(Path(args.dist).resolve()),
                   "DOMAINS_BENCH_OUTPUT": str(out.resolve()), "DOMAINS_BENCH_LABEL": args.label,
                   "DOMAINS_BENCH_REPETITIONS": "3"}
    start = time.monotonic()
    process = subprocess.Popen(["node", "--max-old-space-size=256", "demo/scripts/technical-benchmark.mjs"], env=environment)
    peak = 0
    stop = None
    while process.poll() is None:
        try:
            members = [psutil.Process(process.pid), *psutil.Process(process.pid).children(recursive=True)]
            current = 0
            for member in members:
                try:
                    current += member.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            peak = max(peak, current)
            if current > 960 * 1024**2 or time.monotonic() - start > 300:
                stop = "OBSERVED_RSS_GUARD" if current > 960 * 1024**2 else "WALL_GUARD"
                for member in reversed(members):
                    try:
                        member.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
        except psutil.NoSuchProcess:
            pass
        time.sleep(0.05)
    receipt = {"label": args.label, "exit_code": process.wait(), "stop_reason": stop,
               "seconds": time.monotonic() - start, "observed_process_tree_rss_peak_bytes": peak,
               "scope": "50 ms process-tree RSS sampling including Node/browser automation; shared pages may be counted more than once. This is a sampling guard, not strict allocation containment."}
    out.with_suffix(".resources.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))
    raise SystemExit(receipt["exit_code"] or (1 if stop else 0))

if __name__ == "__main__":
    main()
