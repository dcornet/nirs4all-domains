//! Actual pinned-owner synthetic qualification; no real dataset or local numerical backend.
#![cfg(feature = "native")]
use nirs4all_domains::{
    browser_support::SupportProvider, preprocessing_methods::PreprocessingMethods,
};
use serde_json::{json, Value};

fn provider() -> PreprocessingMethods {
    let path = std::env::var_os("N4DOMAINS_METHODS_LIBRARY").expect("N4DOMAINS_METHODS_LIBRARY");
    let owner = PreprocessingMethods::load(std::path::Path::new(&path)).unwrap();
    assert_eq!(owner.version(), "1.5.1+abi.2.24.0");
    owner
}
fn transform(owner: &PreprocessingMethods, matrix: Value) -> Value {
    let result = owner
        .execute("preprocess_transform", &json!({"matrix":matrix}))
        .unwrap();
    assert_eq!(result["backend_version"], "1.5.1+abi.2.24.0");
    result
}

#[test]
#[ignore = "requires the pinned Methods 1.5.1 native library"]
fn panel_fit_transform_restore_and_failed_candidates_preserve_state() {
    let owner = provider();
    let train: Vec<Vec<f64>> = (0..4)
        .map(|i| {
            (0..13)
                .map(|j| 0.2 * (j * j) as f64 + (i + 1) as f64 * j as f64 + i as f64)
                .collect()
        })
        .collect();
    let query: Vec<Vec<f64>> = (0..2)
        .map(|i| {
            (0..13)
                .map(|j| 0.3 * (j * j) as f64 + (i + 2) as f64 * j as f64 + 2.0)
                .collect()
        })
        .collect();
    let panel = [
        ("SNV", json!({"with_mean":true,"with_std":true,"ddof":0})),
        ("MSC", json!({})),
        ("Detrend", json!({"polyorder":1})),
        (
            "SavitzkyGolay",
            json!({"window_length":11,"polyorder":2,"deriv":1,"delta":1.0,"mode":"mirror","cval":0.0}),
        ),
        (
            "Gaussian",
            json!({"sigma":1.0,"order":0,"mode":"reflect","cval":0.0,"truncate":4.0}),
        ),
        ("StandardScale", json!({"with_mean":true,"with_std":true})),
        ("Normalize", json!({"feature_min":-1.0,"feature_max":1.0})),
        ("CropTransformer", json!({"start":2,"end":11})),
    ];
    for (operator, parameters) in panel {
        let fitted = owner
            .execute(
                "preprocess_fit",
                &json!({"operator":operator,"parameters":parameters,"matrix":train}),
            )
            .unwrap();
        assert_eq!(fitted["backend_version"], owner.version());
        let reference = transform(&owner, json!(train));
        let heldout = transform(&owner, json!(query));
        assert_eq!(
            fitted["state_bytes"], reference["state_bytes"],
            "{operator}"
        );
        assert_eq!(fitted["state_bytes"], heldout["state_bytes"], "{operator}");
        assert_eq!(heldout["matrix"].as_array().unwrap().len(), 2);
        assert_eq!(
            heldout["matrix"][0].as_array().unwrap().len(),
            if operator == "CropTransformer" { 9 } else { 13 }
        );
        assert!(owner
            .execute("preprocess_transform", &json!({"matrix":[[1.0]]}))
            .is_err());
        assert_eq!(
            transform(&owner, json!(query)),
            heldout,
            "failed transform preserves {operator}"
        );
        assert!(owner
            .execute(
                "preprocess_fit",
                &json!({"operator":"StandardScale","parameters":{"with_mean":1},"matrix":train})
            )
            .is_err());
        assert_eq!(
            transform(&owner, json!(query)),
            heldout,
            "failed candidate preserves {operator}"
        );
        assert!(owner
            .execute(
                "preprocess_restore",
                &json!({"operator":operator,"state_bytes":[0,1,2,3]})
            )
            .is_err());
        assert_eq!(
            transform(&owner, json!(query)),
            heldout,
            "failed import preserves {operator}"
        );
        owner.execute("preprocess_destroy", &json!({})).unwrap();
        owner.execute("preprocess_destroy", &json!({})).unwrap();
        assert!(owner
            .execute("preprocess_transform", &json!({"matrix":query}))
            .is_err());
        let restored = owner
            .execute(
                "preprocess_restore",
                &json!({"operator":operator,"state_bytes":fitted["state_bytes"]}),
            )
            .unwrap();
        assert_eq!(restored["state_bytes"], fitted["state_bytes"]);
        assert_eq!(
            transform(&owner, json!(query)),
            heldout,
            "N4ME replay {operator}"
        );
    }
}

