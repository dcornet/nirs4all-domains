"""Add exact axis evidence without modifying the first original-source audit."""
import argparse
import csv
import json
from pathlib import Path

from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leaf", type=Path, required=True)
    args = parser.parse_args()
    first = json.loads(Path("docs/benchmarks/alpha10/cartilage-admission.json").read_text())
    source = args.leaf/"X.csv"
    expected = first["derived_source_hashes"]["X.csv"]
    if digest(source) != expected: raise ValueError("FROZEN_DERIVED_SOURCE_CHANGED")
    previous = json.loads(Path(".audit/alpha10/cartilage-audit-receipt.json").read_text())
    contract = {"task": previous["contract"]["task"], "protocol": "domains.alpha10.exact_axis.v0.1",
                "original_audit_sha256": digest("docs/benchmarks/alpha10/cartilage-admission.json"),
                "derived_x_sha256": expected, "runner_sha256": digest(__file__)}
    plan = {"inputs": [{"path": str(source.resolve()), "sha256": expected, "bytes": source.stat().st_size}],
            "scratch_bytes": 0, "evidence_bytes": 4096, "expected_fits": 0, "expected_permutations": 0,
            "uncertainty": "Header-only exact axis digest verification; no spectral or reference numerical computation."}
    store = StageStore("results/alpha9-perten-keyed/state", ".audit/alpha10/scratch", ".audit/alpha10/evidence", Path.cwd(),
                       json.loads(Path("configs/bank/storage-policy-alpha10.json").read_text()))
    def verify(folder):
        with source.open(encoding="utf-8", newline="") as stream:
            header = next(csv.reader(stream, delimiter=";"))
        axis = [float(v) for v in header[1:]]
        sha = fingerprint(axis)
        if header[0] != "observation_id" or len(axis) != 812 or sha != first["original_to_derived"]["axis"]["original_sha256"]:
            raise ValueError("ORIGINAL_DERIVED_AXIS_NOT_IDENTICAL")
        return {"protocol_version": "domains.alpha10.exact_axis.v0.1", "status": "computed", "reason": None,
                "value": {"n_features": len(axis), "exact_full_axis_digest_match": True, "axis_sha256": sha,
                          "derived_x_sha256": expected, "original_mat_sha256": first["source"]["sha256"],
                          "source_audit_sha256": contract["original_audit_sha256"]},
                "interpretation": "The first audit checked rounded labels only. Exact original/derived axis identity is now verified; its non-identical-axis wording was overly conservative.",
                "predictive_admission": "Still pending donor-to-joint and reference-dependency evidence", "test_target_accessed": False}
    receipt, value = store.run(contract, "P1", plan, verify)
    atomic_json(".audit/alpha10/cartilage-axis-receipt.json", receipt)
    if value is None: raise RuntimeError(receipt)
    destination = Path("docs/benchmarks/alpha10/cartilage-axis-verification.json")
    if not destination.exists(): destination.hardlink_to((Path(".audit/alpha10/evidence")/receipt["artifact"]).resolve())
    if digest(destination) != receipt["sha256"]: raise ValueError("EXACT_AXIS_EVIDENCE_CHANGED")
    print(json.dumps({"status": receipt["status"], "exact_full_axis_match": True, "cache_hit": receipt["cache_hit"]}))


if __name__ == "__main__": main()
