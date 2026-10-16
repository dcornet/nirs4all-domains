use nirs4all_domains::{
    methods::{HdbscanParameters, Methods, SelectionMethod},
    structure::{
        characterize_structure, compare_partitions, StructuralClassification, StructureConfig,
    },
    Partition, Status, Task,
};
use serde_json::Value;
use std::{
    collections::BTreeMap,
    path::{Path, PathBuf},
};

fn root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..")
}
fn fixture(name: &str) -> Task {
    serde_json::from_slice(
        &std::fs::read(root().join(format!("tests/fixtures/structure/{name}.json"))).unwrap(),
    )
    .unwrap()
}
fn config() -> StructureConfig {
    let mut c: StructureConfig = serde_json::from_slice(
        &std::fs::read(root().join("configs/pilots/structure-v1.json")).unwrap(),
    )
    .unwrap();
    c.replicates = 20;
    c.compare_native = false;
    c
}
fn library() -> PathBuf {
    std::env::var_os("N4DOMAINS_METHODS_LIBRARY")
        .expect("real Methods native scientific gate")
        .into()
}
fn run(name: &str) -> nirs4all_domains::structure::StructureReport {
    characterize_structure(&fixture(name), &config(), Some(&library()))
}

#[test]
fn structure_contract_missing_provider_and_split_guards() {
    let task = fixture("separated");
    let cfg = config();
    cfg.validate().unwrap();
    let report = characterize_structure(&task, &cfg, None);
    assert_eq!(report.status, Status::Unavailable);
    assert!(report.settings.is_empty());
    assert_eq!(report.held_out_assignment["status"], "unavailable");
    assert!(!report.test_target_accessed);
    let mut bad = cfg.clone();
    bad.replicates = 201;
    assert!(bad.validate().is_err());
    let mut bad = cfg.clone();
    bad.component_fraction = f64::NAN;
    assert!(bad.validate().is_err());
    let mut leaked = task.clone();
    leaked.observations.last_mut().unwrap().physical_sample_id =
        leaked.observations[0].physical_sample_id.clone();
    let report = characterize_structure(&leaked, &cfg, None);
    assert_eq!(report.status, Status::Error);
    assert!(report.reason.is_some());
}

#[test]
#[ignore = "requires real Methods ABI >=2.19; CI executes native scientific gates"]
fn separated_groups_recover_memberships_and_stability() {
    let task = fixture("separated");
    let report = run("separated");
    assert_eq!(report.status, Status::Computed, "{:?}", report.reason);
    let reference = report.settings[0].reference.as_ref().unwrap();
    assert_eq!(reference.hdbscan.n_clusters, 3);
    assert_eq!(reference.noise_fraction, 0.);
    let truth: BTreeMap<_, _> = task
        .observations
        .iter()
        .filter(|r| r.partition == Partition::Train)
        .map(|r| {
            (
                r.physical_sample_id.clone(),
                r.metadata["generating_group"].parse::<i64>().unwrap(),
            )
        })
        .collect();
    let actual = reference
        .physical_sample_ids
        .iter()
        .cloned()
        .zip(reference.hdbscan.labels.iter().copied())
        .collect();
    let components =
        serde_json::from_value(report.population["physical_sample_components"].clone()).unwrap();
    let comparison = compare_partitions(
        &Methods::load(&library()).unwrap(),
        &truth,
        &actual,
        &components,
        truth.len(),
    )
    .unwrap();
    assert!((comparison.ari_including_noise.value.unwrap() - 1.).abs() < 1e-12);
    assert_eq!(
        report.classification,
        StructuralClassification::RobustStructure,
        "{}",
        report.classification_evidence
    );
    for setting in &report.settings {
        assert_eq!(setting.stability["successful_draws"], 20);
        assert_eq!(setting.stability["eligible_ari_including_noise"], 20);
    }
}

#[test]
#[ignore = "requires real Methods ABI >=2.19; CI executes native scientific gates"]
fn varying_density_reports_sensitivity_without_forced_recovery() {
    let report = run("density");
    assert_eq!(report.status, Status::Computed);
    assert!(report
        .settings
        .iter()
        .any(|s| s.reference.as_ref().unwrap().hdbscan.n_clusters >= 2));
    assert!(report
        .settings
        .iter()
        .any(|s| s.stability["noise_status_agreement"]["value"]["min"]
            .as_f64()
            .unwrap_or(1.)
            < 0.99));
    assert_eq!(
        report.classification,
        StructuralClassification::FragileStructure
    );
    assert_eq!(report.settings.len(), 5);
}

