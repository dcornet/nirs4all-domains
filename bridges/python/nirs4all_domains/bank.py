"""Disk-first bank CLI. Acquisition remains an explicit Datasets-owned P1 action."""
from __future__ import annotations

import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import subprocess

from .storage import StageStore, atomic_json, cleanup_plan, digest, encoded, estimate, fingerprint, safe_path
from .registry import (TASK_FIELDS, compact_stress, evidence, execution_contract, freeze_suite, select,
                       task_identity, verify_evidence, verify_storage)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def schema_check(value, name):
    import jsonschema
    jsonschema.validate(value, read(Path(__file__).with_name(name+".v1.schema.json")))


def file_plan(task, scratch_bytes, evidence_bytes, expected_fits=0, permutations=0):
    path = Path(task)
    return dict(inputs=[{"path":str(path), "sha256":digest(path), "bytes":path.stat().st_size}],
                scratch_bytes=scratch_bytes, evidence_bytes=evidence_bytes,
                expected_fits=expected_fits, expected_permutations=permutations, estimated_seconds=None,
                uncertainty="Native runtime not predicted; byte bounds require post-stage measurement. Input file already present; no acquisition.")


def bounded_qualify(task_path, task_spec, config, policy, *, workspace, state, scratch, output, binary, library, domain="synthetic", admission=None):
    from .dependence import audit_representation, development_rows
    from .split_stress import design_audit, run_experiments
    task = read(task_path)
    if "task_id" in task_spec:
        schema_check(task_spec, "benchmark-task")
        identity = task_identity({k:task_spec[k] for k in TASK_FIELDS})
        if identity != task_spec:
            raise ValueError("BENCHMARK_TASK_ID_DIGEST_MISMATCH")
    else:
        identity = task_identity(task_spec)
    for field in ("dataset_id", "content_version", "source_id", "target_id"):
        if task["context"][field] != identity[field]:
            raise ValueError("INPUT_TASK_CONTEXT_MISMATCH")
    if domain == "real" and (not admission or admission.get("status") != "admitted" or admission.get("task_id") != identity["task_id"] or admission.get("input_sha256") != digest(task_path)):
        raise ValueError("FROZEN_RIGHTS_AND_IDENTITY_ADMISSION_REQUIRED_FOR_NEW_REAL_TASK")
    if admission and "record" in admission:
        from .admission import verify_admission
        verify_admission(admission["record"])
        admitted = admission["record"]
        if admitted["status"] != "admitted" or any(admitted["specification"][k] != identity[k] for k in ("dataset_id", "content_version", "source_id")) or admitted["specification"]["target"]["name"] != identity["target_id"]:
            raise ValueError("ADMISSION_TASK_IDENTITY_MISMATCH")
    if identity["representation"] != "technical_mean" or identity["qualification_protocol"] != "domains.split_stress.v0.1":
        raise ValueError("TASK_MUST_DECLARE_EXECUTED_REPRESENTATION_AND_PROTOCOL")
    schema_check(config, "split-stress-config")
    if version("dag-ml") != "0.3.41" or version("nirs4all-methods") != "1.3.6":
        raise ValueError("QUALIFIED_NATIVE_PROVIDER_VERSIONS_REQUIRED")
    if config["intervention_attempts"] > 19 or len(config["sensitivity_seeds"]) > 1 or config["size_draws"] > 3:
        raise ValueError("ALPHA8_BOUNDED_CAMPAIGN_EXCEEDED")
    scientific_source = [Path(__file__), Path(__file__).with_name("split_stress.py"), Path(__file__).with_name("predictive.py"),
                         Path(__file__).with_name("dependence.py"), Path(__file__).with_name("interventions.py"), Path(__file__).with_name("registry.py"), Path(__file__).with_name("storage.py"), Path(__file__).with_name("admission.py")]
    controller = fingerprint({p.name:digest(p) for p in scientific_source})
    contract = execution_contract(identity, dict(input_sha256=digest(task_path), source_content_sha256=digest(task_path),
        split_folds_sha256=fingerprint({"split_id":task["context"]["split_id"], "config":config,
            "identities":[{k:r.get(k) for k in ("observation_id", "physical_sample_id", "individual_id", "reference_id", "reference_group_id", "independence_group", "partition")} for r in task["observations"]]}),
        dependency_policy=identity["independence_policy"], preprocessing="fold-local centering X/Y; no scaling", models="native PLS + null/group/residual",
        protocol=identity["qualification_protocol"], binaries={"domains":digest(binary), "methods":digest(library)},
        providers={n:version(n) for n in ("dag-ml", "nirs4all-methods", "nirs4all-datasets", "nirs4all-domains-bridge")},
        settings={"config":config, "admission_sha256":fingerprint(admission)}, controller_sha256=controller))
    store = StageStore(state, scratch, output, workspace, policy)
    receipts = []
    def p1(folder):
        audited = audit_representation(task, binary, library, folder)
        rows = development_rows(audited)
        audit = design_audit(rows, config)
        if not any(r["metadata"].get(config["factor"]) for r in rows):
            raise ValueError("NO_OBSERVED_PRESPECIFIED_FACTOR_METADATA")
        return dict(task_id=identity["task_id"], mean_task_ref=(folder/"mean-task.json").relative_to(Path(scratch)).as_posix(),
                    mean_task_sha256=digest(folder/"mean-task.json"), audit_sha256=fingerprint(audit),
                    n_samples=len(rows), n_components=len({r["independence_group"] for r in rows}),
                    test_target_accessed=False)
    p1plan = file_plan(task_path, Path(task_path).stat().st_size*5+1024*1024, 65536)
    receipt, checked = store.run(contract, "P1", p1plan, p1)
    receipts.append(receipt)
    if checked is None:
        return receipts, None
    mean_path = safe_path(scratch, checked["mean_task_ref"])
    if digest(mean_path) != checked["mean_task_sha256"]:
        raise ValueError("P1_REPLAY_INPUT_CACHE_MISMATCH")
    audited = read(mean_path)
    def p2(folder):
        subprocess.run([str(binary), "analyze", str(mean_path), "--out", str(folder/"coverage"), "--methods-library", str(library)], check=True, capture_output=True)
        report = read(folder/"coverage/report.json")
        # Intrinsic source checks remain in Preflight and geometry in Methods.
        return dict(protocol_version=report["protocol_version"],
                    metrics=[{field:value for field,value in metric.items() if field != "provenance"} for metric in report["metrics"]],
                    full_report_sha256=digest(folder/"coverage/report.json"),
                    test_target_accessed=report["test_target_accessed"])
    receipt, moderate = store.run(contract, "P2", file_plan(mean_path, mean_path.stat().st_size*5+1024*1024, 1024*1024, 1), p2)
    receipts.append(receipt)
    if moderate is None:
        return receipts, None
    def p3(folder):
        rows = development_rows(audited)
        report = run_experiments(audited, library, config, design_audit(rows, config))
        return compact_stress(report)
    # A metadata-only audit proves which designs will skip every fit. Account
    # for those explicit unavailable records without reserving fictitious OOFs.
    audit = design_audit(development_rows(audited), config)
    designs = (1 + int(config["shuffle_reference"]) + len(config["sensitivity_seeds"])
               + sum(audit["factor_holdouts"][f]["status"] == "computed" for f in config["holdout_factors"])
               + sum(audit["interventions"][k]["eligible"] for k in config["interventions"])*config["intervention_attempts"])
    # Size controls can have H x R nonempty cells, three orders. Conservative
    # upper bound counts all cells even when matching/admission later fails.
    size_eligible = audit["factor_holdouts"].get(config["factor"], {}).get("status") == "computed"
    cells = config["size_draws"]*config["outer_folds"]**2 if size_eligible else 0
    fits = 2*(designs*config["outer_folds"]+cells)*(config["inner_folds"]*config["max_components"]+1)
    # Empirical conservative envelope from the frozen 65-row/5-fold campaign
    # (2.65 MB compact) and 96-row/4-fold control (258 kB / three designs).
    # Additional conditional size cells are charged separately; overruns fail.
    n = checked["n_samples"]
    deep_upper = 100000 + (n*600+config["outer_folds"]*(5000+n*120))*designs + cells*(5000+n*600)
    receipt, deep = store.run(contract, "P3", file_plan(mean_path, 65536, deep_upper, fits,
                                len(config["interventions"])*config["intervention_attempts"]), p3)
    receipts.append(receipt)
    if deep is None:
        return receipts, None
    def p4(folder):
        unavailable = lambda reason:{"status":"unavailable", "reason":reason, "value":None}
        q = {"identity":{"status":"computed", "reason":None, "value":domain=="synthetic"},
             "xy_signal":unavailable("REQUIRES_SCIENTIFIC_REVIEW_OF_MATCHED_NULL_AND_SPECTRAL_EVIDENCE"),
             "independent_support":unavailable("DECLARED_COMPONENTS_DO_NOT_VERIFY_LABORATORY_INDEPENDENCE"),
             "structural_stress":unavailable("REQUIRES_REVIEW_OF_EFFECTIVE_ATTEMPTS_AND_POWER")}
        return evidence(identity, contract, {"moderate":moderate, "deep":deep}, q, ["insufficient_evidence"],
                        ["Exploratory single-estimator-family evidence; benchmark admission requires scientific review.",
                         "Exact fit scope maps and optional model payloads require authorized input replay."], domain)
    final_payload = p4(None)
    receipt, final = store.run(contract, "P4", file_plan(mean_path, 65536, len(encoded(final_payload))), lambda folder:final_payload,
                               lambda value:(verify_evidence(value), schema_check(value, "qualification-evidence")))
    receipts.append(receipt)
    return receipts, final


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("inventory")
    p.add_argument("--catalog-root", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p = sub.add_parser("estimate")
    p.add_argument("--plan", required=True, type=Path)
    for cmd in (p,):
        for name in ("policy", "workspace", "scratch", "evidence"):
            cmd.add_argument("--"+name, required=True, type=Path)
    p = sub.add_parser("plan-task")
    for name in ("task", "config", "out"):
        p.add_argument("--"+name, required=True, type=Path)
    p = sub.add_parser("qualify")
    for name in ("task", "identity", "config", "policy", "workspace", "state", "scratch", "out", "binary", "library"):
        p.add_argument("--"+name, required=True, type=Path)
    p.add_argument("--domain", choices=("real", "synthetic"), required=True)
    p.add_argument("--admission", type=Path)
    p = sub.add_parser("query")
    p.add_argument("--registry", required=True, type=Path)
    p.add_argument("--purpose", required=True)
    p = sub.add_parser("freeze-suite")
    p.add_argument("--registry", required=True, type=Path)
    p.add_argument("--purpose", required=True)
    p.add_argument("--metrics", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p = sub.add_parser("verify")
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--root", required=True, type=Path)
    p = sub.add_parser("cleanup-plan")
    for name in ("scratch", "owned", "manifests", "running", "frozen", "shared-caches"):
        p.add_argument("--"+name, required=True, type=Path)
    args = parser.parse_args()
    if args.command == "inventory":
        from .inventory import catalog_inventory
        value = catalog_inventory(args.catalog_root)
        atomic_json(args.out, value)
        result = value["counts"]
    elif args.command == "estimate":
        result = estimate(read(args.plan), read(args.policy), args.workspace, args.scratch, args.evidence)
    elif args.command == "plan-task":
        config = read(args.config)
        schema_check(config, "split-stress-config")
        designs = 1+int(config["shuffle_reference"])+len(config["holdout_factors"])+len(config["sensitivity_seeds"])+len(config["interventions"])*config["intervention_attempts"]
        cells = config["size_draws"]*config["outer_folds"]**2
        fits = 1+2*(designs*config["outer_folds"]+cells)*(config["inner_folds"]*config["max_components"]+1)
        result = file_plan(args.task.resolve(), args.task.stat().st_size*10+2*2**20, 4*2**20, fits,
                           len(config["interventions"])*config["intervention_attempts"])
        result["uncertainty"] = "Cooperative whole-task byte envelope; fit count is a prespecified upper bound (PCA plus CV/refit). Blocked folds/attempts can skip fits. No runtime calibration for unacquired data."
        atomic_json(args.out, result)
    elif args.command == "qualify":
        receipts, final = bounded_qualify(args.task, read(args.identity), read(args.config), read(args.policy),
            workspace=args.workspace, state=args.state, scratch=args.scratch, output=args.out,
            binary=args.binary, library=args.library, domain=args.domain, admission=read(args.admission) if args.admission else None)
        result = {"stages":receipts, "evidence_id":final["evidence_id"] if final else None}
    elif args.command in ("query", "freeze-suite"):
        records = [read(p) for p in sorted(args.registry.glob("*.json")) if "evidence_id" in read(p)]
        if args.command == "query":
            result = [{k:r[k] for k in ("task_id", "evidence_id", "purposes")} for r in select(records, args.purpose)]
        else:
            result = freeze_suite(records, args.purpose, read(args.metrics))
            schema_check(result, "benchmark-suite")
            atomic_json(args.out, result)
    elif args.command == "verify":
        value = read(args.manifest)
        schema_check(value, "storage-manifest")
        result = {"verified":verify_storage(value, args.root)}
    else:
        frozen = list(read(args.frozen))
        frozen.extend(str(p.resolve()) for p in Path("results").iterdir() if p.is_dir() and
                      any(token in p.name for token in ("alpha4", "alpha5", "alpha6", "alpha7")))
        frozen.append(str(Path(".audit/datasets").resolve()))
        result = cleanup_plan(args.scratch, read(args.owned), read(args.manifests), frozen, read(args.running), read(args.shared_caches))
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    if isinstance(result, dict) and (result.get("status") in ("budget_exceeded", "insufficient_storage") or
                                    args.command == "qualify" and result.get("evidence_id") is None):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
