"""Matched native-metric contrasts and additive registry publication; no model fits."""
from collections import Counter, defaultdict
import itertools
import json
from pathlib import Path

from nirs4all_domains.dependence import state
from nirs4all_domains.multifamily import paired_contrast, PROTOCOL
from nirs4all_domains.registry import (TASK_FIELDS, evidence, execution_contract, freeze_suite,
                                      task_identity, verify_evidence)
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint, tree_bytes
from run_alpha10_multifamily import inputs, immutable


def size_feasibility(rows, designs):
    """Exact whole-context subset-cardinality reachability, without X or Y."""
    by_id = {r["physical_sample_id"]: r for r in rows}
    reference = designs["reference:17"]
    cells, covered = [], set()
    for stress in designs["holdout:cereal_type"]["folds"]:
        target = len(stress["train_sample_ids"])
        for ref in reference["folds"]:
            counts = Counter(by_id[s]["independence_group"] for s in ref["train_sample_ids"])
            reachable = {(0, 0)}
            for count in counts.values():
                reachable |= {(n+count, g+1) for n, g in list(reachable)}
            feasible = any(n == target and g >= 3 for n, g in reachable)
            ids = set(stress["validation_sample_ids"]) & set(ref["validation_sample_ids"])
            if feasible: covered |= ids
            cells.append({"stress_fold": stress["fold_id"], "reference_fold": ref["fold_id"],
                "required_training_samples": target, "reference_training_samples": len(ref["train_sample_ids"]),
                "exact_subset_with_at_least_3_contexts": feasible, "matched_validation_samples": len(ids)})
    return {"method": "Exhaustive integer subset-cardinality reachability over indivisible original contexts; no outcomes",
            "cells": cells, "potential_exact_match_union_samples": len(covered),
            "potential_exact_match_union_components": len({by_id[s]["independence_group"] for s in covered}),
            "new_predictive_controls_executed": False,
            "limitation": "Feasibility is not a size-adjusted performance estimate; any new matching design needs a separate frozen protocol. Original 38-ID/two-block result remains partial."}


