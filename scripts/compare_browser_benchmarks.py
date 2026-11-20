"""Compare engineering receipts with exact values and explicit source-binding migration.

Hash encoding reproduces the browser_x.v1 transport contract. No scientific
metric is computed here and no substitute backend result is supplied.
"""
import hashlib
import json
import statistics
import struct
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path

FIXTURE = {"name": "X.csv", "contents": "1000\n1\n2\n3\n"}
SCIENTIFIC_PROTOCOL = "domains.browser_x.v1"
SCOPED_WRAPPER = "domains.browser_scoped_report.v1"
BASELINE_PROVIDER = "1.3.13+abi.2.20.0"
CANDIDATE_PROVIDER = "1.5.0+abi.2.24.0"


def migrated_provider_metadata(value):
    """Change only the declared provider label; retain every scientific value."""
    if isinstance(value, dict):
        return {key: CANDIDATE_PROVIDER if key == "backend_version" and item == BASELINE_PROVIDER
                else migrated_provider_metadata(item) for key, item in value.items()}
    if isinstance(value, list):
        return [migrated_provider_metadata(item) for item in value]
    return value


def migrated_live_report(live):
    """Bind expected provenance/hash changes to otherwise identical evidence."""
    expected = deepcopy(live)
    expected["metrics"] = migrated_provider_metadata(expected["metrics"])
    report = expected["scientific_report"]
    report["metrics"] = migrated_provider_metadata(report["metrics"])
    if report.get("engine_version") == "0.1.0-alpha.17":
        report["engine_version"] = "0.2.0"
    for capability in report.get("capabilities", []):
        if capability.get("reason") == BASELINE_PROVIDER + "; bounded browser protocol":
            capability["reason"] = CANDIDATE_PROVIDER + "; bounded browser protocol"
    evidence = digest(evidence_tree({"scope": report["scope"], "metrics": report["metrics"]}), canonical=True)
    expected["evidence_sha256"] = report["evidence_sha256"] = evidence
    if "evidence_sha256" in report.get("interpretation", {}):
        report["interpretation"]["evidence_sha256"] = evidence
    return expected


def encoded(value, *, canonical=False):
    return json.dumps(value, ensure_ascii=False, sort_keys=canonical,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value, *, canonical=False):
    return hashlib.sha256(encoded(value, canonical=canonical)).hexdigest()


def evidence_tree(value):
    """Exact public Rust evidence-hash encoding, including IEEE-754 number bits."""
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return {"scalar": value}
    if isinstance(value, (int, float)):
        number = float(value)
        return {"number": struct.pack(">d", 0.0 if number == 0 else number).hex()}
    if isinstance(value, list):
        return {"array": [evidence_tree(item) for item in value]}
    if isinstance(value, dict):
        return {"object": {key: evidence_tree(item) for key, item in value.items()}}
    raise AssertionError("Unsupported evidence JSON value")


