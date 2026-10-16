"""Deterministic controlled inputs; this script is test data, not an engine."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def base():
    rows = []
    for partition in ("train", "test"):
        for i, t in enumerate(range(-3, 5)):
            sid = f"{partition}-{i}"
            rows.append({"observation_id": f"o-{sid}", "sample_id": sid,
                         "physical_sample_id": sid, "independence_group": sid,
                         "partition": partition, "x": [float(t), float(2*t), float(1-t)],
                         "y": float(t), "reference_id": f"r-{sid}"})
    return {"schema_version": 1,
            "context": {"dataset_id": "synthetic-controlled", "content_version": "1.0.0",
                        "source_id": "nir", "target_id": "concentration", "split_id": "explicit-v1"},
            "data_origin": "synthetic", "axis": [1100.0, 1200.0, 1300.0],
            "axis_unit": "nm", "signal_unit": "absorbance",
            "policy": {"independence_unit": "physical_sample", "audit_mode": "pre_training", "seed": 17,
                       "pca_max_components": 3, "pca_variance_fraction": 0.95},
            "observations": rows,
            "provenance": {"fixture_generator": "controlled-v1; deterministic; no RNG draws"}}


def scenarios():
    original = base()
    result = {"identical": original}
    for name in ("translation", "variance", "outside_support", "two_clusters", "continuum",
                 "instrument_confounded_y", "technical_repeats", "cross_partition_duplicates",
                 "independent_y", "predictable_y", "target_shift", "insufficient", "target_absent",
                 "orthogonal_shift", "missing_x"):
        task = copy.deepcopy(original)
        train = [r for r in task["observations"] if r["partition"] == "train"]
        test = [r for r in task["observations"] if r["partition"] == "test"]
        if name == "translation":
            for r in test: r["x"] = [v + delta for v, delta in zip(r["x"], [10., 20., -10.])]
        elif name == "orthogonal_shift":
            for r in test: r["x"] = [v + delta for v, delta in zip(r["x"], [20., -10., 0.])]
        elif name == "variance":
            center = [.5, 1., .5]
            for r in test: r["x"] = [c + 2*(v-c) for v, c in zip(r["x"], center)]
        elif name == "outside_support":
            for r in test: r["x"] = [1000., 2000., -999.]
        elif name == "two_clusters":
            for part in (train, test):
                for i, r in enumerate(part):
                    t = (-10. if i < 4 else 10.) + (i % 4)*.01
                    r["x"] = [t, 2*t, 1-t]
        elif name == "instrument_confounded_y":
            for part in (train, test):
                for i, r in enumerate(part):
                    r["metadata"] = {"instrument": "A" if i < 4 else "B"}
                    r["y"] = 0. if i < 4 else 1.
        elif name == "technical_repeats":
            for r in train[:2]:
                r["repetition_type"] = "rescan"
                repeat = copy.deepcopy(r)
                repeat["observation_id"] += "-repeat"
                repeat["x"] = [v + .001 for v in r["x"]]
                task["observations"].append(repeat)
        elif name == "independent_y":
            for i, r in enumerate(train): r["y"] = float(i % 2)
        elif name == "target_shift":
            for r in test: r["y"] += 100.
        elif name == "insufficient":
            task["observations"] = train[:2] + test[:1]
        elif name == "target_absent":
            task["context"]["target_id"] = None
            for r in task["observations"]: r.pop("y", None)
        elif name == "missing_x":
            train[0]["x"][0] = None
        task["context"]["dataset_id"] = f"synthetic-{name}"
        result[name] = task
    return result


if __name__ == "__main__":
    destination = ROOT / "tests/fixtures"
    destination.mkdir(parents=True, exist_ok=True)
    for name, task in scenarios().items():
        (destination / f"{name}.json").write_text(json.dumps(task, indent=2, allow_nan=False)+"\n", encoding="utf-8")
