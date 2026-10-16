use nirs4all_domains::{analyze, validate, AuditMode, Partition, Representation, Status, Task};
use serde_json::Value;
use std::path::{Path, PathBuf};

fn fixture(name: &str) -> Task {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../tests/fixtures")
        .join(format!("{name}.json"));
    serde_json::from_slice(&std::fs::read(path).unwrap()).unwrap()
}
fn library() -> PathBuf {
    std::env::var_os("N4DOMAINS_METHODS_LIBRARY")
        .expect("set Methods native library for ignored scientific gates")
        .into()
}
fn value(report: &nirs4all_domains::Report, id: &str) -> Value {
    report
        .metrics
        .iter()
        .find(|m| m.metric_id == id)
        .unwrap()
        .value
        .clone()
}
fn status(report: &nirs4all_domains::Report, id: &str) -> Status {
    report
        .metrics
        .iter()
        .find(|m| m.metric_id == id)
        .unwrap()
        .status
        .clone()
}

#[test]
fn explicit_contract_and_missing_provider() {
    let task = fixture("identical");
    validate(&task).unwrap();
    let r = analyze(&task, None);
    assert_eq!(
        status(&r, "coverage.test_outside_fraction"),
        Status::Unavailable
    );
    assert_eq!(r.status, "partial");
    assert!(r.preflight.is_some());
    assert!(!r.test_target_accessed);
    assert_eq!(
        analyze(&task, Some(Path::new("missing-methods-library"))).status,
        "failed"
    );
    let mut raw = serde_json::to_value(&task).unwrap();
    raw["observations"][0]
        .as_object_mut()
        .unwrap()
        .remove("partition");
    assert!(serde_json::from_value::<Task>(raw).is_err());
}
#[test]
fn identity_group_and_reference_separation() {
    for key in [
        "sample_id",
        "physical_sample_id",
        "independence_group",
        "individual_id",
    ] {
        let mut task = fixture("identical");
        let mut raw = serde_json::to_value(&task).unwrap();
        let first = if key == "individual_id" {
            Value::String("shared".into())
        } else {
            raw["observations"][0][key].clone()
        };
        raw["observations"][0][key] = first.clone();
        raw["observations"][8][key] = first;
        task = serde_json::from_value(raw).unwrap();
        assert!(validate(&task).is_err(), "{key}");
        assert_eq!(analyze(&task, None).status, "failed");
    }
}
#[test]
fn incompatible_axis_and_invalid_budget_rejected() {
    let mut task = fixture("identical");
    task.axis.pop();
    assert!(validate(&task).is_err());
    let mut task = fixture("identical");
    task.axis[1] = task.axis[0];
    assert!(validate(&task).is_err());
    let mut task = fixture("identical");
    task.policy.pca_max_components = 0;
    assert!(validate(&task).is_err());
}
#[test]
fn hidden_test_y_invariant_without_provider() {
    let task = fixture("identical");
    let mut changed = task.clone();
    for r in &mut changed.observations {
        if r.partition == Partition::Test {
            r.y = Some(1e9);
        }
    }
    assert_eq!(
        serde_json::to_value(analyze(&task, None)).unwrap(),
        serde_json::to_value(analyze(&changed, None)).unwrap()
    );
}

