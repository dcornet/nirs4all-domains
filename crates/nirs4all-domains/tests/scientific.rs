use nirs4all_domains::{analyze, validate, AuditMode, Partition, Status, Task};
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
        "reference_id",
        "reference_group_id",
        "individual_id",
    ] {
        let mut task = fixture("identical");
        let mut raw = serde_json::to_value(&task).unwrap();
        let first = if key == "reference_group_id" || key == "individual_id" {
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
        Status::NotIdentifiable
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
