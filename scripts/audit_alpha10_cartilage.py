"""Original MAT identity/reference audit; no predictive fit or canonical mutation."""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path

from nirs4all_domains.dependence import state
from nirs4all_domains.original_keys import cartilage_keys, dependency_closure, full_population_cost
from nirs4all_domains.predictive import native_summary
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leaf", type=Path, required=True)
    args = parser.parse_args()
    root = Path(".audit/alpha10")
    origin = json.loads((root/"cartilage-origin.json").read_text())
    path = Path(origin["relative_path"])
    if digest(path) != origin["sha256"]:
        raise ValueError("ORIGINAL_MAT_CHANGED")
    receipt = json.loads((root/"cartilage-acquisition-receipt.json").read_text())
    contract = {**receipt["contract"], "audit_sha256": digest(__file__),
                "identity_adapter_sha256": digest("bridges/python/nirs4all_domains/original_keys.py"),
                "derived_source_hashes": {name: digest(args.leaf/name) for name in ("X.csv", "Y.csv", "M.csv", "source_to_standard.py")}}
    inputs = [path, *[args.leaf/name for name in ("X.csv", "Y.csv", "M.csv")]]
    plan = {"inputs": [{"path": str(p.resolve()), "sha256": digest(p), "bytes": p.stat().st_size} for p in inputs],
            "scratch_bytes": 65536, "evidence_bytes": 700000, "expected_fits": 0, "expected_permutations": 0,
            "uncertainty": "Decode original MAT in memory; exact keyed float32 transport comparison; no X copies or predictions."}
    store = StageStore("results/alpha9-perten-keyed/state", root/"scratch", root/"evidence", Path.cwd(),
                       json.loads(Path("configs/bank/storage-policy-alpha10.json").read_text()))
    def audit(folder):
        import numpy as np
        import pandas as pd
        from scipy.io import loadmat
        from nirs4all_domains.storage import encoded
        import hashlib
        dataset = loadmat(path, struct_as_record=False, squeeze_me=True)["dataset"]
        records, original_x, target, axis = [], {}, [], None
        for item in dataset:
            key = str(item.sample_id)
            x = np.asarray(item.raw_spectra)
            wave = np.asarray(item.wavelength).reshape(-1)
            if x.ndim != 2 or x.shape[1] != len(wave) or not np.isfinite(x).all() or not np.isfinite(wave).all():
                raise ValueError("INVALID_ORIGINAL_SPECTRUM_AXIS")
            if axis is not None and not np.array_equal(wave, axis):
                raise ValueError("ORIGINAL_LOCATIONS_HAVE_DIFFERENT_AXES")
            axis = wave
            # Original within-location acquisition index is explicit MAT
            # structure membership, never an X/Y table-position join.
            acquisitions = [f"{key}:mat-spectrum:{i+1}" for i in range(x.shape[0])]
            records.append({"sample_id": key, "joint_id": int(item.joint_id), "area_of_interest_id": str(item.area_of_interest_id),
                            "measurement_point_id": int(item.measurement_point_id), "donor_id": None,
                            "reference_key": key+":OCT-thickness", "acquisition_keys": acquisitions})
            original_x[key] = Counter(hashlib.sha256(row.astype("<f4").tobytes()).hexdigest() for row in x)
            value = float(item.cartilage_thickness)
            if math.isfinite(value): target.append(value)
        keys = cartilage_keys(records)
        closure = dependency_closure(keys)
        metadata = pd.read_csv(args.leaf/"M.csv", sep=";", dtype=str).to_dict("records")
        x = pd.read_csv(args.leaf/"X.csv", sep=";")
        y_columns = list(pd.read_csv(args.leaf/"Y.csv", sep=";", nrows=0).columns)
        if "observation_id" not in x or len(set(x.observation_id)) != len(x):
            raise ValueError("DERIVED_X_MISSING_OR_DUPLICATE_OBSERVATION_KEYS")
        m = {r["observation_id"]: r for r in metadata}
        if len(m) != len(metadata) or set(x.observation_id) != set(m):
            raise ValueError("DERIVED_X_METADATA_KEY_MISMATCH")
        canonical = defaultdict(Counter)
        for row in x.itertuples(index=False, name=None):
            oid, values = row[0], np.asarray(row[1:], dtype="<f4")
            key = m[oid]["sample_id"]
            if key not in original_x:
                raise ValueError("DERIVED_SAMPLE_KEY_ABSENT_FROM_ORIGINAL")
            canonical[key][hashlib.sha256(values.tobytes()).hexdigest()] += 1
        matches = sorted(k for k in original_x if canonical[k] == original_x[k])
        axis_headers = list(x.columns)[1:]
        rounded_axis_matches = all(float(h) == round(float(w), 2) for h, w in zip(axis_headers, axis, strict=True))
        region_counts = Counter(r["region_id"] for r in keys)
        joint_counts = Counter(r["joint_id"] for r in keys)
        n_acq = sum(len(r["acquisition_keys"]) for r in keys)
        return {"protocol_version": "domains.alpha10.cartilage_admission.v0.1", "status": "pending",
            "source": {**origin["source"], "sha256": origin["sha256"], "provider": origin["provider"]},
            "derived_source_hashes": contract["derived_source_hashes"],
            "original_identity_evidence": {"status": "computed", "reason": None,
                "value": {"locations": len(keys), "acquisitions": n_acq, "features": len(axis),
                          "location_replication": dict(Counter(len(r["acquisition_keys"]) for r in keys)),
                          "joint_counts": dict(joint_counts), "region_counts": dict(region_counts), "keys": keys,
                          "joint_donor_field_present": False, "mat_fields": list(dataset[0]._fieldnames)}},
            "declared_dependency_closure": closure,
            "original_to_derived": {"spectral_membership": state({"locations_exact_float32_multiset_match": len(matches),
                "total_locations": len(keys), "all_original_locations_present": set(canonical) == set(original_x),
                "mismatched_location_keys": sorted(set(original_x)-set(matches)), "join": "X.observation_id -> M.observation_id -> original MAT sample_id; within-location spectra compared as multisets"}),
                "axis": {"original_sha256": fingerprint(axis.tolist()), "original_nm_range": [float(axis[0]), float(axis[-1])],
                         "derived_headers_match_original_rounded_2_decimals": rounded_axis_matches,
                         "equivalence": "Original axis retained; rounded derived labels are not an identical full-precision axis"},
                "target_alignment": state(reason="DERIVED_Y_HAS_NO_OBSERVATION_OR_ORIGINAL_LOCATION_KEY;_POSITIONAL_JOIN_REFUSED"),
                "original_reference_adapter": state("MAT element sample_id directly owns cartilage_thickness; no table join required"),
                "derived_y_columns": y_columns},
            "reference": {"name": "cartilage_thickness", "unit": "mm", "method": "OCT non-calcified layer",
                          "complete_locations": len(target), "summary": native_summary(target),
                          "assay_event_ids": state(reason="ONLY_LOGICAL_LOCATION_REFERENCE_KEYS;ORIGINAL_EVENT_IDS_NOT_PROVIDED"),
                          "precision": "Paper reports OCT axial resolution <20 micrometres; not an independent assay SD"},
            "full_population_feasibility": full_population_cost(len(keys), n_acq, len(axis)),
            "weak_prediction_hypotheses": {"incorrect_mapping": "Original keyed MAT resolves X/reference ownership; derived unkeyed Y remains unqualified, not proven erroneous",
                "reference_reuse_or_precision": "Replicates share one location-level reference; assay-event reuse beyond location is unknown",
                "biological_dependence": "Five declared joints, 44 regions; joint-to-animal mapping absent; independent donor count not identifiable",
                "dynamic_range": "Native descriptive target summary supplied; no causal explanation of predictive difficulty",
                "representation": "Original raw axis extends beyond the paper analysis window; no unqualified crop/interpolation or preprocessing-equivalence assumption",
                "grouped_split": "Location CV and joint/donor transfer are different; original MATLAB example uses ordinary CV, not a Domains qualification",
                "weak_information_or_misspecification": "Unavailable until a prespecified original-source task passes dependency admission"},
            "predictive_qualification": state(reason="DONOR_TO_JOINT_RELATIONSHIP_AND_REFERENCE_DEPENDENCIES_REQUIRE_SOURCE_CONFIRMATION", status="not_identifiable"),
            "scientific_sources": ["https://doi.org/10.1038/s41597-019-0170-y", "https://doi.org/10.6084/m9.figshare.7803845.v2",
                "https://github.com/uef-bbc/sarin-scientific-data-2019/tree/10e3d789d374f630199199cfc4a0f6954286b02b"],
            "no_predictive_fit": True, "no_population_truncation": True, "test_target_accessed": False}
    receipt, value = store.run(contract, "P2", plan, audit)
    atomic_json(root/"cartilage-audit-receipt.json", receipt)
    if value is None:
        raise RuntimeError(receipt)
    destination = Path("docs/benchmarks/alpha10/cartilage-admission.json")
    if not destination.exists(): destination.hardlink_to((root/"evidence"/receipt["artifact"]).resolve())
    if digest(destination) != receipt["sha256"]: raise ValueError("IMMUTABLE_CARTILAGE_AUDIT_DIFFERS")
    identity = value["original_identity_evidence"]["value"]
    print(json.dumps({"status": value["status"], "locations": identity["locations"], "acquisitions": identity["acquisitions"],
                      "declared_joints": len(identity["joint_counts"]), "regions": len(identity["region_counts"]),
                      "spectra_matched": value["original_to_derived"]["spectral_membership"]["value"]["locations_exact_float32_multiset_match"],
                      "bytes": receipt["measured_evidence_bytes"]}))


if __name__ == "__main__": main()
