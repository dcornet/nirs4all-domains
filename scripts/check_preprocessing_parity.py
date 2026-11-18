#!/usr/bin/env python3
"""Qualify recorded F4.3 outputs; never refit, select a panel or compute a replacement kernel."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

VERSION = "1.3.13+abi.2.20.0"
TOLERANCE = 1e-10


def require(condition, reason):
    if not condition:
        raise AssertionError(reason)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_JSON")))


def canonical(value):
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return {"scalar": value}
    if isinstance(value, (int, float)):
        require(math.isfinite(value), "NONFINITE_NUMBER")
        return {"number": struct.pack(">d", 0.0 if value == 0 else float(value)).hex()}
    if isinstance(value, list):
        return {"array": [canonical(item) for item in value]}
    return {"object": {key: canonical(item) for key, item in sorted(value.items())}}


def fingerprint(value):
    return hashlib.sha256(json.dumps(canonical(value), sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def same(left, right):
    return canonical(left) == canonical(right)


def close(left, right):
    return math.isfinite(left) and math.isfinite(right) and abs(left-right) <= TOLERANCE + TOLERANCE*abs(left)


def indexed(items):
    result = {}
    for item in items:
        require(item["id"] not in result, "DUPLICATE_CASE_ID")
        result[item["id"]] = item
    return result


def project(column, keys):
    result = dict(column)
    values = dict(zip(column["row_keys"], column["values"], strict=True))
    result.update(row_keys=keys, values=[values[key] for key in keys])
    return result


def verify_result(case, previous, label):
    request, result = case["request"], case["result"]
    require(request.get("schema_version") == result.get("schema_version") == 1
            and request.get("protocol_version") == "domains.browser_preprocessing_sensitivity.v1"
            and result.get("protocol_version") == "domains.browser_preprocessing_sensitivity_result.v1"
            and result.get("status") == "computed" and result.get("reason") is None
            and result.get("stage") == request.get("stage") and result.get("population") == request.get("population"),
            label+": protocol/status/stage mismatch")
    unsigned = {key: value for key, value in result.items() if key != "evidence_sha256"}
    require(result["evidence_sha256"] == fingerprint(unsigned), label+": invalid canonical result evidence")
    require(result["dataset"] == request["dataset"] and same(result["plan"], request["plan"]), label+": original parent/plan changed")
    require(result["plan_sha256"] == fingerprint(request["plan"]), label+": plan digest changed")
    keys, query = request["reference_keys"], request["query_keys"]
    raw = request["x"]["matrix"][:len(keys)]
    query_matrix = request["x"]["matrix"][len(keys):]
    reference = {"dataset": request["dataset"], "manifest": request["manifest"], "reference_keys": keys,
                 "axis": request["x"]["axis"], "axis_unit": request["x"]["axis_unit"], "matrix": raw,
                 "factors": request["factors"], "dependencies": [project(c, keys) for c in request["dependencies"]]}
    require(result["reference_input_sha256"] == fingerprint(reference), label+": original reference binding changed")
    numerical_input = {"reference_input_sha256": result["reference_input_sha256"], "plan_sha256": result["plan_sha256"],
                       "stage": request["stage"], "query_keys": query, "query_matrix": query_matrix, "dependencies": request["dependencies"]}
    require(result["input_sha256"] == fingerprint(numerical_input), label+": original input binding changed")
    receipt = result["receipt"]
    require(receipt["provider"] == VERSION and receipt["reference_keys"] == keys and receipt["query_keys"] == query, label+": provider/population changed")
    require(receipt["y_accessed"] is False and receipt["x_predict_accessed"] is False and receipt["test_x_accessed"] == (request["stage"] == "test_audit"), label+": forbidden access")
    if request["stage"] == "test_audit":
        ancestor = case.get("reference_case_id")
        require(ancestor in previous, label+": earlier backend-own reference missing")
        require(same(request["frozen_reference"], previous[ancestor]["result"]), label+": frozen reference is not backend-own ancestor")
        require(receipt["frozen_reference_sha256"] == previous[ancestor]["result"]["evidence_sha256"], label+": frozen evidence link changed")
        require(receipt["query_raw_sha256"] == fingerprint(query_matrix), label+": raw query binding changed")
    else:
        require(request["frozen_reference"] is None and receipt["frozen_reference_sha256"] is None, label+": unexpected frozen reference")
    require([rep["id"] for rep in result["representations"]] == [rep["id"] for rep in request["plan"]["representations"]], label+": requested entries dropped/reordered")
    for spec, rep in zip(request["plan"]["representations"], result["representations"], strict=True):
        require(same(rep["steps"], spec["steps"]) and rep["family"] == spec["family"], label+": preprocessing plan mutated")
        if rep["status"] != "computed":
            require(rep["value"] is None and isinstance(rep["reason"], str), label+": invalid unavailable entry")
            continue
        value = rep["value"]
        source = value["source"]
        suffix = "::f43::"+result["plan_sha256"]+"::"+spec["id"]
        require(source["dataset_id"] == request["dataset"]["dataset_id"]+suffix and source["source_id"] == request["dataset"]["source_id"]+suffix and source["content_version"] == "derived-reference-v1", label+": derived source relabelled")
        axis, matrix_hash = request["x"]["axis"], fingerprint(raw)
        require(value["original_axis_sha256"] == fingerprint(axis), label+": original axis changed")
        require(len(value["transformations"]) == len(spec["steps"]), label+": missing state provenance")
        for step, state in zip(spec["steps"], value["transformations"], strict=True):
            require(state["operator"] == step["operator"] and same(state["parameters"], step["parameters"]), label+": effective operator changed")
            require(state["reference_input_sha256"] == matrix_hash and state["input_axis_sha256"] == fingerprint(axis), label+": stage input binding changed")
            if step["operator"] == "CropTransformer":
                axis = axis[step["parameters"]["start"]:step["parameters"]["end"]]
            require(state["output_axis_sha256"] == fingerprint(axis) and state["output_bands"] == len(axis) and state["state_unchanged_after_transform"] is True, label+": axis/state changed")
            matrix_hash = state["reference_output_sha256"]
        require(value["reference_matrix_sha256"] == matrix_hash and same(value["axis"], axis), label+": terminal reference lineage changed")
        if not spec["steps"]:
            expected_source = fingerprint({"parent": request["dataset"]["content_sha256"], "reference_matrix": raw, "axis": axis, "plan": result["plan_sha256"]})
            require(source["content_sha256"] == expected_source, label+": raw-derived source hash changed")
            if query:
                require(value["query_matrix_sha256"] == fingerprint(query_matrix), label+": raw-derived query hash changed")
        structure = value["structure"]
        if structure["status"] == "computed":
            scope = structure["value"]["report"]["scope"]
            require(all(scope[key] == source[key] for key in ("dataset_id", "source_id", "content_sha256")), label+": diagnostic source identity changed")
            require(scope["n_observations"] == len(keys), label+": diagnostic reference population changed")
        for report in value["factors"]:
            if report["status"] == "computed":
                require(report["receipt"]["dataset"] == source and report["receipt"]["fit_keys"] == keys, label+": factor source/population changed")
        if value["support"]["status"] == "computed":
            inner = value["support"]["value"]["receipt"]
            require(inner["dataset"] == source and inner["fit_keys"] == keys and inner["query_keys"] == query, label+": support source/population changed")
    for call in receipt["provider_calls"]:
        require(set(call["row_keys"]) <= set(keys+query), label+": predict/unknown provider row")
        if call["operation"] in ("preprocess_fit", "pca_fit", "pca", "hdbscan", "factor_descriptive", "correlation_descriptive"):
            if call["operation"] not in ("factor_descriptive", "correlation_descriptive"):
                require(call["row_keys"] == keys, label+": non-reference fit")
        if call["operation"] == "pca_monitor":
            require(call["reference_row_keys"] == keys and call["monitored_row_keys"] == query, label+": monitor scope changed")
        require(call["payload_sha256"] == call["request_sha256"], label+": payload hash aliases differ")
    if "provider_calls" in case:
        require(case["provider_calls"] == len(receipt["provider_calls"]), label+": actual provider count changed")


def gram(rows):
    require(bool(rows) and bool(rows[0]) and all(len(row) == len(rows[0]) for row in rows), "INVALID_SCORE_SHAPE")
    return [[sum(x*y for x, y in zip(a, b, strict=True)) for b in rows] for a in rows]


def compare(left, right, path, count, exclude):
    if exclude(path, left, right):
        return
    if isinstance(left, bool) or isinstance(right, bool):
        require(type(left) is type(right) and left == right, path+": boolean differs")
    elif isinstance(left, (int, float)) and isinstance(right, (int, float)):
        require(left == right if isinstance(left, int) and isinstance(right, int) else close(left, right), path+": numeric disagreement")
        count["numeric"] += 1
    elif isinstance(left, dict):
        require(isinstance(right, dict) and left.keys() == right.keys(), path+": object fields differ")
        for key in sorted(left):
            compare(left[key], right[key], path+"/"+key, count, exclude)
    elif isinstance(left, list):
        require(isinstance(right, list) and len(left) == len(right), path+": array shape differs")
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            compare(a, b, path+f"/{index}", count, exclude)
    else:
        require(type(left) is type(right) and left == right, path+": value/status/reason differs")


def geometry(left, right, energies, path, count):
    require(bool(left) and bool(right) and bool(left[0]) and bool(right[0])
            and len(left) == len(right) and len(left[0]) == len(right[0]) == len(energies)
            and all(math.isfinite(v) and v >= 0 for v in energies), path+": PCA rank differs")
    compare(gram(left), gram(right), path+"/combined_score_gram", count, lambda *_: False)
    signs, degenerate = [], set()
    remaining = set(range(len(energies)))
    while remaining:
        group = {remaining.pop()}
        while True:
            added = {j for j in remaining if any(close(energies[i], energies[j]) for i in group)}
            if not added:
                break
            group.update(added)
            remaining -= added
        if len(group) > 1:
            columns = sorted(group)
            compare(gram([[row[j] for j in columns] for row in left]), gram([[row[j] for j in columns] for row in right]), path+"/degenerate_block_gram/"+str(columns), count, lambda *_: False)
    for index, energy in enumerate(energies):
        if any(other != index and close(energy, value) for other, value in enumerate(energies)):
            degenerate.add(index)
        dot = sum(a[index]*b[index] for a, b in zip(left, right, strict=True))
        sign = 1 if dot >= 0 else -1
        signs.append(sign)
        if index not in degenerate:
            if not all(close(a[index], sign*b[index]) for a, b in zip(left, right, strict=True)):
                count.setdefault("coordinate_diagnostics", []).append(path+f"/PC{index+1}")
    return signs, degenerate


def walk(value, callback):
    if isinstance(value, dict):
        callback(value)
        for item in list(value.values()):
            walk(item, callback)
    elif isinstance(value, list):
        for item in value:
            walk(item, callback)


def align_density(expected, actual, keys, path):
    if expected["status"] != "computed" or actual["status"] != "computed":
        return {}
    a, b = expected["value"]["labels"], actual["value"]["labels"]
    require(len(a) == len(b) == len(keys), path+": density rows differ")
    def clusters(labels):
        return {label: tuple(key for key, value in zip(keys, labels, strict=True) if value == label) for label in set(labels) if label >= 0}
    ac, bc = clusters(a), clusters(b)
    require(set(ac.values()) == set(bc.values()) and [key for key, label in zip(keys, a, strict=True) if label < 0] == [key for key, label in zip(keys, b, strict=True) if label < 0], path+": density partitions differ")
    return {label: next(original for original, members in ac.items() if members == group) for label, group in bc.items()}


def prepare_pair(left, right, request, label, count, conditional):
    a, b = copy.deepcopy(left), copy.deepcopy(right)
    maps = {}
    for index, (ar, br) in enumerate(zip(a["representations"], b["representations"], strict=True)):
        if ar["status"] != "computed" or br["status"] != "computed":
            continue
        av, bv = ar["value"], br["value"]
        report_a = av["structure"].get("value") or {}
        report_b = bv["structure"].get("value") or {}
        pa = report_a.get("report", {}).get("metrics", {}).get("pca", {})
        pb = report_b.get("report", {}).get("metrics", {}).get("pca", {})
        signs, degenerate = [], set()
        if pa.get("status") == pb.get("status") == "computed":
            signs, degenerate = geometry(pa["value"]["scores"], pb["value"]["scores"], pa["value"]["eigenvalues"], label+f"/representations/{index}/pca", count)
        da = report_a.get("report", {}).get("metrics", {}).get("density", {})
        db = report_b.get("report", {}).get("metrics", {}).get("density", {})
        mapping = align_density(da, db, request["reference_keys"], label+f"/{ar['id']}") if da and db else {}
        maps[ar["id"]] = mapping
        def normalize(value):
            if "scores" in value and "eigenvalues" in value and "n_components_resolved" in value:
                value["scores"] = gram(value["scores"])
        walk(av, normalize)
        walk(bv, normalize)
        def normalize_labels(value):
            if all(key in value for key in ("labels", "membership", "persistence", "n_clusters")):
                value["labels"] = [mapping[label] if label >= 0 else label for label in value["labels"]]
                old = value["persistence"]
                value["persistence"] = [old[next(native for native, original in mapping.items() if original == index)] for index in range(len(old))]
        walk(bv, normalize_labels)
        for fa, fb in zip(av["factors"], bv["factors"], strict=True):
            if fa["status"] != "computed" or fb["status"] != "computed":
                continue
            for ca, cb in zip(fa["value"]["factors"], fb["value"]["factors"], strict=True):
                for pc, (sa, sb) in enumerate(zip(ca["components"], cb["components"], strict=True)):
                    va, vb = sa["descriptive"], sb["descriptive"]
                    if va["status"] != "computed" or vb["status"] != "computed":
                        continue
                    for output in (va["value"]["owner_output"], vb["value"]["owner_output"]):
                        require(output["p_value"] is None and output["n_permutations_executed"] == output["n_at_least_observed"] == 0, label+": unexpected factor inference")
                    if pc in degenerate:
                        conditional.append(label+f"/{ar['id']}/factor/{ca['factor_id']}/PC{pc+1}: per-PC statistic non-comparable in a degenerate basis; statuses/counts preserved")
                        for target in (va["value"], vb["value"]):
                            target["estimate"] = "CONDITIONAL_DEGENERATE_BASIS"
                            for field in ("eta_squared", "f_statistic", "coefficient", "n_score_values", "n_distinct_score", "log10_distinct_arrangements"):
                                if field in target["owner_output"]:
                                    target["owner_output"][field] = "CONDITIONAL_DEGENERATE_BASIS"
                    elif pc < len(signs) and signs[pc] < 0 and va["value"]["measure"] in ("pearson_r", "spearman_rho"):
                        vb["value"]["estimate"] *= -1
                        vb["value"]["owner_output"]["coefficient"] *= -1
        projections = [av["support"].get("value", {}).get("projection", {}), bv["support"].get("value", {}).get("projection", {})] if av["support"].get("value") and bv["support"].get("value") else []
        if projections and all(p.get("status") == "computed" for p in projections):
            p, q = [v["value"] for v in projections]
            x, y = p["train_scores"]+p["test_scores"], q["train_scores"]+q["test_scores"]
            energies = [sum(row[j]**2 for row in p["train_scores"]) for j in range(p["components"])]
            orientations, blocks = geometry(x, y, energies, label+f"/{ar['id']}/support", count)
            for value in (p, q):
                value["train_scores"] = gram(value["train_scores"]+value["test_scores"])
                value["test_scores"] = "INCLUDED_IN_COMBINED_SCORE_GRAM"
            for pc, (sa, sb) in enumerate(zip(p["component_summaries"], q["component_summaries"], strict=True)):
                if sa["summary"]["status"] == sb["summary"]["status"] == "computed":
                    if pc in blocks:
                        conditional.append(label+f"/{ar['id']}/support/PC{pc+1}: component summary conditional on a degenerate fitted basis")
                        for target in (sa["summary"], sb["summary"]):
                            for field in ("min", "max", "mean", "sample_sd", "q25", "median", "q75"):
                                target["value"][field] = "CONDITIONAL_DEGENERATE_BASIS"
                    elif orientations[pc] < 0:
                        old = dict(sb["summary"]["value"])
                        for target, original in (("min", "max"), ("max", "min"), ("q25", "q75"), ("q75", "q25"), ("mean", "mean"), ("median", "median")):
                            sb["summary"]["value"][target] = -old[original]
    for ar, br in zip(a["representations"], b["representations"], strict=True):
        if br["status"] != "computed":
            continue
        slot = br["value"]["comparisons"]["clusters"]
        if slot["status"] == "computed" and slot["value"]["cluster_jaccard"]["status"] == "computed":
            v = slot["value"]["cluster_jaccard"]["value"]
            rows, cols = maps.get("raw", {}), maps.get(ar["id"], {})
            ri = [next(k for k, value in rows.items() if value == i) for i in range(len(rows))]
            ci = [next(k for k, value in cols.items() if value == i) for i in range(len(cols))]
            for key in ("jaccard", "intersections"):
                v[key] = [[v[key][i][j] for j in ci] for i in ri]
            v["sizes_a"] = [v["sizes_a"][i] for i in ri]
            v["sizes_b"] = [v["sizes_b"][j] for j in ci]
    return a, b


def exclude_derived_hash(_path, _case, _excluded):
    """Fail closed pending review of explicit, backend-bound hash comparisons."""
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("wasm", "native", "out"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    wasm, native = read(args.wasm), read(args.native)
    require(wasm["protocol_version"] == "domains.browser_preprocessing_sensitivity_wasm.v1" and native["protocol_version"] == "domains.browser_preprocessing_sensitivity_native.v1", "ARTIFACT_PROTOCOL_MISMATCH")
    require(wasm["provider"]["version"] == native["provider_version"] == VERSION, "PINNED_PROVIDER_REQUIRED")
    require(native["wasm_artifact_sha256"] == hashlib.sha256(args.wasm.read_bytes()).hexdigest(), "EXACT_WASM_ARTIFACT_BINDING_REQUIRED")
    require(wasm["fixture_sha256"] == native["fixture_sha256"] and wasm["descriptor_bank_sha256"] == native["descriptor_bank_sha256"], "FIXTURE_OR_BANK_CHANGED")
    require(wasm["new_real_scientific_fits"] == native["new_real_scientific_fits"] == 0, "REAL_FITS_FORBIDDEN")
    wc, nc = indexed(wasm["cases"]), indexed(native["cases"])
    require(list(wc) == list(nc), "CASE_ORDER_OR_IDS_CHANGED")
    count, excluded, conditional, wp, np = {"numeric": 0, "bindings_verified": 0}, [], [], {}, {}
    failures = []
    for identifier, left in wc.items():
        try:
            right = nc[identifier]
            require(same(left["request"], right["original_wasm_request"]), identifier+": recorded original request changed")
            original = {k: v for k, v in left["request"].items() if k != "frozen_reference"}
            actual = {k: v for k, v in right["request"].items() if k != "frozen_reference"}
            require(same(original, actual), identifier+": native raw input/metadata/axis/plan changed")
            require(left.get("reference_case_id") == right.get("reference_case_id"), identifier+": reference ancestor changed")
            verify_result(left, wp, identifier+"/wasm")
            verify_result(right, np, identifier+"/native")
            count["bindings_verified"] += 1
            a, b = prepare_pair(left["result"], right["result"], left["request"], identifier, count, conditional)
            # Only derived hashes are excluded; original parent, plan/reference/input,
            # original/cropped-axis and original M/key hashes remain exact comparisons.
            exclude = lambda path, _x, _y: exclude_derived_hash(path, left, excluded)
            compare(a, b, identifier, count, exclude)
        except AssertionError as error:
            failures.append({"case": identifier, "reason": str(error)})
        wp[identifier], np[identifier] = left, nc[identifier]
    wr, nr = indexed(wasm["refusals"]), indexed(native["refused_before_provider"])
    require(set(wr) == set(nr) and not(set(wr) & set(wc)), "REFUSAL_IDS_CHANGED")
    for identifier, refusal in wr.items():
        other = nr[identifier]
        require(refusal["provider_calls"] == other["provider_calls"] == 0 and refusal["reason"] == other["reason"], identifier+": refusal status/reason/provider count differs")
        require(same(refusal.get("request"), other.get("request")) and refusal.get("request_json") == other.get("request_json"), identifier+": refused original request changed")
    cache_receipts = {}
    for backend, cases in (("wasm", wc), ("native", nc)):
        if "cache-enabled-reference" in cases and "cache-disabled-reference" in cases:
            on, off = cases["cache-enabled-reference"]["result"], cases["cache-disabled-reference"]["result"]
            require(same(on["representations"], off["representations"]), backend+": cached versus uncached reference evidence differs")
            enabled = on["receipt"]["provider_calls"]
            disabled = off["receipt"]["provider_calls"]
            fits_on = sum(c["operation"] == "preprocess_fit" for c in enabled)
            fits_off = sum(c["operation"] == "preprocess_fit" for c in disabled)
            require(on["receipt"]["exact_prefix_cache_hits"] > 0 and off["receipt"]["exact_prefix_cache_hits"] == 0 and fits_on < fits_off and len(enabled) < len(disabled), backend+": cache did not reduce actual owner calls")
            cache_receipts[backend] = {"fits_with_reuse": fits_on, "fits_without_reuse": fits_off, "calls_with_reuse": len(enabled), "calls_without_reuse": len(disabled), "reference_evidence_exactly_equal": True}
    receipt = {"protocol_version": "domains.browser_preprocessing_sensitivity_parity.v1", "status": "failed" if failures else "passed", "failures": failures, "cases": len(wc), "pre_provider_refusals": len(wr), "numeric_comparisons": count["numeric"], "tolerance": {"absolute": TOLERANCE, "relative": TOLERANCE}, "excluded_derived_hash_paths": excluded, "conditional_per_component_paths": conditional, "original_parent_inputs_plans_metadata_axes_compared_exactly": True, "backend_own_reference_and_canonical_evidence_verified": count["bindings_verified"] == len(wc), "pca_comparison": "Score Gram geometry plus per-degenerate-block Gram; eigenvalues/rank/statuses retained; coordinates are diagnostic only and factor statistics stay strict", "partitions": "Exact observation-identity membership with native label/persistence/Jaccard index alignment; no substitute ARI", "state_byte_equality_between_backends_asserted": False, "unexported_transformed_X_and_state_hashes": "Bound by each backend's canonical evidence and stage chain; not independently recomputed from hidden arrays", "provider": VERSION, "new_real_scientific_fits": 0}
    receipt["coordinate_parity_diagnostics"] = count.get("coordinate_diagnostics", [])
    receipt["cache_call_reduction"] = cache_receipts
    receipt["degeneracy_condition"] = "Eigenvalue/score-energy indistinguishability at the frozen parity tolerance; not a new scientific rank estimate. Each indistinguishable block Gram is checked separately."
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        stream.write("\n")
    print(f"Preprocessing parity: {receipt['status']}; {len(wc)} cases, {len(wr)} refusals, {count['numeric']} numerical comparisons, {len(failures)} failed cases")
    if failures:
        for failure in failures:
            print(failure["case"]+": "+failure["reason"])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
