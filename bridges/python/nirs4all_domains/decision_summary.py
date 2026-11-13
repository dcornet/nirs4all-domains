"""Presentation-only D6.1 reading of already validated companion objects.

No scientific states, metrics, thresholds, grants or split choices are produced.
The existing report consumer owns validation and rendering of this optional view.
"""

from copy import deepcopy
import json

PROTOCOL = "domains.decision_summary.v1"
METADATA_SCOPE = (
    "Missing or false context/physical/reference-unit flags describe information not "
    "documented or transported in the evidence qualified for this analysis. Absence "
    "from the original source has not been established."
)
NOT_ESTABLISHED = [
    "Causal shortcuts, leakage, future prediction error and independent external generalization are not established by these X observations.",
    "Spectral clusters and categorical factor labels do not certify physical specimens, shared-reference independence or new experimental populations.",
    "No preprocessing winner, universal validation protocol, severity grade or probability of failure is selected.",
]


def _annotation(case, name):
    slot = case["companions"].get(name, {})
    return slot.get("value") if slot.get("status") == "computed" else None


def _state(record, name):
    item = record[name]
    return item["value"] if item["status"] == "computed" else "unknown"


def _brief_mechanism(item):
    values = item["values"]
    if item["kind"] == "density_parameter":
        text = (
            "Density-parameter comparison: "
            + " → ".join(str(n) for n in values.get("cluster_counts", []))
            + " clusters; parameter ARI = "
            + str(values.get("parameter_ari_min", "unavailable"))
            + ". This is not a measured preprocessing effect."
        )
    elif item["kind"] == "representation":
        text = (
            "Spectral-representation comparison: partition ARI = "
            + str(values.get("partition_ari", "unavailable"))
            + ". Density-parameter sensitivity is a separate comparison."
        )
    elif item["kind"] == "neighborhood":
        text = (
            "Mean neighbor intersection / k: "
            + ", ".join(
                ("full-X" if k == "full_x_overlap" else "PCA") + " = " + str(v)
                for k, v in values.items()
            )
            + "; not Jaccard."
        )
    elif item["kind"] == "partition_noninformative_or_unavailable":
        text = "Computed all-noise/trivial partitions or unavailable comparisons do not supply informative partition ARI or exclude continuous structure."
    else:
        text = (
            "Admissible recorded comparison; the mechanism is not separately qualified."
        )
    if item["finding"] == "contradicted":
        text = (
            "No variation detected in this recorded comparison; no active sensitivity caution on this aspect. "
            + text
        )
    return text


