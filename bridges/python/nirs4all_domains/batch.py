"""Continue a campaign after per-task acquisition, conversion or engine failures."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess

import yaml

from .dataset import task_from_dataset


def run_campaign(config_path, out, binary, methods_library=None):
    config_path, out = Path(config_path).resolve(), Path(out).resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if config.get("schema_version") != 1 or not isinstance(config.get("tasks"), list):
        raise ValueError("Campaign schema_version=1 and tasks array required")
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for index, entry in enumerate(config["tasks"]):
        task_out = out / f"task-{index:03d}"
        task_out.mkdir(exist_ok=True)
        # Remove only our named outputs before rerunning this task: a failed
        # invocation must never be represented by an older successful report.
        for name in ("task.json", "report.json", "report.md", "campaign-task.json"):
            (task_out / name).unlink(missing_ok=True)
        record = {"task_index": index, "dataset_id": entry.get("dataset_id"), "configuration": entry}
        try:
            if not entry.get("enabled", True):
                record.update(status="unavailable", reason=entry.get("reason", "TASK_DISABLED"))
            else:
                if "task_file" in entry:
                    task = json.loads((config_path.parent / entry["task_file"]).read_text(encoding="utf-8"))
                else:
                    import nirs4all_datasets as datasets
                    root = (config_path.parent / config["catalog_root"]).resolve()
                    ds = datasets.get(entry["dataset_id"], root=root)
                    task = task_from_dataset(ds, entry)
                task_path = task_out / "task.json"
                task_path.write_text(json.dumps(task, indent=2, allow_nan=False), encoding="utf-8")
                command = [str(binary), "analyze", str(task_path), "--out", str(task_out)]
                if methods_library:
                    command.extend(["--methods-library", str(methods_library)])
                execution = subprocess.run(command, capture_output=True, text=True, check=False)
                record["exit_code"] = execution.returncode
                report_path = task_out / "report.json"
                if report_path.exists():
                    report = json.loads(report_path.read_text(encoding="utf-8"))
                    record.update(status=report["status"], provenance=report["provenance"], protocol_version=report["protocol_version"])
                else:
                    record.update(status="error", reason="ENGINE_DID_NOT_PRODUCE_REPORT")
                if execution.returncode:
                    record["error"] = execution.stderr.strip()
        except Exception as exc:  # each failure is retained; subsequent tasks still run
            record.update(status="error", reason=f"{type(exc).__name__}: {exc}")
        (task_out / "campaign-task.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        results.append(record)
    summary = {"schema_version": 1, "tasks": results,
               "status": "partial" if any(r["status"] != "complete" for r in results) else "complete"}
    (out / "campaign.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-config", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--methods-library")
    args = parser.parse_args()
    binary = os.environ.get("N4DOMAINS_BIN", "n4domains")
    summary = run_campaign(args.catalog_config, args.out, binary, args.methods_library)
    print(f"{len(summary['tasks'])} tasks: {summary['status']}")
    return 2 if any(r["status"] in ("error", "failed") for r in summary["tasks"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
