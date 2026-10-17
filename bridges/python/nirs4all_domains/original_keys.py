"""Original-location identity transport; never estimates biological independence."""
import re

from .storage import fingerprint
from .dependence import state


def cartilage_keys(records):
    result, seen = [], set()
    for record in records:
        key = record.get("sample_id")
        if not isinstance(key, str) or not key or key in seen:
            raise ValueError("MISSING_OR_DUPLICATE_ORIGINAL_LOCATION_KEY")
        seen.add(key)
        match = re.fullmatch(r"sample_(\d+)_([a-zA-Z]+)_(\d+)", key)
        if not match or (int(match[1]), match[2].upper(), int(match[3])) != (
                int(record["joint_id"]), str(record["area_of_interest_id"]).upper(), int(record["measurement_point_id"])):
            raise ValueError("ORIGINAL_LOCATION_METADATA_CONTRADICTION")
        acquisitions = record["acquisition_keys"]
        if not acquisitions or len(set(acquisitions)) != len(acquisitions) or any(not k for k in acquisitions):
            raise ValueError("MISSING_OR_DUPLICATE_ORIGINAL_ACQUISITION_KEY")
        result.append({"physical_location_id": key, "joint_id": str(record["joint_id"]),
                       "region_id": f"joint:{record['joint_id']}:AI:{str(record['area_of_interest_id']).upper()}",
                       "donor_id": record.get("donor_id"), "reference_key": record.get("reference_key"),
                       "acquisition_keys": sorted(acquisitions)})
    all_acquisitions = [s for r in result for s in r["acquisition_keys"]]
    if len(set(all_acquisitions)) != len(all_acquisitions):
        raise ValueError("ACQUISITION_KEY_REUSED_ACROSS_LOCATIONS")
    return sorted(result, key=lambda r: r["physical_location_id"])


def dependency_closure(records):
    """Union declared location/reference/region/joint/donor links, by identity."""
    if len({r["physical_location_id"] for r in records}) != len(records):
        raise ValueError("DUPLICATE_PHYSICAL_LOCATION")
    parent = {r["physical_location_id"]: r["physical_location_id"] for r in records}
    def find(key):
        while parent[key] != key:
            key = parent[key]
        return key
    links = {}
    for record in records:
        key = record["physical_location_id"]
        for field in ("reference_key", "region_id", "joint_id", "donor_id"):
            value = record.get(field)
            if value:
                token = (field, str(value))
                if token in links:
                    a, b = find(key), find(links[token])
                    parent[max(a, b)] = min(a, b)
                else:
                    links[token] = key
    groups = {}
    for key in sorted(parent):
        groups.setdefault(find(key), []).append(key)
    missing = sum(not r.get("donor_id") for r in records)
    return {"declared_components": sorted(groups.values()), "n_declared_components": len(groups),
            "membership_sha256": fingerprint(sorted(groups.values())), "locations_missing_donor": missing,
            "biological_independence": state(reason="DONOR_TO_JOINT_RELATIONSHIP_NOT_IDENTIFIABLE", status="not_identifiable") if missing else state("Declared donor closure; source evidence still required")}


def keyed_equivalence(original, canonical, *, key, columns):
    """Explicit original keys are mandatory; row permutations do not alter joins."""
    maps = []
    for rows in (original, canonical):
        if any(not row.get(key) for row in rows):
            raise ValueError("POSITIONAL_JOIN_FORBIDDEN_MISSING_ORIGINAL_KEY")
        table = {row[key]: row for row in rows}
        if len(table) != len(rows):
            raise ValueError("AMBIGUOUS_DUPLICATE_ORIGINAL_KEY")
        maps.append(table)
    if set(maps[0]) != set(maps[1]):
        raise ValueError("ORIGINAL_CANONICAL_KEY_POPULATIONS_DIFFER")
    for identity in maps[0]:
        if any(maps[0][identity].get(c) != maps[1][identity].get(c) for c in columns):
            raise ValueError("ORIGINAL_CANONICAL_VALUE_CONTRADICTION")
    return {"keys": sorted(maps[0]), "n": len(maps[0]), "status": "computed"}


def full_population_cost(n_locations, n_acquisitions, n_features, outer_folds=5, inner_folds=3, candidates=3):
    if not (0 < n_locations <= n_acquisitions and n_features > 0):
        raise ValueError("INVALID_FULL_POPULATION_DIMENSIONS")
    return {"n_locations": n_locations, "n_acquisitions": n_acquisitions, "n_features": n_features,
            "full_population_preserved": True, "old_500_row_guard_is_software_budget": True,
            "mean_f64_bytes": n_locations*n_features*8, "native_acquisition_f64_bytes": n_acquisitions*n_features*8,
            "native_fit_count": outer_folds*(inner_folds*candidates+1),
            "dense_ridge_kernel_f64_upper_bytes": n_locations*n_locations*8,
            "thin_svd_storage_order_cells": n_locations*n_features + min(n_locations, n_features)*(n_locations+n_features+1),
            "predictive_execution": state(reason="ORIGINAL_ALIGNMENT_AND_DEPENDENCY_ADMISSION_REQUIRED"),
            "limitation": "Dimension-based storage/fit-count estimate, not a measured runtime or a qualified scalable protocol."}
