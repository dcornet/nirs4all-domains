//! Owner-shaped stubs qualify access/lifecycle only; actual numerical oracles run separately.
use nirs4all_domains::browser_support::{self as support, SupportProvider, SupportRequest};
use nirs4all_preflight::ProviderError;
use serde_json::{json, Value};
use std::cell::RefCell;

#[derive(Default)]
struct Spy {
    calls: RefCell<Vec<(String, Value)>>,
    tamper_state: bool,
    invalid_monitor: bool,
}
impl SupportProvider for Spy {
    fn version(&self) -> String {
        "1.3.13+abi.2.20.0".into()
    }
    fn execute(&self, op: &str, r: &Value) -> Result<Value, ProviderError> {
        self.calls.borrow_mut().push((op.into(), r.clone()));
        let mut out = match op {
            "pca_fit" => json!({"state_bytes":[1,2,3]}),
            "pca_transform" => {
                json!({"scores":r["matrix"],"state_bytes":if self.tamper_state {vec![3,2,1]} else {vec![1,2,3]}})
            }
            "pca_destroy" => json!({"destroyed":true}),
            "summary" => {
                json!({"count":r["values"].as_array().unwrap().len(),"min":0,"max":1,"mean":0.5,"sample_sd":0.5,"q25":0,"median":0.5,"q75":1})
            }
            "pca_monitor" => {
                let nr = r["reference"].as_array().unwrap().len();
                let nq = r["monitored"].as_array().unwrap().len();
                let mut v = json!({"eigenvalues":[1,1],"effective_components":2,"reference_t2":vec![0.;nr],"reference_q":vec![0.;nr],
                    "monitored_t2":vec![0.;nq],"monitored_q":vec![0.;nq],"n_beyond_t2":0,"n_beyond_q":0,"n_beyond_either":0,
                    "n_near_t2":0,"n_near_q":0,"n_near_either":0});
                for key in [
                    "t2_limit",
                    "q_limit",
                    "tolerance",
                    "condition",
                    "q_tolerance_scale",
                    "eigenvalue_resolution",
                    "reference_total_variance",
                    "monitored_total_variance",
                    "centroid_distance",
                    "centroid_subspace_distance",
                    "centroid_residual_distance",
                    "centroid_t2",
                    "retained_fraction",
                ] {
                    v[key] = json!(0.);
                }
                if self.invalid_monitor {
                    v["q_limit"] = json!("not a numeric owner value");
                }
                v
            }
            _ => return Err(ProviderError::unsupported("UNEXPECTED_TEST_OPERATION")),
        };
        out["backend_version"] = json!(self.version());
        Ok(out)
    }
}
fn fixture() -> SupportRequest {
    let train = vec![
        vec![-4., 1.],
        vec![-3., 1.],
        vec![-2., -1.],
        vec![-1., -1.],
        vec![1., -1.],
        vec![2., -1.],
        vec![3., 1.],
        vec![4., 1.],
    ];
    let query = vec![vec![12., 0.], vec![0., 5.]];
    let reference: Vec<_> = (0..8).map(|i| format!("train-{i}")).collect();
    let query_keys = vec!["test-0", "test-1"];
    let mut manifest: Vec<_> = reference
        .iter()
        .map(|k| json!({"key":k,"partition":"train"}))
        .collect();
    manifest.extend(
        query_keys
            .iter()
            .map(|k| json!({"key":k,"partition":"test"})),
    );
    manifest.push(json!({"key":"predict-not-granted","partition":"predict"}));
    let request = json!({"schema_version":1,"protocol_version":support::PROTOCOL,"fit":"train",
        "scope":{"schema_version":1,"protocol_version":"domains.browser_scoped_analysis.v1","operation":"train_reference_test_query","diagnostic":null,
            "dataset":{"dataset_id":"synthetic-access","source_id":"public-fixture","content_version":"1","content_sha256":"a".repeat(64)},
            "manifest":manifest,"reference_keys":reference,"query_keys":query_keys,"access":{"x":true,"m_fields":[],"y_fields":[]},
            "fit":"none","representation":"raw","selection_context":"unspecified","explicit_transductive":false,
            "parameters":{"preset":"f4_fixed_raw_v1"},"exclusion_field":null,
            "x":{"row_keys":reference.iter().map(String::as_str).chain(query_keys).collect::<Vec<_>>(),"matrix":train.into_iter().chain(query).collect::<Vec<_>>(),"axis":[1000.,1100.],"axis_unit":"nm"},"metadata":[]},
        "parameters":{"n_components":2,"monitoring":true,"max_components":2,"n_folds":5,"alpha":0.05},
        "dependencies":[],"dependency_fields":[],"external_limit_plan":null});
    support::parse(&request.to_string()).unwrap()
}
#[test]
fn actual_arguments_close_fit_train_transform_query_and_monitor_populations() {
    let r = fixture();
    let spy = Spy::default();
    let out = support::analyze(&r, &spy).unwrap();
    assert_eq!(out["status"], "computed");
    let calls = spy.calls.borrow();
    assert_eq!(calls.iter().filter(|(op, _)| op == "pca_fit").count(), 1);
    let matrices: Vec<_> = calls
        .iter()
        .filter(|(op, _)| op == "pca_transform")
        .map(|(_, v)| v["matrix"].clone())
        .collect();
    assert_eq!(calls[0].1["matrix"].as_array().unwrap().len(), 8);
    assert_eq!(matrices[0], calls[0].1["matrix"]);
    assert_eq!(matrices[1], json!([[12., 0.], [0., 5.]]));
    let monitor = &calls.iter().find(|(op, _)| op == "pca_monitor").unwrap().1;
    assert_eq!(monitor["reference"], matrices[0]);
    assert_eq!(monitor["monitored"], matrices[1]);
    assert_eq!(
        calls.iter().filter(|(op, _)| op == "pca_destroy").count(),
        1
    );
    assert!(!out.to_string().contains("state_bytes"));
    assert_eq!(out["receipt"]["y_test_accessed"], false);
    assert_eq!(out["limit_qualification"]["status"], "unknown");
}
#[test]
fn changed_test_never_changes_train_identity_or_scores() {
    let r = fixture();
    let mut changed = r.clone();
    changed.scope.x.as_mut().unwrap().matrix[8][0] = Some(99.);
    let a = support::analyze(&r, &Spy::default()).unwrap();
    let b = support::analyze(&changed, &Spy::default()).unwrap();
    for key in ["train_scores", "fit_identity_sha256", "fit_state_sha256"] {
        assert_eq!(a["projection"]["value"][key], b["projection"]["value"][key]);
    }
    assert_ne!(
        a["receipt"]["query_spectra_sha256"],
        b["receipt"]["query_spectra_sha256"]
    );
}
#[test]
fn retained_labels_predict_rows_bad_axes_and_forbidden_fits_refuse_before_owner() {
    let mut cases = Vec::new();
    let mut r = fixture();
    r.fit = "test".into();
    cases.push(r);
    let mut r = fixture();
    r.scope.access.y_fields.push("Y_test".into());
    cases.push(r);
    let mut r = fixture();
    r.scope.query_keys.push("predict-not-granted".into());
    cases.push(r);
    let mut r = fixture();
    r.scope.x.as_mut().unwrap().axis.swap(0, 1);
    r.scope.x.as_mut().unwrap().axis[1] = 1100.;
    cases.push(r);
    let mut r = fixture();
    r.scope.x.as_mut().unwrap().matrix[0][0] = None;
    cases.push(r);
    for r in cases {
        let spy = Spy::default();
        assert!(support::analyze(&r, &spy).is_err());
        assert!(spy.calls.borrow().is_empty());
    }
}
#[test]
fn invalid_monitoring_is_local_without_changing_projection_or_parameters() {
    let mut r = fixture();
    r.parameters.n_folds = 99;
    let spy = Spy::default();
    let out = support::analyze(&r, &spy).unwrap();
    assert_eq!(out["status"], "partial");
    assert_eq!(out["projection"]["status"], "computed");
    assert_eq!(out["monitoring"]["reason"], "MONITORING_PARAMETERS_INVALID");
    assert!(!spy.calls.borrow().iter().any(|(op, _)| op == "pca_monitor"));
    assert_eq!(out["receipt"]["parameters"]["n_folds"], 99);
}
#[test]
fn state_mutation_refuses_projection_and_always_destroys_handle() {
    let mut r = fixture();
    r.parameters.monitoring = false;
    let spy = Spy {
        tamper_state: true,
        ..Spy::default()
    };
    let out = support::analyze(&r, &spy).unwrap();
    assert_eq!(
        out["projection"]["reason"],
        "TRAIN_TRANSFORM_CHANGED_FITTED_STATE"
    );
    assert_eq!(out["projection"]["value"], Value::Null);
    assert_eq!(spy.calls.borrow().last().unwrap().0, "pca_destroy");
    assert_eq!(
        spy.calls
            .borrow()
            .iter()
            .filter(|(op, _)| op == "pca_transform")
            .count(),
        1
    );
}
#[test]
fn invalid_numeric_owner_monitor_reply_cannot_be_presented_as_computed() {
    let spy = Spy {
        invalid_monitor: true,
        ..Spy::default()
    };
    let out = support::analyze(&fixture(), &spy).unwrap();
    assert_eq!(out["projection"]["status"], "computed");
    assert_eq!(
        out["monitoring"]["reason"],
        "INVALID_METHODS_MONITOR_RESPONSE"
    );
}
#[test]
fn external_qualification_is_conditional_and_declared_repeats_contradict_it() {
    let mut r = fixture();
    r.external_limit_plan=Some(serde_json::from_value(json!({"protocol_version":"domains.monitor_indexed_folds_design.v1",
        "dataset_content_sha256":r.scope.dataset.content_sha256,"reference_keys":r.scope.reference_keys,
        "max_components":2,"n_folds":5,"alpha":0.05,"independent_unit_ids":r.scope.reference_keys,"indivisible_dependency_fields":[],
        "source":"Synthetic external design fixture; not a real study","prospective":true,"row_index_modulo_folds_authorized":true})).unwrap());
    let a = support::analyze(&r, &Spy::default()).unwrap();
    assert_eq!(a["limit_qualification"]["status"], "conditional_external");
    let keys: Vec<_> = r
        .scope
        .reference_keys
        .iter()
        .chain(&r.scope.query_keys)
        .cloned()
        .collect();
    r.dependencies=serde_json::from_value(json!([{"name":"specimen","role":"specimen","kind":"categorical","origin":"declared synthetic field",
        "derived_from_target":false,"evidence":"declared","row_keys":keys,"values":["same","same","s2","s3","s4","s5","s6","s7","same","query"]}])).unwrap();
    r.dependency_fields = vec!["specimen".into()];
    let b = support::analyze(&r, &Spy::default()).unwrap();
    assert_eq!(b["limit_qualification"]["status"], "not_qualified");
    assert_eq!(b["projection"]["value"], a["projection"]["value"]);
    assert_eq!(
        b["dependence"]["fields"][0]["train_cross_fold_identities"],
        1
    );
    assert_eq!(
        b["dependence"]["fields"][0]["train_test_shared_identities"],
        1
    );
}
