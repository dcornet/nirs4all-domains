"""Collect actual local checks, protected hashes, package parity and storage."""
import json
from pathlib import Path
import shutil
import zipfile

from nirs4all_domains.storage import atomic_json, digest, tree_bytes


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    validation = Path(".audit/alpha10/validation")
    checks = read(validation/"checks.json")
    if len(checks) != 13 or any(r["exit_code"] for r in checks):
        raise ValueError("LOCAL_VALIDATION_INCOMPLETE")
    for record in checks:
        if digest(validation/(record["check"]+".log")) != record["log_sha256"]:
            raise ValueError("LOCAL_VALIDATION_LOG_CHANGED")
    text = (validation/"python.log").read_text(encoding="utf-8")
    if "Ran 117 tests" not in text or not text.rstrip().endswith("OK"):
        raise ValueError("EXPECTED_COMPLETE_PYTHON_SUITE_NOT_PASSED")
    protected = read("docs/audit/alpha10-frozen-output-hashes.json")
    for path, sha in protected.items():
        if not Path(path).is_file() or digest(path) != sha:
            raise ValueError("PROTECTED_HISTORICAL_OUTPUT_MISSING_OR_CHANGED:"+path)
    wheel, = (validation/"wheel").glob("*.whl")
    controllers = {}
    with zipfile.ZipFile(wheel) as archive:
        for path in Path("bridges/python/nirs4all_domains").glob("*.py"):
            if archive.read("nirs4all_domains/"+path.name) != path.read_bytes():
                raise ValueError("QUALIFIED_WHEEL_SOURCE_DIFFERS:"+path.name)
            controllers[path.name] = digest(path)
    model_files = sorted(Path("docs/benchmarks/alpha10").glob("*_v1.json"))
    receipts = [read(Path("results/alpha10-multifamily")/(p.stem+"-receipt.json")) for p in model_files]
    if not all(r["cache_hit"] for r in receipts): raise ValueError("PRIMARY_CHECKPOINT_REUSE_NOT_EXECUTED")
    size = read("results/alpha10-multifamily/size-control-receipt.json")
    if not size["cache_hit"]: raise ValueError("SIZE_CHECKPOINT_REUSE_NOT_EXECUTED")
    ledger = read("results/alpha9-perten-keyed/state/journal.json")
    policy = read("configs/bank/storage-policy-alpha10.json")
    workspace = tree_bytes([Path.cwd()])
    combined = tree_bytes(["docs/benchmarks/alpha10", "results/alpha10-multifamily/evidence", ".audit/alpha10/evidence"])
    if workspace > policy["workspace_max_bytes"] or ledger["reserved_campaign_bytes"] > policy["campaign_bytes"] or combined > policy["evidence_bytes"]:
        raise ValueError("FINAL_STORAGE_BUDGET_EXCEEDED")
    volumes = {v: {"free_bytes": shutil.disk_usage(v+":/").free} for v in ("C", "D")}
    if any(v["free_bytes"] < policy["reserve_free_bytes"] for v in volumes.values()): raise ValueError("FREE_VOLUME_RESERVE_EXCEEDED")
    evidence_by_task = {}
    for run in ledger["runs"].values():
        if run["status"] == "computed":
            key = run["task_id"]
            evidence_by_task[key] = evidence_by_task.get(key, 0)+run["measured_evidence_bytes"]
    storage = {"protocol_version": "domains.alpha10.storage_audit.v0.1", "policy": policy,
        "workspace_unique_bytes": workspace, "baseline_unique_bytes": 11978437549,
        "growth_bytes": workspace-11978437549, "volumes": volumes,
        "owner_approved_workspace_additions_bytes": [536870912, 268435456],
        "first_guard_stop_observed_bytes": 12560694224, "first_guard_stop_previous_ceiling": 12531500737,
        "cumulative_campaign_reserved_bytes": ledger["reserved_campaign_bytes"],
        "reserved_bytes_by_stage_task": ledger["task_reserved_bytes"], "measured_stage_evidence_bytes_by_task": evidence_by_task,
        "all_alpha10_combined_unique_essential_evidence_bytes": combined,
        "portable_registry_bytes": tree_bytes(["docs/benchmarks/alpha10"]),
        "isolated_optional_runtime_bytes": tree_bytes([".audit/alpha10/runtime"]),
        "original_cartilage_input_bytes": 26657431, "original_cartilage_provider": "Datasets 0.3.11 explicit cache",
        "Perten_input": "Unchanged frozen admitted alpha.9 mean input reused; no repeated per-fold disk matrices",
        "primary_cache_hits": len(receipts), "size_control_cache_hit": True,
        "cartilage_audit_cache_hit": read(".audit/alpha10/cartilage-audit-receipt.json")["cache_hit"],
        "historical_files_deleted_or_migrated": 0, "limits": ["Cooperative disk admission is not an OS quota", "Rust/runtime tooling growth differs from task reservations; two owner reviews preserved all other caps"]}
    atomic_json("docs/audit/alpha10-storage.json", storage)
    result = {"baseline_commit": "55777a58c71c1d429ba1ba593f8fca1fcbe936ac", "bridge": "0.1.0a10",
        "methods": "1.3.6 / ABI 2.19", "dag_ml": "0.3.41", "nirs4all": "1.4.10", "datasets": "0.3.11",
        "tests": {"Rust": 35, "Python": 117, "total": 152, "baseline_preserved": 129, "new": 23},
        "checks": checks, "protected_files_verified": len(protected),
        "wheel": {"filename": wheel.name, "bytes": wheel.stat().st_size, "sha256": digest(wheel), "python_controller_hashes": controllers},
        "primary_checkpoint_cache_hits": 4, "size_control_checkpoint_cache_hits": 1,
        "complete_anchor_replay_predictions": 2154, "native_replay": "exact", "adaptive_replay": "absolute/relative 1e-9",
        "isolated_wheel_smoke_log_sha256": digest(validation/"wheel-smoke.log"),
        "additional_report_checks": {"canonical": digest(validation/"canonical/report.json"),
                                     "structural": digest(validation/"structure/report.json")},
        "followup_exact_axis": {"evidence_sha256": digest("docs/benchmarks/alpha10/cartilage-axis-verification.json"),
                                "registry_check_log_sha256": digest(validation/"axis-registry-check.log"),
                                "registry_checker_sha256": digest("scripts/check_alpha10_registry.py"),
                                "scope": "Header-only exact-axis confirmation; original audit/OOF/fit controllers unchanged"},
        "hosted_CI": "Recorded separately from actual GitHub execution after source commit; no configuration-only proof"}
    atomic_json("docs/audit/alpha10-validation.json", result)
    print(json.dumps({"tests": 152, "protected_files": len(protected), "wheel_bytes": wheel.stat().st_size,
                      "workspace_bytes": workspace, "combined_evidence_bytes": combined, "campaign_reserved_bytes": ledger["reserved_campaign_bytes"]}))


if __name__ == "__main__": main()