#[test]
#[ignore = "requires real Methods ABI >=2.19; CI executes native scientific gates"]
fn smooth_manifold_does_not_become_robust_discrete_structure() {
    let report = run("continuum");
    assert_eq!(report.status, Status::Computed);
    assert_ne!(
        report.classification,
        StructuralClassification::RobustStructure
    );
    assert_eq!(
        report.settings[0].reference.as_ref().unwrap().pca["n_components"],
        1
    );
    assert!(report.classification_evidence["regular_one_dimensional_gap_evidence"].is_object());
}

#[test]
#[ignore = "requires real Methods ABI >=2.19; CI executes native scientific gates"]
fn impossible_cluster_scales_cannot_manufacture_continuum_evidence() {
    let mut cfg = config();
    cfg.primary.min_cluster_size = 100;
    for s in &mut cfg.sensitivity {
        s.min_cluster_size = 100;
    }
    let report = characterize_structure(&fixture("continuum"), &cfg, Some(&library()));
    assert_eq!(report.status, Status::Computed);
    assert_eq!(
        report.classification,
        StructuralClassification::InsufficientInformation
    );
    assert_eq!(
        report.classification_evidence["tested_scales_allow_multiple_clusters"],
        false
    );
    assert!(report
        .settings
        .iter()
        .all(|s| s.reference.as_ref().unwrap().hdbscan.n_clusters == 0));
}

#[test]
#[ignore = "requires real Methods ABI >=2.19; CI executes native scientific gates"]
fn diffuse_cloud_reports_noise_without_spurious_stability() {
    let report = run("diffuse");
    assert_eq!(report.status, Status::Computed);
    assert_ne!(
        report.classification,
        StructuralClassification::RobustStructure
    );
    assert!(
        report.settings[0]
            .reference
            .as_ref()
            .unwrap()
            .noise_fraction
            >= 0.25
    );
    assert!(report.settings.iter().flat_map(|s| &s.replicates).any(|r| r
        .comparison
        .as_ref()
        .unwrap()
        .ari_including_noise
        .value
        .is_none()));
}

#[test]
#[ignore = "requires real Methods ABI >=2.19; CI executes native scientific gates"]
fn insufficient_components_and_degenerate_pca_remain_explicit() {
    let small = run("small");
    assert_eq!(small.status, Status::InsufficientData);
    assert!(small.settings.is_empty());
    assert_eq!(
        small.classification,
        StructuralClassification::InsufficientInformation
    );
    let duplicates = run("duplicates");
    assert!(duplicates.reason.is_some());
    assert!(duplicates.settings.is_empty());
    assert_eq!(
        duplicates.classification,
        StructuralClassification::InsufficientInformation
    );
    assert_eq!(duplicates.population["n_physical_samples"], 64);
}

#[test]
#[ignore = "requires real Methods ABI >=2.19; CI executes native scientific gates"]
fn nuisance_and_y_independent_structure_make_no_predictive_claim() {
    for name in ["nuisance", "independent_y"] {
        let report = run(name);
        assert_eq!(report.status, Status::Computed);
        assert_eq!(
            report.settings[0]
                .reference
                .as_ref()
                .unwrap()
                .hdbscan
                .n_clusters,
            3
        );
        assert_eq!(report.shortcut_risk_evidence["status"], "unavailable");
        assert!(report.shortcut_risk_evidence["value"].is_null());
        assert_eq!(report.held_out_assignment["status"], "unavailable");
    }
}

#[test]
#[ignore = "requires real Methods ABI >=2.19; CI executes native scientific gates"]
fn structural_fit_ignores_test_x_y_and_target_values_and_replays_canonical_order() {
    let mut task = fixture("separated");
    let cfg = config();
    let lib = library();
    let before = characterize_structure(&task, &cfg, Some(&lib));
    for row in &mut task.observations {
        row.y = Some(-1e20);
        if row.partition == Partition::Test {
            row.x = vec![Some(-1e10); task.axis.len()];
        }
    }
    task.policy.audit_mode = nirs4all_domains::AuditMode::PostEvaluation;
    for row in &mut task.observations {
        if row.partition == Partition::Test {
            row.y = Some(f64::NAN);
            row.category = Some("inaccessible held-out category".into());
        }
    }
    task.observations.reverse();
    let after = characterize_structure(&task, &cfg, Some(&lib));
    assert_eq!(
        serde_json::to_vec(&before).unwrap(),
        serde_json::to_vec(&after).unwrap()
    );
}

