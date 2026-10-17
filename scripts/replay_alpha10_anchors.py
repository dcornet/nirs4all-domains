"""Exact complete frozen PLS/fixed-Ridge replay and measured anchor costs."""
import json
from pathlib import Path
import time

from nirs4all_domains.dependence import development_rows
from nirs4all_domains.predictive import _inner_fit
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint
from run_alpha10_multifamily import inputs, peak_memory


def main():
    from n4m._ffi import library_path
    from threadpoolctl import threadpool_limits
    old, path, task = inputs()
    frozen = json.loads(Path("docs/benchmarks/alpha10/perten-evaluation.json").read_text())
    fixed = json.loads(Path("docs/benchmarks/alpha9/perten-family-comparison.json").read_text())
    designs = {d["design_id"]: d["value"] for d in old["scientific"]["deep"]["experiments"] if d["status"] == "computed"}
    rows = {r["physical_sample_id"]: r for r in development_rows(task)}
    task_id = fingerprint([old["task_id"], "domains.multifamily.v0.1", frozen["evaluation_id"]])
    contract = {"task": {"task_id": task_id}, "settings": {"runner_sha256": digest(__file__),
        "predictive_controller_sha256": digest("bridges/python/nirs4all_domains/predictive.py"),
        "evaluation_id": frozen["evaluation_id"], "library_sha256": digest(library_path())}}
    root = Path("results/alpha10-multifamily")
    store = StageStore("results/alpha9-perten-keyed/state", root/"scratch", root/"evidence", Path.cwd(),
                       json.loads(Path("configs/bank/storage-policy-alpha10.json").read_text()))
    plan = {"inputs": [{"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": digest(path)}],
            "scratch_bytes": 65536, "evidence_bytes": 20000, "expected_fits": 112, "expected_permutations": 0,
            "uncertainty": "Replay all eight frozen outer scopes per anchor; exact OOF comparison, no second report/matrix copies."}
    def replay(folder):
        result = {}
        for family in ("pls", "ridge"):
            output = {}
            for name, baseline in designs.items():
                expected = {r["physical_sample_id"]: r["spectral"] for r in baseline["oof"]} if family == "pls" else {
                    r["physical_sample_id"]: r["ridge"] for r in fixed["designs"][name]["result"]["value"]["oof"]}
                predictions, timings = {}, []
                for fold in frozen["outer_designs"][name]["folds"]:
                    train = [rows[s] for s in fold["train_sample_ids"]]
                    began = time.perf_counter()
                    fitted, trace = _inner_fit(train, library_path(), 17, 3, 3, fold["fold_id"]+":inner", family=family)
                    fit_seconds = time.perf_counter()-began
                    began = time.perf_counter()
                    pred = fitted.predict([rows[s]["x"] for s in fold["validation_sample_ids"]]).reshape(-1).tolist()
                    pred_seconds = time.perf_counter()-began
                    predictions.update(zip(fold["validation_sample_ids"], pred, strict=True))
                    timings.append({"fold_id": fold["fold_id"], "fit_and_selection_seconds": fit_seconds,
                                    "prediction_seconds": pred_seconds, "artifact_sha256": trace["artifact_sha256"]})
                if predictions != expected:
                    raise ValueError("HISTORICAL_ANCHOR_EXACT_REPLAY_DIFFERS:"+family+":"+name)
                output[name] = {"exact_equality": True, "n_predictions": len(predictions), "oof_sha256": fingerprint(predictions), "timings": timings}
            result[family] = output
        return {"protocol_version": "domains.alpha10.anchor_replay.v0.1", "evaluation_id": frozen["evaluation_id"],
                "anchors": result, "peak_process_resident_bytes": peak_memory(), "test_target_accessed": False}
    with threadpool_limits(limits=1):
        receipt, value = store.run(contract, "P1", plan, replay)
    atomic_json(root/"anchors-replay-receipt.json", receipt)
    if value is None: raise RuntimeError(receipt)
    destination = Path("docs/benchmarks/alpha10/anchors-replay.json")
    if not destination.exists(): destination.hardlink_to((root/"evidence"/receipt["artifact"]).resolve())
    if digest(destination) != receipt["sha256"]: raise ValueError("ANCHOR_EXPORT_CHANGED")
    print(json.dumps({"status": receipt["status"], "cache_hit": receipt["cache_hit"], "exact_predictions": 2154, "fit_count": 112}))


if __name__ == "__main__": main()
