"""Local Shootout qualification through an existing converter and Datasets.

No vendor parser, canonical writer or numerical method is implemented here.
All raw bytes, keyed exports, canonical data and reports stay under results/.
The supplied converter is executable Python: its SHA-256 is required explicitly.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from importlib.metadata import version
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

import yaml

from nirs4all_domains.batch import run_campaign


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(converter_path, expected_sha, raw_zip, descriptor_path, staging, registry_manifest=None):
    """Delegate regeneration and canonicalization into a fresh verified tree."""
    from nirs4all_datasets.canonical import build_canonical
    from nirs4all_datasets.schema import DatasetDescriptor

    converter_path, raw_zip, staging = map(lambda p: Path(p).resolve(), (converter_path, raw_zip, staging))
    if digest(converter_path) != expected_sha:
        raise ValueError("Audited converter SHA-256 mismatch")
    if staging.exists():
        raise ValueError("Staging must be a new directory; no recursive replacement allowed")
    staging.mkdir(parents=True)
    leaf_root = staging / "keyed"
    leaf_root.mkdir()
    with zipfile.ZipFile(raw_zip) as archive:
        for member in archive.namelist():
            resolved = (staging / member).resolve()
            if not resolved.is_relative_to(staging):
                raise ValueError("Archive member escapes staging")
    spec = importlib.util.spec_from_file_location("audited_source_converter", converter_path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load supplied converter")
    module = importlib.util.module_from_spec(spec)
    previous_bytecode_policy = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous_bytecode_policy
    module.OUT_ROOT = leaf_root
    # Use the already downloaded official archive; this helper cannot fetch it.
    module.download_zip = lambda *_args, **_kwargs: raw_zip
    module.convert_shootout()
    descriptor = DatasetDescriptor.model_validate(yaml.safe_load(Path(descriptor_path).read_text(encoding="utf-8")))
    dataset_id = descriptor.id
    if dataset_id != "pharmaceutical_tablets_nir_shootout_eigenvector":
        raise ValueError("This qualification script only supports the audited Shootout case")
    leaf = leaf_root / dataset_id
    catalog_root = staging / "catalog-root"
    destination = catalog_root / "datasets" / dataset_id
    # The upstream canonical writer can replace an existing canonical tree;
    # this fresh destination guarantees there is no tree to delete.
    if destination.exists():
        raise ValueError("Canonical destination already exists")
    result = build_canonical(leaf, descriptor, destination)
    if result.status.value != "ok" or result.warnings:
        raise ValueError(f"Canonical conversion needs review: {result.status}: {result.warnings}")
    catalog = catalog_root / "catalog/datasets"
    catalog.mkdir(parents=True)
    shutil.copyfile(descriptor_path, catalog / f"{dataset_id}.yaml")
    source_evidence = {
        "raw_zip_sha256": digest(raw_zip), "source_converter_sha256": digest(converter_path),
        "descriptor_sha256": digest(descriptor_path),
        "keyed_files_sha256": {p.name: digest(p) for p in leaf.glob("*.csv") if p.name in ("X1.csv", "X2.csv", "Y.csv", "M.csv")},
        "canonical_converter": result.converter_name, "canonical_converter_version": result.converter_version,
        "canonical_hashes": result.canonical_hashes, "canonical_counts": result.row_counts,
        "canonical_warnings": result.warnings,
        "origin_url": "https://eigenvector.com/wp-content/uploads/2019/06/nir_shootout_2002.mat_.zip",
        "restriction": "Local internal-use qualification only; redistribution rights not cleared",
        "materialization_kind": "local_raw_reproduction",
        "registry_byte_identity_verified": False,
        "dependency_versions": {name: version(name) for name in
            ("nirs4all-domains-bridge", "nirs4all-datasets", "numpy", "scipy", "pandas", "pyarrow")},
    }
    if registry_manifest is not None:
        registry_manifest = Path(registry_manifest)
        registry = json.loads(registry_manifest.read_text(encoding="utf-8"))
        expected = {Path(k).name: v for k, v in registry.get("canonical_hashes", {}).items()}
        actual = {Path(k).name: v for k, v in result.canonical_hashes.items()}
        source_evidence.update(registry_manifest_sha256=digest(registry_manifest),
            registry_converter_version=registry.get("converter_version"),
            registry_byte_identity_verified=bool(expected) and expected == actual)
    (staging / "preparation.json").write_text(json.dumps(source_evidence, indent=2), encoding="utf-8")
    return catalog_root, source_evidence


def qualify(catalog_root, evidence, config, output, binary, methods_library):
    import nirs4all_datasets as datasets
    from nirs4all_domains import task_from_dataset

    ds = datasets.get(config["dataset_id"], root=catalog_root)
    split = ds.split(config["split_id"])
    counts = split["partition"].value_counts().to_dict() if split is not None else {}
    if counts != {"calibration": 155, "test": 460, "validation": 40}:
        raise ValueError(f"Unexpected native split counts: {counts}")
    if ds.sources() != ["X1", "X2"] or ds.x(config["source_id"]).shape != (655, 650):
        raise ValueError("Unexpected source shapes")
    config = dict(config)
    config["provenance"] = {**config.get("provenance", {}), **{k: evidence[k] for k in ("raw_zip_sha256", "source_converter_sha256", "descriptor_sha256", "origin_url")}}
    config["provenance"]["target_unit_evidence"] = config["target_unit_evidence"]
    config["provenance"]["materialization_kind"] = evidence["materialization_kind"]
    config["provenance"]["registry_byte_identity_verified"] = str(evidence["registry_byte_identity_verified"]).lower()
    config["provenance"]["canonical_materialization_sha256"] = hashlib.sha256(json.dumps(evidence["canonical_hashes"], sort_keys=True).encode()).hexdigest()
    task = task_from_dataset(ds, config)
    if any("y" in r or "category" in r for r in task["observations"] if r["partition"] == "test"):
        raise AssertionError("Test target escaped pre-training conversion")
    if len(task["observations"]) != 615:
        raise ValueError("Expected exactly 155 train and 460 test observations")
    task_path = output / "shootout-task.json"
    task_path.write_text(json.dumps(task, allow_nan=False), encoding="utf-8")
    for name in ("first", "repeat"):
        subprocess.run([str(binary), "analyze", str(task_path), "--out", str(output / name),
                        "--methods-library", str(methods_library)], check=True)
    first = (output / "first/report.json").read_bytes()
    if first != (output / "repeat/report.json").read_bytes():
        raise AssertionError("Real task scientific reports are not reproducible")
    report = json.loads(first)
    by_id = {m["metric_id"]: m for m in report["metrics"]}
    if report["test_target_accessed"] or report["fit"] is None or len(report["fit"]["fit_observation_ids"]) != 155:
        raise AssertionError("Real task did not retain a train-only fit")
    if by_id["coverage.test_outside_fraction"]["status"] != "computed":
        raise AssertionError("Real coverage protocol was not computed")
    # Exercise the real task alongside the two remaining honest pilot blockers.
    campaign = {"schema_version": 1, "tasks": [
        {"dataset_id": ds.id, "task_file": task_path.name},
        {"dataset_id": "corn_eigenvector_nir", "enabled": False, "reason": "NO_NATIVE_SPLIT; paired-instrument protocol deferred"},
        {"dataset_id": "ucph_tablet_nir", "enabled": False, "reason": "REPEAT_IDENTITIES_AND_GROUP_SPLIT_UNQUALIFIED"}]}
    campaign_path = output / "campaign.yaml"
    campaign_path.write_text(yaml.safe_dump(campaign), encoding="utf-8")
    run_campaign(campaign_path, output / "batch", binary, methods_library)
    summary = {"dataset_id": ds.id, "catalog_root": str(catalog_root), "content_version": config["content_version"], "source_id": config["source_id"],
        "target_id": config["target_id"], "target_unit": config["target_unit"], "split_id": config["split_id"],
        "native_split_counts": counts, "task_partition_mapping": config["partition_labels"],
        "n_train": 155, "n_test": 460, "n_excluded_validation": 40, "seed": config["seed"],
        "protocol_version": report["protocol_version"], "provenance": report["provenance"],
        "report_sha256": hashlib.sha256(first).hexdigest(), "reproducible": True,
        "test_target_accessed": False, "metrics": {key: by_id[key]["value"] for key in
            ("coverage.effective_dimension", "domain.centroid_distance", "domain.dispersion_ratio", "coverage.test_outside_fraction")},
        "limitations": report["limitations"], "source_evidence": evidence,
        "identity_assumption": config["sample_identity_evidence"]}
    (output / "qualification.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("converter", "raw-zip", "descriptor", "binary", "methods-library", "out"):
        parser.add_argument(f"--{arg}", required=True)
    parser.add_argument("--converter-sha256")
    parser.add_argument("--registry-manifest")
    parser.add_argument("--config", default="configs/pilot-shootout.yaml")
    args = parser.parse_args()
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    fresh = Path(tempfile.mkdtemp(prefix="staging-", dir=output)) / "prepared"
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    expected_sha = args.converter_sha256 or config["source_converter_sha256"]
    catalog, evidence = prepare(args.converter, expected_sha, args.raw_zip, args.descriptor, fresh, args.registry_manifest)
    summary = qualify(catalog, evidence, config, output,
                      Path(args.binary).resolve(), Path(args.methods_library).resolve())
    print(json.dumps({k: summary[k] for k in ("dataset_id", "n_train", "n_test", "n_excluded_validation", "reproducible", "metrics")}, indent=2))


if __name__ == "__main__":
    main()