def mechanisms(warning):
    """Name only the measured mechanism qualified in the original observation."""
    out = []
    for m in (warning["observation"]["value"] or {}).get("measurements", []):
        q, v = m["qualifications"], m["values"]
        settings = m["method"]["settings"]
        informative = not (v.get("trivial_partition") or v.get("all_noise_settings"))
        admissible = (
            q.get("admissible") is True and q.get("matched_observations") is True
        )
        finding = warning["value"] if warning["status"] == "computed" else "unavailable"
        active = finding == "observed" and informative and admissible

        def add(kind, description, keys, caution):
            out.append(
                {
                    "kind": kind,
                    "finding": finding,
                    "active_sensitivity_caution": caution,
                    "description": description,
                    "values": {k: deepcopy(v[k]) for k in keys if k in v},
                    "scope": deepcopy(warning["evidence_scope"]),
                    "recorded_density_settings": deepcopy(
                        settings.get("actual_native_configuration", {}).get(
                            "HDBSCAN", []
                        )
                    ),
                    "method_reference": m["method"]["reference"],
                }
            )

        if not informative or finding == "unavailable" or not admissible:
            add(
                "partition_noninformative_or_unavailable",
                "Partition non-informative or unavailable: computed all-noise/trivial partitions and native refusals do not exclude continuous structure or establish safety. Partition ARI remains uninformative/unavailable where recorded.",
                (
                    "all_noise_settings",
                    "trivial_partition",
                    "native_refusals",
                    "cluster_counts",
                    "parameter_ari_min",
                    "partition_ari",
                ),
                False,
            )
        else:
            kind = q.get("comparison_kind")
            if kind == "density_parameter" or "parameter_ari_min" in v:
                add(
                    "density_parameter",
                    "Sensitivity to density parameters on the same recorded spectral representation. Cluster-count variation and parameter ARI describe settings, not preprocessing effects or physical populations.",
                    ("cluster_counts", "noise_fractions", "parameter_ari_min"),
                    active,
                )
            if kind == "representation":
                add(
                    "representation",
                    "Sensitivity to a spectral-representation change in this admissible matched population. The cross-representation partition ARI is separate from density-parameter ARI; no representation is selected as superior.",
                    ("partition_ari",),
                    active,
                )
            if (
                kind not in ("representation", "density_parameter")
                and "parameter_ari_min" not in v
            ):
                add(
                    "comparison_mechanism_unspecified",
                    "Recorded admissible comparison; its mechanism is not separately qualified. Do not rename it a preprocessing or density effect.",
                    ("partition_ari",),
                    False,
                )
        if admissible and q.get("matched_queries") is True:
            keys = [k for k in ("full_x_overlap", "pca_overlap") if k in v]
            if keys:
                add(
                    "neighborhood",
                    "Recorded mean neighbor intersection / k, separately for full-X and PCA where available; this is not Jaccard. Values describe the recorded queries/reference scope only.",
                    keys,
                    active,
                )
        if finding == "contradicted":
            for item in out:
                item["active_sensitivity_caution"] = False
                item["description"] = (
                    "No change detected on the available measures in this recorded comparison; no active sensitivity caution on this aspect. This does not establish universal stability. "
                    + item["description"]
                )
    if not out:
        out.append(
            {
                "kind": "partition_noninformative_or_unavailable",
                "finding": "unavailable",
                "active_sensitivity_caution": False,
                "description": "No qualified sensitivity comparison is available; this is not evidence of absent risk.",
                "values": {},
                "scope": deepcopy(warning["evidence_scope"]),
                "recorded_density_settings": [],
                "method_reference": warning["observation"]["reason"]
                or warning["reason"],
            }
        )
    return out


def _factor_questions(parent, facts):
    measured = {}
    for w in parent["warnings"]:
        if (
            w["warning_id"] != "experimental_factor_structure"
            or w["status"] != "computed"
            or w["value"] not in ("observed", "conditional")
        ):
            continue
        for m in (w["observation"]["value"] or {}).get("measurements", []):
            if m["kind"] == "factor_geometry" and m["qualifications"].get("factor"):
                if (
                    m["qualifications"].get("role") != "metadata"
                    or m["qualifications"].get("duplicated_from_target") is not False
                ):
                    continue
                measured[m["qualifications"]["factor"]] = m
    declared = {f["name"]: f for f in facts.get("factors", [])}
    questions = []
    for name, m in measured.items():
        relevance = declared.get(name, {}).get("relevant_to_intent")
        if relevance is True and facts.get("intended_use") != "unknown":
            question = (
                "For the declared prediction population, qualify the units, original memberships, references and crossed factors for "
                + name
                + ". "
                "Only if these keys and the intended novelty are qualified, examine a factor-excluded contrast matching that objective; this is a conditional investigation, not a split recommendation."
            )
        elif relevance is False:
            question = (
                "Inspect representation of the recorded "
                + name
                + " levels and acquisition/session/repeat/reference units within the declared context; exclusion of this factor is not automatically necessary."
            )
        else:
            question = (
                "Clarify whether "
                + name
                + " changes in the intended prediction population; qualify crossed context/preparation/acquisition/specimen units before a targeted contrast."
            )
        questions.append(
            {
                "factor": name,
                "relevance_to_declared_intent": relevance,
                "question": question,
                "values": deepcopy(m["values"]),
                "membership_evidence": m["qualifications"].get(
                    "factor_memberships_available"
                ),
                "limit": "Association is descriptive, not causal leakage, error degradation or certified biological independence.",
            }
        )
    if "date" in measured and "measurement_date" in measured:
        if measured["date"]["values"] == measured["measurement_date"]["values"]:
            questions.append(
                {
                    "factor": "date / measurement_date",
                    "relevance_to_declared_intent": None,
                    "question": "These date fields carry identical reported statistics and may be aliases. Do not count them as independent confirmations; qualify their mapping and date/site/treatment crossings first.",
                    "values": {},
                    "membership_evidence": None,
                    "limit": "Matching aggregate statistics do not by themselves prove identical original memberships.",
                }
            )
    return questions


