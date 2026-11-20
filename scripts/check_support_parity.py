#!/usr/bin/env python3
"""Compare recorded F4.2 native and WASM results without asserting PCA basis identity."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

VERSION = "1.3.13+abi.2.20.0"

HASH_FIELDS = {
    "evidence_sha256", "fit_state_sha256",
}
TOLERANCE = 1e-10


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"non-finite JSON token: {token}")))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


ROTATION_EQUIVALENT_FIXTURES = {"degenerate-all-constant", "isotropic-equal-eigenvalues"}


def compare_value(expected: Any, actual: Any, path: str, counts: dict[str, int], fixture_id: str) -> None:
    if isinstance(expected, bool) or isinstance(actual, bool):
        if expected != actual or type(expected) is not type(actual):
            raise AssertionError(f"{path}: {actual!r} != {expected!r}")
        return
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if isinstance(expected, int) and isinstance(actual, int):
            if expected != actual:
                raise AssertionError(f"{path}: {actual!r} != {expected!r}")
        else:
            e, a = float(expected), float(actual)
            if not math.isfinite(e) or not math.isfinite(a) or abs(a - e) > TOLERANCE + TOLERANCE * abs(e):
                raise AssertionError(f"{path}: {a!r} != {e!r} (abs/rel tolerance {TOLERANCE})")
            counts["numeric"] += 1
        return
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            raise AssertionError(f"{path}: array shape differs")
        for index, (left, right) in enumerate(zip(expected, actual, strict=True)):
            compare_value(left, right, f"{path}/{index}", counts, fixture_id)
        return
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            raise AssertionError(f"{path}: object differs")
        keys = {key for key in expected if key not in HASH_FIELDS}
        actual_keys = {key for key in actual if key not in HASH_FIELDS}
        if path.startswith("provider_calls/") or "/provider_calls/" in path:
            if expected.get("operation") == "summary":
                keys.discard("request_sha256")
                actual_keys.discard("request_sha256")
        if fixture_id in ROTATION_EQUIVALENT_FIXTURES and path.endswith("/projection/value"):
            coordinates = {"train_scores", "test_scores", "components", "display_components", "component_summaries"}
            keys -= coordinates
            actual_keys -= coordinates
        if keys != actual_keys:
            raise AssertionError(f"{path}: object keys differ: {sorted(actual_keys)} != {sorted(keys)}")
        for key in sorted(keys):
            compare_value(expected[key], actual[key], f"{path}/{key}", counts, fixture_id)
        return
    if expected != actual or type(expected) is not type(actual):
        raise AssertionError(f"{path}: {actual!r} != {expected!r}")


def result_by_id(artifact: dict[str, Any], label: str) -> dict[str, dict[str, Any]]:
    reports = artifact.get("reports")
    if isinstance(reports, dict):
        return reports
    cases = artifact.get("cases")
    if isinstance(cases, list):
        return {case["id"]: case["result"] for case in cases}
    raise ValueError(f"{label}: expected reports map or cases array")


def request_by_id(artifact: dict[str, Any]) -> dict[str, Any] | None:
    requests = artifact.get("requests")
    if isinstance(requests, dict):
        return requests
    cases = artifact.get("cases")
    if isinstance(cases, list) and all(isinstance(case, dict) and "request" in case for case in cases):
        return {case["id"]: case["request"] for case in cases}
    return None


def gram(rows: list[list[float]], label: str) -> list[list[float]]:
    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise AssertionError(f"{label}: invalid score matrix")
    return [[sum(x * y for x, y in zip(left, right, strict=True)) for right in rows] for left in rows]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wasm", required=True, type=Path, help="actual WASM protocol output")
    parser.add_argument("--native", required=True, type=Path, help="native replay output keyed by fixture id")
    parser.add_argument("--out", required=True, type=Path, help="parity receipt output")
    parser.add_argument("--provider-version", choices=("1.3.13+abi.2.20.0", "1.5.1+abi.2.24.0"), default="1.3.13+abi.2.20.0")
    args = parser.parse_args()
    global VERSION
    VERSION = args.provider_version

    wasm = read_json(args.wasm)
    native = read_json(args.native)
    if wasm.get("protocol_version") != "domains.browser_train_fitted_support_wasm.v1":
        raise ValueError("unexpected WASM protocol artifact")
    if wasm.get("provider", {}).get("version") != VERSION:
        raise ValueError(f"WASM report does not pin Methods {VERSION}")
    if native.get("protocol_version") != "domains.browser_train_fitted_support_native.v1":
        raise ValueError("unexpected native replay protocol")
    if native.get("provider_version") != VERSION:
        raise ValueError(f"native report does not pin Methods {VERSION}")
    if native.get("pca_refits") != 0 or native.get("new_real_scientific_fits") != 0 or wasm.get("new_real_scientific_fits") != 0:
        raise ValueError("native replay must consume the recorded requests without additional PCA refits")
    if native.get("fixture_sha256") != wasm.get("fixture_sha256"):
        raise ValueError("native replay fixture digest does not match WASM artifact")
    if native.get("wasm_artifact_sha256") != hashlib.sha256(args.wasm.read_bytes()).hexdigest():
        raise ValueError("native replay is not bound to these exact WASM artifact bytes")

    wasm_cases = wasm.get("cases")
    if not isinstance(wasm_cases, list):
        raise ValueError("WASM artifact has no cases array")
    native_results = result_by_id(native, "native")
    native_requests = request_by_id(native)
    if native_requests is None:
        raise ValueError("native replay must preserve exact requests in a requests map or cases array")
    ids = [case["id"] for case in wasm_cases]
    if len(ids) != len(set(ids)) or set(ids) != set(native_results):
        raise ValueError("native and WASM computational fixture ids differ")
    counts = {"numeric": 0}
    for case in wasm_cases:
        identifier = case["id"]
        if identifier not in native_requests or native_requests[identifier] != case["request"]:
            raise AssertionError(f"{identifier}: native replay request differs from the recorded WASM input")
        actual = native_results[identifier]
        if actual.get("protocol_version") != "domains.browser_train_fitted_support_result.v1":
            raise AssertionError(f"{identifier}: native result protocol differs")
        # Ignore only digests tied to runtime serialization/state bytes. Compare the
        # owner outputs, requested/fitted populations, statuses and numerical arrays.
        compare_value(case["result"], actual, identifier, counts, identifier)
        if identifier in ROTATION_EQUIVALENT_FIXTURES:
            left_projection = case["result"]["projection"]["value"]
            right_projection = actual["projection"]["value"]
            left_rows = left_projection["train_scores"] + left_projection["test_scores"]
            right_rows = right_projection["train_scores"] + right_projection["test_scores"]
            compare_value(gram(left_rows, identifier), gram(right_rows, identifier), f"{identifier}/combined_score_gram", counts, identifier)
        wasm_receipt = case["result"]["receipt"]
        native_receipt = actual["receipt"]
        for key in ("fit_keys", "query_keys", "fit_population", "query_population", "x_test_accessed",
                    "y_train_accessed", "y_test_accessed", "x_predict_accessed", "f41_pca_reused"):
            if wasm_receipt[key] != native_receipt[key]:
                raise AssertionError(f"{identifier}/receipt/{key}: population or access differs")
        left_calls = [(call["operation"], call["row_keys"], call["provider_success"]) for call in wasm_receipt["provider_calls"]]
        right_calls = [(call["operation"], call["row_keys"], call["provider_success"]) for call in native_receipt["provider_calls"]]
        if left_calls != right_calls:
            raise AssertionError(f"{identifier}: Methods call order or row scopes differ")

    refusal_ids = {item["id"] for item in wasm.get("refusals", [])}
    native_refusals = native.get("refused_before_provider")
    if not isinstance(native_refusals, list) or any(item.get("provider_calls") != 0 for item in native_refusals):
        raise AssertionError("native pre-provider refusal receipts are required")
    if isinstance(native_refusals, list):
        native_refusals = {item.get("id") if isinstance(item, dict) else item for item in native_refusals}
    else:
        native_refusals = set(native_refusals)
    if not refusal_ids <= native_refusals:
        raise AssertionError("native replay did not preserve every pre-provider refusal")
    receipt = {
        "protocol_version": "domains.browser_train_fitted_support_parity_receipt.v1",
        "status": "passed",
        "cases": len(ids),
        "numeric_comparisons": counts["numeric"],
        "pre_provider_refusals": len(refusal_ids),
        "tolerance": {"absolute": TOLERANCE, "relative": TOLERANCE},
        "universal_pca_basis_identity_asserted": False,
        "rotation_invariant_fixtures": sorted(ROTATION_EQUIVALENT_FIXTURES),
        "well_conditioned_recorded_coordinates_compared": True,
        "cross_runtime_state_or_evidence_digests_compared": False,
        "provider_version": VERSION,
        "new_real_scientific_fits": 0,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Train-fitted support parity: {len(ids)} cases, {counts['numeric']} numeric comparisons, {len(refusal_ids)} pre-provider refusals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
