"""Convert one named source using public dataset accessors and keyed joins."""
from __future__ import annotations

import math
import json
from collections import Counter
from importlib.metadata import version


def _keyed(frame, columns):
    if frame is None:
        return {}
    if "sample_id" not in frame.columns or frame["sample_id"].isna().any():
        raise ValueError("A nonmissing sample_id column is required")
    records = {}
    for row in frame.to_dict("records"):
        key = str(row["sample_id"])
        if key in records:
            raise ValueError(f"Ambiguous sample join: {key}")
        records[key] = {name: row[name] for name in columns if name in row}
    return records


def _number(value):
    if value is None:
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def task_from_dataset(ds, config):
    """No source fusion, generated split, inferred physical IDs or numeric fit.

    `sample_identity_confirmed` explicitly asserts one physical object per supplied
    sample ID. Otherwise an `identity_table` must map sample IDs to physical IDs
    and independence groups. A metadata group column is an additional dependency.
    """
    source = config["source_id"]
    if source not in ds.sources():
        raise ValueError(f"Unknown source: {source}")
    descriptor = ds.descriptor
    content = str(descriptor.versions.content)
    if content != config["content_version"]:
        raise ValueError(f"Content version mismatch: {content}")
    target = config.get("target_id")
    mode = config.get("audit_mode", "pre_training")
    split_frame = ds.split(config["split_id"])
    if split_frame is None:
        raise ValueError("Native split unavailable; supply a separately named explicit task")
    split = _keyed(split_frame, ["partition"])
    labels = config["partition_labels"]  # explicit mapping; never guess labels
    if not labels or any(v not in ("train", "test", "exclude") for v in labels.values()):
        raise ValueError("Partition mapping must explicitly use train/test/exclude")
    metadata_frame = ds.metadata()
    metadata = _keyed(metadata_frame, list(metadata_frame.columns) if metadata_frame is not None else [])
    # The public y() accessor returns a full per-sample frame. Materialization can
    # include test rows, but values are accessed only for permitted partitions.
    targets_frame = ds.y(target) if target else None
    if target and (targets_frame is None or target not in targets_frame.columns):
        raise ValueError(f"Requested target unavailable in canonical data: {target}")
    if targets_frame is not None and ("sample_id" not in targets_frame or targets_frame["sample_id"].astype(str).duplicated().any()):
        raise ValueError("Ambiguous target identity")
    targets = targets_frame.assign(sample_id=targets_frame["sample_id"].astype(str)).set_index("sample_id") if targets_frame is not None else None
    identities = config.get("identity_table", {})
    if not identities and not config.get("sample_identity_confirmed", False):
        raise ValueError("Physical identities must be confirmed or explicitly mapped")
    x = ds.x(source)
    axis = ds.wavelengths(source)
    sample_ids = ds.sample_ids(source)
    observation_ids = ds.observation_ids(source)
    if not (len(x) == len(sample_ids) == len(observation_ids)):
        raise ValueError("Source identity length mismatch")
    source_descriptor = next(s for s in descriptor.sources if s.source_id == source)
    rows = []
    excluded = []
    native_counts = Counter()
    categorical = config.get("target_kind", "continuous") == "categorical"
    for oid, sid, spectrum in zip(observation_ids, sample_ids, x, strict=True):
        sid = str(sid)
        if sid not in split or str(split[sid]["partition"]) not in labels:
            raise ValueError(f"Unassigned or unknown partition for sample: {sid}")
        native_partition = str(split[sid]["partition"])
        native_counts[native_partition] += 1
        partition = labels[native_partition]
        if partition == "exclude":
            excluded.append(str(oid))
            continue
        identity = identities.get(sid)
        if identities and identity is None:
            raise ValueError(f"Missing physical identity: {sid}")
        physical = str(identity["physical_sample_id"]) if identity else sid
        group_column = config.get("group_column")
        if group_column:
            group = metadata.get(sid, {}).get(group_column)
            if group is None or str(group) in ("nan", "None", ""):
                raise ValueError(f"Missing independent group: {sid}")
            group = str(group)
        else:
            group = str(identity.get("independence_group", physical)) if identity else physical
        row = {"observation_id": str(oid), "sample_id": sid, "physical_sample_id": physical,
               "independence_group": group, "partition": partition,
               "x": [_number(v) for v in spectrum],
               "metadata": {str(k): str(v) for k, v in metadata.get(sid, {}).items() if k != "sample_id"}}
        if identity:
            for name in ("reference_id", "reference_group_id", "individual_id", "repetition_type"):
                if identity.get(name) is not None:
                    row[name] = str(identity[name])
        if target and targets is not None and sid in targets.index and (partition == "train" or mode == "post_evaluation"):
            value = targets.at[sid, target]
            if categorical:
                if value is not None and str(value) not in ("nan", "None", "<NA>"):
                    row["category"] = str(value)
            else:
                row["y"] = _number(value)
        rows.append(row)
    target_descriptor = next((v for v in descriptor.variables if v.name == target), None) if hasattr(descriptor, "variables") else None
    target_unit = config.get("target_unit", getattr(target_descriptor, "unit", None))
    if target_unit is not None and not str(target_unit).strip():
        raise ValueError("Target unit must be nonempty when supplied")
    provenance = {"datasets": version("nirs4all-datasets"),
                "task_conversion_protocol": "datasets.task.v0.2",
                "sample_identity_assumption": config.get("sample_identity_evidence", "explicit mapping" if identities else "sample_identity_confirmed"),
                "partition_mapping": json.dumps(labels, sort_keys=True),
                "native_partition_observation_counts": json.dumps(native_counts, sort_keys=True),
                "excluded_observation_ids": json.dumps(excluded),
                "test_target_materialization": "public y() may materialize test rows; pre-training conversion reads train values only"}
    for key, value in config.get("provenance", {}).items():
        if key in provenance:
            raise ValueError(f"Reserved provenance field: {key}")
        provenance[str(key)] = str(value)
    task = {"schema_version": 1, "context": {"dataset_id": ds.id, "content_version": content,
                "source_id": source, "target_id": target, "split_id": config["split_id"]},
            "data_origin": config.get("data_origin", "user_provided"), "axis": [float(v) for v in axis],
            "axis_unit": source_descriptor.axis_unit, "signal_unit": config["signal_unit"],
            "target_kind": config.get("target_kind", "continuous"),
            "policy": {"independence_unit": "group" if group_column or identities else "physical_sample",
                "audit_mode": mode, "seed": config.get("seed", 17), "pca_max_components": config.get("pca_max_components", 20),
                "pca_variance_fraction": config.get("pca_variance_fraction", 0.95)},
            "observations": rows, "provenance": provenance}
    if target_unit is not None:
        task["target_unit"] = str(target_unit)
    return task