#[test]
#[ignore = "requires the pinned Methods 1.5.1 native library"]
fn train_statistics_crop_and_snv_have_independent_analytical_expectations() {
    let owner = provider();
    owner.execute("preprocess_fit",&json!({"operator":"StandardScale","parameters":{"with_mean":true,"with_std":true},"matrix":[[1.0,10.0],[3.0,10.0]]})).unwrap();
    assert_eq!(
        transform(&owner, json!([[5.0, 10.0]]))["matrix"],
        json!([[3.0, 0.0]])
    );
    owner.execute("preprocess_fit",&json!({"operator":"CropTransformer","parameters":{"start":1,"end":3},"matrix":[[0.0,1.0,2.0,3.0]]})).unwrap();
    assert_eq!(
        transform(&owner, json!([[10.0, 11.0, 12.0, 13.0]]))["matrix"],
        json!([[11.0, 12.0]])
    );
    owner.execute("preprocess_fit",&json!({"operator":"SNV","parameters":{"with_mean":true,"with_std":true,"ddof":0},"matrix":[[1.0,2.0,4.0,8.0]]})).unwrap();
    let result = transform(
        &owner,
        json!([
            [1.0, 2.0, 4.0, 8.0],
            [11.0, 12.0, 14.0, 18.0],
            [3.0, 6.0, 12.0, 24.0]
        ]),
    );
    for row in [1, 2] {
        for col in 0..4 {
            assert!(
                (result["matrix"][row][col].as_f64().unwrap()
                    - result["matrix"][0][col].as_f64().unwrap())
                .abs()
                    <= 1e-10
            );
        }
    }
}

#[test]
#[ignore = "requires the pinned Methods 1.5.1 native library"]
fn restored_operator_mismatch_and_forbidden_fit_inputs_keep_live_state() {
    let owner = provider();
    let fitted = owner
        .execute(
            "preprocess_fit",
            &json!({"operator":"SNV","parameters":{},"matrix":[[1.0,2.0,3.0]]}),
        )
        .unwrap();
    let expected = transform(&owner, json!([[4.0, 5.0, 6.0]]));
    assert!(owner
        .execute(
            "preprocess_restore",
            &json!({"operator":"StandardScale","state_bytes":fitted["state_bytes"]})
        )
        .is_err());
    assert!(owner
        .execute(
            "preprocess_fit",
            &json!({"operator":"SNV","parameters":{},"matrix":[[1.0,2.0,3.0]],"Y":[1.0]})
        )
        .is_err());
    assert!(owner
        .execute(
            "preprocess_fit",
            &json!({"operator":"Resampler","parameters":{},"matrix":[[1.0,2.0,3.0]]})
        )
        .is_err());
    assert_eq!(transform(&owner, json!([[4.0, 5.0, 6.0]])), expected);
}

#[test]
#[ignore = "requires the pinned Methods 1.5.1 native library"]
fn official_partition_comparisons_preserve_noise_and_undefined_outputs() {
    let owner = provider();
    let permutation = owner
        .execute(
            "adjusted_rand",
            &json!({"labels_a":[-1,-1,0,0],"labels_b":[7,7,3,3]}),
        )
        .unwrap();
    assert_eq!(permutation["value"], 1.0); // -1 is a regular class in this owner kernel.
    let trivial = owner
        .execute("adjusted_rand", &json!({"labels_a":[0,0],"labels_b":[1,1]}))
        .unwrap();
    assert!(trivial["value"].is_null());
    let overlap = owner
        .execute(
            "cluster_jaccard",
            &json!({"labels_a":[0,0,1,-1],"labels_b":[1,0,0,-1],"n_clusters_a":2,"n_clusters_b":2}),
        )
        .unwrap();
    assert_eq!(overlap["intersections"], json!([[1, 1], [1, 0]]));
    assert_eq!(overlap["sizes_a"], json!([2, 1]));
    assert_eq!(overlap["sizes_b"], json!([2, 1]));
    assert_eq!(overlap["jaccard"], json!([[1.0 / 3.0, 0.5], [0.5, 0.0]]));
    let empty = owner
        .execute(
            "cluster_jaccard",
            &json!({"labels_a":[-1,-1],"labels_b":[-1,-1],"n_clusters_a":2,"n_clusters_b":2}),
        )
        .unwrap();
    assert_eq!(empty["jaccard"], json!([[null, null], [null, null]]));
    assert_eq!(empty["sizes_a"], json!([0, 0]));
    assert!(owner
        .execute(
            "cluster_jaccard",
            &json!({"labels_a":[2],"labels_b":[0],"n_clusters_a":2,"n_clusters_b":1})
        )
        .is_err());
}
