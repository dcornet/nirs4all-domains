"""Compact, content-addressed scientific evidence and estimator-independent suites."""
from __future__ import annotations

import gzip
import io
import json
from pathlib import Path
import zlib

from .storage import digest, encoded, fingerprint, safe_path

PROTOCOL = "domains.bank.v0.1"
TASK_FIELDS = ("dataset_id", "content_version", "dataset_revision", "source_id", "target_id",
               "representation", "split_protocol", "independence_policy", "qualification_protocol")
EXECUTION_FIELDS = ("input_sha256", "source_content_sha256", "split_folds_sha256", "dependency_policy",
                    "preprocessing", "models", "protocol", "binaries", "providers", "settings", "controller_sha256")
PURPOSES = ("candidate_low_structural_dependence", "structure_sensitive_challenge", "transfer_challenge",
            "insufficient_evidence", "not_suitable_for_current_benchmark", "within_population_estimator_comparison")


def task_identity(specification):
    if set(specification) != set(TASK_FIELDS) or any(not specification[k] for k in TASK_FIELDS):
        raise ValueError("COMPLETE_EXPLICIT_BENCHMARK_TASK_REQUIRED")
    return {"schema_version": 1, "task_id": fingerprint(specification), **specification}


def execution_contract(task, specification):
    if set(specification) != set(EXECUTION_FIELDS):
        raise ValueError("COMPLETE_CONTENT_KEYED_EXECUTION_CONTRACT_REQUIRED")
    return {"task": task, "execution": specification}


def compact_tree(value):
    """Remove optional draw/debug payloads; retain statuses, denominators and CIs."""
    if isinstance(value, list):
        return [compact_tree(v) for v in value]
    if isinstance(value, dict):
        return {k:compact_tree(v) for k,v in value.items() if k not in
                ("draws", "lineage", "target_map", "source_component_map", "blocks", "closures", "scopes")}
    return value


def compact_lineage(lineage):
    records = []
    for entry in lineage:
        result = {k:entry[k] for k in ("fold_id", "train_sample_ids", "validation_sample_ids", "n_train_samples", "n_train_components",
                  "n_validation_samples", "n_validation_components", "factor_overlap", "original_training_target_summary",
                  "validation_target_summary_post_evaluation") if k in entry}
        result["full_lineage_sha256"] = fingerprint(entry)
        result["models"] = {}
        for model in ("spectral", "residual", "frozen_alpha6_residual_lineage", "frozen_alpha6_spectral_lineage"):
            if model not in entry:
                continue
            trace = entry[model]
            item = {k:trace[k] for k in ("artifact_sha256", "n_components", "native_fit_lineage_verified", "input_sha256",
                    "outer_intervention_sha256", "selection_engine", "selection_payload_sha256") if k in trace}
            item["inner_folds_sha256"] = fingerprint(trace.get("inner_fold_set"))
            item["fit_events_sha256"] = fingerprint(trace.get("residual_fit_events"))
            item["intervention_scopes"] = [{k:receipt[k] for k in ("attempt", "kind", "factor", "seed", "audit_sha256",
                    "original_target_sha256", "intervened_target_sha256", "changed_target_fraction", "moved_identity_fraction",
                    "effective", "power_reason", "attainable_numerical_vector_assignments") if k in receipt} |
                    {"receipt_sha256":sha, "target_map_sha256":fingerprint(receipt["target_map"]),
                     "training_ids_sha256":fingerprint(receipt["training_ids"])}
                    for sha,receipt in sorted(trace.get("intervention_scopes", {}).items())]
            result["models"][model] = item
        records.append(result)
    return records


def compact_design(value):
    if value is None:
        return None
    return {k:value[k] for k in ("oof", "n_samples", "n_components", "scores", "outer_fold_set", "y_range", "reuse") if k in value} | {
        "lineage":compact_lineage(value.get("lineage", []))}


def compact_stress(report):
    if report["test_target_accessed"]:
        raise ValueError("RETAINED_TEST_TARGET_ACCESS_NOT_ALLOWED")
    experiments = []
    for e in report["experiments"]:
        item = {k:compact_tree(v) for k,v in e.items() if k not in ("value", "size_controls")}
        item["value"] = compact_design(e["value"])
        if "size_controls" in e:
            controls = e["size_controls"]
            item["size_controls"] = {k:compact_tree(v) for k,v in controls.items() if k != "draws"}
            item["size_controls"]["draws"] = []
            for draw in controls["draws"]:
                d = {k:compact_tree(v) for k,v in draw.items() if k not in ("value", "cells")}
                d["value"] = compact_design(draw.get("value"))
                d["cells"] = [{k:compact_tree(v) for k,v in c.items() if k not in ("value", "lineage", "oof")} for c in draw["cells"]]
                item["size_controls"]["draws"].append(d)
        experiments.append(item)
    families = []
    for family in report["interventions"]:
        f = {k:v for k,v in family.items() if k != "attempts"}
        f["attempts"] = [{k:compact_tree(v) for k,v in attempt.items() if k != "value"} |
                         {"value":compact_design(attempt["value"])} for attempt in family["attempts"]]
        families.append(f)
    return {k:compact_tree(report[k]) for k in ("protocol_version", "context", "config", "engine_versions", "target_unit",
                "n_samples", "n_components", "development_input_sha256", "findings", "cluster_derived_prediction", "audit") if k in report} | {
                    "test_target_accessed":False, "experiments":experiments, "interventions":families}


