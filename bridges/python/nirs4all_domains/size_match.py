"""Outcome-blind exact whole-component cardinality matching for task protocols."""
from collections import defaultdict

from .storage import fingerprint


def exact_training_subset(rows, allowed_ids, target, *, seed=17, scope="size", minimum_components=3):
    by_id = {r["physical_sample_id"]: r for r in rows}
    if len(by_id) != len(rows) or len(set(allowed_ids)) != len(allowed_ids) or not set(allowed_ids) <= set(by_id):
        raise ValueError("INVALID_TRAINING_IDENTITY_POPULATION")
    groups, complete = defaultdict(list), defaultdict(set)
    for row in rows:
        complete[row["independence_group"]].add(row["physical_sample_id"])
    for s in allowed_ids:
        groups[by_id[s]["independence_group"]].append(s)
    if any(set(ids) != complete[g] for g, ids in groups.items()):
        raise ValueError("TRAINING_POPULATION_SPLITS_DEPENDENCY_COMPONENT")
    states = {(0, 0): ()}
    for group in sorted(groups, key=lambda g: fingerprint([seed, scope, g])):
        for (n, count), selected in list(states.items()):
            new = (n+len(groups[group]), count+1)
            if new[0] <= target:
                states.setdefault(new, (*selected, group))
    counts = [count for n, count in states if n == target and count >= minimum_components]
    if not counts:
        return None
    # Prespecified priority: retain the greatest available context diversity,
    # then the first witness in deterministic identity-hash order. No Y or X.
    selected = states[(target, max(counts))]
    return sorted(s for g in selected for s in groups[g])
