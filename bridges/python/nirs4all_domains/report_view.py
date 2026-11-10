"""Standalone read-only presentation of existing Domains and Preflight reports."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

from . import comparison_interpretation as d3
from . import structural_warnings as d1
from . import validation_intent as d2
from .storage import encoded, fingerprint, safe_path

PROTOCOL = "domains.standalone_report.v1"
SCHEMA_PATH = Path(__file__).with_name("standalone-report.v1.schema.json")
CHECK_AVAILABILITY_NOTE = (
    "Testability describes referenced prerequisites. It does not mean that a new analysis is authorized or has been executed. "
    "Review existing evidence where available; new fits require a separate protocol and authorization. "
    "A check requiring information remains deferred until its original mappings or other stated prerequisites are available."
)
LIMITS = [
    "This report presents existing evidence; it fits no model, PCA or clustering.",
    "Warning hypotheses and checks are conditional, not probabilities of calibration failure or a global risk grade.",
    "Report hashes bind content, not authorship, source rights or physical/assay independence.",
    "Dataset IDs, X views, populations, targets and representations are not independent studies.",
    "Unknown identities, original databases and independence remain unknown; absent warnings are not safety certificates.",
    "Native Preflight observations remain separate; similarly named Domains metrics are not substituted.",
]


def _slot(annotation=None, reason="COMPANION_NOT_SUPPLIED"):
    return {
        "status": "computed" if annotation is not None else "unavailable",
        "reason": None if annotation is not None else reason,
        "value": deepcopy(annotation),
        "sha256": fingerprint(annotation) if annotation is not None else None,
        "protocol_version": annotation["protocol_version"]
        if annotation is not None
        else None,
    }


def _native(report):
    required = (
        "engine_version",
        "protocol_bundle_version",
        "metrics",
        "findings",
        "validation",
        "capabilities",
    )
    if report.get("schema_version") != 1 or not all(k in report for k in required):
        return {
            "status": "unavailable",
            "reason": "NO_SUPPORTED_NATIVE_REPORT_PROJECTION",
            "value": None,
        }
    metrics = []
    for metric in report["metrics"]:
        if not isinstance(metric, dict):
            raise TypeError("INVALID_PREFLIGHT_METRIC_OBJECT")
        scalar = metric.get("value")
        scalar = (
            scalar
            if scalar is None or isinstance(scalar, (str, bool, int, float))
            else None
        )
        metrics.append(
            {
                **{
                    k: deepcopy(metric.get(k))
                    for k in (
                        "metric_id",
                        "protocol_version",
                        "status",
                        "reason_code",
                        "source_id",
                        "target_id",
                        "view_id",
                        "population_id",
                        "unit",
                        "parameters",
                        "denominators",
                    )
                },
                "displayed_scalar": scalar,
                "display_limit": "Non-scalar payload remains in the original report"
                if metric.get("value") is not None and scalar is None
                else None,
            }
        )
    return {
        "status": "computed",
        "reason": None,
        "value": {
            "engine_version": report["engine_version"],
            "protocol_bundle_version": report["protocol_bundle_version"],
            "profile_status": report.get("profile_status"),
            "native_status": report.get("status"),
            "metrics": metrics,
            "findings": deepcopy(report["findings"]),
            "limitations": deepcopy(report.get("limitations", [])),
            "identity_limit": "Native schema1 alone does not provide canonical dataset/content identity; no identity is invented.",
        },
    }


def _case(spec):
    allowed = {
        "case_id",
        "label",
        "report",
        "d1",
        "d2",
        "d3",
        "comparison_report",
        "source_ref",
    }
    if (
        set(spec) - allowed
        or not isinstance(spec.get("case_id"), str)
        or not spec["case_id"]
    ):
        raise ValueError("INVALID_STANDALONE_CASE_SPECIFICATION")
    report = spec["report"]
    if not isinstance(report, dict):
        raise TypeError("REPORT_OBJECT_REQUIRED")
    fingerprint(report)
    a1, a2, a3 = spec.get("d1"), spec.get("d2"), spec.get("d3")
    if a1 is not None:
        d1.validate_annotation(report, a1)
        if a2 is None:
            a2 = a1["validation_intent"]  # reuse an already computed companion
    if a2 is not None:
        d2.validate_annotation(report, a2)
        if a1 is not None and fingerprint(a2) != fingerprint(a1["validation_intent"]):
            raise ValueError("D1_D2_INTENT_MISMATCH")
    sources = {
        "reference": {
            "sha256": fingerprint(report),
            "hash_scope": "canonical_json_with_newline",
        }
    }
    if a3 is not None:
        if a1 is not None:
            raise ValueError("D1_D3_SCOPE_CROSSWALK_REQUIRED_USE_SEPARATE_CASES")
        stress = spec.get("comparison_report")
        if not isinstance(stress, dict):
            raise ValueError("D3_REQUIRES_EXPLICIT_COMPARISON_REPORT")
        d3.validate_annotation(report, stress, a3)
        if a2 is None:
            a2 = a3["validation_intent"]["reference"]
            d2.validate_annotation(report, a2)
        sources["stress"] = {
            "sha256": fingerprint(stress),
            "hash_scope": "canonical_json_with_newline",
        }
        # A D3 reference intent may add its own metric pointers. The declared
        # deployment facts must nevertheless agree with a separately supplied D2.
        if a2 is not None:
            for key in (
                "intended_use",
                "prediction_population",
                "prediction_unit",
                "split",
                "dependencies",
                "factors",
                "groups",
                "transductive",
            ):
                if (
                    a2["facts"][key]
                    != a3["validation_intent"]["reference"]["facts"][key]
                ):
                    raise ValueError("D2_D3_INTENT_MISMATCH:" + key)
    identity = deepcopy(a1["request"]["source"]) if a1 is not None else None
    counts = (
        Counter(
            w["value"] if w["status"] == "computed" else "unavailable"
            for w in a1["warnings"]
        )
        if a1 is not None
        else Counter()
    )
    return {
        "case_id": spec["case_id"],
        "label": spec.get("label", spec["case_id"]),
        "source_ref": spec.get("source_ref"),
        "source_reports": sources,
        "identity": {
            "status": "computed" if identity else "unavailable",
            "reason": None if identity else "NO_QUALIFIED_D1_SOURCE_IDENTITY",
            "value": identity,
        },
        "companions": {
            "d1": _slot(a1, "D1_COMPANION_NOT_SUPPLIED"),
            "d2": _slot(a2, "D2_COMPANION_NOT_SUPPLIED"),
            "d3": _slot(a3, "D3_COMPANION_NOT_SUPPLIED"),
        },
        "warning_counts": {
            k: counts[k]
            for k in ("observed", "conditional", "contradicted", "unavailable")
        },
        "native_preflight": _native(report),
    }


def build_report(cases, title="Observations and conditional analyses to consider"):
    """Validate original owner companions and build a presentation-only view."""
    if not isinstance(cases, list) or not cases or len(cases) > 128:
        raise ValueError("ONE_TO_128_CASES_REQUIRED")
    rows = [_case(c) for c in cases]
    if len({c["case_id"] for c in rows}) != len(rows):
        raise ValueError("DUPLICATE_CASE_ID")
    sources = [
        c["identity"]["value"] for c in rows if c["identity"]["status"] == "computed"
    ]
    canonical = sorted(
        {
            s["dataset_id"]
            for s in sources
            if s["identity_scope"] == "current_canonical_id"
        }
    )
    synthetic = sorted(
        {s["dataset_id"] for s in sources if s["scope_kind"] == "synthetic"}
    )
    annotations = {
        (s["protocol_version"], s["sha256"])
        for c in rows
        for s in c["companions"].values()
        if s["status"] == "computed"
    }
    coverage = {
        "n_cases": len(rows),
        "n_unique_source_reports": len(
            {s["sha256"] for c in rows for s in c["source_reports"].values()}
        ),
        "n_unique_annotations": len(annotations),
        "canonical_dataset_ids": canonical,
        "n_canonical_dataset_ids": len(canonical),
        "synthetic_dataset_ids": synthetic,
        "n_synthetic_dataset_ids": len(synthetic),
        "all_declared_dataset_ids": sorted({s["dataset_id"] for s in sources}),
        "canonical_X_views": [
            {"dataset_id": d, "source_id": v}
            for d, v in sorted(
                {
                    (s["dataset_id"], s["source_id"])
                    for s in sources
                    if s["identity_scope"] == "current_canonical_id"
                }
            )
        ],
        "n_unidentified_cases": sum(
            c["identity"]["status"] != "computed" for c in rows
        ),
        "documented_provenance_groups": sorted(
            {
                s["provenance_group"]
                for s in sources
                if s.get("provenance_group") and s["references"]
            }
        ),
        "original_source_identifiers": sorted(
            {v for s in sources for v in s["original_source_identifiers"]}
        ),
        "original_database_count": "unknown",
        "independent_study_count": "unknown",
        "warning_record_counts": {
            k: sum(c["warning_counts"][k] for c in rows)
            for k in ("observed", "conditional", "contradicted", "unavailable")
        },
        "companion_slot_counts": {
            kind: dict(Counter(c["companions"][kind]["status"] for c in rows))
            for kind in ("d1", "d2", "d3")
        },
        "new_scientific_fits": 0,
        "interpretation": "Counts describe presented saved cases and existing annotations, not independent studies, new scientific observations or failure prevalence.",
    }
    view = {
        "protocol_version": PROTOCOL,
        "title": title,
        "coverage": coverage,
        "cases": rows,
        "limitations": LIMITS,
    }
    fingerprint(view)
    Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))).validate(
        view
    )
    return view


def _sections(case):
    """Common presentation sections; no scientific decision or numeric estimate."""
    out = []
    intent = case["companions"]["d2"]
    if intent["status"] == "computed":
        facts = intent["value"]["facts"]
        out += [
            ("Declared prediction objective", facts["intended_use"], "text"),
            (
                "Intended prediction population",
                facts["prediction_population"]
                or "Not supplied; conditional interpretations follow.",
                "text",
            ),
            ("Intended prediction unit", facts["prediction_unit"], "text"),
            (
                "Actual evaluation split",
                facts["split"]["family"]
                + " / "
                + (
                    facts["split"].get("description")
                    or "No further split description supplied."
                ),
                "text",
            ),
            (
                "Declared dependency, factor and grouping evidence",
                {
                    k: facts[k]
                    for k in ("dependencies", "factors", "groups", "transductive")
                },
                "json",
            ),
        ]
    else:
        out.append(
            (
                "Declared prediction objective",
                "Unavailable: no validated intended-use companion supplied.",
                "text",
            )
        )
    out += [
        ("Source and scope", case["identity"], "json"),
        ("Source report hashes", case["source_reports"], "json"),
    ]
    native = case["native_preflight"]
    if native["status"] == "computed":
        out.append(
            (
                "Native Preflight observations and findings (separate)",
                native["value"],
                "json",
            )
        )
    a1 = case["companions"]["d1"]
    if a1["status"] == "computed":
        warnings = a1["value"]["warnings"]
        ordered = [w for w in warnings if w["status"] == "computed"] + [
            w for w in warnings if w["status"] != "computed"
        ]
        for w in ordered:
            label = (
                w["warning_id"].replace("_", " ")
                + " / "
                + (w["value"] or "unavailable")
            )
            if w["status"] != "computed":
                label += " (not assessable)"
                out.append(("Why this finding is not assessable", w["reason"], "text"))
            out += [
                (label, w["reason"] or w["value"], "heading"),
                (
                    "What was observed?",
                    w["observation"]["value"]["description"]
                    if w["observation"]["value"]
                    else w["observation"]["reason"],
                    "text",
                ),
                ("Conditional methodological hypothesis", w["risk_hypothesis"], "text"),
                (
                    "Recorded measurements (unchanged)",
                    (w["observation"]["value"] or {}).get("measurements", []),
                    "measurements",
                ),
                ("When could it matter?", w["conditions"], "list"),
                ("What should be checked next?", w["recommended_checks"], "checks"),
                (
                    "Information needed for interpretation",
                    w["required_information"],
                    "list",
                ),
                (
                    "Alternatives and limits",
                    [*w["alternative_explanations"], *w["limitations"]],
                    "details",
                ),
                (
                    "Exact observation provenance and scope",
                    {
                        "measurements": (w["observation"]["value"] or {}).get(
                            "measurements", []
                        ),
                        "scope": w["evidence_scope"],
                        "scientific_basis": w["scientific_basis"],
                    },
                    "json",
                ),
            ]
    else:
        out.append(("Structural warnings (D1) unavailable", a1["reason"], "text"))
    for kind in ("d2", "d3"):
        slot = case["companions"][kind]
        if slot["status"] != "computed":
            out.append((kind.upper() + " unavailable", slot["reason"], "text"))
            continue
        a = slot["value"]
        if kind == "d2":
            for reading in a["interpretations"]:
                out += [
                    (
                        "Validation interpretation: " + reading["intended_use"],
                        reading["conditions"],
                        "list",
                    ),
                    ("Claims supported", reading["supported_claims"], "list"),
                    (
                        "Stronger claims not established",
                        reading["stronger_claims_not_established"],
                        "list",
                    ),
                ]
            out += [
                ("Missing evaluation information", a["missing_information"], "list"),
                ("Validation interpretation limits", a["limitations"], "details"),
            ]
        else:
            out += [
                ("Prediction comparison (D3)", a["direct_comparison"], "text"),
                (
                    "Existing performance and contrast",
                    {
                        k: a[k]
                        for k in (
                            "performance",
                            "rmse_difference",
                            "relative_rmse_deterioration",
                            "evaluation_matching",
                            "baseline_context",
                        )
                    },
                    "json",
                ),
                ("Comparison claims supported", a["supported_claims"], "list"),
                (
                    "Comparison claims not established",
                    a["stronger_claims_not_established"],
                    "list",
                ),
                ("Comparison limits", a["limitations"], "details"),
                ("Exact comparison conditions", a["context"], "json"),
                (
                    "Reference and stress deployment interpretations",
                    a["validation_intent"],
                    "json",
                ),
            ]
    out.append(
        (
            "Annotation hashes and protocols",
            {
                k: {
                    "status": s["status"],
                    "reason": s["reason"],
                    "protocol_version": s["protocol_version"],
                    "sha256": s["sha256"],
                }
                for k, s in case["companions"].items()
            },
            "json",
        )
    )
    return out


def _validate_view(view):
    fingerprint(view)
    Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))).validate(
        view
    )


def _render_html(view):
    _validate_view(view)
    esc = lambda v: html.escape(str(v), quote=True)
    listing = lambda values: (
        "<ul>" + "".join("<li>" + esc(v) + "</li>" for v in values) + "</ul>"
    )
    parts = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:; base-uri \'none\'"><title>'
        + esc(view["title"])
        + "</title><style>body{font:16px/1.5 system-ui,sans-serif;max-width:78rem;margin:auto;padding:1.5rem;color:#202428;background:#fff;overflow-wrap:anywhere}section{border-top:1px solid #999;padding-top:1rem;margin-top:2rem}h2,h3{overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.85rem}details{border-left:2px solid #999;padding-left:1rem;margin:1rem 0}nav a{display:inline-block;max-width:100%;overflow-wrap:anywhere;margin:.25rem .75rem .25rem 0}table{border-collapse:collapse;width:100%;table-layout:fixed}td,th{border:1px solid #aaa;text-align:left;padding:.4rem;overflow-wrap:anywhere}summary{cursor:pointer}</style></head><body><h1>"
        + esc(view["title"])
        + "</h1>",
        "<p>Saved observations, plausible methodological concerns, proposed checks and scientific limits. No global risk grade; an absent warning is not a safety certificate.</p>",
        "<p>" + esc(CHECK_AVAILABILITY_NOTE) + "</p>",
        "<p>"
        + esc(
            str(view["coverage"]["n_cases"])
            + " saved cases; "
            + str(view["coverage"]["n_canonical_dataset_ids"])
            + " declared canonical dataset IDs; "
            + str(len(view["coverage"]["canonical_X_views"]))
            + " canonical dataset/source X views. Original databases and independent studies: unknown."
        )
        + "</p><details><summary>Exact coverage and denominators</summary><pre>"
        + esc(json.dumps(view["coverage"], indent=2, ensure_ascii=False))
        + "</pre></details>",
        listing(view["limitations"]),
        '<nav aria-label="Report cases">'
        + "".join(
            f'<a href="#case-{i}">{esc(c["label"])}</a>'
            for i, c in enumerate(view["cases"])
        )
        + "</nav>",
    ]
    for i, c in enumerate(view["cases"]):
        parts.append(f'<section id="case-{i}"><h2>{esc(c["label"])}</h2>')
        for title, value, kind in _sections(c):
            if kind == "json":
                parts.append(
                    "<details><summary>"
                    + esc(title)
                    + "</summary><pre>"
                    + esc(json.dumps(value, indent=2, ensure_ascii=False))
                    + "</pre></details>"
                )
            elif kind == "details":
                parts.append(
                    "<details><summary>"
                    + esc(title)
                    + "</summary>"
                    + listing(value)
                    + "</details>"
                )
            elif kind == "checks":
                parts.append(
                    "<h4>"
                    + esc(title)
                    + "</h4>"
                    + "".join(
                        "<p>"
                        + esc(check["description"])
                        + "</p><p>Applies when:</p>"
                        + listing(check["applies_when"])
                        + "<p>Required data:</p>"
                        + listing(check["required_information"])
                        + "<p>Testability: "
                        + esc(check["testability"])
                        + "</p>"
                        for check in value
                    )
                )
            elif kind == "measurements":
                parts.append(
                    "<h4>"
                    + esc(title)
                    + "</h4><table><thead><tr><th>Recorded metric</th><th>Original value/state</th><th>Declared factor</th></tr></thead><tbody>"
                    + "".join(
                        "<tr><td>"
                        + esc(key)
                        + "</td><td>"
                        + esc(json.dumps(v, ensure_ascii=False))
                        + "</td><td>"
                        + esc(m.get("qualifications", {}).get("factor", ""))
                        + "</td></tr>"
                        for m in value
                        for key, v in m["values"].items()
                    )
                    + "</tbody></table>"
                )
            else:
                parts.append(
                    ("<h3>" if kind == "heading" else "<h4>")
                    + esc(title)
                    + ("</h3>" if kind == "heading" else "</h4>")
                    + (
                        listing(value)
                        if kind == "list"
                        else "<p>" + esc(value) + "</p>"
                    )
                )
        parts.append("</section>")
    # No executable script. JSON is preserved as escaped text, with exact hashes.
    parts += [
        '<details><summary>Complete view JSON, exact validated annotations and provenance</summary><pre id="domains-view-data">'
        + esc(encoded(view).decode())
        + "</pre></details></body></html>"
    ]
    return "\n".join(parts) + "\n"


def _md(value):
    return re.sub(
        r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", html.escape(str(value), quote=False)
    )


def _render_markdown(view):
    _validate_view(view)
    lines = [
        "# " + _md(view["title"]),
        "",
        *["- " + _md(v) for v in view["limitations"]],
        "",
        CHECK_AVAILABILITY_NOTE,
        "",
        "## Coverage",
        "",
        "```json",
        json.dumps(view["coverage"], indent=2, ensure_ascii=True),
        "```",
        "",
    ]
    for c in view["cases"]:
        lines += ["## " + _md(c["label"]), ""]
        for title, value, kind in _sections(c):
            lines += ["### " + _md(title), ""]
            if kind in ("json", "measurements"):
                # JSON strings escape embedded newlines; no source can close this fence.
                lines += [
                    "```json",
                    json.dumps(value, indent=2, ensure_ascii=True).replace(
                        "`", "\\u0060"
                    ),
                    "```",
                    "",
                ]
            elif kind in ("list", "details"):
                lines += [*["- " + _md(v) for v in value], ""]
            elif kind == "checks":
                for check in value:
                    lines += [
                        _md(check["description"]),
                        "",
                        "Applies when:",
                        "",
                        *["- " + _md(v) for v in check["applies_when"]],
                        "",
                        "Required data:",
                        "",
                        *["- " + _md(v) for v in check["required_information"]],
                        "",
                        "Testability: " + _md(check["testability"]),
                        "",
                    ]
            else:
                lines += [_md(value), ""]
    return "\n".join(lines).rstrip() + "\n"


def render_report(cases, title="Observations and conditional analyses to consider"):
    """Validate against original sources before rendering any scientific claims."""
    view = build_report(cases, title)
    return {
        "view": view,
        "html": _render_html(view),
        "markdown": _render_markdown(view),
    }


def export_report(
    cases,
    prefix,
    protected=(),
    title="Observations and conditional analyses to consider",
):
    rendered = render_report(cases, title)
    view = rendered["view"]
    prefix = Path(prefix)
    outputs = {ext: prefix.with_suffix("." + ext) for ext in ("html", "md", "json")}
    protected = {Path(p).resolve() for p in protected}
    if any(p.exists() or p.resolve() in protected for p in outputs.values()):
        raise ValueError("OUTPUT_EXISTS_OR_WOULD_OVERWRITE_SOURCE")
    data = {
        "html": rendered["html"].encode(),
        "md": rendered["markdown"].encode(),
        "json": encoded(view),
    }
    for ext, p in outputs.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("xb") as stream:
            stream.write(data[ext])
    return {
        k: {"file": p.name, "sha256": __import__("hashlib").sha256(data[k]).hexdigest()}
        for k, p in outputs.items()
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?")
    parser.add_argument("--manifest")
    parser.add_argument("--d1")
    parser.add_argument("--d2")
    parser.add_argument("--d3")
    parser.add_argument("--comparison-report")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    protected = []

    def read(path):
        protected.append(Path(path))
        return d2._read(path)

    if args.manifest:
        if args.report or args.d1 or args.d2 or args.d3 or args.comparison_report:
            parser.error("Manifest and individual input options are mutually exclusive")
        manifest = read(args.manifest)
        if set(manifest) - {"title", "cases"}:
            raise ValueError("UNKNOWN_MANIFEST_FIELD")
        base = Path(args.manifest).resolve().parent
        specs = []
        for row in manifest["cases"]:
            if set(row) - {
                "case_id",
                "label",
                "report",
                "d1",
                "d2",
                "d3",
                "comparison_report",
            }:
                raise ValueError("UNKNOWN_MANIFEST_CASE_FIELD")
            case = {k: row[k] for k in ("case_id", "label") if k in row}
            for key in ("report", "d1", "d2", "d3", "comparison_report"):
                if row.get(key) is not None:
                    case[key] = read(safe_path(base, row[key]))
            case["source_ref"] = row["report"]
            specs.append(case)
        title = manifest.get(
            "title", "Saved structural evidence and conditional analyses"
        )
    else:
        if not args.report:
            parser.error("A source report or manifest is required")
        spec = {
            "case_id": "report",
            "source_ref": Path(args.report).name,
            "report": read(args.report),
        }
        for key in ("d1", "d2", "d3", "comparison_report"):
            if getattr(args, key):
                spec[key] = read(getattr(args, key))
        specs = [spec]
        title = "Observations and conditional analyses to consider"
    result = export_report(specs, args.out, protected, title)
    print(json.dumps({"protocol": PROTOCOL, "cases": len(specs), "artifacts": result}))


if __name__ == "__main__":
    main()