def verify_rank_one(rank, *, import_route=None):
    assert rank["protocol_version"] == SCIENTIFIC_PROTOCOL
    binding = rank["source_binding"]
    assert binding["fixture"] == FIXTURE, "Benchmark filename and bytes must remain unchanged"
    files = [{"name": FIXTURE["name"], "sha256": hashlib.sha256(FIXTURE["contents"].encode()).hexdigest()}]
    old_content = digest(files)
    request = binding["input"]
    assert request["schema_version"] == 1 and request["axis"] == [1000]
    assert request["group_ids"] is None and len(request["observation_ids"]) == 3
    expected_keys = [json.dumps([request["source_id"], "train", row], separators=(",", ":")) for row in range(3)]
    assert request["observation_ids"] == expected_keys, "Changed or hidden rank-one observations"
    if binding["kind"] == "file_bindings.v1":
        assert import_route in (None, "automatic"), "Legacy binding has an incompatible import route"
        assert binding["import_provenance"] is None and binding["reviewed_spec"] is None
        assert request["content_sha256"] == old_content, "Legacy file binding mismatch"
        assert rank["wrapper_protocol"] == SCIENTIFIC_PROTOCOL and rank["operation"] == "analyze"
        assert rank["population_manifest"] is None
        reviewed_sha = None
    else:
        assert binding["kind"] == "file_bindings_reviewed_spec.v1"
        provenance, spec = binding["import_provenance"], binding["reviewed_spec"]
        assert provenance["protocol"] == "domains.import_xy_m.v1"
        assert len(spec["sources"]) == 1 and spec["sources"][0]["input"] == FIXTURE["name"]
        roles_reviewed = provenance["roles_reviewed"]
        if import_route == "one_shot":
            assert roles_reviewed is False, "Automatic one-shot import must not claim a user role review"
            assert provenance["identity_independence"] == "unknown", "Technical import cannot qualify physical independence"
            source = spec["sources"][0]
            assert source["id"] == request["source_id"], "Automatic source identity disagrees with the scientific request"
            assert provenance["original_source_ids"] == [source["id"]], "Automatic source identities changed"
            assert source["columns"] == {"features": ["1000"]}, "Automatic benchmark must preserve the sole original X band"
            assert not any(spec.get(key) for key in ("aggregate", "repetition", "partitions")), "Automatic benchmark cannot change population or create partitions"
        else:
            assert roles_reviewed is True, "Unreviewed roles require the explicit one-shot import route"
        assert provenance["files"] == files and provenance["file_content_sha256"] == old_content
        reviewed_sha = digest(spec, canonical=True)
        assert provenance["reviewed_spec_sha256"] == reviewed_sha, "Reviewed specification fingerprint mismatch"
        assert request["content_sha256"] == digest({"files": files, "reviewed_spec": spec}, canonical=True), "Reviewed composite binding mismatch"
        assert rank["wrapper_protocol"] == SCOPED_WRAPPER
        assert rank["operation"] == "train_structure"
        assert rank["population_manifest"] == [{"key": key, "partition": "train"} for key in expected_keys], "Rank-one fit must use exactly the three declared training rows"
        assert spec["sources"][0]["partition"] == "train"
    scope = rank["scope"]
    for key in ["dataset_id", "source_id", "content_sha256", "axis_unit"]:
        assert scope[key] == request[key], f"Scientific scope disagrees with actual request: {key}"
    assert scope["n_observations"] == 3 and scope["n_bands"] == 1
    assert scope["axis_sha256"] == digest([1000.0])
    assert scope["observation_ids_sha256"] == digest(expected_keys)
    # BrowserRequest serializes fields in declaration order and f64 values
    # with '.0'. These fixed public values are not a generic JSON codec.
    numerical_input = {"schema_version": 1, "dataset_id": request["dataset_id"],
                       "source_id": request["source_id"], "content_sha256": request["content_sha256"],
                       "observation_ids": expected_keys, "axis": [1000.0],
                       "axis_unit": request["axis_unit"], "spectra": [[1.0], [2.0], [3.0]],
                       "group_ids": None, "prediction_intent": "unknown"}
    assert rank["input_sha256"] == digest(numerical_input), "Scientific input hash is not bound to the recorded request"
    assert rank["evidence_sha256"] == digest(evidence_tree({"scope": scope, "metrics": rank["metrics"]}), canonical=True), "Scientific evidence hash mismatch"
    assert rank["metrics"]["pca"]["value"]["eigenvalues"][0] == 1
    return {"kind": binding["kind"], "wrapper_protocol": rank["wrapper_protocol"],
            "scientific_protocol": rank["protocol_version"], "content_sha256": request["content_sha256"],
            "file_content_sha256": old_content, "reviewed_spec_sha256": reviewed_sha,
            "input_sha256": rank["input_sha256"], "evidence_sha256": rank["evidence_sha256"],
            "roles_reviewed": binding["import_provenance"]["roles_reviewed"] if binding["import_provenance"] else None,
            "import_route": import_route}


def wasm_kind(asset):
    name = asset.lower()
    if "formats" in name:
        return "formats"
    if "io_wasm" in name:
        return "io"
    if "domains" in name:
        return "domains"
    if "methods" in name or "n4m" in name:
        return "methods"
    raise AssertionError(f"Unknown WASM module: {asset}")


def verify_loading(receipt, sample, *, before):
    counts = Counter(wasm_kind(entry["asset"]) for entry in sample["network"])
    scoped = sample["rank_one"]["source_binding"]["kind"] == "file_bindings_reviewed_spec.v1"
    expected = {"io": 2, "domains": 1, "methods": 1} if scoped else {"io": 1, "domains": 1, "methods": 1, **({"formats": 1} if before else {})}
    assert counts == expected, f"Unexpected actual per-stage WASM loads: {dict(counts)}"
    assets = {Path(asset["file"]).name: asset for asset in receipt["assets"]}
    for entry in sample["network"]:
        assert entry["asset"] in assets, "Requested WASM was not inventoried in the served build"
        assert entry["body_bytes"] == assets[entry["asset"]]["bytes"]
    workers = sample["workers"]
    assert [worker["operation"] for worker in workers] == (["prepare_import", "assemble_import", "scoped"] if scoped else ["import", "analyze"])
    first = workers[0]
    assert first["input_bytes"] == len(FIXTURE["contents"].encode())
    if before:
        assert first["transferred_bytes"] == 0
    else:
        assert first["transferred_bytes"] == first["input_bytes"] and first["sender_detached"] is True
    assert all(worker.get("terminated") is not None and any(message["final"] and message["ok"] for message in worker["messages"]) for worker in workers)
    return dict(counts)


