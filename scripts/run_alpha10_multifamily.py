"""Freeze, execute and replay the bounded alpha.10 development comparison."""
import argparse
import json
from pathlib import Path
import time
import os

from nirs4all_domains.dependence import development_rows
from nirs4all_domains.multifamily import freeze_evaluation, compare_design, PROTOCOL
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint
from importlib.metadata import version


def inputs():
    old = json.loads(Path("docs/benchmarks/alpha9/perten-evidence.json").read_text())
    receipts = json.loads(Path("results/alpha9-perten-keyed/stage-receipts.json").read_text())
    p1 = json.loads((Path("results/alpha9-perten-keyed/evidence")/receipts[0]["artifact"]).read_text())
    path = Path("results/alpha9-perten-keyed/scratch")/p1["mean_task_ref"]
    if digest(path) != p1["mean_task_sha256"]:
        raise ValueError("FROZEN_ALPHA9_INPUT_CHANGED")
    return old, path, json.loads(path.read_text())


def immutable(path, value):
    if path.exists():
        if json.loads(path.read_text()) != value:
            raise ValueError("IMMUTABLE_ALPHA10_OUTPUT_DIFFERS:"+str(path))
    else:
        atomic_json(path, value)


def peak_memory():
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [(k, ctypes.c_size_t) for k in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
                "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
        value = Counters()
        value.cb = ctypes.sizeof(value)
        get_process = ctypes.windll.kernel32.GetCurrentProcess
        get_process.restype = wintypes.HANDLE
        read = ctypes.windll.psapi.GetProcessMemoryInfo
        read.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        if not read(get_process(), ctypes.byref(value), value.cb):
            raise OSError("PROCESS_MEMORY_MEASUREMENT_FAILED")
        return value.PeakWorkingSetSize
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024


def provider_contract(spec):
    value = {k: version(k) for k in ("nirs4all-methods", "dag-ml", "numpy", "scipy", "scikit-learn")}
    if spec["engine"] == "nirs4all":
        import nirs4all
        source = Path(nirs4all.__file__).parent/"operators/models/_aom_nirs"
        paths = list((source/"fast").rglob("*.py")) + [source/"pls"/p for p in ("__init__.py", "banks.py", "operators.py", "preprocessing.py")]
        value.update(nirs4all=version("nirs4all"),
                     implementation={p.relative_to(source).as_posix(): digest(p) for p in paths})
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "run", "replay"))
    parser.add_argument("--model")
    parser.add_argument("--library", type=Path)
    args = parser.parse_args()
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        execute(args)


