use nirs4all_domains::{association::group_target_association, methods::Methods, Task};
use std::path::PathBuf;

fn library() -> PathBuf {
    std::env::var_os("N4DOMAINS_METHODS_LIBRARY")
        .unwrap()
        .into()
}
fn task() -> Task {
    serde_json::from_str(include_str!(
        "../../../tests/fixtures/dependence/mixed.json"
    ))
    .unwrap()
}

#[test]
#[ignore = "requires real Methods ABI 2.19"]
fn analytical_native_eta_and_undefined_cases() {
    let m = Methods::load(&library()).unwrap();
    let y = [0., 2., 4., 6.];
    assert!((m.factor_association(&[0, 0, 1, 1], &y).unwrap()[0].unwrap() - 0.8).abs() < 1e-10);
    assert!(
        m.factor_association(&[0, 1, 1, 0], &y).unwrap()[0]
            .unwrap()
            .abs()
            < 1e-10
    );
    let perfect = m
        .factor_association(&[0, 0, 1, 1], &[0., 0., 4., 4.])
        .unwrap();
    assert_eq!(perfect[0], Some(1.));
    assert_eq!(perfect[1], None);
    assert_eq!(m.factor_association(&[0, 0, 0, 0], &y).unwrap()[0], None);
    assert_eq!(
        m.factor_association(&[0, 0, 1, 1], &[1.; 4]).unwrap()[0],
        None
    );
    let saturated = m.factor_association(&[0, 1, 2, 3], &y).unwrap();
    assert_eq!(saturated[0], Some(1.));
    assert_eq!(saturated[1], None);
    assert!(m.factor_association(&[0], &[0.]).is_err());
}

#[test]
#[ignore = "requires real Methods ABI 2.19"]
fn physical_weighting_ss_identity_bootstrap_and_hidden_label_invariance() {
    let t = task();
    let lib = library();
    let a = group_target_association(&t, "factor", &lib, 200, 17).unwrap();
    let v = &a["association"]["value"];
    let total = v["ss_total"].as_f64().unwrap();
    assert!(
        (total - v["ss_between"].as_f64().unwrap() - v["ss_within"].as_f64().unwrap()).abs()
            < 1e-10 * (1. + total)
    );
    assert_eq!(a["bootstrap"]["successful"], 200);
    let mut changed = t.clone();
    for r in &mut changed.observations {
        if r.partition == nirs4all_domains::Partition::Test {
            r.y = Some(1e30);
        }
    }
    changed.observations.reverse();
    assert_eq!(
        a,
        group_target_association(&changed, "factor", &lib, 200, 17).unwrap()
    );
    let train: Vec<_> = changed
        .observations
        .iter()
        .filter(|r| r.partition == nirs4all_domains::Partition::Train)
        .cloned()
        .collect();
    for mut r in train {
        r.observation_id.push_str("_copy");
        changed.observations.push(r);
    }
    assert_eq!(
        a,
        group_target_association(&changed, "factor", &lib, 200, 17).unwrap()
    );
}

#[test]
#[ignore = "requires real Methods ABI 2.19"]
fn missing_factor_reference_blocks_and_unbalanced_population() {
    let mut t = task();
    let lib = library();
    t.observations[0].metadata.remove("factor");
    t.observations[1].y = None;
    let a = group_target_association(&t, "factor", &lib, 200, 17).unwrap();
    assert_eq!(a["association"]["value"]["n_physical"], 94);
    assert_eq!(a["excluded_missing_y_ids"].as_array().unwrap().len(), 1);
    assert_eq!(
        a["excluded_missing_factor_ids"].as_array().unwrap().len(),
        1
    );
    assert_eq!(
        group_target_association(&t, "absent", &lib, 3, 17).unwrap()["association"]["status"],
        "insufficient_data"
    );
    t.observations[1].reference_id = t.observations[0].reference_id.clone();
    assert_eq!(
        group_target_association(&t, "factor", &lib, 3, 17).unwrap()["association"]["reason"],
        "REFERENCE_AUDIT_BLOCKS_XY"
    );
}

#[test]
#[ignore = "requires real Methods ABI 2.19"]
fn failed_component_draws_are_retained_without_redraw() {
    let mut t = task();
    t.observations.retain(|r| {
        r.partition == nirs4all_domains::Partition::Test
            || ["p000", "p001", "p002", "p003"].contains(&r.physical_sample_id.as_str())
    });
    let a = group_target_association(&t, "factor", &library(), 200, 17).unwrap();
    assert!(a["bootstrap"]["failed"].as_u64().unwrap() > 0);
    assert_eq!(a["bootstrap"]["draws"].as_array().unwrap().len(), 200);
    assert_eq!(
        a["bootstrap"]["successful"].as_u64().unwrap() + a["bootstrap"]["failed"].as_u64().unwrap(),
        200
    );
    assert!(a["bootstrap"]["interval_95"].is_null());
}
