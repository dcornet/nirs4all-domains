"""P0: documented Datasets descriptors/cards only; never get/retrieve/fetch."""
from collections import Counter
import json
from pathlib import Path
import subprocess

import yaml

from .storage import digest, fingerprint


def catalog_inventory(root):
    from importlib.metadata import version
    from nirs4all_datasets.schema import DatasetDescriptor
    if version("nirs4all-datasets") != "0.3.11":
        raise ValueError("PINNED_DATASETS_0_3_11_REQUIRED")
    root = Path(root)
    revision = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    records = []
    # Descriptors are a documented public format; model validation catches stale
    # shapes. Do not call settings, credentials or acquisition to inspect them.
    for path in sorted((root / "catalog/datasets").glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        d = DatasetDescriptor.model_validate(raw).model_dump(mode="json")
        targets = [v for v in d["variables"] if v["role"] == "target"]
        numeric = [v for v in targets if v["type"] == "numeric"]
        metadata = [v["name"] for v in d["variables"] if v["role"] == "metadata"]
        blockers = []
        if d["tier"] != "public":
            blockers.append("RESTRICTED_TIER_NO_ACQUISITION_AUTHORIZATION")
        if d["governance"]["license"].startswith("LicenseRef"):
            blockers.append("RIGHTS_NOT_CLEARED")
        if not d["ids"]["sample_id_available"]:
            blockers.append("PHYSICAL_IDENTITY_UNAVAILABLE")
        if not numeric:
            blockers.append("NO_DECLARED_NUMERIC_REGRESSION_TARGET")
        if not metadata:
            blockers.append("NO_DECLARED_EXPLANATORY_METADATA")
        blockers.append("P1_KEY_REFERENCE_GROUP_AND_TARGET_COMPLETENESS_AUDIT_REQUIRED")
        source = [{k: s.get(k) for k in ("source_id", "modality", "instrument_name", "n_observations", "n_variables", "axis_unit", "axis_min", "axis_max")} for s in d["sources"]]
        dense = sum(s["n_observations"]*s["n_variables"]*4 for s in source if s["n_observations"] is not None and s["n_variables"] is not None)
        card_path = root / "datasets" / d["id"] / "card.json"
        card = json.loads(card_path.read_text(encoding="utf-8")) if card_path.exists() else {}
        manifest_path = card_path.with_name("manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
        variable_cards = {v["name"]:v for v in card.get("variables", [])}
        alignment = card.get("alignment", {})
        records.append(dict(dataset_id=d["id"], dataset_revision=fingerprint({"catalog_commit": revision, "descriptor_sha256": digest(path)}),
                            descriptor_sha256=digest(path), content_version=d["versions"]["content"],
                            tier=d["tier"], license=d["governance"]["license"],
                            declared_permitted_use=d["governance"].get("permitted_use"),
                            sources=source, targets=[{k:v.get(k) for k in ("name", "type", "unit", "units")} |
                                {"card_n":variable_cards.get(v["name"], {}).get("stats", {}).get("n"),
                                 "card_n_missing":variable_cards.get(v["name"], {}).get("stats", {}).get("n_missing"),
                                 "card_unit":variable_cards.get(v["name"], {}).get("unit"),
                                 "card_n_classes":variable_cards.get(v["name"], {}).get("stats", {}).get("n_classes")}
                                for v in targets],
                            metadata_fields=metadata, ids=d["ids"], alignment=d["alignment_level"],
                            splits=[{k:s.get(k) for k in ("name", "kind", "documented_origin", "applied")} for s in d["splits"]],
                            origins=[{"kind":o["kind"], "mode":o["mode"], "access":o["access"]} for o in d.get("origin_sources", [])],
                            raw_hashes=d.get("provenance", {}).get("raw_sha256", []),
                            declared_source_fingerprint=(d.get("generation") or {}).get("source_fingerprint"),
                            content_hash=(card.get("integrity") or {}).get("content_hash"),
                            manifest_present=bool(manifest),
                            target_completeness="card_declarations_only_not_key_verified", reference_identity="unverified_without_P1",
                            card_sample_count=alignment.get("n_samples"), card_reps_per_sample=alignment.get("reps_per_sample"),
                            metadata_card_support={v["name"]:{k:variable_cards.get(v["name"], {}).get("stats", {}).get(k) for k in ("n", "n_missing", "n_classes")}
                                                   for v in d["variables"] if v["role"]=="metadata"},
                            repetitions="card_declarations_only_not_P1_qualified", source_pairing="unverified_without_key_audit",
                            dense_float32_bytes_lower_bound=dense or None, raw_bytes=None, canonical_bytes=None,
                            primary_source_numeric_target_templates=len(source)*len(numeric),
                            stages={"P0":"computed", "P1":"pending", "P2":"pending", "P3":"pending", "P4":"pending"},
                            admission_status="pending_P1" if len(blockers)==1 else "ineligible_for_automatic_P1",
                            blockers=blockers))
    return dict(schema_version=1, protocol_version="domains.catalog_inventory.v0.1", catalog_revision=revision,
                datasets=records, counts={"datasets":len(records), "sources":sum(len(r["sources"]) for r in records),
                    "declared_targets":sum(len(r["targets"]) for r in records),
                    "primary_source_numeric_target_templates":sum(r["primary_source_numeric_target_templates"] for r in records),
                    "tiers":dict(Counter(r["tier"] for r in records)),
                    "pending_metadata_eligible_P1":sum(r["admission_status"]=="pending_P1" for r in records)},
                limitations=["Metadata declarations are not physical/reference qualification.",
                             "Templates do not enumerate additional representations, splits or policies.",
                             "Dense float32 counts exclude raw/canonical compression, Y and metadata; not a download estimate.",
                             "Public origin status does not override a restricted tier or uncleared license.",
                             "No network, credential lookup, canonical matrix access or modelling."])