#[test]
#[ignore = "requires real Methods ABI >=2.19; CI executes native scientific gates"]
fn repeated_acquisitions_do_not_add_votes_or_change_component_resamples() {
    let mut task = fixture("separated");
    let cfg = config();
    let lib = library();
    let before = characterize_structure(&task, &cfg, Some(&lib));
    let mut repeated = task.observations[0].clone();
    repeated.observation_id = "extra-identical-acquisition".into();
    task.observations.push(repeated);
    let after = characterize_structure(&task, &cfg, Some(&lib));
    assert_eq!(after.population["n_physical_samples"], 72);
    for (a, b) in before.settings.iter().zip(&after.settings) {
        assert_eq!(
            a.reference.as_ref().unwrap().pca,
            b.reference.as_ref().unwrap().pca
        );
        assert_eq!(
            a.reference.as_ref().unwrap().hdbscan.labels,
            b.reference.as_ref().unwrap().hdbscan.labels
        );
        for (x, y) in a.replicates.iter().zip(&b.replicates) {
            assert_eq!(x.selected_components, y.selected_components);
            assert_eq!(x.physical_sample_ids, y.physical_sample_ids);
            assert_eq!(x.fit.as_ref().unwrap().pca, y.fit.as_ref().unwrap().pca);
        }
        assert_eq!(a.stability, b.stability);
    }
}

#[test]
#[ignore = "requires real Methods ABI >=2.19; CI executes native scientific gates"]
fn transitive_reference_components_are_subsampled_whole_and_failures_not_redrawn() {
    let mut task = fixture("separated");
    for row in &mut task.observations[..16] {
        row.reference_group_id = Some("shared-batch".into());
    }
    let mut cfg = config();
    cfg.sensitivity[0].min_samples = 70;
    let report = characterize_structure(&task, &cfg, Some(&library()));
    assert_eq!(report.population["n_dependency_components"], 29);
    for r in &report.settings[0].replicates {
        let n = r
            .physical_sample_ids
            .iter()
            .filter(|id| id.as_str() < "p016")
            .count();
        assert!(n == 0 || n == 16);
        assert_eq!(r.selected_components.len(), 24);
    }
    assert_eq!(report.settings[1].replicates.len(), 20);
    assert!(report.settings[1]
        .replicates
        .iter()
        .any(|r| r.failure.is_some()));
    for (a, b) in report.settings[0]
        .replicates
        .iter()
        .zip(&report.settings[1].replicates)
    {
        assert_eq!(a.selected_components, b.selected_components);
    }
    assert_eq!(
        report.classification,
        StructuralClassification::InsufficientInformation
    );
}

#[test]
#[ignore = "requires real Methods ABI >=2.19; CI executes native scientific gates"]
fn native_ari_matches_ids_and_labels_and_rejects_favorable_trivial_values() {
    let methods = Methods::load(&library()).unwrap();
    assert!(methods
        .adjusted_rand_index(&[-1; 40], &[-1; 40])
        .unwrap()
        .is_none());
    assert!(methods
        .adjusted_rand_index(&[1, 1, 2, 2], &[9, 9, 7, 7])
        .unwrap()
        .is_some_and(|v| (v - 1.).abs() < 1e-12));
    let a = (0..60)
        .map(|i| (format!("s{i:03}"), i / 20))
        .collect::<BTreeMap<_, _>>();
    let b = a.iter().rev().map(|(id, c)| (id.clone(), 10 - c)).collect();
    let components = a.keys().map(|id| (id.clone(), id.clone())).collect();
    let comparison = compare_partitions(&methods, &a, &b, &components, 60).unwrap();
    assert_eq!(comparison.ari_including_noise.value, Some(1.));
    let partial = a
        .iter()
        .skip(10)
        .take(40)
        .map(|(id, c)| (id.clone(), 100 - c))
        .collect();
    let comparison = compare_partitions(&methods, &a, &partial, &components, 60).unwrap();
    assert_eq!(comparison.ari_including_noise.value, Some(1.));
    assert_eq!(
        comparison.common_physical_sample_ids,
        a.keys().skip(10).take(40).cloned().collect::<Vec<_>>()
    );
    let with_noise = a
        .iter()
        .enumerate()
        .map(|(i, (id, c))| (id.clone(), if i % 3 == 0 { -1 } else { 100 - c }))
        .collect();
    let comparison = compare_partitions(&methods, &a, &with_noise, &components, 60).unwrap();
    assert_eq!(comparison.ari_excluding_noise.value, Some(1.));
    assert!(comparison.ari_including_noise.value.unwrap() < 1.);
    assert!((comparison.noise_status_agreement.unwrap() - 2. / 3.).abs() < 1e-12);
    let small = a.iter().take(19).map(|(id, v)| (id.clone(), *v)).collect();
    let comparison = compare_partitions(&methods, &a, &small, &components, 60).unwrap();
    assert_eq!(
        comparison.ari_including_noise.status,
        Status::InsufficientData
    );
    let noise = a.keys().map(|id| (id.clone(), -1)).collect();
    let comparison = compare_partitions(&methods, &noise, &noise, &components, 60).unwrap();
    assert!(comparison.ari_including_noise.value.is_none());
    assert_eq!(comparison.noise_status_agreement, Some(1.));
}

