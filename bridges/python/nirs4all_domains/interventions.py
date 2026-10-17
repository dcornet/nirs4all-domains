"""Training-scope identity interventions, not numerical estimators."""
from collections import Counter, defaultdict
import math
import random

from .predictive import fingerprint


def components(rows):
    result = defaultdict(list)
    for row in rows:
        result[row["independence_group"]].append(row)
    return {k: sorted(v, key=lambda r:r["physical_sample_id"]) for k,v in sorted(result.items())}


def exchangeability(rows, kind, factor, min_fraction=.5, min_components=6):
    """Metadata/identity only; target values are not inspected for eligibility."""
    if kind not in ("global", "within_factor"):
        raise ValueError("Unknown training intervention")
    blocks = components(rows)
    strata = defaultdict(list)
    blocked = []
    descriptions = []
    for group, members in blocks.items():
        composition = Counter(r["metadata"].get(factor) for r in members)
        # Existing reference audit excludes shared/contradictory units. Keep
        # status/unit patterns compatible without inventing assay independence.
        aligned = sorted(members,key=lambda r:((r["metadata"].get(factor) or "") if kind=="within_factor" else "",r["physical_sample_id"]))
        reference_pattern = tuple((r.get("reference_status") or "unknown",r.get("reference_unit") or "unspecified") for r in aligned)
        if kind == "within_factor" and any(not key for key in composition):
            blocked.append(group)
            signature = None
        else:
            signature = (len(members), reference_pattern,
                         tuple(sorted(composition.items())) if kind=="within_factor" else ())
            strata[signature].append(group)
        descriptions.append({"component_id":group,"physical_ids":[r["physical_sample_id"] for r in members],
            "cardinality":len(members),"composition":[{"level":k,"n":v} for k,v in sorted(composition.items(),key=lambda p:p[0] or "")],
            "compatible_stratum":fingerprint(signature) if signature is not None else None})
    swappable = [g for groups in strata.values() if len(groups)>1 for g in groups]
    movable = sum(len(blocks[g]) for g in swappable)
    fraction = movable/len(rows) if rows else 0.
    possible = math.prod(math.factorial(len(groups)) for groups in strata.values())
    eligible = len(swappable)>=min_components and fraction>=min_fraction
    return {"kind":kind,"factor":factor,"n_components":len(blocks),"n_targets":len(rows),
        "n_levels":len({r["metadata"].get(factor) for r in rows}-{None,""}),
        "blocks":descriptions,"strata":[{"signature":fingerprint(k),"components":v} for k,v in sorted(strata.items(),key=lambda p:fingerprint(p[0]))],
        "swappable_components":swappable,"unswappable_components":sorted(set(blocks)-set(swappable)),
        "missing_factor_components":blocked,"movable_target_fraction":fraction,
        "attainable_identity_assignments":str(possible),
        "eligible":eligible,"reason":None if eligible else "INSUFFICIENT_SWAPPABLE_COMPONENTS_OR_MOVABLE_TARGET_FRACTION",
        "assumption":"Conditional exchangeability of whole declared component target vectors within cardinality/reference patterns and, for within-factor, exact factor composition; biological/assay independence unverified"}


def intervene(rows, *, kind, factor, seed, attempt, min_fraction=.5, min_components=6, min_changed_fraction=.5):
    """Called only after native scheduler selects the actual training IDs."""
    audit = exchangeability(rows,kind,factor,min_fraction,min_components)
    if not audit["eligible"]:
        raise ValueError(audit["reason"])
    blocks = components(rows)
    ids = sorted(r["physical_sample_id"] for r in rows)
    rng = random.Random(int(fingerprint([seed,attempt,kind,factor,ids]),16))
    source_component = {g:g for g in blocks}
    for stratum in audit["strata"]:
        dest = stratum["components"]
        sources = list(dest)
        rng.shuffle(sources)
        source_component.update(zip(dest,sources,strict=True))
    target_map = {}
    entries = []
    signatures = defaultdict(Counter)
    for stratum in audit["strata"]:
        for g in stratum["components"]:
            # Count repeated numerical target vectors to distinguish numerical
            # outcome assignments from mere source-identity assignments.
            ordered = sorted(blocks[g], key=lambda r:((r["metadata"].get(factor) or "") if kind=="within_factor" else "",r["physical_sample_id"]))
            signatures[stratum["signature"]][tuple(r["y"] for r in ordered)] += 1
    numerical_assignments = math.prod(math.factorial(sum(c.values()))//math.prod(math.factorial(n) for n in c.values()) for c in signatures.values())
    for dest, members in blocks.items():
        src = source_component[dest]
        order = lambda r:((r["metadata"].get(factor) or "") if kind=="within_factor" else "",r["physical_sample_id"])
        for a,b in zip(sorted(members,key=order),sorted(blocks[src],key=order),strict=True):
            target_map[a["physical_sample_id"]] = b["y"]
            entries.append({"destination_id":a["physical_sample_id"],"source_id":b["physical_sample_id"],
                "destination_component":dest,"source_component":src,"source_reference_id":b.get("reference_id"),
                "destination_factor":a["metadata"].get(factor),"source_factor":b["metadata"].get(factor),
                "original_y":a["y"],"training_y":b["y"]})
    entries.sort(key=lambda e:e["destination_id"])
    if set(target_map)!=set(ids) or any(e["source_id"] not in target_map for e in entries):
        raise ValueError("Intervention source/destination escaped training scope")
    moved = sum(e["source_id"]!=e["destination_id"] for e in entries)/len(entries)
    changed = sum(e["training_y"]!=e["original_y"] for e in entries)/len(entries)
    receipt = {"kind":kind,"factor":factor,"seed":seed,"attempt":attempt,"training_ids":ids,
        "target_map":entries,"source_component_map":source_component,"moved_identity_fraction":moved,
        "changed_target_fraction":changed,"effective":changed>=min_changed_fraction,
        "power_reason":None if changed>=min_changed_fraction else "CHANGED_TARGET_FRACTION_BELOW_PRESPECIFIED_MINIMUM",
        "attainable_numerical_vector_assignments":str(numerical_assignments),
        "original_target_sha256":fingerprint([[r["physical_sample_id"],r["y"]] for r in sorted(rows,key=lambda r:r["physical_sample_id"])]),
        "intervened_target_sha256":fingerprint([[s,target_map[s]] for s in ids]),
        "audit_sha256":fingerprint(audit)}
    return [{**r,"y":target_map[r["physical_sample_id"]]} for r in rows], receipt
