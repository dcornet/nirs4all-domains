"""Information-dependent orchestration; all geometry/association kernels are native."""
from __future__ import annotations

import ctypes
import json
import math
from pathlib import Path
import subprocess

from .dependence import state
from .storage import fingerprint

PROTOCOL = "domains.adaptive_structure.v0.1"
IDENTITIES = ("verified_physical_identity", "declared_but_unverified_identity",
              "observation_identity_only", "identity_unavailable")


def spectral_request(path, source_id, identity="observation_identity_only"):
    """Read a declared complete CSV axis; row aliases never assert physical identity."""
    import pandas as pd
    if identity not in IDENTITIES:
        raise ValueError("UNKNOWN_IDENTITY_EVIDENCE")
    frame = pd.read_csv(path, sep=";")
    keys = [c for c in frame if c in ("observation_id", "sample_id", "ID_sample")]
    axis = [c for c in frame if c not in keys]
    try:
        wavelengths = list(map(float, axis))
    except ValueError as error:
        raise ValueError("NUMERIC_SPECTRAL_AXIS_REQUIRED") from error
    if not wavelengths or any(not math.isfinite(v) for v in wavelengths):
        raise ValueError("FINITE_SPECTRAL_AXIS_REQUIRED")
    if any(a >= b for a, b in zip(wavelengths, wavelengths[1:])):
        raise ValueError("DECLARED_AXIS_NOT_STRICTLY_INCREASING")
    ids = frame["observation_id"].astype(str).tolist() if "observation_id" in frame else [
        "scoped-row:"+fingerprint([source_id, i]) for i in range(len(frame))]
    if len(ids) != len(set(ids)):
        raise ValueError("DUPLICATE_OBSERVATION_ID")
    return {"source_id": source_id, "observation_ids": ids, "identity_evidence": identity,
            "axis": wavelengths, "axis_unit": "source-declared", "spectra": frame[axis].values.tolist()}


def x_characterization(request, binary, library):
    # No retained Y can enter this deliberately target-free native contract.
    payload = json.dumps(request, allow_nan=False, separators=(",", ":"))
    result = subprocess.run([str(binary), "x-structure", "--methods-library", str(library)],
                            input=payload, capture_output=True, text=True, timeout=300)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    value = json.loads(result.stdout)
    if value["test_target_accessed"] or value["protocol_version"] != PROTOCOL:
        raise ValueError("X_ONLY_SCOPE_VIOLATION")
    return value


def association(labels, targets):
    """Public Methods factor association ABI, no unrestricted permutation inference."""
    from n4m import Context
    from n4m._ffi import lib
    if len(labels) != len(targets) or not targets or not all(map(math.isfinite, targets)):
        raise ValueError("MATCHED_FINITE_ASSOCIATION_REQUIRED")
    levels = {v: i for i, v in enumerate(sorted(set(labels)))}
    if len(levels) < 2 or len(levels) >= len(labels):
        return state(reason="INSUFFICIENT_FACTOR_LEVEL_OR_RESIDUAL_SUPPORT")
    codes = (ctypes.c_int64 * len(labels))(*(levels[v] for v in labels))
    y = (ctypes.c_double * len(targets))(*targets)
    out, counts = (ctypes.c_double * 8)(), (ctypes.c_int64 * 2)()
    with Context() as ctx:
        status = lib.n4m_preflight_factor_association(ctx.handle, codes, y, len(labels), 0, 0, 17, out, counts)
    if status:
        return state(reason=f"METHODS_FACTOR_ASSOCIATION_STATUS_{status}")
    if not math.isfinite(out[0]):
        return state(reason="NATIVE_UNDEFINED_ASSOCIATION")
    return state({"eta_squared": out[0], "n_observations": len(labels), "n_levels": len(levels),
                  "scope": "descriptive matched development observations; not independent predictive evidence",
                  "permutations": 0, "provider": "Methods 1.3.6 factor_association"})


def partition_agreement(a, b):
    from n4m import Context
    from n4m._ffi import lib
    if len(a) != len(b) or len(a) < 2:
        raise ValueError("MATCHED_PARTITION_IDENTITIES_REQUIRED")
    codes = []
    for labels in (a, b):
        levels = {v: i for i, v in enumerate(sorted(set(labels)))}
        codes.append((ctypes.c_int64 * len(labels))(*(levels[v] for v in labels)))
    out = ctypes.c_double()
    with Context() as ctx:
        status = lib.n4m_preflight_adjusted_rand_index(ctx.handle, *codes, len(a), ctypes.byref(out))
    return state(out.value) if not status and math.isfinite(out.value) else state(reason="NATIVE_UNDEFINED_ARI")


def scientific_relation(a, b):
    """Declared source identity sets, never row counts or scores, establish overlap."""
    required = ("study_id", "population_id", "physical_keys_verified", "physical_keys")
    if any(k not in item for item in (a, b) for k in required):
        raise ValueError("SOURCE_POPULATION_CONTRACT_REQUIRED")
    if a["population_id"] == b["population_id"]:
        return "same_declared_population"
    if a["study_id"] == b["study_id"]:
        return "shared_study_independence_unverified"
    if a["physical_keys_verified"] and b["physical_keys_verified"] and set(a["physical_keys"]) & set(b["physical_keys"]):
        return "shared_physical_specimens"
    return "distinct_provenance_overlap_unverified"


def coverage_record(dataset_id, source, identity, levels, report=None, **details):
    if identity not in IDENTITIES:
        raise ValueError("UNKNOWN_IDENTITY_EVIDENCE")
    expected = {"X0", "X1", "XY", "XYM", "MODEL"}
    if set(levels) != expected:
        raise ValueError("COMPLETE_INFORMATION_LEVELS_REQUIRED")
    for value in levels.values():
        if (value["status"] == "computed") != (value["reason"] is None and value["value"] is not None):
            raise ValueError("LEVEL_STATUS_REASON_VALUE_MISMATCH")
    result = {"schema_version": 1, "protocol_version": PROTOCOL, "dataset_id": dataset_id,
              "source_id": source, "identity_evidence": identity, "levels": levels,
              "structural_susceptibility": report, "universal_shortcut_score": None, **details}
    return {**result, "record_id": fingerprint(result)}