def execute(args):
    root, public = Path("results/alpha10-multifamily"), Path("docs/benchmarks/alpha10")
    root.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)
    config = json.loads(Path("configs/pilots/multifamily-alpha10-v1.json").read_text())
    old, path, task = inputs()
    frozen_path = public/"perten-evaluation.json"
    designs = {d["design_id"]: d["value"]["outer_fold_set"] for d in old["scientific"]["deep"]["experiments"] if d["status"] == "computed"}
    if args.command == "freeze":
        frozen = freeze_evaluation(task, designs, config["models"], old["evidence_id"])
        frozen.update(config_sha256=digest("configs/pilots/multifamily-alpha10-v1.json"),
                      expected_behavior_sha256=digest("docs/ALPHA10_MULTIFAMILY_PROTOCOL.md"))
        frozen.pop("evaluation_id")
        frozen["evaluation_id"] = fingerprint(frozen)
        immutable(frozen_path, frozen)
        print(json.dumps({"evaluation_id": frozen["evaluation_id"], "n_designs": len(designs), "outer_folds": sum(len(f["folds"]) for f in designs.values())}))
        return
    frozen = json.loads(frozen_path.read_text())
    if frozen["config_sha256"] != digest("configs/pilots/multifamily-alpha10-v1.json"):
        raise ValueError("PRESPECIFIED_GRID_CHANGED")
    spec, = [s for s in config["models"] if s["id"] == args.model]
    library = args.library.resolve()
    settings = {"protocol": PROTOCOL, "evaluation_id": frozen["evaluation_id"], "specification": spec,
                "runner_sha256": digest(__file__), "controller_sha256": digest("bridges/python/nirs4all_domains/multifamily.py"),
                "methods_library_sha256": digest(library), "mode": args.command, "providers": provider_contract(spec)}
    # Separate versioned task protocol, same frozen physical/scientific parent.
    task_id = fingerprint([old["task_id"], PROTOCOL, frozen["evaluation_id"]])
    contract = {"task": {"task_id": task_id, "alpha9_parent_task_id": old["task_id"]}, "execution": settings}
    store = StageStore("results/alpha9-perten-keyed/state", root/"scratch", root/"evidence", Path.cwd(),
                       json.loads(Path("configs/bank/storage-policy-alpha10.json").read_text()))
    count = 1
    for values in spec["grid"].values():
        count *= len(values)
    fit_count = sum(len(f["folds"]) for f in designs.values())*(3*count+1)
    plan = {"inputs": [{"path": str(path.resolve()), "sha256": digest(path), "bytes": path.stat().st_size}],
            "scratch_bytes": 65536, "evidence_bytes": 600000, "expected_fits": fit_count, "expected_permutations": 0,
            "uncertainty": "No per-fold X copies; native/NumPy fitted states remain in memory. Four families, serial. Compact scalar/OOF/lineage output."}
    def run(folder):
        began = time.perf_counter()
        baseline_memory = peak_memory()
        out = {}
        for design in designs:
            print("Running "+spec["id"]+" / "+design, flush=True)
            out[design] = compare_design(task, frozen, design, spec, str(library))
            print(json.dumps({"design": design, "status": out[design]["status"], "reason": out[design]["reason"]}), flush=True)
        return {"protocol_version": PROTOCOL, "task_id": task_id, "parent_task_id": old["task_id"],
                "evaluation_id": frozen["evaluation_id"], "specification": spec, "designs": out,
                "wall_seconds": time.perf_counter()-began, "expected_fit_upper": fit_count,
                "memory": {"peak_resident_bytes": peak_memory(), "baseline_process_peak_bytes": baseline_memory,
                           "scope": "OS process lifetime high-water resident memory, including imports; not incremental native allocations"},
                "source_fingerprints": settings, "test_target_accessed": False}
    if args.command == "replay":
        # One exact native or tolerance-qualified adaptive outer scope. Reuses
        # frozen outer/inner identities; no second whole-campaign claim.
        original = json.loads((public/(spec["id"]+".json")).read_text())
        design = next(iter(designs))
        from nirs4all_domains.multifamily import inner_fit
        from nirs4all_domains.storage import encoded
        import numpy as np
        fold = frozen["outer_designs"][design]["folds"][0]
        by_id = {r["physical_sample_id"]: r for r in development_rows(task)}
        def replay(folder):
            fitted, _ = inner_fit([by_id[s] for s in fold["train_sample_ids"]], frozen["inner_designs"][design][fold["fold_id"]], spec, str(library))
            actual = fitted.predict([by_id[s]["x"] for s in fold["validation_sample_ids"]]).reshape(-1).tolist()
            lookup = {r["physical_sample_id"]: r["prediction"] for r in original["designs"][design]["value"]["oof"]}
            expected = [lookup[s] for s in fold["validation_sample_ids"]]
            same = actual == expected if spec["engine"] == "methods" else bool(np.allclose(actual, expected, atol=1e-9, rtol=1e-9))
            if not same:
                raise ValueError("SCOPED_REPLAY_DIFFERS")
            return {"model_id": spec["id"], "fold_id": fold["fold_id"], "n_predictions": len(actual), "equality": "exact" if spec["engine"] == "methods" else "atol=rtol=1e-9", "oof_sha256": fingerprint(actual)}
        plan.update(expected_fits=3*count+1, evidence_bytes=4096)
        receipt, value = store.run(contract, "P1", plan, replay)
        atomic_json(root/(spec["id"]+"-replay-receipt.json"), receipt)
        if value is None:
            raise RuntimeError(receipt)
        immutable(public/(spec["id"]+"-replay.json"), value)
    else:
        receipt, value = store.run(contract, "P3", plan, run)
        atomic_json(root/(spec["id"]+"-receipt.json"), receipt)
        if value is None:
            raise RuntimeError(receipt)
        # New portable byte-identical export shares the immutable stage file.
        destination = public/(spec["id"]+".json")
        if not destination.exists():
            destination.hardlink_to((root/"evidence"/receipt["artifact"]).resolve())
        if digest(destination) != receipt["sha256"]:
            raise ValueError("PORTABLE_EXPORT_DIFFERS")
        print(json.dumps({"status": receipt["status"], "cache_hit": receipt["cache_hit"], "bytes": receipt["measured_evidence_bytes"], "seconds": value["wall_seconds"]}))


if __name__ == "__main__":
    main()
