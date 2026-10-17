"""Disk accounting and serialized, resumable stage publication. No numerical work."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import time
import uuid


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def fingerprint(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_path(root, relative):
    """Portable manifest paths; resolving a junction cannot escape root."""
    p = PurePosixPath(relative)
    if not relative or "\\" in relative or ":" in relative or p.is_absolute() or PureWindowsPath(relative).is_absolute() or ".." in p.parts:
        raise ValueError("UNSAFE_ARTIFACT_REFERENCE")
    base = Path(root).resolve()
    result = (base / relative).resolve()
    if not result.is_relative_to(base):
        raise ValueError("ARTIFACT_REFERENCE_ESCAPES_ROOT")
    return result


def atomic_json(path, value, max_bytes=None):
    data = encoded(value)
    if max_bytes is not None and len(data) > max_bytes:
        raise ValueError("PERSISTENT_EVIDENCE_BUDGET_EXCEEDED")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".part")
    with temp.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)
    return {"sha256": digest(path), "bytes": len(data)}


def tree_bytes(roots):
    """Unique file identities across overlapping roots; no reparse traversal."""
    seen, visited, total = set(), set(), 0
    for root in roots:
        pending = [Path(root)]
        while pending:
            current = pending.pop()
            if not current.exists():
                continue
            info = current.lstat()
            if current.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
                continue
            if current.is_dir():
                key = os.path.normcase(str(current.absolute()))
                if key not in visited:
                    visited.add(key)
                    pending.extend(current.iterdir())
            else:
                key = (info.st_dev, info.st_ino) if info.st_ino else str(current.resolve())
                if key not in seen:
                    seen.add(key)
                    total += info.st_size
    return total


def estimate(plan, policy, workspace, scratch, evidence):
    """No writes/downloads/fits. Budgets are supplied by the caller, not universal."""
    required = ("per_task_bytes", "campaign_bytes", "evidence_bytes", "workspace_max_bytes", "reserve_free_bytes", "max_concurrency")
    if any(not isinstance(policy.get(k), int) or isinstance(policy[k], bool) or policy[k] < 0 for k in required):
        raise ValueError("EXPLICIT_NONNEGATIVE_BUDGETS_REQUIRED")
    if policy["max_concurrency"] != 1:
        raise ValueError("ALPHA8_SERIAL_SCHEDULER_REQUIRES_MAX_CONCURRENCY_1")
    inputs = {}
    for item in plan["inputs"]:
        if item["sha256"] in inputs and item["bytes"] != inputs[item["sha256"]]["bytes"]:
            raise ValueError("CONFLICTING_SHARED_CONTENT_SIZE")
        inputs.setdefault(item["sha256"], item)
    input_bytes = sum(x["bytes"] for x in inputs.values())
    new_inputs = 0
    for item in inputs.values():
        if item.get("path"):
            p = Path(item["path"])
            if not p.is_file() or p.stat().st_size != item["bytes"] or digest(p) != item["sha256"]:
                raise ValueError("INPUT_CACHE_DIGEST_OR_SIZE_MISMATCH")
        else:
            new_inputs += item["bytes"]
    scratch_bytes, persistent = plan["scratch_bytes"], plan["evidence_bytes"]
    if min(scratch_bytes, persistent, new_inputs, plan["expected_fits"], plan["expected_permutations"]) < 0:
        raise ValueError("NEGATIVE_ESTIMATE")
    incremental = new_inputs + scratch_bytes + persistent
    # Current scratch, failed/partial stages and existing inputs are included in
    # these observed totals. Shared verified inputs add zero incremental bytes.
    observed = tree_bytes([workspace, scratch, evidence, *[x["path"] for x in inputs.values() if x.get("path")]])
    reasons = []
    if incremental > policy["per_task_bytes"]:
        reasons.append("PER_TASK_DISK_BUDGET_EXCEEDED")
    if persistent > policy["evidence_bytes"]:
        reasons.append("PERSISTENT_EVIDENCE_BUDGET_EXCEEDED")
    if observed + incremental > policy["workspace_max_bytes"]:
        reasons.append("WORKSPACE_DISK_BUDGET_EXCEEDED")
    # Charge conservatively on every participating volume; no assumed placement
    # of an as-yet-unacquired provider cache. Existing bytes are already occupied.
    volumes = {}
    for path in (workspace, scratch, evidence, *[x["path"] for x in inputs.values() if x.get("path")]):
        p = Path(path).absolute()
        while not p.exists():
            p = p.parent
        device = str(p.stat().st_dev)
        free = shutil.disk_usage(p).free
        volumes[device] = {"free_bytes": free, "required_incremental_upper_bytes": incremental,
                           "reserve_free_bytes": policy["reserve_free_bytes"]}
        if free < incremental + policy["reserve_free_bytes"]:
            reasons.append("INSUFFICIENT_AVAILABLE_VOLUME_STORAGE")
    return dict(protocol_version="domains.storage.v0.1", status="insufficient_storage" if any("VOLUME" in r for r in reasons) else "budget_exceeded" if reasons else "ready",
                reasons=sorted(set(reasons)), input_bytes=input_bytes, new_input_bytes=new_inputs,
                scratch_bytes=scratch_bytes, persistent_evidence_bytes=persistent,
                existing_verified_input_bytes=input_bytes-new_inputs,
                peak_incremental_bytes=incremental, measured_existing_bytes=observed,
                peak_observed_plus_incremental_bytes=observed+incremental, volumes=volumes,
                expected_fits=plan["expected_fits"], expected_permutations=plan["expected_permutations"],
                estimated_seconds=plan.get("estimated_seconds"), uncertainty=plan["uncertainty"])


@contextmanager
def serial_lease(path):
    """Kernel lock released after a crash; the persistent lock file is not a lease."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            if path.stat().st_size == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError("SCHEDULER_BUSY") from exc
        else:
            import fcntl
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError("SCHEDULER_BUSY") from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