def reject_heavy_payload(value):
    if isinstance(value, dict):
        if set(value) & {"x", "X", "pca_scores", "n4me", "artifact_json", "loadings"} or (
                "artifact_bytes" in value and (type(value["artifact_bytes"]) is not int or value["artifact_bytes"] < 0)):
            raise ValueError("HEAVY_NUMERICAL_PAYLOAD_IN_PERSISTENT_EVIDENCE")
        for child in value.values():
            reject_heavy_payload(child)
    elif isinstance(value, list):
        for child in value:
            reject_heavy_payload(child)


def evidence(task, contract, scientific, qualifications, purposes, limitations, domain="real", status="exploratory", reason=None):
    statuses = ("computed", "exploratory", "inconclusive", "insufficient_information", "not_identifiable", "unavailable", "ineligible", "failed")
    if status not in statuses or (status in ("computed", "exploratory") and reason is not None) or (status not in ("computed", "exploratory") and not reason):
        raise ValueError("INVALID_EVIDENCE_STATUS_REASON")
    if contract["task"] != task or task_identity({k:task[k] for k in TASK_FIELDS}) != task:
        raise ValueError("TASK_CONTRACT_IDENTITY_MISMATCH")
    if not purposes or not set(purposes) <= set(PURPOSES):
        raise ValueError("UNKNOWN_BENCHMARK_PURPOSE")
    if "candidate_low_structural_dependence" in purposes:
        required = ("identity", "xy_signal", "independent_support", "structural_stress", "reviewed_low_dependence_candidate")
        if any(qualifications.get(k) != {"status":"computed", "reason":None, "value":True} for k in required):
            raise ValueError("INSUFFICIENT_EVIDENCE_FOR_LOW_DEPENDENCE_CANDIDATE")
    reject_heavy_payload(scientific)
    result = dict(schema_version=1, protocol_version=PROTOCOL, task_id=task["task_id"],
                  execution_id=fingerprint(contract), task=task, contract=contract, domain=domain,
                  status=status, reason=reason, qualifications=qualifications,
                  purposes=sorted(purposes), scientific=scientific, limitations=limitations)
    result["evidence_id"] = fingerprint(result)
    return result


def verify_evidence(record):
    if record["evidence_id"] != fingerprint({k:v for k,v in record.items() if k != "evidence_id"}):
        raise ValueError("EVIDENCE_CONTENT_DIGEST_MISMATCH")
    reconstructed = evidence(record["task"], record["contract"], record["scientific"], record["qualifications"],
                             record["purposes"], record["limitations"], record["domain"], record["status"], record["reason"])
    if reconstructed != record:
        raise ValueError("EVIDENCE_CONTRACT_MISMATCH")


def select(records, purpose, domain="real"):
    if purpose not in PURPOSES:
        raise ValueError("UNKNOWN_BENCHMARK_PURPOSE")
    for r in records:
        verify_evidence(r)
    selected = sorted([r for r in records if r["domain"] == domain and purpose in r["purposes"]], key=lambda r:r["task_id"])
    if len({r["task_id"] for r in selected}) != len(selected):
        raise ValueError("AMBIGUOUS_EVIDENCE_REVISIONS_REQUIRE_EXPLICIT_SELECTION")
    return selected


def freeze_suite(records, purpose, metric_contract):
    selected = select(records, purpose)
    payload = dict(schema_version=1, protocol_version=PROTOCOL, purpose=purpose,
                   selection_basis="qualification evidence fixed before evaluation of a new estimator",
                   metric_contract=metric_contract,
                   tasks=[{"task_id":r["task_id"], "evidence_id":r["evidence_id"], "evidence_sha256":fingerprint(r),
                           "split_protocol":r["task"]["split_protocol"]} for r in selected])
    return {**payload, "suite_id":fingerprint(payload)}


def verify_storage(manifest, root):
    if manifest["schema_version"] != 1:
        raise ValueError("UNKNOWN_STORAGE_MANIFEST_VERSION")
    seen = set()
    for item in manifest["artifacts"]:
        path = safe_path(root, item["path"])
        if item["path"] in seen or path.stat().st_size != item["bytes"] or digest(path) != item["sha256"]:
            raise ValueError("ARTIFACT_SIZE_DIGEST_OR_IDENTITY_MISMATCH")
        seen.add(item["path"])
    return True


def compressed_archive(data, level=9):
    stream = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=stream, compresslevel=level, mtime=0) as archive:
        archive.write(data)
    compressed = stream.getvalue()
    import hashlib
    return compressed, dict(format="gzip", level=level, mtime=0, filename="", zlib_version=zlib.ZLIB_VERSION,
                            uncompressed_sha256=hashlib.sha256(data).hexdigest(),
                            compressed_sha256=hashlib.sha256(compressed).hexdigest(),
                            uncompressed_bytes=len(data), compressed_bytes=len(compressed))