#[test]
#[ignore = "requires real Methods ABI >= 2.18; CI runs this gate explicitly"]
fn controlled_scientific_scenarios() {
    let lib = library();
    let baseline = analyze(&fixture("identical"), Some(&lib));
    assert_eq!(value(&baseline, "coverage.test_outside_fraction"), 0.0);
    assert!(
        value(&baseline, "domain.centroid_distance")
            .as_f64()
            .unwrap()
            < 1e-10
    );
    assert!(
        (value(&baseline, "domain.dispersion_ratio")
            .as_f64()
            .unwrap()
            - 1.0)
            .abs()
            < 1e-10
    );
    assert!(
        (value(&baseline, "coverage.effective_dimension")
            .as_f64()
            .unwrap()
            - 1.0)
            .abs()
            < 1e-10
    );
    assert!(baseline
        .findings
        .iter()
        .any(|f| f.rule_id.contains("duplicate")));
    for name in ["translation", "outside_support", "orthogonal_shift"] {
        let report = analyze(&fixture(name), Some(&lib));
        assert_eq!(
            value(&report, "coverage.test_outside_fraction"),
            1.0,
            "{name}"
        );
        if name == "translation" {
            assert!(
                (value(&report, "domain.centroid_distance").as_f64().unwrap() - 600.0_f64.sqrt())
                    .abs()
                    < 1e-10
            );
        }
        assert_eq!(
            report.fit.as_ref().unwrap()["mean"],
            baseline.fit.as_ref().unwrap()["mean"]
        );
        assert_eq!(
            report.fit.as_ref().unwrap()["loadings"],
            baseline.fit.as_ref().unwrap()["loadings"]
        );
        assert_eq!(
            report.fit.as_ref().unwrap()["nn_threshold"],
            baseline.fit.as_ref().unwrap()["nn_threshold"]
        );
    }
    let variance = analyze(&fixture("variance"), Some(&lib));
    assert!(
        (value(&variance, "domain.dispersion_ratio")
            .as_f64()
            .unwrap()
            - 4.0)
            .abs()
            < 1e-10
    );
    for name in [
        "two_clusters",
        "continuum",
        "instrument_confounded_y",
        "independent_y",
        "predictable_y",
    ] {
        let report = analyze(&fixture(name), Some(&lib));
        assert_eq!(status(&report, "structure.clustering"), Status::Unavailable);
        assert_eq!(status(&report, "xy.nested_probe"), Status::Unavailable);
        assert_eq!(
            status(&report, "explainability.conditional_effects"),
            Status::Unavailable
        );
    }
    let repeats = analyze(&fixture("technical_repeats"), Some(&lib));
    assert_eq!(
        status(&repeats, "coverage.test_outside_fraction"),
        Status::NotIdentifiable
    );
    let repeated_metric = repeats
        .metrics
        .iter()
        .find(|m| m.metric_id == "coverage.test_outside_fraction")
        .unwrap();
    assert_eq!(repeated_metric.population.n_train_physical_samples, 8);
    assert_eq!(repeated_metric.population.n_train_observations, 10);
    assert_eq!(
        status(
            &analyze(&fixture("insufficient"), Some(&lib)),
            "domain.centroid_distance"
        ),
        Status::InsufficientData
    );
    assert_eq!(
        status(
            &analyze(&fixture("target_absent"), Some(&lib)),
            "target.train_summary"
        ),
        Status::Unavailable
    );
    assert_eq!(
        status(
            &analyze(&fixture("missing_x"), Some(&lib)),
            "domain.centroid_distance"
        ),
        Status::Unavailable
    );
    let duplicates = analyze(&fixture("cross_partition_duplicates"), Some(&lib));
    let pf = duplicates.preflight.as_ref().unwrap();
    let dup = pf["metrics"]
        .as_array()
        .unwrap()
        .iter()
        .find(|m| m["metric_id"] == "integrity.cross_partition_exact_duplicate_pairs")
        .unwrap();
    assert_eq!(dup["value"], 8);
}

#[test]
#[ignore = "requires real Methods ABI >= 2.18; CI runs this gate explicitly"]
fn native_reproducibility_and_no_test_fit_or_y_selection() {
    let lib = library();
    let task = fixture("identical");
    let a = analyze(&task, Some(&lib));
    let b = analyze(&task, Some(&lib));
    assert_eq!(
        serde_json::to_vec(&a).unwrap(),
        serde_json::to_vec(&b).unwrap()
    );
    assert_eq!(
        a.fit.as_ref().unwrap()["fit_observation_ids"]
            .as_array()
            .unwrap()
            .len(),
        8
    );
    let mut changed = task.clone();
    for r in &mut changed.observations {
        if r.partition == Partition::Test {
            r.y = Some(10000.);
            r.category = Some("hidden".into());
        }
    }
    assert_eq!(
        serde_json::to_vec(&a).unwrap(),
        serde_json::to_vec(&analyze(&changed, Some(&lib))).unwrap()
    );
    let mut post = fixture("target_shift");
    post.target_unit = Some("mg/tablet".into());
    post.policy.audit_mode = AuditMode::PostEvaluation;
    let after = analyze(&post, Some(&lib));
    assert_eq!(
        after
            .metrics
            .iter()
            .find(|m| m.metric_id == "target.test_summary")
            .unwrap()
            .unit,
        "mg/tablet"
    );
    assert!(after.test_target_accessed);
    assert!(
        (value(&after, "target.test_summary")["mean"]
            .as_f64()
            .unwrap()
            - 100.5)
            .abs()
            < 1e-10
    );
    assert_eq!(a.fit, after.fit);
    assert!(after
        .findings
        .iter()
        .any(|f| f.rule_id == "domains.test_target_access.v1"));
    let mut repeated = post.clone();
    let mut row = repeated.observations[8].clone();
    row.observation_id.push_str("-repeat");
    repeated.observations.push(row);
    assert_eq!(
        status(&analyze(&repeated, Some(&lib)), "target.test_summary"),
        Status::Computed
    );
    assert_eq!(
        value(&analyze(&repeated, Some(&lib)), "target.test_summary")["count"],
        8
    );
    let mut categorical = task.clone();
    categorical.target_kind = nirs4all_domains::TargetKind::Categorical;
    categorical.policy.audit_mode = AuditMode::PostEvaluation;
    for (i, row) in categorical.observations.iter_mut().enumerate() {
        row.y = None;
        row.category = Some(if i % 2 == 0 { "A" } else { "B" }.into());
    }
    let categories = analyze(&categorical, Some(&lib));
    assert_eq!(
        value(&categories, "target.test_summary"),
        serde_json::json!({"A":4,"B":4})
    );
}

