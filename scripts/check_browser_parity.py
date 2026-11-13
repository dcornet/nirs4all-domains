"""Compare the same synthetic Domains protocol through native and WASM Methods.

This is an engineering oracle, not a numerical backend: scalar comparisons,
PCA score Gram products and pairwise partition relations are test-only checks.
Signs, rotations in tied PCA eigenspaces and cluster label numbering may vary.
Tolerance is abs+rel 1e-8; statuses, reasons, settings, populations and order are exact.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

ABS_TOL = 1e-8
REL_TOL = 1e-8


def near(left, right, path):
    assert math.isfinite(left) and math.isfinite(right), path
    assert math.isclose(left, right, rel_tol=REL_TOL, abs_tol=ABS_TOL), (path, left, right)


def compare(left, right, path="metrics"):
    if isinstance(left, bool) or left is None or isinstance(left, str):
        assert left == right, (path, left, right)
    elif isinstance(left, (int, float)):
        assert isinstance(right, (int, float)) and not isinstance(right, bool), path
        if isinstance(left, int) and isinstance(right, int):
            assert left == right, (path, left, right)
        else:
            near(left, right, path)
    elif isinstance(left, list):
        assert isinstance(right, list) and len(left) == len(right), path
        for i, (a, b) in enumerate(zip(left, right)):
            compare(a, b, f"{path}/{i}")
    else:
        assert isinstance(left, dict) and isinstance(right, dict) and left.keys() == right.keys(), path
        for key in left:
            compare(left[key], right[key], f"{path}/{key}")


def geometry(left, right, path):
    assert len(left) == len(right), path
    assert all(len(a) == len(b) for a, b in zip(left, right)), path
    for i, a in enumerate(left):
        for j, b in enumerate(left):
            # Test oracle only. No score or fit is emitted from these products.
            near(math.fsum(x*y for x, y in zip(a, b)),
                 math.fsum(x*y for x, y in zip(right[i], right[j])), f"{path}/gram/{i}/{j}")


def partition(left, right, path):
    assert len(left) == len(right), path
    mapping = {}
    for i, (a, b) in enumerate(zip(left, right)):
        assert (a < 0) == (b < 0), (path, "noise", i)
        if a >= 0:
            mapping[a] = b
        for j in range(len(left)):
            assert (a == left[j]) == (b == right[j]), (path, "pair", i, j)
    return mapping


def metrics(native, wasm, name):
    assert native.keys() == wasm.keys(), name
    for key in native:
        a, b = native[key], wasm[key]
        assert (a["status"], a["reason"]) == (b["status"], b["reason"]), (name, key)
        if key == "pca" and a["status"] == "computed":
            a, b = dict(a["value"]), dict(b["value"])
            geometry(a.pop("scores"), b.pop("scores"), f"{name}/pca")
        elif key == "density" and a["status"] == "computed":
            a, b = dict(a["value"]), dict(b["value"])
            mapping = partition(a.pop("labels"), b.pop("labels"), f"{name}/density")
            persistence_a, persistence_b = a.pop("persistence"), b.pop("persistence")
            assert len(persistence_a) == len(persistence_b) == len(mapping)
            for label, target in mapping.items():
                near(persistence_a[label], persistence_b[target], f"{name}/persistence/{label}")
        compare(a, b, f"{name}/{key}")


def versions(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "backend_version":
                assert child == "1.3.13+abi.2.20.0", ("provider_version", child)
            else:
                versions(child)
    elif isinstance(value, list):
        for child in value:
            versions(child)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", required=True, type=Path)
    parser.add_argument("--wasm", required=True, type=Path)
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).resolve().parents[1] / "bindings/wasm/tests/parity-fixtures.json")
    args = parser.parse_args()
    fixture_bytes = args.fixtures.read_bytes()
    fixtures = json.loads(fixture_bytes)
    native, wasm = (json.loads(path.read_bytes()) for path in (args.native, args.wasm))
    fixture_hash = hashlib.sha256(fixture_bytes).hexdigest()
    for result, backend in ((native, "native"), (wasm, "wasm")):
        assert result["schema_version"] == 1 and result["protocol_version"] == "domains.browser_parity.v1"
        assert result["backend"] == backend
        assert result["fixture_file_sha256"] == fixture_hash
        assert result["new_real_scientific_fits"] == 0
        assert set(result["reports"]) == {f["id"] for f in fixtures["fixtures"]}
        versions(result["reports"])
    assert wasm["provider"]["version"] == "1.3.13+abi.2.20.0"
    for fixture in fixtures["fixtures"]:
        name = fixture["id"]
        a, b = native["reports"][name], wasm["reports"][name]
        for report in (a, b):
            assert report["metrics"]["pca"]["status"] == fixture["expected"]["pca_status"]
            expected = fixture["expected"]
            if "pca_reason" in expected:
                assert report["metrics"]["pca"]["reason"] == expected["pca_reason"]
            if "first_eigenvalue" in expected:
                near(report["metrics"]["pca"]["value"]["eigenvalues"][0], expected["first_eigenvalue"], name+"/analytical-eigenvalue")
            if "n_clusters" in expected:
                assert report["metrics"]["density"]["value"]["n_clusters"] == expected["n_clusters"]
            if "rows_with_neighbor" in expected:
                assert report["metrics"]["raw_neighbors"]["value"]["rows_with_neighbor"] == expected["rows_with_neighbor"]
            assert report["scope"]["n_observations"] == len(fixture["input"]["spectra"])
            assert report["scope"]["identity_evidence"] == "observation_identity_only"
            assert report["raw_spectra_included"] is False and report["test_target_accessed"] is False
            assert report["metrics"]["parameter_sensitivity"]["reason"] == "NO_PARAMETER_COMPARISON"
        compare(a["scope"], b["scope"], name+"/scope")
        metrics(a["metrics"], b["metrics"], name)
        compare(a["interpretation"]["boundaries"], b["interpretation"]["boundaries"], name+"/boundaries")
    print(json.dumps({"native_wasm_parity": "passed", "fixtures": len(fixtures["fixtures"]),
                      "abs_tolerance": ABS_TOL, "rel_tolerance": REL_TOL,
                      "pca_score_check": "Gram geometry; signs and tied-subspace rotations ignored",
                      "partition_check": "exact pairwise membership and noise", "new_real_scientific_fits": 0}))


if __name__ == "__main__":
    main()