#[test]
#[ignore = "requires real Methods ABI >=2.19; CI executes native scientific gates"]
fn native_duplicate_hierarchy_preserves_nonfinite_diagnostic_reasons() {
    let methods = Methods::load(&library()).unwrap();
    let params = HdbscanParameters {
        min_cluster_size: 3,
        min_samples: 2,
        selection_method: SelectionMethod::Eom,
        allow_single_cluster: true,
    };
    let x = vec![vec![1., 1.]; 40];
    let result = methods.hdbscan(&x, &params).unwrap();
    assert_eq!(result.labels.len(), 40);
    assert!(!result.nonfinite_diagnostics.is_empty());
    let serialized = serde_json::to_string(&result).unwrap();
    let _: Value = serde_json::from_str(&serialized).unwrap();
    assert!(!serialized.contains("NaN"));
    assert_eq!(
        serialized,
        serde_json::to_string(&methods.hdbscan(&x, &params).unwrap()).unwrap()
    );
    assert!(methods.hdbscan(&[vec![f64::NAN]], &params).is_err());
}

#[test]
#[ignore = "requires real Methods ABI >=2.19; CI executes native scientific gates"]
fn native_consensus_counts_physical_samples_and_excludes_mixed_assignments() {
    let mut task = fixture("separated");
    let mut cfg = config();
    cfg.compare_native = true;
    let mut expanded = Vec::new();
    for row in &task.observations {
        if row.partition == Partition::Train {
            for replica in 0..6 {
                let mut r = row.clone();
                r.observation_id = format!("{}:r{replica}", r.observation_id);
                expanded.push(r);
            }
        } else {
            expanded.push(row.clone());
        }
    }
    task.observations = expanded;
    let report = characterize_structure(&task, &cfg, Some(&library()));
    let v = &report.native_comparison["value"];
    assert_eq!(report.native_comparison["status"], "computed");
    assert_eq!(
        v["acquisition_fit"]["observation_ids"]
            .as_array()
            .unwrap()
            .len(),
        432
    );
    assert_eq!(v["physical_consensus"].as_object().unwrap().len(), 72);
    assert_eq!(v["comparison"]["ari_including_noise"]["value"], 1.);
    assert_eq!(v["excluded_mixed_assignments"].as_array().unwrap().len(), 0);
    let replacement = task
        .observations
        .iter()
        .find(|r| r.physical_sample_id == "p048")
        .unwrap()
        .x
        .clone();
    task.observations[0].x = replacement;
    let mixed = characterize_structure(&task, &cfg, Some(&library()));
    assert!(
        mixed.native_comparison["value"]["excluded_mixed_assignments"]
            .as_array()
            .unwrap()
            .iter()
            .any(|r| r["physical_sample_id"] == "p000")
    );
    let mut extra = task.observations[0].clone();
    extra.observation_id = "seventh-repeat".into();
    task.observations.push(extra);
    let unequal = characterize_structure(&task, &cfg, Some(&library()));
    assert_eq!(unequal.native_comparison["status"], "unavailable");
    assert_eq!(
        unequal.native_comparison["reason"],
        "UNEQUAL_REPEAT_MULTIPLICITY_NATIVE_DENSITY_NOT_QUALIFIED"
    );
}