def _action_reading(record):
    if record["action_kind"] == "review_saved_evidence":
        return "Read existing evidence; an execution receipt, when present, covers this exact documentary action only."
    check = record["check_id"]
    if check == "obtain_experimental_context" or record["action"].startswith(
        "First establish"
    ):
        return "Clarification/documentary prerequisite first; the legacy new_analysis label does not imply a new chemometric fit. Any subsequent analysis is separate."
    return "Review existing measurements and qualify metadata first; any proposed new scientific calculation requires its own qualified protocol and authorization."


def summarize(case):
    parent = _annotation(case, "d1")
    intent = _annotation(case, "d2")
    ready = _annotation(case, "readiness")
    facts = intent["facts"] if intent else {}
    observed, why, now, needs = [], [], [], []
    mechanism_rows = []
    if not parent:
        observed.append(
            "No qualified D1 structural companion or readiness crosswalk is supplied. Keep existing D2/D3 conclusions and refusals unchanged; no additional D6 benefit is established."
        )
    else:
        for w in parent["warnings"]:
            if w["warning_id"] == "preprocessing_dependent_organization":
                mechanism_rows = mechanisms(w)
            elif w["status"] == "computed" and w["observation"]["value"]:
                observed.append(w["observation"]["value"]["description"])
                if w["warning_id"] == "spectral_support_mismatch":
                    for m in w["observation"]["value"].get("measurements", []):
                        if (
                            "n_exceedances" in m["values"]
                            and "n_evaluation" in m["values"]
                        ):
                            observed.append(
                                "Recorded support counts: n_exceedances="
                                + str(m["values"]["n_exceedances"])
                                + "; n_evaluation="
                                + str(m["values"]["n_evaluation"])
                                + ". This reading covers these observed evaluation X only, not an unobserved future context."
                            )
        if mechanism_rows:
            for m in mechanism_rows:
                observation = _brief_mechanism(m)
                if m["values"]:
                    observed.insert(0, observation)
                else:
                    observed.append(observation)
        now.append(
            "Read the existing recorded measurements and their exact population, representation and native settings; this documentary review performs no new fit."
        )
    if facts.get("intended_use", "unknown") == "unknown":
        now.insert(
            0,
            "First clarify which new unit or context will be predicted and the intended population. Do not prescribe GroupKFold/LOGO before that clarification.",
        )
        why.append(
            "Relevance to deployment is unknown; several conditional interpretations remain possible."
        )
    else:
        why.append(
            "Declared objective: "
            + (facts.get("prediction_population") or "population not documented")
            + "; prediction unit: "
            + facts.get("prediction_unit", "unknown")
            + "."
        )
        if facts["intended_use"] == "proof_of_concept":
            why.append(
                "Within-experiment proof of concept does not automatically require exclusion of batches or other categorical factors, and does not establish external transfer."
            )
        if facts.get("prediction_unit") == "new_acquisitions":
            now.append(
                "Inspect session/repetition/reference documentation for additional acquisitions; known context labels do not establish independent new specimens."
            )
    factors = _factor_questions(parent, facts) if parent else []
    if factors:
        names = sorted({x["factor"] for x in factors if x["values"]})
        why.append(
            "Recorded factor associations: "
            + ", ".join(names)
            + ". Effects for other factors mentioned only in the objective are not measured by these associations."
        )
        if (
            "treatment" in (facts.get("prediction_population") or "").lower()
            and "treatment" not in names
        ):
            why.insert(
                1,
                "No treatment association is documented in these measurements; qualify date/site/treatment confounding and crossings before attributing a treatment effect.",
            )
        if "site" in names:
            why.insert(
                2
                if "treatment" in (facts.get("prediction_population") or "").lower()
                else 1,
                "A site association does not establish a preparation/grinding effect; qualify site/preparation/specimen crossings and the kind of intended novelty.",
            )
        now.append(
            "Review the documented factor-to-objective questions below; their plausibility is separate from the selected D6 check's readiness."
        )
        if facts.get("intended_use", "unknown") != "unknown":
            relevant = [
                f["factor"]
                for f in factors
                if f["relevance_to_declared_intent"] is True
            ]
            names_to_qualify = relevant or [f["factor"] for f in factors if f["values"]]
            now.insert(
                0,
                "Qualify the documented "
                + ", ".join(names_to_qualify)
                + " mappings, physical/reference units and crossed factors against the declared novelty. Any factor-specific scientific contrast remains conditional, separately unqualified and unscheduled.",
            )
    readings = []
    for r in (ready or {}).get("records", []):
        states = {
            k: _state(r, k)
            for k in (
                "applicability",
                "inputs",
                "protocol",
                "authorization",
                "execution",
            )
        }
        readings.append(
            {
                "record_id": r["record_id"],
                "action": r["action"],
                "legacy_action_kind": r["action_kind"],
                "presentation": _action_reading(r),
                **states,
            }
        )
        if states["applicability"] == "inapplicable":
            needs.append(
                "Selected check "
                + r["record_id"]
                + " is inapplicable to the declared objective; do not prescribe it."
            )
            continue
        if states["applicability"] == "unknown":
            needs.append(
                "Applicability of "
                + r["record_id"]
                + " is unknown; clarify relevance before prescribing it."
            )
        needs.append(
            "Selected check "
            + r["record_id"]
            + ": inputs "
            + states["inputs"].replace("_", " ")
            + "; protocol "
            + states["protocol"].replace("_", " ")
            + "; authorization "
            + states["authorization"].replace("_", " ")
            + "; execution "
            + states["execution"].replace("_", " ")
            + ". These declarations trigger no work."
        )
        pending_names = [
            item["name"]
            for item in r["inputs"]["requirements"]
            if item["accessible"] is not True
        ]
        if pending_names:
            needs.append(
                "Requirements not qualified in the carried evidence: "
                + "; ".join(pending_names)
                + ". Source availability remains unestablished."
            )
        if states["inputs"] == "unknown":
            needs.append(
                "Some requirements for "
                + r["record_id"]
                + " remain undocumented; completeness is unknown, not complete or false."
            )
        elif states["inputs"] == "requires_data":
            needs.append(
                "Additional qualified input/access documentation is required for "
                + r["record_id"]
                + "; this does not prove absence from the authorized source/cache."
            )
        undocumented = [
            item["name"] + ": " + (item["reference"] or "not documented")
            for item in r["inputs"]["requirements"]
            if item["accessible"] is not True
        ]
        if undocumented:
            needs.append(
                "Unqualified requirements in the carried evidence for "
                + r["record_id"]
                + ": "
                + "; ".join(undocumented)
            )
        if states["protocol"] != "qualified" or states["authorization"] != "authorized":
            needs.append(
                "Protocol/authorization for "
                + r["record_id"]
                + ": "
                + states["protocol"]
                + " / "
                + states["authorization"]
                + "; no new numerical verification is implied or scheduled."
            )
        if states["execution"] == "executed":
            now.append(
                "Inspect the exact linked receipt for the recorded action only: "
                + r["action"]
            )
    if ready:
        needs.append(
            "D6 qualifies selected checks only, not an exhaustive assessment of every useful investigation. Other factor/context questions remain separately unqualified."
        )
    elif parent:
        needs.append(
            "No readiness declaration is supplied. Existing legacy check flags are not complete feasibility, permission or proof of execution."
        )
    return {
        "protocol_version": PROTOCOL,
        "observed": observed[:5],
        "why_it_may_matter": why,
        "verify_now": now,
        "additional_requirements": needs,
        "not_established": [NOT_ESTABLISHED[0], METADATA_SCOPE, *NOT_ESTABLISHED[1:]],
        "mechanisms": mechanism_rows,
        "factor_questions": factors,
        "selected_readiness_checks": readings,
        "paired_representation_counts": [],
    }


