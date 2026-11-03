//! Provider qualification against published frozen data, never another engine.
use nirs4all_domains::methods::{HdbscanParameters, Methods, SelectionMethod};
use serde_json::Value;
use std::path::{Path, PathBuf};

fn number(value: &Value) -> f64 {
    f64::from_bits(u64::from_str_radix(value.as_str().unwrap(), 16).unwrap())
}

fn close(actual: Option<f64>, expected: f64) {
    if expected.is_finite() {
        let actual = actual.unwrap();
        assert!((actual - expected).abs() <= 1e-12 * expected.abs().max(1.));
    } else {
        assert!(actual.is_none());
    }
}

#[test]
#[ignore = "requires published Methods ABI 2.19; executed in both CI platforms"]
fn selected_persistence_and_original_hierarchy_match_frozen_public_reference() {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../tests/fixtures/multiscale/methods-hdbscan-v1.json");
    let data: Value = serde_json::from_slice(&std::fs::read(path).unwrap()).unwrap();
    let library = PathBuf::from(std::env::var_os("N4DOMAINS_METHODS_LIBRARY").unwrap());
    let m = Methods::load(&library).unwrap();
    let cases = data["cases"].as_array().unwrap();
    assert_eq!(cases.len(), 8);
    for case in cases {
        let cols = case["cols"].as_u64().unwrap() as usize;
        let x = case["input_hex"]
            .as_array()
            .unwrap()
            .chunks(cols)
            .map(|row| row.iter().map(number).collect::<Vec<_>>())
            .collect::<Vec<_>>();
        let p = &case["params"];
        let h = m
            .hdbscan(
                &x,
                &HdbscanParameters {
                    min_cluster_size: p["min_cluster_size"].as_u64().unwrap() as usize,
                    min_samples: p["min_samples"].as_u64().unwrap() as usize,
                    selection_method: if p["selection_method"] == 0 {
                        SelectionMethod::Eom
                    } else {
                        SelectionMethod::Leaf
                    },
                    allow_single_cluster: p["allow_single_cluster"] == 1,
                },
            )
            .unwrap();
        assert_eq!(h.n_clusters, case["n_clusters"].as_u64().unwrap() as usize);
        assert_eq!(serde_json::json!(h.labels), case["labels"]);
        assert_eq!(h.cluster_persistence.len(), h.n_clusters);
        for (i, v) in h.cluster_persistence.iter().enumerate() {
            close(*v, number(&case["persistence_hex"][i]));
        }
        assert_eq!(
            h.hierarchy.len(),
            case["tree_parent"].as_array().unwrap().len()
        );
        for (i, node) in h.hierarchy.iter().enumerate() {
            assert_eq!(node.parent, case["tree_parent"][i].as_i64().unwrap());
            assert_eq!(node.size, case["tree_size"][i].as_i64().unwrap());
            assert_eq!(node.label, case["tree_label"][i].as_i64().unwrap());
            close(node.lambda_birth, number(&case["tree_lambda_birth_hex"][i]));
            close(node.lambda_death, number(&case["tree_lambda_death_hex"][i]));
            close(node.stability, number(&case["tree_stability_hex"][i]));
        }
    }
}
