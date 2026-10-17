"""Serial local validation with exact command/exit/log evidence and byte checks."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import argparse

from nirs4all_domains.storage import atomic_json, digest, tree_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-at")
    args = parser.parse_args()
    root = Path(".audit/alpha10/validation")
    root.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    env = os.environ.copy()
    env["N4DOMAINS_BIN"] = str(Path("target/debug/n4domains.exe").resolve())
    env["N4DOMAINS_METHODS_LIBRARY"] = str(Path(".venv/Lib/site-packages/n4m/lib/n4m.dll").resolve())
    env["OPENBLAS_NUM_THREADS"] = "1"; env["OMP_NUM_THREADS"] = "1"
    commands = [
        ("editable", [py, "-m", "pip", "install", "--no-deps", "-e", "bridges/python"]),
        ("fmt", ["cargo", "fmt", "--all", "--check"]),
        ("clippy", ["cargo", "clippy", "--workspace", "--all-targets", "--locked", "--", "-D", "warnings"]),
        ("workspace", ["cargo", "test", "--workspace", "--locked"]),
        ("native", ["cargo", "test", "--workspace", "--locked", "--", "--ignored"]),
        ("rustdoc", ["cargo", "doc", "--workspace", "--no-deps", "--locked"]),
        ("build", ["cargo", "build", "--workspace", "--locked"]),
        ("schemas-rust", [str(Path(env["N4DOMAINS_BIN"])), "schema", "--out", "schemas"]),
        ("schemas-bank", [py, "scripts/generate_bank_schemas.py"]),
        ("python", [py, "-m", "unittest", "discover", "-s", "tests/integration", "-v"]),
        ("alpha9-registry", [py, "scripts/check_alpha9_registry.py"]),
        ("alpha10-registry", [py, "scripts/check_alpha10_registry.py"]),
        ("wheel", [py, "-m", "pip", "wheel", "--no-deps", "bridges/python", "--wheel-dir", str(root/"wheel")])]
    records = []
    if args.start_at:
        previous = json.loads((root/"checks.json").read_text())
        for name, _ in commands:
            if name == args.start_at: break
            record, = [r for r in previous if r["check"] == name and r["exit_code"] == 0]
            if digest(root/(name+".log")) != record["log_sha256"]: raise ValueError("VALIDATION_LOG_CHANGED")
            records.append(record)
        else: raise ValueError("UNKNOWN_RESUME_CHECK")
        commands = commands[len(records):]
    ceiling = json.loads(Path("configs/bank/storage-policy-alpha10.json").read_text())["workspace_max_bytes"]
    for name, command in commands:
        begin = time.perf_counter()
        log = root/(name+".log")
        with log.open("w", encoding="utf-8") as stream:
            result = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT, text=True)
        record = {"check": name, "exit_code": result.returncode, "seconds": time.perf_counter()-begin,
                  "log_sha256": digest(log), "workspace_unique_bytes_after": tree_bytes([Path.cwd()])}
        records.append(record)
        atomic_json(root/"checks.json", records)
        print(json.dumps(record), flush=True)
        if result.returncode:
            print(log.read_text(encoding="utf-8")[-6000:])
            raise SystemExit(result.returncode)
        if record["workspace_unique_bytes_after"] > ceiling:
            raise RuntimeError("WORKSPACE_CEILING_EXCEEDED_REVIEW_REQUIRED")


if __name__ == "__main__": main()
