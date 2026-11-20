"""F4.3 verification v2: independent integrity and exhaustive numeric parity.

Authorized prospective contract: docs/browser/F4_3_FINALIZATION_CONTRACT_V2.md.
The historical v1 comparator and its mathematical rules remain unmodified.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import check_preprocessing_parity as v1

PROTOCOL = "domains.browser_preprocessing_sensitivity_parity.v2"
DERIVED_RESULT_FIELDS = {
    "evidence_sha256", "response_sha256", "receipt_sha256", "scores_sha256",
    "source_pca_evidence_sha256", "source_pca_fit_receipt_sha256",
}


def fingerprint_role(path):
    """An explicit structural registry, not a hash-name wildcard."""
    if path == "/evidence_sha256":
        return "backend_result_integrity"
    if path == "/receipt/frozen_reference_sha256":
        return "backend_own_frozen_ancestor"
    if re.fullmatch(r"/receipt/provider_calls/\d+/(payload|request)_sha256", path):
        return "backend_provider_payload"
    prefix = r"/representations/\d+/value"
    if re.fullmatch(prefix + r"/(reference|query)_matrix_sha256", path):
        return "backend_derived_matrix"
    if re.fullmatch(prefix + r"/transformations/\d+/(state_sha256|reference_input_sha256|reference_output_sha256)", path):
        return "backend_fitted_state_or_stage_matrix"
    if re.fullmatch(prefix + r"/support/value/projection/value/(fit_state_sha256|fit_identity_sha256)", path):
        return "backend_fitted_projection_identity"
    if re.fullmatch(prefix + r"/support/value/receipt/(query_spectra_sha256|train_spectra_sha256|source_request_sha256)", path):
        return "backend_derived_support_request"
    if re.fullmatch(prefix + r"/factors/\d+/receipt/source_pca_input_sha256", path):
        return "backend_derived_pca_input_link"
    if re.match(prefix + r"/(structure|factors|support)/", path):
        field = path.rsplit("/", 1)[-1]
        if field in DERIVED_RESULT_FIELDS:
            return "backend_diagnostic_result"
        if re.fullmatch(prefix + r"/factors/\d+/(receipt|value)/pca_id", path):
            return "backend_pca_evidence_identity"
        if re.fullmatch(prefix + r"/factors/\d+/receipt/request_sha256", path):
            return "backend_factor_request_including_recorded_pca"
        if re.search(r"/provider_calls/\d+/(request|payload)_sha256$", path):
            return "backend_diagnostic_payload"
        if re.search(r"/provider_calls/\d+/(inputs/scores|matrices/(matrix|query|reference|values))/sha256$", path):
            return "backend_diagnostic_array"
    return None


def differences(left, right, path="", failures=None, roles=None, count=None, derived=None):
    failures = [] if failures is None else failures
    roles = [] if roles is None else roles
    count = {"numeric": 0} if count is None else count
    role = fingerprint_role(path)
    if (path.endswith("/content_sha256") and re.match(r"/representations/\d+/value/", path)
            and derived and left in derived[0] and right in derived[1]):
        role = "backend_derived_source_bound_to_own_diagnostics"
    if role:
        v1.require((left is None and right is None) or
                   (isinstance(left, str) and isinstance(right, str) and
                    re.fullmatch(r"[a-f0-9]{64}", left) and re.fullmatch(r"[a-f0-9]{64}", right)),
                   path + ": INVALID_FINGERPRINT_SHAPE")
        roles.append({"path": path, "role": role, "equal": left == right})
        return failures
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            failures.append({"path": path, "reason": "object fields differ"})
        for key in sorted(left.keys() & right.keys()):
            differences(left[key], right[key], path + "/" + key, failures, roles, count, derived)
    elif isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            failures.append({"path": path, "reason": "array dimensions differ", "wasm": len(left), "native": len(right)})
        for i, (a, b) in enumerate(zip(left, right)):
            differences(a, b, path + "/" + str(i), failures, roles, count, derived)
    else:
        try:
            v1.compare(left, right, path, count, lambda *_: False)
        except AssertionError as error:
            failures.append({"path": path, "reason": str(error), "wasm": left, "native": right})
    return failures


def verify_raw(case, previous, label):
    text = case.get("result_json")
    v1.require(isinstance(text, str) and case.get("result_json_sha256") == hashlib.sha256(text.encode()).hexdigest(),
               label + ": RAW_RESULT_INTEGRITY_FAILED")
    v1.require(v1.same(json.loads(text), case["result"]), label + ": RAW_RESULT_SEMANTICS_FAILED")
    v1.verify_result(case, previous, label)
    def validate_roles(value, path=""):
        if fingerprint_role(path):
            nullable = path.rsplit("/", 1)[-1] in {"query_matrix_sha256", "frozen_reference_sha256", "source_pca_fit_receipt_sha256"}
            v1.require(value is None and nullable or isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value), label + path + ": INVALID_FINGERPRINT_SHAPE")
        elif isinstance(value, dict):
            for key, item in value.items():
                validate_roles(item, path + "/" + key)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                validate_roles(item, path + "/" + str(index))
    validate_roles(case["result"])
    for rep in case["result"]["representations"]:
        if rep["status"] != "computed":
            continue
        value = rep["value"]
        v1.require(re.fullmatch(r"[a-f0-9]{64}", value["source"]["content_sha256"]), label + ": INVALID_DERIVED_SOURCE_FINGERPRINT")
        source = (value["structure"].get("value") or {}).get("report", {})
        for factor in value["factors"]:
            if factor["status"] != "computed":
                continue
            receipt = factor["receipt"]
            v1.require(receipt["source_pca_input_sha256"] == source["input_sha256"] and
                       receipt["source_pca_evidence_sha256"] == source["evidence_sha256"], label + ": FACTOR_PCA_SOURCE_BINDING_CHANGED")
            # This public ID hashes strings/ordered keys with serde JSON, not
            # the canonical IEEE fingerprint used by the outer F4.3 result.
            pca_id = hashlib.sha256(json.dumps([source["input_sha256"], source["evidence_sha256"], receipt["fit_keys"]],
                ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
            v1.require(receipt["pca_id"] == factor["value"]["pca_id"] == pca_id and
                       receipt["scores_sha256"] == factor["value"]["scores_sha256"], label + ": FACTOR_PCA_IDENTITY_CHANGED")


def qualify(wasm, native, wasm_sha256):
    v1.require(wasm["protocol_version"] == "domains.browser_preprocessing_sensitivity_wasm.v1" and
               native["protocol_version"] == "domains.browser_preprocessing_sensitivity_native.v1", "ARTIFACT_PROTOCOL_MISMATCH")
    v1.require(wasm["provider"]["version"] == native["provider_version"] == v1.VERSION, "PINNED_PROVIDER_AND_ABI_REQUIRED")
    v1.require(native["wasm_artifact_sha256"] == wasm_sha256, "EXACT_WASM_ARTIFACT_BINDING_REQUIRED")
    for key in ("fixture_sha256", "descriptor_bank_sha256"):
        v1.require(wasm[key] == native[key], "FIXTURE_OR_CATALOG_CHANGED")
    v1.require(wasm["new_real_scientific_fits"] == native["new_real_scientific_fits"] == 0, "REAL_FITS_FORBIDDEN")
    wc, nc = v1.indexed(wasm["cases"]), v1.indexed(native["cases"])
    v1.require(list(wc) == list(nc), "CASE_ORDER_OR_IDENTITIES_CHANGED")
    previous = ({}, {})
    # Validate every original envelope before any normalization or tolerance.
    for key, a in wc.items():
        b = nc[key]
        v1.require(v1.same(a["request"], b["original_wasm_request"]), "ORIGINAL_REQUEST_CHANGED")
        v1.require(v1.same({k: x for k, x in a["request"].items() if k != "frozen_reference"},
                           {k: x for k, x in b["request"].items() if k != "frozen_reference"}), "ORIGINAL_INPUT_CHANGED")
        v1.require(a.get("reference_case_id") == b.get("reference_case_id"), "REFERENCE_ANCESTOR_CHANGED")
        for case, old, backend in ((a, previous[0], "wasm"), (b, previous[1], "native")):
            verify_raw(case, old, key + "/" + backend)
            old[key] = case
    wr, nr = v1.indexed(wasm["refusals"]), v1.indexed(native["refused_before_provider"])
    v1.require(set(wr) == set(nr) and not (set(wr) & set(wc)), "REFUSAL_IDENTITIES_CHANGED")
    for key, a in wr.items():
        b = nr[key]
        v1.require(a["provider_calls"] == b["provider_calls"] == 0 and a["reason"] == b["reason"], "REFUSAL_SEMANTICS_CHANGED")
        v1.require(v1.same(a.get("request"), b.get("request")) and a.get("request_json") == b.get("request_json"), "REFUSED_INPUT_CHANGED")
    failures, roles, conditional, count = [], [], [], {"numeric": 0}
    for key, a in wc.items():
        b = nc[key]
        try:
            left, right = v1.prepare_pair(a["result"], b["result"], a["request"], key, count, conditional)
            derived = tuple({r["value"]["source"]["content_sha256"] for r in c["result"]["representations"] if r["status"] == "computed"} for c in (a, b))
            case_failures, case_roles = [], []
            differences(left, right, failures=case_failures, roles=case_roles, count=count, derived=derived)
            failures.extend({"case": key, **f} for f in case_failures)
            roles.extend({"case": key, **r} for r in case_roles)
        except AssertionError as error:
            failures.append({"case": key, "path": "", "reason": str(error)})
    # Prefix reuse remains an exact within-backend semantic requirement.
    for cases in (wc, nc):
        if "cache-enabled-reference" in cases and "cache-disabled-reference" in cases:
            a, b = (cases[k]["result"] for k in ("cache-enabled-reference", "cache-disabled-reference"))
            v1.require(v1.same(a["representations"], b["representations"]), "CACHE_SEMANTICS_CHANGED")
            fits = lambda r: sum(c["operation"] == "preprocess_fit" for c in r["receipt"]["provider_calls"])
            v1.require(a["receipt"]["exact_prefix_cache_hits"] > 0 and b["receipt"]["exact_prefix_cache_hits"] == 0 and fits(a) < fits(b)
                       and len(a["receipt"]["provider_calls"]) < len(b["receipt"]["provider_calls"]), "CACHE_REUSE_NOT_DEMONSTRATED")
    return {"protocol_version": PROTOCOL, "integrity": "passed", "numeric_parity": "failed" if failures else "passed",
            "status": "failed" if failures else "passed", "cases": len(wc), "pre_provider_refusals": len(wr),
            "numeric_comparisons": count["numeric"], "tolerance": {"absolute": v1.TOLERANCE, "relative": v1.TOLERANCE},
            "failures": failures, "fingerprint_roles": roles, "conditional_per_component_paths": conditional,
            "coordinate_parity_diagnostics": count.get("coordinate_diagnostics", []),
            "scientific_protocol_changed": False, "new_real_scientific_fits": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("wasm", "native", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = qualify(v1.read(args.wasm), v1.read(args.native), hashlib.sha256(args.wasm.read_bytes()).hexdigest())
    except (AssertionError, KeyError, ValueError, TypeError) as error:
        receipt = {"protocol_version": PROTOCOL, "status": "failed", "integrity": "failed", "numeric_parity": "not_evaluated", "reason": str(error)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    receipt["comparator_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    receipt["legacy_rules_source_sha256"] = hashlib.sha256(Path(v1.__file__).read_bytes()).hexdigest()
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")
    print(json.dumps({k: receipt.get(k) for k in ("protocol_version", "status", "integrity", "numeric_parity", "cases", "numeric_comparisons")}) + " failures=" + str(len(receipt.get("failures", []))))
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