class StageStore:
    """One execution per fingerprint; completed artifacts verified on every hit.

    Callers must use the same state root for a campaign. Unknown partial files
    remain inventoried and are never automatically discarded on restart.
    """
    def __init__(self, state_root, scratch_root, evidence_root, workspace, policy):
        self.root, self.scratch, self.evidence, self.workspace = map(Path, (state_root, scratch_root, evidence_root, workspace))
        self.policy = policy

    def run(self, contract, stage, plan, callback, validate=lambda value: None):
        if stage not in ("P0", "P1", "P2", "P3", "P4"):
            raise ValueError("UNKNOWN_STAGE")
        execution = fingerprint(contract)
        with serial_lease(self.root / "scheduler.lock"):
            journal = self.root / "journal.json"
            ledger = json.loads(journal.read_text()) if journal.exists() else {"runs": {}, "reserved_campaign_bytes": 0, "task_reserved_bytes":{}}
            if "task_reserved_bytes" not in ledger:
                raise ValueError("BUDGET_JOURNAL_REQUIRES_NEW_STATE_ROOT")
            key = execution + ":" + stage
            task_id = contract.get("task", {}).get("task_id", execution)
            old = ledger["runs"].get(key)
            if old and old["contract"] != contract:
                raise ValueError("EXECUTION_FINGERPRINT_COLLISION")
            if old and old["status"] == "computed":
                artifact = safe_path(self.evidence, old["artifact"])
                if digest(artifact) != old["sha256"]:
                    raise ValueError("CHECKPOINT_ARTIFACT_CORRUPT")
                value = json.loads(artifact.read_text())
                validate(value)
                return {**old, "cache_hit": True}, value
            budget = estimate(plan, self.policy, self.workspace, self.scratch, self.evidence)
            # A reservation is retained for failed/crashed stages: their partial
            # bytes remain on disk. A retry needs another explicit reservation.
            reserve = budget["peak_incremental_bytes"]
            if ledger["task_reserved_bytes"].get(task_id, 0) + reserve > self.policy["per_task_bytes"]:
                budget["status"] = "budget_exceeded"
                budget["reasons"].append("CUMULATIVE_TASK_DISK_BUDGET_EXCEEDED")
            existing_evidence = sum(r.get("measured_evidence_bytes", 0) for r in ledger["runs"].values()
                                    if r.get("task_id")==task_id and r["status"]=="computed")
            if existing_evidence + plan["evidence_bytes"] > self.policy["evidence_bytes"]:
                budget["status"] = "budget_exceeded"
                budget["reasons"].append("CUMULATIVE_TASK_EVIDENCE_BUDGET_EXCEEDED")
            if ledger["reserved_campaign_bytes"] + reserve > self.policy["campaign_bytes"]:
                budget["status"] = "budget_exceeded"
                budget["reasons"].append("CAMPAIGN_DISK_BUDGET_EXCEEDED")
            if budget["status"] != "ready":
                return {"status": budget["status"], "reason": ";".join(budget["reasons"]), "cache_hit": False, "estimate": budget}, None
            attempt = (old or {}).get("attempt", 0) + 1
            scratch = self.scratch / execution / stage / str(attempt)
            scratch.mkdir(parents=True, exist_ok=False)
            entry = {"contract": contract, "task_id":task_id, "stage": stage, "execution_id": execution,
                     "attempt": attempt, "status": "running", "reason": None,
                     "previous_status": (old or {}).get("status"), "estimate": budget}
            ledger["runs"][key] = entry
            ledger["reserved_campaign_bytes"] += reserve
            ledger["task_reserved_bytes"][task_id] = ledger["task_reserved_bytes"].get(task_id,0) + reserve
            atomic_json(journal, ledger)
            begin = time.monotonic()
            try:
                value = callback(scratch)
                validate(value)
                data_bytes = len(encoded(value))
                measured_scratch = tree_bytes([scratch])
                entry.update(measured_scratch_bytes=measured_scratch, measured_evidence_bytes=data_bytes)
                if measured_scratch + data_bytes > self.policy["per_task_bytes"] or existing_evidence + data_bytes > self.policy["evidence_bytes"]:
                    raise ValueError("MEASURED_DISK_BUDGET_EXCEEDED")
                if measured_scratch > plan["scratch_bytes"] or data_bytes > plan["evidence_bytes"]:
                    raise ValueError("STORAGE_ESTIMATE_UNDERRUN_REQUIRES_REVIEW")
                artifact = f"{execution}/{stage}/{fingerprint(value)}.json"
                target = safe_path(self.evidence, artifact)
                if target.exists() and target.read_bytes() != encoded(value):
                    raise ValueError("ARTIFACT_HASH_COLLISION")
                receipt = atomic_json(target, value, self.policy["evidence_bytes"])
                entry.update(status="computed", reason=None, artifact=artifact, **receipt,
                             scratch_eligible_for_cleanup=True, cache_hit=False)
            except Exception as exc:
                entry.update(status="failed", reason=f"{type(exc).__name__}:{exc}",
                             measured_scratch_bytes=tree_bytes([scratch]), cache_hit=False)
                value = None
            finally:
                entry["duration_seconds"] = time.monotonic()-begin
                atomic_json(journal, ledger)
            return entry, value


