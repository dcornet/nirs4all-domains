"""Metadata-only paired-source and reference-provenance review; no target fits."""
import argparse
import json
from pathlib import Path
import urllib.request

from nirs4all_domains.storage import atomic_json, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    from scipy.io import loadmat
    root = Path(".audit/alpha10/source-pages")
    root.mkdir(parents=True, exist_ok=True)
    links = {"eigenvector": "https://eigenvector.com/resources/data-sets/", "ucph": "https://ucphchemometrics.com/tablet/",
             "perten": "https://zenodo.org/api/records/15838136"}
    sources = {}
    for key, url in links.items():
        destination = root/(key+".txt")
        content = urllib.request.urlopen(url, timeout=40).read()
        destination.write_bytes(content)
        sources[key] = {"url": url, "bytes": len(content), "sha256": digest(destination)}
    path = args.source_root/"pharmaceutical_tablets_nir_shootout_eigenvector/raw/nir_shootout_2002.mat"
    mat = loadmat(path, struct_as_record=False, squeeze_me=True)
    objects = {k: {"shape": list(v.data.shape), "original_row_labels_count": int(v.label[0, 0].size),
                   "original_row_axis_keys_count": int(v.axisscale[0, 0].size)} for k, v in mat.items() if not k.startswith("__")}
    # Only sizes and identity fields are inspected. Reference values are not
    # used for admission, model selection or experiment design.
    paired = {"protocol_version": "domains.alpha10.paired_admission.v0.1", "status": "pending", "admitted_tasks": 0,
        "source_evidence": sources,
        "records": [
            {"dataset_id": "corn_eigenvector_nir", "status": "pending", "owner_decision": "Keep pending without rights justification",
             "original_key_evidence": "Alpha.9 original MAT row labels and row-axis keys empty in m5/mp5/mp6/propvals; unchanged preserved evidence",
             "blockers": ["ORIGINAL_SPECIMEN_ASSAY_KEYS_MISSING", "ANALYSIS_AND_PUBLICATION_SCOPE_UNKNOWN"],
             "request": "Provide instrument/property-row -> original specimen/assay key tables and allowed analysis/non-reconstructive publication scope. Never infer pairing from 80 rows."},
            {"dataset_id": "pharmaceutical_tablets_nir_shootout_eigenvector", "status": "pending",
             "original_mat_sha256": digest(path), "objects": objects, "original_partition_total": sum(objects[k]["shape"][0] for k in ("calibrate_1", "test_1", "validate_1")),
             "count_finding": "Original MAT itself has 155+460+40=655 per instrument; official page says 654. Local 655 is not evidence of a converter off-by-one error.",
             "blockers": ["ORIGINAL_ROW_SAMPLE_AND_REFERENCE_KEYS_EMPTY", "OFFICIAL_COUNT_CONTRADICTION_UNRESOLVED", "PAIRED_ANALYSIS_AND_PUBLICATION_SCOPE_UNKNOWN"],
             "request": "Confirm the 655-row original release versus 654 announcement; supply original physical/reference/partition key maps for both instruments and permitted paired-study publication."},
            {"dataset_id": "ucph_tablet_nir", "status": "pending", "original_mat_available_in_inspected_local_leaf": False,
             "blockers": ["SOURCE_CONFIRMED_NIR_NIT_RAMAN_SPECIMEN_ASSAY_MAP_MISSING", "REUSE_SCOPE_UNKNOWN"],
             "request": "Supply physical tablet and reference-event keys across modalities, source/split definitions and allowed analysis/publication scope. Batch/replicate labels cannot establish pairing."}],
        "transfer_contract": {"paired_instrument": "same physical objects, source/context transfer; whole objects remain indivisible where required",
                              "new_sample": "all test physical objects absent from training, with declared deployment context",
                              "spectral_axes": "Preserve each original axis; no interpolation or pooled-source refit is qualified"},
        "upstream_modified": False, "messages_or_issues_posted": False, "new_restricted_acquisition_or_fits": False}
    atomic_json("docs/benchmarks/alpha10/paired-admission.json", paired)
    api = json.loads((root/"perten.txt").read_text())
    if api["metadata"]["license"]["id"] != "cc-by-4.0": raise ValueError("PERTEN_RIGHTS_CHANGED")
    moisture = {"protocol_version": "domains.alpha10.reference_review.v0.1", "dataset_id": "perten_cereals_nir",
        "source_evidence": sources["perten"], "frozen_alpha9_admission_sha256": digest("docs/benchmarks/alpha9/perten-admission.json"),
        "finding": "Official version-1 description and preserved original XLSX evidence provide no new assay-event/precision/farm/serial-instrument keys or unambiguous moisture-basis resolution.",
        "method": "Oven; source moisture percent, no wet/dry conversion", "unresolved": ["wet versus dry basis", "oven temperature/duration/standard", "assay event identity and precision", "farm/harvest/lot links", "country as crop origin versus measurement site", "model versus serial instrument"],
        "historical_target_or_task_mutated": False,
        "request": "Original assay protocol/standard and basis, event IDs and precision, lot/farm/harvest metadata, country definition and instrument serial/acquisition relationships."}
    atomic_json("docs/benchmarks/alpha10/perten-reference-review.json", moisture)
    print(json.dumps({"paired_admitted": 0, "shootout_original_total": paired["records"][1]["original_partition_total"], "perten_new_reference_resolution": False}))


if __name__ == "__main__": main()