def main():
    from nirs4all_domains.dependence import development_rows
    from nirs4all_domains.split_stress import factor_holdout
    public, root = Path("docs/benchmarks/alpha10"), Path("results/alpha10-multifamily")
    old, input_path, task = inputs()
    frozen = json.loads((public/"perten-evaluation.json").read_text())
    alpha9_ridge = json.loads(Path("docs/benchmarks/alpha9/perten-family-comparison.json").read_text())
    old_designs = {d["design_id"]: d["value"] for d in old["scientific"]["deep"]["experiments"] if d["status"] == "computed"}
    models = {p.stem: json.loads(p.read_text()) for p in public.glob("*_v1.json")}
    vectors = {"pls_alpha9": {}, "ridge_fixed_alpha9": {}}
    scores = {}
    def vector(rows, column):
        return [{**{k: r[k] for k in ("physical_sample_id", "component_id", "y")}, "prediction": r[column]} for r in rows]
    for design, data in old_designs.items():
        vectors["pls_alpha9"][design] = vector(data["oof"], "spectral")
        vectors["ridge_fixed_alpha9"][design] = vector(alpha9_ridge["designs"][design]["result"]["value"]["oof"], "ridge")
    for name, result in models.items():
        vectors[name] = {design: value["value"]["oof"] for design, value in result["designs"].items() if value["status"] == "computed"}
    from nirs4all_domains.dependence import score_oof
    for name, designs in vectors.items():
        scores[name] = {d: score_oof(v, "prediction") for d, v in designs.items()}
    rows = development_rows(task)
    closure = factor_holdout(rows, "cereal_type", 3, 3, 17)
    support = {k: closure[k] for k in ("n_closure_units", "n_original_components", "closures", "effective_outer_folds")}
    budget_id = next(iter(models.values()))["task_id"]
    contract = {"task": {"task_id": budget_id}, "execution": {"protocol": PROTOCOL, "evaluation_id": frozen["evaluation_id"],
        "model_evidence_sha256": {name: fingerprint(value) for name, value in models.items()},
        "runner_sha256": digest(__file__), "comparison_controller_sha256": digest("bridges/python/nirs4all_domains/multifamily.py")}}
    store = StageStore("results/alpha9-perten-keyed/state", root/"scratch", root/"evidence", Path.cwd(),
                       json.loads(Path("configs/bank/storage-policy-alpha10.json").read_text()))
    plan = {"inputs": [{"path": str(input_path.resolve()), "sha256": digest(input_path), "bytes": input_path.stat().st_size}],
            "scratch_bytes": 65536, "evidence_bytes": 350000, "expected_fits": 0, "expected_permutations": 0,
            "uncertainty": "Paired frozen OOF component bootstrap, 100 draws; native RMSE only, no refitting or matrices."}
    def calculate(folder):
        degradation, interaction, null_gain = {}, {}, {}
        reference, stresses = "reference:17", ("holdout:cereal_type", "holdout:instrument")
        for name, data in vectors.items():
            degradation[name] = {stress: paired_contrast([data[stress], data[reference]], [1, -1]) for stress in stresses}
            null_gain[name] = {design: paired_contrast([vector(old_designs[design]["oof"], "null"), values], [1, -1]) for design, values in data.items()}
        for a, b in itertools.combinations(vectors, 2):
            interaction[a+" minus "+b] = {stress: paired_contrast([vectors[a][stress], vectors[a][reference],
                vectors[b][stress], vectors[b][reference]], [1, -1, -1, 1]) for stress in stresses}
        return {"protocol_version": PROTOCOL, "evaluation_id": frozen["evaluation_id"], "scores": scores,
            "degradations": degradation, "estimator_by_split_interactions": interaction, "gain_over_matched_null": null_gain,
            "cereal_support": support, "size_matching_feasibility": size_feasibility(rows, frozen["outer_designs"]),
            "unseen_cereal_uncertainty": state(reason="ONLY_TWO_CEREAL_CLOSURE_UNITS"),
            "refitted_model_or_repeated_design_uncertainty": state(reason="ONLY_FROZEN_OOF_CONDITIONAL_BOOTSTRAP_EXECUTED"),
            "low_structural_dependence": state(reason="UNRESOLVED_DEPENDENCIES;UNDERPOWERED_CEREAL_SUPPORT;UNAVAILABLE_INTERVENTIONS"),
            "test_target_accessed": False}
    receipt, summary = store.run(contract, "P4", plan, calculate)
    atomic_json(root/"summary-receipt.json", receipt)
    if summary is None: raise RuntimeError(receipt)
    destination = public/"perten-summary.json"
    if not destination.exists(): destination.hardlink_to((root/"evidence"/receipt["artifact"]).resolve())
    if digest(destination) != receipt["sha256"]: raise ValueError("SUMMARY_EXPORT_DIFFERS")
    # Bank identity and stage-budget identity are separate explicit contracts.
    # The stage key groups the bounded protocol responses; bank identity carries
    # all standard dataset/content/source/target/split/independence fields.
    spec = {k: old["task"][k] for k in TASK_FIELDS}
    spec["qualification_protocol"] = PROTOCOL+":"+frozen["evaluation_id"]
    new_task = task_identity(spec)
    settings = old["contract"]["execution"].copy()
    settings.update(models=frozen["specifications"], protocol=PROTOCOL, preprocessing="Prespecified raw, native SNV and adaptive raw/SNV operator candidates",
                    input_sha256=digest(input_path), split_folds_sha256=fingerprint(frozen["outer_designs"]),
                    providers={"Methods": "1.3.6 / ABI 2.19", "DAG-ML": "0.3.41", "nirs4all": "1.4.10", "NumPy": "2.4.6", "SciPy": "1.17.1", "sklearn": "1.7.2"},
                    settings={"frozen_evaluation_id": frozen["evaluation_id"], "parent_task_id": old["task_id"], "stage_budget_task_id": budget_id},
                    controller_sha256=digest("bridges/python/nirs4all_domains/multifamily.py"))
    qualification = {"identity": state(True), "xy_signal": state(True), "independent_support": state({"observed_contexts": 17, "unseen_cereal_closures": 2}),
                     "structural_stress": state("Matched frozen designs; estimator-specific response, limited independent category support"),
                     "reviewed_low_dependence_candidate": state(reason="NOT_QUALIFIED")}
    refs = {p.name: {"sha256": digest(p), "bytes": p.stat().st_size} for p in public.glob("*.json") if p.name in (
        "perten-evaluation.json", "perten-summary.json", "size-control-evaluation.json", "size-control-results.json", *[name+".json" for name in models])}
    record = evidence(new_task, execution_contract(new_task, settings),
        {"parent_alpha9_task_id": old["task_id"], "parent_alpha9_evidence_id": old["evidence_id"],
         "membership_frozen_before_new_scores": {"evaluation_id": frozen["evaluation_id"], "original_tasks": [old["task_id"]]},
         "artifacts": refs, "response_dimensions": ["estimator_family", "hyperparameter_selection", "preprocessing", "split_sensitivity"],
         "availability": {"conditional_component_interactions": "computed", "unseen_cereal_uncertainty": "unavailable", "causal_shortcut_probability": "not_identifiable"}},
        qualification, ["structure_sensitive_challenge", "within_population_estimator_comparison"],
        ["Two cereal closure units; conditional specimen-context bootstrap does not estimate new-cereal generalization.",
         "Original assay/farm/donor dependencies may be unknown; no low-dependence certification.",
         "Different candidate budgets and upstream adaptive fitting protocols; no claim of equal search effort or chemical causality."])
    verify_evidence(record)
    # Consolidation metadata is finalized before the first alpha.10 publication;
    # every executed stage artifact and prior alpha.4–alpha.9 record is preserved.
    atomic_json(public/"perten-evidence.json", record)
    for purpose, name, members in (("within_population_estimator_comparison", "within-population-suite.json", [record]),
                                   ("structure_sensitive_challenge", "structure-challenge-suite.json", [record, json.loads(Path("docs/benchmarks/alpha8/ecosis-evidence.json").read_text())]),
                                   ("candidate_low_structural_dependence", "low-dependence-candidate-suite.json", [record]),
                                   ("transfer_challenge", "transfer-suite.json", [record])):
        atomic_json(public/name, freeze_suite(members, purpose, {"primary": "task-wise RMSE in original units",
            "membership_basis": "Pre-score alpha.10 evaluation manifest for Perten; unchanged earlier EcoSIS qualification",
            "no_cross_task_raw_rmse_average": True, "comparison_evidence_after_execution": True}))
    sidecar = {"schema_version": 1, "integration_protocol": "domains.datasets_sidecar.v0.1", "dataset_id": new_task["dataset_id"],
        "content_version": new_task["content_version"], "task_id": new_task["task_id"], "qualification_protocol": spec["qualification_protocol"],
        "evidence_sha256": fingerprint(record), "evidence_ref": "perten-evidence.json", "purposes": record["purposes"]}
    atomic_json(public/"datasets-sidecar.json", sidecar)
    artifacts = [{"path": p.name, "sha256": digest(p), "bytes": p.stat().st_size, "retention": "essential_evidence"} for p in sorted(public.glob("*.json")) if p.name != "storage.json"]
    manifest = {"schema_version": 1, "protocol_version": "domains.storage.v0.1", "execution_id": record["execution_id"], "artifacts": artifacts,
        "cache_dependencies": [{"content_sha256": digest(input_path), "bytes": input_path.stat().st_size, "provider": "Frozen alpha.9 Perten admitted input", "access": "public", "local_locator_key": "perten-alpha9-mean-task"}],
        "replay_grade": "reconstructed_from_cache", "measured_bytes": sum(a["bytes"] for a in artifacts), "optional_archives": [],
        "limitations": ["Models require pinned upstream providers/source and authorized original data; compact evidence contains no X or serialized models.", "Native exact anchor replay and adaptive tolerance replay have different contracts."]}
    atomic_json(public/"storage.json", manifest)
    print(json.dumps({"task_id": record["task_id"], "evidence_id": record["evidence_id"], "portable_bytes": manifest["measured_bytes"],
                      "whole_context_size_match_feasibility": summary["size_matching_feasibility"]}))


if __name__ == "__main__": main()