def cleanup_plan(scratch_root, owned, manifests, frozen=(), running=(), shared_caches=()):
    """Only a plan. Unknown, linked, frozen and referenced files always excluded.

    owned entries require relative path, sha256, validated=True and
    retention='scratch'. All manifests supplied by the campaign are roots.
    """
    defaults = [Path.home()/".cache/nirs4all-datasets"]
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        defaults.append(Path(os.environ["LOCALAPPDATA"])/"nirs4all-datasets/cache")
    protected = {Path(p).resolve() for p in (*frozen, *running, *shared_caches, *defaults)}
    for manifest in manifests:
        for item in manifest.get("artifacts", []):
            protected.add(safe_path(manifest["local_root"], item["path"]))
    eligible, rejected = [], []
    for item in owned:
        p = safe_path(scratch_root, item["path"])
        reason = None
        if item.get("retention") != "scratch" or item.get("validated") is not True:
            reason = "NOT_VALIDATED_OWNED_SCRATCH"
        elif any(p == q or p.is_relative_to(q) or q.is_relative_to(p) for q in protected):
            reason = "FROZEN_REFERENCED_OR_RUNNING"
        elif any(any(token in part.lower() for token in ("alpha4", "alpha5", "alpha6", "alpha7")) for part in p.parts):
            reason = "HISTORICAL_ALPHA_ARTIFACT"
        elif not p.is_file() or p.stat().st_nlink > 1 or digest(p) != item["sha256"]:
            reason = "MISSING_LINKED_OR_CHANGED"
        else:
            # Resolve has already rejected junction escapes; links inside root
            # remain protected too, including ancestors of the original path.
            original = Path(scratch_root) / item["path"]
            if any(q.is_symlink() or getattr(q.lstat(), "st_file_attributes", 0) & 0x400 for q in (original, *original.parents) if q.exists()):
                reason = "FILESYSTEM_LINK"
        target = {"path": item["path"], "reason": reason}
        (rejected if reason else eligible).append(target)
    return {"mode": "plan_only", "bytes_removed": 0, "eligible": eligible, "rejected": rejected,
            "unknown_files": "never targeted", "shared_caches": "never targeted"}