#[test]
#[ignore = "requires real Methods ABI >= 2.18; CI runs this gate explicitly"]
fn pca_analytical_projection_and_row_order_invariance() {
    let lib = library();
    let task = fixture("identical");
    let report = analyze(&task, Some(&lib));
    assert_eq!(
        report.fit.as_ref().unwrap()["mean"],
        serde_json::json!([0.5, 1.0, 0.5])
    );
    let trace = report.fit.as_ref().unwrap()["full_moments"][0]
        .as_f64()
        .unwrap();
    assert!((trace - 36.0).abs() < 1e-10);
    assert!(value(&report, "coverage.test_reconstruction_squared")
        .as_array()
        .unwrap()
        .iter()
        .all(|v| v.as_f64().unwrap() < 1e-20));
    let mut reordered = task.clone();
    reordered.observations.reverse();
    let other = analyze(&reordered, Some(&lib));
    for id in [
        "domain.centroid_distance",
        "domain.dispersion_ratio",
        "coverage.effective_dimension",
        "coverage.test_outside_fraction",
    ] {
        assert!(
            (value(&report, id).as_f64().unwrap() - value(&other, id).as_f64().unwrap()).abs()
                < 1e-10
        );
    }
}

fn qualified_repeats() -> Task {
    let mut task = fixture("identical");
    task.policy.representation = Representation::TechnicalMean;
    for row in &mut task.observations {
        row.metadata.insert("instrument".into(), "A".into());
        row.metadata.insert("campaign".into(), "C1".into());
        row.repetition_type = Some("rescan".into());
        row.reference_status = Some("exact".into());
    }
    for i in 0..2 {
        let mut row = task.observations[i].clone();
        row.observation_id.push_str("-repeat");
        task.observations.push(row);
    }
    task
}

fn excluded(report: &nirs4all_domains::Report, reason: &str) -> usize {
    report.representations["sample_context_groups"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|g| g["reason"] == reason)
        .map(|g| g["observation_ids"].as_array().unwrap().len())
        .sum()
}

#[test]
fn reference_dependencies_and_missing_identities_are_explicit() {
    let mut chain = fixture("identical");
    chain.observations[0].reference_group_id = Some("linked-batch".into());
    chain.observations[1].reference_group_id = Some("linked-batch".into());
    chain.observations[8].reference_id = chain.observations[1].reference_id.clone();
    let chain = analyze(&chain, None);
    assert_eq!(chain.unit_audit["train"]["validation_groups"], 7);
    assert_eq!(chain.unit_audit["test"]["validation_groups"], 8);
    assert_eq!(chain.unit_audit["validation_groups_total"], 14);
    assert_eq!(chain.unit_audit["known_reference_ids_total"], 15);
    assert!(chain.unit_audit["dependency_components"]
        .as_array()
        .unwrap()
        .iter()
        .any(|c| c["observation_ids"].as_array().unwrap().len() == 3
            && c["has_train"] == true
            && c["has_test"] == true));
    for key in ["reference_id", "reference_group_id"] {
        let mut task = fixture("identical");
        if key == "reference_id" {
            task.observations[8].reference_id = task.observations[0].reference_id.clone();
        } else {
            task.observations[0].reference_group_id = Some("shared".into());
            task.observations[8].reference_group_id = Some("shared".into());
        }
        validate(&task).unwrap();
        let report = analyze(&task, None);
        assert_eq!(report.status, "partial");
        assert_eq!(report.unit_audit["xy_blocked"], true);
        assert!(report.unit_audit["dependency_components"]
            .as_array()
            .unwrap()
            .iter()
            .any(|c| c["has_train"] == true && c["has_test"] == true));
        assert_eq!(
            status(&report, "target.train_summary"),
            Status::NotIdentifiable
        );
    }
    let mut task = fixture("identical");
    task.observations[0].physical_sample_id.clear();
    assert!(validate(&task).unwrap_err().contains("IDENTITIES"));
    let mut task = fixture("identical");
    for row in &mut task.observations {
        row.reference_id = None;
        row.reference_status = None;
    }
    let report = analyze(&task, None);
    assert_eq!(report.unit_audit["train"]["known_references"], 0);
    assert_eq!(
        report.unit_audit["train"]["missing_reference_acquisitions"],
        8
    );
    assert_eq!(
        report.unit_audit["train"]["missing_instrument_or_campaign_acquisitions"],
        8
    );
}