def qualify_pairs(cases):
    """Carry existing counts across matched declared X scopes, never infer units.

    A single-case export without the paired record keeps this field empty.
    Count arrays are joined only through exact original settings, not array order.
    """
    for case in cases:
        summary = case.get("decision_summary")
        parent = _annotation(case, "d1")
        if not summary or not parent:
            continue
        src = parent["request"]["source"]
        for other in cases:
            if other is case:
                continue
            peer = _annotation(other, "d1")
            if not peer:
                continue
            dst = peer["request"]["source"]
            keys = (
                "dataset_id",
                "content_version",
                "source_id",
                "population_id",
                "scope_kind",
                "n_observations",
            )
            if (
                any(src[k] != dst[k] for k in keys)
                or src["representation"] == dst["representation"]
            ):
                continue

            def wm(a):
                return [
                    m
                    for w in a["warnings"]
                    if w["warning_id"] == "preprocessing_dependent_organization"
                    for m in (w["observation"]["value"] or {}).get("measurements", [])
                ]

            for m in wm(parent):
                q = m["qualifications"]
                if (
                    q.get("comparison_kind") != "representation"
                    or q.get("admissible") is not True
                    or q.get("matched_observations") is not True
                    or dst["representation"] not in q.get("representations", [])
                ):
                    continue
                for p in wm(peer):
                    ms, ps = m["method"]["settings"], p["method"]["settings"]
                    mc = ms.get("actual_native_configuration", {})
                    pc = ps.get("actual_native_configuration", {})
                    if (
                        mc.get("PCA") is None
                        or mc.get("provider") is None
                        or ms.get("query_support") is None
                        or m["method"]["owner"] != p["method"]["owner"]
                        or m["method"]["version"] != p["method"]["version"]
                        or mc.get("PCA") != pc.get("PCA")
                        or mc.get("provider") != pc.get("provider")
                        or ms.get("query_support") != ps.get("query_support")
                    ):
                        continue
                    for measure, counterpart in ((m, p),):
                        configs = (
                            measure["method"]["settings"]
                            .get("actual_native_configuration", {})
                            .get("HDBSCAN", [])
                        )
                        pconfigs = (
                            counterpart["method"]["settings"]
                            .get("actual_native_configuration", {})
                            .get("HDBSCAN", [])
                        )
                        counts, pcounts = (
                            measure["values"].get("cluster_counts", []),
                            counterpart["values"].get("cluster_counts", []),
                        )
                        if len(configs) != len(counts) or len(pconfigs) != len(pcounts):
                            continue
                        for cfg, n in zip(configs, counts):
                            matches = [
                                pn
                                for pcfg, pn in zip(pconfigs, pcounts)
                                if pcfg == cfg and cfg.get("status") == "computed"
                            ]
                            if len(matches) != 1:
                                continue
                            row = {
                                "reference_representation": dst["representation"],
                                "reference_clusters": matches[0],
                                "representation": src["representation"],
                                "clusters": n,
                                "settings": deepcopy(cfg),
                                "peer_report_sha256": other["source_reports"][
                                    "reference"
                                ]["sha256"],
                                "scope_limit": "Matched declared X population and recorded density settings, not physical populations or independent replication.",
                            }
                            if row not in summary["paired_representation_counts"]:
                                summary["paired_representation_counts"].append(row)


