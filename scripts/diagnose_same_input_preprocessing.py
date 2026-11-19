"""Quantify public-provider same-input results; never replaces the frozen parity gate."""
import argparse
import hashlib
import json
from pathlib import Path

import check_preprocessing_parity as parity


def verify_phase(wasm, native, request_bytes):
    """Bind both result sequences to each exact requested IEEE input, not to each other alone."""
    request = json.loads(request_bytes)
    digest = hashlib.sha256(request_bytes).hexdigest()
    parity.require(request["protocol_version"] == "domains.f43_same_input_requests.v1" and request["synthetic_only"] is True, "SYNTHETIC_REQUEST_PROTOCOL_REQUIRED")
    parity.require(wasm["protocol_version"] == "domains.f43_same_input_wasm.v1" and native["protocol_version"] == "domains.f43_same_input_native.v1", "RESULT_PROTOCOL_REQUIRED")
    parity.require(wasm["input_sha256"] == native["input_sha256"] == digest, "EXACT_REQUEST_FILE_REQUIRED")
    parity.require(request["provider_version"] == wasm["provider_version"] == native["provider_version"] == parity.VERSION, "PINNED_OWNER_REQUIRED")
    parity.require(wasm["new_real_scientific_fits"] == native["new_real_scientific_fits"] == 0, "REAL_FITS_FORBIDDEN")
    ids = [r["id"] for r in request["requests"]]
    parity.require(len(ids) == len(set(ids)) and ids == [r["id"] for r in wasm["results"]] == [r["id"] for r in native["results"]], "REQUEST_ORDER_CHANGED")

    def wire_bytes(value):
        if isinstance(value, list):
            return b"".join(wire_bytes(item) for item in value)
        parity.require(isinstance(value, str) and len(value) == 16, "F64_HEX_REQUIRED")
        return int(value, 16).to_bytes(8, "little")

    for r, a, b in zip(request["requests"], wasm["results"], native["results"], strict=True):
        expected = {key: hashlib.sha256(wire_bytes(value)).hexdigest() for key, value in r["f64_fields"].items()}
        parity.require(r["operation"] == a["operation"] == b["operation"] and expected == a["input_f64_le_sha256"] == b["input_f64_le_sha256"], "EXACT_IEEE_INPUT_REQUIRED")