def compare(a, b):
    assert a["success"] and b["success"] and a["browser"] == b["browser"] and a["node"] == b["node"]
    assert a["protocol"] == b["protocol"] == "domains.technical_benchmark.v2"
    assert len(a["samples"]) == len(b["samples"]) == 3
    verified, loaded = [], []
    for left, right in zip(a["samples"], b["samples"]):
        original = verify_rank_one(left["rank_one"], import_route=left.get("import_route"))
        reviewed = verify_rank_one(right["rank_one"], import_route=right.get("import_route"))
        assert original["kind"] == "file_bindings.v1"
        before_metrics, after_metrics = left["rank_one"]["metrics"], right["rank_one"]["metrics"]
        assert before_metrics == after_metrics or migrated_provider_metadata(before_metrics) == after_metrics, "CSV scientific values changed"
        assert left["live"] == right["live"] or migrated_live_report(left["live"]) == right["live"], "Matched synthetic report, scientific values or hashes changed"
        for sample in [left, right]:
            scientific = sample["live"]["scientific_report"]
            assert scientific["protocol_version"] == SCIENTIFIC_PROTOCOL
            assert scientific["metrics"] == sample["live"]["metrics"]
            assert scientific["input_sha256"] == sample["live"]["input_sha256"] and scientific["evidence_sha256"] == sample["live"]["evidence_sha256"]
            assert scientific["evidence_sha256"] == digest(evidence_tree({"scope": scientific["scope"], "metrics": scientific["metrics"]}), canonical=True)
        verified.append({"before": original, "after": reviewed})
        loaded.append({"before": verify_loading(a, left, before=True), "after": verify_loading(b, right, before=False)})
    # Repeated same-source runs must remain exact, not merely match each other
    # across versions. No changed declaration/population can enter one repeat.
    for receipt in [a, b]:
        assert all(sample["rank_one"] == receipt["samples"][0]["rank_one"] and sample["live"] == receipt["samples"][0]["live"] for sample in receipt["samples"])
    assert verified.count(verified[0]) == 3 and loaded.count(loaded[0]) == 3
    transition = verified[0]
    rank_hashes_equal = all(transition["before"][field] == transition["after"][field] for field in ["content_sha256", "input_sha256", "evidence_sha256"])
    migrated = transition["after"]["kind"] == "file_bindings_reviewed_spec.v1"
    if migrated:
        assert not rank_hashes_equal and transition["before"]["file_content_sha256"] == transition["after"]["file_content_sha256"]
    else:
        assert rank_hashes_equal, "Unexpected same-protocol binding/hash change"
    keys = ["landing_ms", "import_to_visible_ms", "declaration_edit_ms", "main_thread_script_delta_ms", "layout_delta_ms", "main_thread_heap_sample_bytes", "offline_render_ms"]
    timings = {key: {"before": statistics.median(sample[key] for sample in a["samples"]), "after": statistics.median(sample[key] for sample in b["samples"])} for key in keys}
    for kind in ["json_export", "html_export", "markdown_export"]:
        timings[kind + "_ms"] = {"before": statistics.median(sample[kind]["ms"] for sample in a["samples"]), "after": statistics.median(sample[kind]["ms"] for sample in b["samples"])}
    synthetic_exact = all(left["live"] == right["live"] for left, right in zip(a["samples"], b["samples"]))
    synthetic_hashes_equal = all(left["live"][key] == right["live"][key]
                                 for left, right in zip(a["samples"], b["samples"])
                                 for key in ("input_sha256", "evidence_sha256"))
    return {"protocol": "domains.technical_comparison.v2", "scientific_values_equal": True,
            "same_protocol_hashes_equal": {"synthetic": synthetic_hashes_equal, "rank_one": rank_hashes_equal},
            "scientific_values_and_hashes_equal": rank_hashes_equal and synthetic_hashes_equal,
            "declared_provider_metadata_transition": None if synthetic_exact else {
                "methods_before": BASELINE_PROVIDER, "methods_after": CANDIDATE_PROVIDER,
                "domains_before": "0.1.0-alpha.17", "domains_after": "0.2.0",
                "scientific_values_exact": True, "evidence_hashes_recomputed_and_verified": True},
            "declared_verified_binding_transition": {"verified": True, "kind": "file_bindings_to_reviewed_spec" if migrated else "unchanged_legacy_binding", **transition},
            "synthetic_report_exactly_equal": synthetic_exact,
            "browser": b["browser"], "node": b["node"], "repetitions_each": 3,
            "assets": {"before_bytes": sum(asset["bytes"] for asset in a["assets"]), "after_bytes": sum(asset["bytes"] for asset in b["assets"]),
                       "before_wasm": [asset for asset in a["assets"] if asset["file"].endswith(".wasm")], "after_wasm": [asset for asset in b["assets"] if asset["file"].endswith(".wasm")]},
            "csv_loaded_wasm_modules": {side: sum(counts.values()) for side, counts in loaded[0].items()},
            "csv_wasm_loads_by_module": loaded[0], "csv_workflow_timing_matched": not migrated,
            "medians": timings, "limits": b["measurement_limits"],
            "limits_interpretation": "Limits are capture-time receipt text; the equality fields above report actual values, metadata and hashes after the declared migration.",
            "statistical_significance_or_whole_bank_claimed": False}


def main():
    before, after, output = map(Path, sys.argv[1:])
    result = compare(json.loads(before.read_bytes()), json.loads(after.read_bytes()))
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
