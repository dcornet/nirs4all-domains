"""Conditional scientific checks over existing reports, without numerical fitting."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

from . import validation_intent
from .storage import atomic_json, fingerprint

PROTOCOL = "domains.structural_warnings.v1"
SCHEMA_PATH = Path(__file__).with_name("structural-warnings.v1.schema.json")
KINDS = (
    "physical_units",
    "factor_geometry",
    "representation",
    "spectral_support",
    "context",
)
WARNING_IDS = (
    "physical_unit_dependence",
    "experimental_factor_structure",
    "preprocessing_dependent_organization",
    "spectral_support_mismatch",
    "insufficient_experimental_context",
)
IDENTITY = (
    "dataset_id",
    "source_id",
    "content_version",
    "population_id",
    "scope_kind",
    "representation",
    "n_observations",
)
LIMITS = [
    "This is conditional methodological caution, not a probability, severity grade or prediction of calibration failure.",
    "Declared provenance is retained, not independently authenticated by this interpreter.",
    "Clusters, factor cardinality and variance concentration do not establish physical identities, causation or leakage.",
    "Dataset identities, X views, profile rows and provenance components are not independent experiments.",
    "Validation and preprocessing choices depend on the intended deployment; none is universally best.",
]


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _state(value=None, reason="EVIDENCE_NOT_AVAILABLE"):
    return {
        "status": "computed" if value is not None else "unavailable",
        "reason": None if value is not None else reason,
        "value": value,
    }


def _unwrap(value):
    if isinstance(value, dict) and "status" in value:
        if value["status"] not in (
            "computed",
            "unavailable",
            "failed",
            "insufficient_data",
            "insufficient_information",
            "not_identifiable",
            "inconclusive",
            "not_applicable",
        ):
            raise ValueError("Unknown scientific evidence status")
        if not {"value", "reason"} <= value.keys():
            raise ValueError("Evidence state requires status/reason/value")
        if value["status"] == "computed":
            if value["value"] is None or value["reason"] is not None:
                raise ValueError("Invalid computed evidence")
            return value["value"]
        if (
            value["value"] is not None
            or not isinstance(value["reason"], str)
            or not value["reason"]
        ):
            raise ValueError("Invalid unavailable evidence")
        return None
    return value


def _numeric(v):
    return not isinstance(v, bool) and isinstance(v, (float, int))


def _check_values(values):
    fractions = {
        "eta_squared",
        "full_x_overlap",
        "pca_overlap",
        "pc1_before",
        "pc1_after",
        "noise_fractions",
    }
    aris = {"partition_ari", "partition_ari_range", "parameter_ari_min"}
    counts = {
        "n_levels",
        "n_missing",
        "n_repeated_acquisitions",
        "n_overlapping_units",
        "cluster_counts",
        "all_noise_settings",
        "n_exceedances",
        "n_evaluation",
    }
    for key, value in values.items():
        if value is None:
            continue
        items = value if isinstance(value, list) else [value]
        if key in fractions | aris | counts:
            for v in items:
                if v is None:
                    continue
                if not _numeric(v):
                    raise ValueError(f"Numeric evidence required for {key}")
                if key in fractions and not 0 <= v <= 1:
                    raise ValueError(f"Fraction outside [0,1]: {key}")
                if key in aris and not -1 <= v <= 1:
                    raise ValueError(f"ARI outside [-1,1]: {key}")
                if key in counts and (v < 0 or int(v) != v):
                    raise ValueError(f"Nonnegative count required: {key}")
        elif (
            key
            in (
                "has_shared_units",
                "qualified_preflight_finding",
                "physical_units_known",
                "acquisition_context_known",
                "reference_units_known",
                "trivial_partition",
            )
            and type(value) is not bool
        ):
            raise ValueError(f"Boolean evidence required: {key}")
    if (
        values.get("n_exceedances") is not None
        and values.get("n_evaluation") is not None
    ) and values["n_exceedances"] > values["n_evaluation"]:
        raise ValueError("Support exceedance exceeds evaluation count")


def _bindings(report, request):
    resolved = {k: [] for k in KINDS}
    source = request["source"]
    for b in request.get("evidence", []):
        if any(b["scope"][k] != source[k] for k in IDENTITY):
            raise ValueError(
                "Evidence source/content/population/representation scope mismatch"
            )
        record = validation_intent._pointer(report, b["root"])
        if not isinstance(record, dict):
            raise TypeError("Evidence root must reference an object")
        for key in (
            "dataset_id",
            "source_id",
            "content_version",
            "population_id",
            "representation",
            "n_observations",
        ):
            if record.get(key) is not None and record[key] != source[key]:
                raise ValueError(f"Evidence record disagrees with declared {key}")
        if (
            record.get("scope") is not None
            and isinstance(record["scope"], str)
            and record["scope"] != source["scope_kind"]
        ):
            raise ValueError("Evidence population scope differs from report")
        q = b.get("qualifications", {})
        if (
            b["kind"] == "factor_geometry"
            and q.get("role") == "metadata"
            and not q.get("duplicated_from_target", True)
        ) and (
            record.get("primary_X_only_eligible") is False
            or record.get("role") == "target"
            or record.get("original_role") == "Y"
        ):
            raise ValueError(
                "Target-derived source evidence cannot be qualified as non-Y metadata"
            )
        values = {}
        for name, pointer in b["metrics"].items():
            if b["root"] and not pointer.startswith(b["root"] + "/"):
                raise ValueError("Measurement pointer is outside its evidence root")
            values[name] = _unwrap(validation_intent._pointer(report, pointer))
        _check_values(values)
        resolved[b["kind"]].append({"binding": b, "values": values})
    return resolved


def coverage(source, computed):
    """One report population is one case, irrespective of factor/metric rows."""
    refs = source["references"]
    group = source.get("provenance_group")
    family = source.get("original_study_family")
    return {
        "canonical_dataset_ids": [source["dataset_id"]]
        if source["identity_scope"] == "current_canonical_id"
        else [],
        "historical_or_unknown_dataset_ids": [source["dataset_id"]]
        if source["identity_scope"] != "current_canonical_id"
        else [],
        "dataset_identities": [source["dataset_id"]],
        "n_dataset_identities": 1,
        "x_views": [
            {"dataset_id": source["dataset_id"], "source_id": source["source_id"]}
        ],
        "n_x_views": 1,
        "eligible_cases": 1,
        "computed_cases": int(computed),
        "unavailable_cases": int(not computed),
        "original_source_identifiers": source["original_source_identifiers"],
        "documented_references": refs,
        "database_count": _state(reason="AUTHORITATIVE_DATABASE_GROUPING_NOT_SUPPLIED"),
        "declared_provenance_groups": [group] if group else [],
        "documented_provenance_group_count": _state(1)
        if group and refs
        else _state(reason="SOURCE_GROUPING_UNKNOWN"),
        "original_study_families": [family] if family else [],
        "original_study_family_count": _state(1)
        if family and source.get("study_reference")
        else _state(reason="ORIGINAL_STUDY_GROUPING_NOT_ESTABLISHED"),
        "observation_evidence_level": "descriptive",
        "risk_evidence_level": "hypothesis",
        "externally_validated_warning": False,
    }


def _check(check_id, text, when, information, available=False):
    return {
        "check_id": check_id,
        "description": text,
        "applies_when": when,
        "required_information": information,
        "testability": "available" if available else "requires_information",
    }


def _warning(
    index,
    source,
    rows,
    assessment,
    reason,
    description,
    hypothesis,
    checks,
    required,
    alternatives,
    limits=(),
):
    return {
        "warning_id": WARNING_IDS[index],
        "definition_version": 1,
        **_state(assessment, reason),
        "observation": _state(
            {
                "description": description,
                "measurements": [
                    {
                        "kind": r["binding"]["kind"],
                        "root": r["binding"]["root"],
                        "pointers": r["binding"]["metrics"],
                        "values": r["values"],
                        "method": r["binding"]["method"],
                        "qualifications": r["binding"].get("qualifications", {}),
                    }
                    for r in rows
                ],
            }
        )
        if rows
        else _state(reason=reason),
        "risk_hypothesis": hypothesis,
        "conditions": [c for check in checks for c in check["applies_when"]],
        "alternative_explanations": list(alternatives),
        "recommended_checks": checks,
        "required_information": list(required),
        "evidence_scope": {k: source[k] for k in IDENTITY},
        "scientific_basis": coverage(source, assessment is not None),
        "limitations": [*LIMITS, *limits],
    }


def _physical(source, rows, facts):
    good = [
        r
        for r in rows
        if r["binding"].get("qualifications", {}).get("dependency_basis")
        in (
            "declared_technical_repetitions",
            "shared_specimen",
            "shared_reference",
            "qualified_preflight",
        )
        and r["binding"].get("qualifications", {}).get("evidence_quality")
        in ("declared", "verified")
    ]
    good = [
        r
        for r in good
        if r["binding"]["qualifications"]["dependency_basis"] != "qualified_preflight"
        or (
            r["binding"]["method"]["owner"] == "Preflight"
            and r["binding"]["qualifications"]["evidence_quality"] == "verified"
            and r["binding"]["qualifications"].get("preflight_finding_scope")
            in ("declared_identity_overlap", "shared_reference_overlap")
        )
    ]
    measured = [
        r
        for r in good
        if any(
            r["values"].get(k) is not None
            for k in (
                "has_shared_units",
                "n_overlapping_units",
                "qualified_preflight_finding",
            )
        )
    ]
    observed = any(
        r["values"].get("has_shared_units")
        or (r["values"].get("n_overlapping_units") or 0) > 0
        or r["values"].get("qualified_preflight_finding")
        for r in measured
    )
    new_unit = facts["prediction_unit"] == "new_specimens"
    assessment = (
        ("observed" if new_unit else "conditional")
        if observed
        else "contradicted"
        if measured
        else None
    )
    return _warning(
        0,
        source,
        measured,
        assessment,
        "PHYSICAL_UNIT_EVIDENCE_UNAVAILABLE",
        "Declared shared-unit evidence is retained; it is not reconstructed from X."
        if observed
        else "This report does not establish shared physical units."
        if not measured
        else "Available declared-unit evidence does not show overlap in this scope.",
        "Observation-level partitioning could be optimistic for prediction of new units when shared specimens, technical repetitions or references cross the split.",
        [
            _check(
                "audit_declared_unit_overlap",
                "Use the declared identity/reference mapping and existing Preflight integrity controls to inspect overlap; evaluate a whole-unit contrast matching deployment.",
                [
                    "The objective is prediction of new specimens or independent reference units; the declared dependency applies to that objective."
                ],
                [
                    "Original specimen/reference membership",
                    "Actual split membership",
                    "Intended prediction unit",
                ],
                any(
                    r["binding"]
                    .get("qualifications", {})
                    .get("unit_memberships_available")
                    for r in measured
                ),
            )
        ],
        ["Physical and assay identities may be incomplete."],
        [
            "Repeated observations may be legitimate for within-unit monitoring.",
            "Shared context is not necessarily a shared physical specimen.",
        ],
        [
            "X-derived groups and repeated sample-key counts alone are not accepted physical-unit evidence; this layer does not duplicate Preflight's detector."
        ],
    )


def _factors(source, rows, facts):
    good = []
    for r in rows:
        q = r["binding"].get("qualifications", {})
        if (
            q.get("role") == "metadata"
            and q.get("role_reference")
            and not q.get("duplicated_from_target", True)
        ):
            eta = r["values"].get("eta_squared")
            eta = eta if isinstance(eta, list) else [eta]
            if any(v is not None for v in eta):
                good.append(r)
    positive = [
        r
        for r in good
        if any(
            v is not None and v > 0
            for v in (
                r["values"]["eta_squared"]
                if isinstance(r["values"]["eta_squared"], list)
                else [r["values"]["eta_squared"]]
            )
        )
    ]
    checks = []
    for r in positive:
        q = r["binding"]["qualifications"]
        name = q["factor"]
        relevant = any(
            f["name"] == name and f["relevant_to_intent"] for f in facts["factors"]
        )
        when = [
            f"If the intended deployment changes or excludes documented factor '{name}'; its relevance must be established."
        ]
        text = (
            f"Examine the declared '{name}' contrast with indivisible units and crossed factors preserved."
            if relevant
            else f"First establish whether '{name}' changes in deployment; a categorical column alone does not require GroupKFold/LOGO."
        )
        checks.append(
            _check(
                "factor_contrast:" + name,
                text,
                when,
                [
                    "Original factor memberships",
                    "Physical/reference dependencies",
                    "Crossed-factor coverage and deployment objective",
                ],
                relevant and q.get("factor_memberships_available", False),
            )
        )
    if not checks:
        checks = [
            _check(
                "qualify_non_target_factors",
                "Obtain non-target role evidence and original factor memberships before interpreting correspondence.",
                ["Documented experimental factors could be relevant to deployment."],
                ["Qualified metadata roles and keys"],
            )
        ]
    reason = (
        "TARGET_DERIVED_METADATA_EXCLUDED"
        if any(
            r["binding"].get("qualifications", {}).get("role") == "target"
            or r["binding"].get("qualifications", {}).get("duplicated_from_target")
            for r in rows
        )
        else "QUALIFIED_NON_TARGET_FACTOR_GEOMETRY_UNAVAILABLE"
    )
    return _warning(
        1,
        source,
        good,
        "conditional" if positive else "contradicted" if good else None,
        reason,
        "Nonzero descriptive factor-PC correspondence is observed independently of flat-cluster agreement."
        if positive
        else "No qualified non-target factor-PC correspondence is available."
        if not good
        else "Available factor-PC measurements show zero correspondence on the recorded axes.",
        "A factor associated with X may affect the applicability of a validation result when that factor changes in intended deployment.",
        checks,
        [
            "Cardinality, missing levels, acquisition weighting, repeat counts and confounding remain relevant."
        ],
        [
            "Chemistry, material composition, legitimate biological variation or instrument response may explain association."
        ],
        [
            "Nonzero eta-squared is not significance, causation, leakage or predicted failure; no severity threshold is used.",
            "Weak/negative cluster ARI does not negate continuous geometry. Y-derived metadata are excluded from primary evidence.",
            "Repeated acquisitions are not automatically independent specimen or reference units.",
            "Marginal associations do not separate crossed or confounded factors.",
        ],
    )


def _representations(source, rows):
    good = [
        r
        for r in rows
        if r["binding"].get("qualifications", {}).get("admissible") is True
    ]
    observations = []
    changed = False
    all_noise = False
    stable = False
    for r in good:
        q = r["binding"]["qualifications"]
        v = r["values"]
        used = {}
        distinct_representations = len(set(q.get("representations", []))) > 1
        for key in ("full_x_overlap", "pca_overlap"):
            if (
                distinct_representations
                and q.get("matched_queries") is True
                and v.get(key) is not None
            ):
                used[key] = v[key]
                changed |= v[key] < 1
        for key in ("partition_ari", "parameter_ari_min"):
            if (
                q.get("matched_observations") is True
                and (key == "parameter_ari_min" or distinct_representations)
                and not v.get("trivial_partition")
                and v.get(key) is not None
            ):
                used[key] = v[key]
                changed |= v[key] < 1
        if (
            distinct_representations
            and q.get("matched_observations") is True
            and all(v.get(k) is not None for k in ("pc1_before", "pc1_after"))
        ):
            used.update({k: v[k] for k in ("pc1_before", "pc1_after")})
            changed |= v["pc1_before"] != v["pc1_after"]
        for key in (
            "cluster_counts",
            "noise_fractions",
            "all_noise_settings",
            "trivial_partition",
            "native_refusals",
        ):
            if v.get(key) is not None:
                used[key] = v[key]
        all_noise |= (v.get("all_noise_settings") or 0) > 0
        if used:
            observations.append({**r, "values": used})
            stable |= any(
                k in used
                for k in (
                    "full_x_overlap",
                    "pca_overlap",
                    "partition_ari",
                    "parameter_ari_min",
                    "pc1_before",
                )
            )
    assessment = (
        "observed" if changed or all_noise else "contradicted" if stable else None
    )
    return _warning(
        2,
        source,
        observations,
        assessment,
        "NO_ADMISSIBLE_MATCHED_REPRESENTATION_EVIDENCE",
        "Recorded representations/settings change at least one measured aspect of organization."
        if changed
        else "A density setting computed an all-noise partition; continuous structure is not ruled out."
        if all_noise
        else "Recorded matched comparisons show no change on the available measures."
        if stable
        else "Informative comparisons are unavailable; recorded trivial partitions or native refusals do not establish absent continuous structure.",
        "A conclusion based on one representation or density setting may be specific to that assumption.",
        [
            _check(
                "representation_sensitivity",
                "Check whether the scientific conclusion persists across predefined physically admissible representations and density settings; inspect full-X neighbors separately from PCA geometry and partitions.",
                [
                    "The intended validation/preprocessing rationale relies on the observed organization."
                ],
                [
                    "Admissible representation definitions",
                    "Matched populations/query references",
                    "Original native settings",
                ],
                bool(observations),
            )
        ],
        [
            "Unavailable representations and resampling robustness remain separate evidence."
        ],
        [
            "Noise suppression, baseline/scale removal, real chemical variation and density thresholds can all change the result."
        ],
        [
            "No family is selected as a winner. Cluster counts are not physical populations.",
            "All-noise is computed, a trivial partition has no informative ARI, and native refusal is unavailable; none establishes absence of continuous structure.",
        ],
    )


def _support(source, rows):
    good = [
        r
        for r in rows
        if r["binding"].get("qualifications", {}).get("fit_scope") == "training_only"
        and r["binding"].get("qualifications", {}).get("evaluation_X_observed") is True
        and r["binding"].get("qualifications", {}).get("reference_population_id")
        == source["population_id"]
        and r["binding"].get("qualifications", {}).get("evaluation_population_id")
        and r["values"].get("n_evaluation", 0) is not None
        and (r["values"].get("n_evaluation") or 0) > 0
        and r["values"].get("n_exceedances") is not None
    ]
    positive = any(r["values"]["n_exceedances"] > 0 for r in good)
    return _warning(
        3,
        source,
        good,
        "conditional" if positive else "contradicted" if good else None,
        "TRAIN_FITTED_EVALUATION_X_SUPPORT_UNAVAILABLE",
        "Observed evaluation X exceeds the recorded training-fitted PC1 range."
        if positive
        else "No exceedance was observed on the recorded PC1 diagnostic."
        if good
        else "Training-fitted support for observed evaluation X is unavailable.",
        "Observed deployment/evaluation spectra may require extrapolation beyond the recorded training support.",
        [
            _check(
                "examine_spectral_support",
                "Examine extrapolation and domain overlap using train-fitted diagnostics and a validation contrast matching the intended deployment.",
                [
                    "The observed evaluation X represents the intended application population."
                ],
                [
                    "Training/evaluation population identities",
                    "Additional multivariate support evidence",
                ],
                bool(good),
            )
        ],
        [
            "Entirely unseen future X cannot be assessed by this observed-evaluation diagnostic."
        ],
        [
            "PC1 may describe benign scale variation or omit differences in other directions."
        ],
        [
            "This warning is evaluation-X-aware. One-PC exceedance is not predicted failure; zero exceedance is not full multivariate support."
        ],
    )


def _context(source, rows, resolved, facts):
    flags = {
        k: None
        for k in (
            "physical_units_known",
            "acquisition_context_known",
            "reference_units_known",
        )
    }
    for row in rows:
        flags.update({k: v for k, v in row["values"].items() if k in flags})
    if flags["physical_units_known"] is None and any(
        d["evidence"] in ("declared", "verified") and d["kind"] == "specimen"
        for d in facts["dependencies"]
    ):
        flags["physical_units_known"] = True
    questions = {
        "physical_units_known": "Which observations share a physical specimen or technical acquisition unit?",
        "acquisition_context_known": "Which instrument, session, date, site or experimental conditions apply?",
        "reference_units_known": "Which observations share an assay/reference measurement?",
    }
    missing = [text for k, text in questions.items() if flags[k] is not True]
    if facts["intended_use"] == "unknown":
        missing.append(
            "Is deployment within the experiment, on new units, or in a specified new context?"
        )
    return _warning(
        4,
        source,
        rows,
        "observed" if missing else "contradicted",
        "CONTEXT_NOT_REFERENCED",
        "The report leaves specific experimental/deployment questions unanswered."
        if missing
        else "The requested context fields are supplied; completeness beyond them is not certified.",
        "Missing context limits the validation/dependency questions that can be answered; unknown structure is not evidence of a dangerous dataset.",
        [
            _check(
                "obtain_experimental_context",
                "Obtain the original identity/context/reference mappings. Until then, report the limitations and use explicitly exploratory representation/support sensitivity without reconstructing physical groups.",
                ["The unanswered questions affect the intended deployment claim."],
                missing,
            )
        ],
        missing,
        [
            "Metadata may be missing from this report while existing elsewhere; spectral similarity cannot restore original experimental identities."
        ],
    )


def interpret(report, request):
    """Return an optional content-bound warning section; no source report mutation."""
    fingerprint(report)
    fingerprint(request)
    schema = _schema()
    Draft202012Validator(
        {"$ref": "#/$defs/request", "$defs": schema["$defs"]}
    ).validate(request)
    request = deepcopy(request)
    intent = validation_intent.interpret(report, request.get("validation_intent", {}))
    rows = _bindings(report, request)
    source = request["source"]
    facts = intent["facts"]
    result = {
        "protocol_version": PROTOCOL,
        "source_report": {
            "sha256": fingerprint(report),
            "hash_scope": "canonical_json_with_newline",
        },
        "request": request,
        "validation_intent": intent,
        "warnings": [
            _physical(source, rows["physical_units"], facts),
            _factors(source, rows["factor_geometry"], facts),
            _representations(source, rows["representation"]),
            _support(source, rows["spectral_support"]),
            _context(source, rows["context"], rows, facts),
        ],
        "limitations": LIMITS,
    }
    fingerprint(result)
    Draft202012Validator(schema).validate(result)
    return deepcopy(result)


def validate_annotation(report, annotation):
    Draft202012Validator(_schema()).validate(annotation)
    if fingerprint(interpret(report, annotation["request"])) != fingerprint(annotation):
        raise ValueError("Stale or altered structural-warning annotation")


def markdown(annotation):
    fingerprint(annotation)
    Draft202012Validator(_schema()).validate(annotation)
    source = annotation["request"]["source"]
    lines = [
        "## Conditional structural warnings",
        "",
        f"Protocol: `{PROTOCOL}`; source report SHA256 `{annotation['source_report']['sha256']}`.",
        "",
        f"Dataset `{source['dataset_id']}`, view `{source['source_id']}`, population `{source['population_id']}`, representation `{source['representation']}`.",
        "",
        "These findings guide verification; they are not a global dataset-risk grade.",
        "",
    ]
    for w in annotation["warnings"]:
        lines += [
            f"### {w['warning_id']}",
            "",
            f"Assessment: {w['value'] or w['reason']}.",
            "",
            "What was observed?",
            "",
            w["observation"]["value"]["description"]
            if w["observation"]["value"]
            else w["observation"]["reason"],
            "",
            "Why might it matter?",
            "",
            w["risk_hypothesis"],
            "",
            "What should be checked next?",
            "",
        ]
        for c in w["recommended_checks"]:
            lines += [
                f"- {c['description']} Conditions: {'; '.join(c['applies_when'])} Prerequisites: {'; '.join(c['required_information']) or 'none added'}. Testability: {c['testability']}."
            ]
        lines += [
            "",
            "What remains unknown?",
            "",
            *["- " + t for t in [*w["required_information"], *w["limitations"]]],
            "",
            "Evidence scope and coverage:",
            "",
            "```json",
            json.dumps(
                {"scope": w["evidence_scope"], "coverage": w["scientific_basis"]},
                indent=2,
            ),
            "```",
            "",
        ]
    lines.extend([validation_intent.markdown(annotation["validation_intent"])])
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("report")
    p.add_argument("--request", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    out = Path(a.out)
    rendered = out.with_suffix(".md")
    if out.resolve() == rendered.resolve() or any(
        x.resolve() in {Path(a.report).resolve(), Path(a.request).resolve()}
        for x in (out, rendered)
    ):
        p.error("Outputs must differ from source report/request")
    if out.exists() or rendered.exists():
        p.error("Outputs already exist")
    value = interpret(
        validation_intent._read(a.report), validation_intent._read(a.request)
    )
    atomic_json(out, value)
    rendered.write_text(markdown(value), encoding="utf-8", newline="\n")
    print(f"Annotation: {out}\nInterpretation: {rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