def numeric_comparison(left, right):
    errors, maximum, count = [], 0.0, 0

    def walk(a, b, path=""):
        nonlocal maximum, count
        if isinstance(a, bool) or isinstance(b, bool):
            if type(a) is not type(b) or a != b:
                errors.append({"path": path, "kind": "value"})
        elif isinstance(a, (float, int)) and isinstance(b, (float, int)):
            count += 1
            maximum = max(maximum, abs(a - b))
            if not parity.close(a, b):
                errors.append({"path": path, "kind": "numeric", "wasm": a, "native": b, "absolute_error": abs(a-b)})
        elif isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys():
            for key in a:
                walk(a[key], b[key], path + "/" + key)
        elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
            for index, (x, y) in enumerate(zip(a, b, strict=True)):
                walk(x, y, path + "/" + str(index))
        elif a != b or type(a) is not type(b):
            errors.append({"path": path, "kind": "shape_or_value"})

    walk(left, right)
    return {"numeric_count": count, "maximum_absolute_error": maximum, "failures": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    context = parity.read(args.directory / "context.json")
    reports, all_results, inputs = [], {}, {}
    for phase in ("prepare", "extend"):
        request_bytes = (args.directory / (phase + "-requests.json")).read_bytes()
        digest = hashlib.sha256(request_bytes).hexdigest()
        wasm = parity.read(args.directory / (phase + "-wasm.json"))
        native = parity.read(args.directory / (phase + "-native.json"))
        verify_phase(wasm, native, request_bytes)
        inputs[phase] = {"requests_sha256": digest,
                         "wasm_sha256": hashlib.sha256((args.directory / (phase + "-wasm.json")).read_bytes()).hexdigest(),
                         "native_sha256": hashlib.sha256((args.directory / (phase + "-native.json")).read_bytes()).hexdigest(),
                         "native_library_sha256": native["library_sha256"]}
        parity.require([r["id"] for r in wasm["results"]] == [r["id"] for r in native["results"]], "REQUEST_ORDER_CHANGED")
        for a, b in zip(wasm["results"], native["results"], strict=True):
            parity.require(a["operation"] == b["operation"] and a["input_f64_le_sha256"] == b["input_f64_le_sha256"], "EXACT_IEEE_INPUT_REQUIRED")
            item = {"id": a["id"], "operation": a["operation"], "identical_ieee_inputs": True}
            left, right = a["result"], b["result"]
            all_results[a["id"]] = (left, right)
            if a["operation"] == "pca":
                counts = {"numeric": 0}
                try:
                    signs, degenerate = parity.geometry(left["scores"], right["scores"], left["eigenvalues"], a["id"], counts)
                    item["score_gram_at_frozen_tolerance"] = "passed"
                except AssertionError as error:
                    signs, degenerate = [1] * len(left["eigenvalues"]), set()
                    item["score_gram_at_frozen_tolerance"] = str(error)
                item["eigenvalues"] = numeric_comparison(left["eigenvalues"], right["eigenvalues"])
                item["full_moments"] = numeric_comparison(left["full_moments"], right["full_moments"])
                item["resolution"] = numeric_comparison(left["resolution"], right["resolution"])
                item["unresolved_flags_identical"] = left["unresolved"] == right["unresolved"]
                item["components"] = [{"component": j+1, "eigenvalue_wasm": eigen,
                    "unresolved_wasm": left["unresolved"][j], "unresolved_native": right["unresolved"][j],
                    "indistinguishable_at_tolerance": j in degenerate, "sign": signs[j],
                    "coordinate_diagnostic": numeric_comparison([row[j] for row in left["scores"]], [signs[j]*row[j] for row in right["scores"]])}
                    for j, eigen in enumerate(left["eigenvalues"])]
            elif a["operation"] == "preprocess_fit":
                item["backend_local_state"] = {"equality_required_by_diagnostic": False,
                    "wasm_sha256": hashlib.sha256(bytes(left["state_bytes"])).hexdigest(),
                    "native_sha256": hashlib.sha256(bytes(right["state_bytes"])).hexdigest()}
            elif a["operation"] == "preprocess_transform":
                item["matrix"] = numeric_comparison(left["matrix"], right["matrix"])
            else:
                item["owner_outputs"] = numeric_comparison(left, right)
            reports.append(item)
    factor_changes = []
    for entry in context["cases"]:
        for pca in entry["pca"]:
            left, right = all_results[pca["id"]]
            for j, eigen in enumerate(left["eigenvalues"]):
                for measure, key in (("pearson", "coefficient"), ("eta", "eta_squared")):
                    wasm_key = pca["id"] + f"/wasm-scores/pc{j+1}/" + measure
                    native_key = pca["id"] + f"/native-scores/pc{j+1}/" + measure
                    # Both vectors evaluated by the SAME official WASM statistic API.
                    # This measures the consequence of changing PCA scores without a
                    # locally reimplemented correlation or ANOVA calculation.
                    x, y = all_results[wasm_key][0][key], all_results[native_key][0][key]
                    dot = sum(a[j]*b[j] for a, b in zip(left["scores"], right["scores"], strict=True))
                    if measure == "pearson" and y is not None and dot < 0:
                        y = -y
                    factor_changes.append({"pca": pca["id"], "component": j+1, "measure": measure,
                        "eigenvalue": eigen, "unresolved": left["unresolved"][j] or right["unresolved"][j],
                        "comparison": numeric_comparison(x, y)})
    same_score = [r for r in reports if r["operation"] in ("factor_descriptive", "correlation_descriptive")]
    summary = {"requests": len(reports), "provider_calls_per_backend": len(reports), "same_input_hashes_verified": len(reports),
               "same_score_statistic_requests": len(same_score),
               "same_score_statistic_failures": sum(len(r["owner_outputs"]["failures"]) for r in same_score),
               "same_score_statistic_maximum_absolute_error": max(r["owner_outputs"]["maximum_absolute_error"] for r in same_score),
               "resolved_pca_induced_factor_failures": sum(len(r["comparison"]["failures"]) for r in factor_changes if not r["unresolved"])}
    receipt = {"protocol_version": "domains.f43_same_input_attribution.v1", "status": "DIAGNOSTIC_ONLY_NOT_A_PARITY_GATE",
               "provider_version": parity.VERSION, "tolerance": {"absolute": parity.TOLERANCE, "relative": parity.TOLERANCE},
               "original_synthetic_source_sha256": context["source_sha256"], "inputs": inputs,
               "summary": summary, "comparisons": reports, "pca_induced_factor_changes": factor_changes,
               "eigenpair_residuals": {"status": "unavailable", "value": None, "reason": "NOT_EXPOSED_BY_THE_PINNED_PUBLIC_PREFLIGHT_PCA_API"},
               "qualification": "NOT_QUALIFIED; original strict numerical and hash gates remain mandatory",
               "new_real_scientific_fits": 0, "new_scientific_reservations": 0}
    with args.out.open("x", encoding="utf-8") as output:
        json.dump(receipt, output, indent=2, allow_nan=False)
        output.write("\n")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