#[test]
#[ignore = "requires real Methods ABI >= 2.18; CI runs this gate explicitly"]
fn technical_means_equal_sample_weight_and_native_retention() {
    let lib = library();
    let task = qualified_repeats();
    let report = analyze(&task, Some(&lib));
    assert_eq!(
        status(&report, "coverage.test_outside_fraction"),
        Status::Computed
    );
    assert_eq!(report.unit_audit["train"]["acquisitions"], 10);
    assert_eq!(report.unit_audit["train"]["physical_samples"], 8);
    assert_eq!(report.unit_audit["train"]["known_references"], 8);
    assert_eq!(report.unit_audit["train"]["repeat_groups"], 2);
    assert_eq!(report.unit_audit["train"]["validation_groups"], 8);
    assert_eq!(
        report.representations["native_observation_ids"]
            .as_array()
            .unwrap()
            .len(),
        18
    );
    assert_eq!(
        report.fit.as_ref().unwrap()["fit_observation_ids"]
            .as_array()
            .unwrap()
            .len(),
        8
    );
    assert!(report.representations["sample_context_groups"]
        .as_array()
        .unwrap()
        .iter()
        .all(|g| g["weight"] == 1));
    let pf = report.preflight.as_ref().unwrap()["metrics"]
        .as_array()
        .unwrap();
    assert_eq!(
        pf.iter()
            .find(|m| m["metric_id"] == "target.exact_eligible_samples")
            .unwrap()["value"],
        8
    );
    assert!(pf
        .iter()
        .any(|m| m["metric_id"] == "measurement.repeatability_sd" && m["status"] == "computed"));
    let mut baseline = task.clone();
    baseline.observations.truncate(16);
    let baseline = analyze(&baseline, Some(&lib));
    for key in [
        "mean",
        "loadings",
        "full_moments",
        "nn_threshold",
        "reconstruction_squared_threshold",
    ] {
        assert_eq!(
            report.fit.as_ref().unwrap()[key],
            baseline.fit.as_ref().unwrap()[key],
            "{key}"
        );
    }
    let mut duplicated = task.clone();
    let mut row = duplicated.observations[0].clone();
    row.observation_id.push_str("-extra");
    duplicated.observations.push(row);
    let duplicated = analyze(&duplicated, Some(&lib));
    for key in ["mean", "loadings", "full_moments", "nn_threshold"] {
        assert_eq!(
            report.fit.as_ref().unwrap()[key],
            duplicated.fit.as_ref().unwrap()[key]
        );
    }
    assert_eq!(
        serde_json::to_vec(&report).unwrap(),
        serde_json::to_vec(&analyze(&task, Some(&lib))).unwrap()
    );
    // A nonzero repeat difference must be averaged, not represented by the first acquisition.
    let mut changed = task.clone();
    changed.observations[0].x[0] = Some(-5.0);
    changed.observations[16].x[0] = Some(-1.0);
    assert_eq!(
        analyze(&changed, Some(&lib)).fit.as_ref().unwrap()["mean"],
        report.fit.as_ref().unwrap()["mean"]
    );
}