def sections(summary):
    """The sole section mapping consumed by existing HTML and Markdown renderers."""
    labels = [
        ("observed", "What was observed"),
        ("why_it_may_matter", "Why it could matter here"),
        ("verify_now", "What the analyst can verify now"),
        ("additional_requirements", "What needs further information or authorization"),
        ("not_established", "What is not established"),
    ]
    # A presentation bound, never a scientific sampling/severity threshold.
    out = [(label, summary[key][:2], "list") for key, label in labels]
    out += [
        ("Additional detail: " + label, summary[key][2:], "list")
        for key, label in labels
        if len(summary[key]) > 2
    ]
    for m in summary["mechanisms"]:
        out.append(
            (
                "Measured mechanism: " + m["kind"],
                m["description"]
                + " Recorded values: "
                + json.dumps(m["values"], ensure_ascii=False),
                "text",
            )
        )
    for f in summary["factor_questions"]:
        out.append(
            (
                "Other conditional question: " + f["factor"],
                f["question"] + " " + f["limit"],
                "text",
            )
        )
    for r in summary["selected_readiness_checks"]:
        out.append(
            (
                "Selected D6 check (not exhaustive): " + r["record_id"],
                r["presentation"]
                + " Applicability: "
                + r["applicability"]
                + "; execution: "
                + r["execution"]
                + ".",
                "text",
            )
        )
    if summary["paired_representation_counts"]:
        out.append(
            (
                "Paired representation counts at exact recorded settings",
                summary["paired_representation_counts"],
                "json",
            )
        )
    return out