#[test]
#[ignore = "requires real Methods ABI >= 2.18; CI runs this gate explicitly"]
fn heterogeneous_and_ambiguous_repeats_are_linked_without_averaging() {
    let lib = library();
    for (kind, reason) in [
        ("biological", "NONTECHNICAL_UNKNOWN_OR_MIXED_REPEAT_TYPE"),
        ("unknown", "NONTECHNICAL_UNKNOWN_OR_MIXED_REPEAT_TYPE"),
        ("context", "CROSS_CONTEXT_REQUIRES_PAIRED_PROTOCOL"),
        ("missing", "MISSING_REPEAT_CONTEXT"),
    ] {
        let mut task = qualified_repeats();
        for i in [0, 16] {
            if kind == "missing" {
                task.observations[i].metadata.remove("campaign");
            } else if kind != "context" {
                task.observations[i].repetition_type = Some(kind.into());
            }
        }
        if kind == "context" {
            task.observations[16]
                .metadata
                .insert("instrument".into(), "B".into());
        }
        let report = analyze(&task, Some(&lib));
        assert_eq!(excluded(&report, reason), 2, "{kind}");
        assert_eq!(
            report.fit.as_ref().unwrap()["fit_observation_ids"]
                .as_array()
                .unwrap()
                .len(),
            7
        );
        assert_eq!(
            report.representations["native_observation_ids"]
                .as_array()
                .unwrap()
                .len(),
            18
        );
        assert_eq!(report.unit_audit["train"]["validation_groups"], 8);
    }
    let mut task = qualified_repeats();
    task.observations[16].partition = Partition::Test;
    assert!(validate(&task).is_err());
    assert!(analyze(&task, Some(&lib)).fit.is_none());
}

#[test]
#[ignore = "requires real Methods ABI >= 2.18; CI runs this gate explicitly"]
fn reference_anomalies_block_xy_and_preserve_x() {
    let lib = library();
    for kind in [
        "shared_reference",
        "shared_group",
        "contradiction",
        "censored",
        "composite",
        "unit",
        "invalid_metadata",
    ] {
        let mut task = qualified_repeats();
        match kind {
            "invalid_metadata" => task.observations[0].reference_id = Some("".into()),
            "shared_reference" => {
                task.observations[8].reference_id = task.observations[0].reference_id.clone()
            }
            "shared_group" => {
                task.observations[0].reference_group_id = Some("shared".into());
                task.observations[8].reference_group_id = Some("shared".into());
            }
            "contradiction" => task.observations[16].y = Some(123.0),
            "unit" => {
                task.target_unit = Some("mg".into());
                task.observations[0].reference_unit = Some("g".into());
            }
            _ => task.observations[0].reference_status = Some(kind.into()),
        }
        let report = analyze(&task, Some(&lib));
        assert_eq!(
            status(&report, "coverage.test_outside_fraction"),
            Status::Computed,
            "{kind}"
        );
        assert_eq!(
            status(&report, "target.train_summary"),
            Status::NotIdentifiable,
            "{kind}"
        );
        assert_eq!(report.unit_audit["xy_blocked"], true);
        if kind == "contradiction" || kind == "unit" || kind == "invalid_metadata" {
            assert_eq!(
                excluded(&report, "CONTRADICTORY_REFERENCE_NO_AGGREGATION"),
                2
            );
        }
    }
}

#[test]
#[ignore = "requires real Methods ABI >= 2.18; CI runs this gate explicitly"]
fn aggregated_fit_ignores_test_x_and_hidden_targets() {
    let lib = library();
    let task = qualified_repeats();
    let report = analyze(&task, Some(&lib));
    let mut changed = task.clone();
    for row in &mut changed.observations {
        if row.partition == Partition::Test {
            row.y = Some(999999.);
            row.category = Some("hidden".into());
        }
    }
    assert_eq!(
        serde_json::to_vec(&report).unwrap(),
        serde_json::to_vec(&analyze(&changed, Some(&lib))).unwrap()
    );
    for row in &mut changed.observations {
        if row.partition == Partition::Test {
            for x in row.x.iter_mut().flatten() {
                *x += 1000.;
            }
        }
    }
    let shifted = analyze(&changed, Some(&lib));
    assert_eq!(report.fit, shifted.fit);
    assert_eq!(value(&shifted, "coverage.test_outside_fraction"), 1.0);
    let coverage = shifted
        .metrics
        .iter()
        .find(|m| m.metric_id == "coverage.test_outside_fraction")
        .unwrap();
    assert_eq!(coverage.parameters["denominator"], 8);
    assert_eq!(
        coverage.parameters["test_population"]
            .as_array()
            .unwrap()
            .len(),
        8
    );
}
