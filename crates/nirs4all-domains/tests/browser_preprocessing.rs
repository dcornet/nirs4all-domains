//! Protocol spies inspect actual payloads; they are not numerical oracles.
use nirs4all_domains::{
    browser_preprocessing::{self as protocol, SensitivityRequest},
    browser_support::SupportProvider,
};
use nirs4all_preflight::ProviderError;
use serde_json::{json, Value};
use std::cell::RefCell;

#[derive(Default)]
struct Spy {
    calls: RefCell<Vec<(String, Value)>>,
    active: RefCell<Option<(String, Value, Vec<u8>)>>,
    fail_fit: bool,
    corrupt_reference: bool,
    mutate_state: bool,
}
impl SupportProvider for Spy {
    fn version(&self) -> String {
        "1.3.13+abi.2.20.0".into()
    }
    fn execute(&self, op: &str, r: &Value) -> Result<Value, ProviderError> {
        self.calls.borrow_mut().push((op.into(), r.clone()));
        let mut value = match op {
            "preprocess_fit" => {
                if self.fail_fit {
                    return Err(ProviderError::unsupported("SYNTHETIC_OWNER_REFUSAL"));
                }
                let operator = r["operator"].as_str().unwrap().to_string();
                let bytes = serde_json::to_vec(&json!([operator, r["parameters"]])).unwrap();
                *self.active.borrow_mut() =
                    Some((operator, r["parameters"].clone(), bytes.clone()));
                json!({"state_bytes":bytes})
            }
            "preprocess_restore" => {
                let bytes: Vec<u8> = serde_json::from_value(r["state_bytes"].clone()).unwrap();
                let saved: Value = serde_json::from_slice(&bytes).unwrap();
                *self.active.borrow_mut() = Some((
                    saved[0].as_str().unwrap().into(),
                    saved[1].clone(),
                    bytes.clone(),
                ));
                json!({"state_bytes":bytes})
            }
            "preprocess_transform" => {
                let active = self.active.borrow();
                let (op, parameters, bytes) = active.as_ref().unwrap();
                let mut matrix = r["matrix"].clone();
                if op == "CropTransformer" {
                    let start = parameters["start"].as_u64().unwrap() as usize;
                    let end = parameters["end"].as_u64().unwrap() as usize;
                    matrix = json!(matrix
                        .as_array()
                        .unwrap()
                        .iter()
                        .map(|row| row.as_array().unwrap()[start..end].to_vec())
                        .collect::<Vec<_>>());
                }
                if self.corrupt_reference && matrix[0][0].as_f64().unwrap() < 100. {
                    matrix[0][0] = json!(matrix[0][0].as_f64().unwrap() + 1.);
                }
                json!({"matrix":matrix,"state_bytes":if self.mutate_state{vec![9,9,9]}else{bytes.clone()}})
            }
            "preprocess_destroy" => {
                self.active.borrow_mut().take();
                json!({"destroyed":true})
            }
            "pca_fit" => json!({"state_bytes":[1,2,3]}),
            "pca_transform" => {
                json!({"scores":r["matrix"].as_array().unwrap().iter().map(|row|vec![row[0].clone()]).collect::<Vec<_>>(),"state_bytes":[1,2,3]})
            }
            "pca_destroy" => json!({"destroyed":true}),
            "summary" => {
                json!({"count":r["values"].as_array().unwrap().len(),"min":0.,"max":1.,"mean":0.5,"sample_sd":0.5,"q25":0.,"median":0.5,"q75":1.})
            }
            "capabilities" => return Ok(json!([])),
            _ => return Err(ProviderError::unsupported("SPY_DIAGNOSTIC_NOT_CONFIGURED")),
        };
        value["backend_version"] = json!(self.version());
        Ok(value)
    }
}
fn fixture() -> SensitivityRequest {
    protocol::parse(&json!({"schema_version":1,"protocol_version":protocol::PROTOCOL,"dataset":{"dataset_id":"synthetic","source_id":"public-fixture","content_version":"1","content_sha256":"a".repeat(64)},"manifest":[{"key":"r0","partition":"train"},{"key":"r1","partition":"train"},{"key":"r2","partition":"train"},{"key":"q0","partition":"test"},{"key":"q1","partition":"test"},{"key":"q2","partition":"test"},{"key":"predict-forbidden","partition":"predict"}],"population":"train","reference_keys":["r0","r1","r2"],"query_keys":[],"x":{"row_keys":["r0","r1","r2"],"matrix":[[1.,2.,3.],[4.,5.,6.],[7.,8.,9.]],"axis":[1000.,1100.,1300.],"axis_unit":"nm"},"factors":[],"dependencies":[],"exclusion_field":null,"access":{"x":true,"m_fields":[],"y_fields":[]},"plan":{"bank_id":"prospective-fixture-v1","kind":"prospective","parent_plan_sha256":null,"representations":[{"id":"raw","family":"raw","steps":[]},{"id":"snv","family":"scatter","steps":[{"operator":"SNV","parameters":{"with_mean":true,"with_std":true,"ddof":0}}]},{"id":"snv-crop","family":"scatter-crop","steps":[{"operator":"SNV","parameters":{"with_mean":true,"with_std":true,"ddof":0}},{"operator":"CropTransformer","parameters":{"start":1,"end":3}}]}],"structure":false,"compare_neighbors":false,"compare_clusters":false,"correlation_method":"pearson","support":{"n_components":1,"monitoring":false,"max_components":1,"n_folds":2,"alpha":0.05}},"stage":"reference_only","frozen_reference":null,"reuse_exact_prefixes":true}).to_string()).unwrap()
}
fn test_audit(mut request: SensitivityRequest, frozen: Value) -> SensitivityRequest {
    request.stage = "test_audit".into();
    request.query_keys = vec!["q0".into(), "q1".into(), "q2".into()];
    request.x.row_keys.extend(request.query_keys.clone());
    request.x.matrix.extend(
        [[101., 102., 103.], [104., 105., 106.], [107., 108., 109.]]
            .map(|r| r.into_iter().map(Some).collect()),
    );
    request.frozen_reference = Some(frozen);
    request
}
#[test]
fn actual_reference_payloads_axis_lineage_and_prefix_reuse_are_exact() {
    let request = fixture();
    let spy = Spy::default();
    let out = protocol::analyze(&request, &spy).unwrap();
    assert_eq!(out["representations"].as_array().unwrap().len(), 3);
    assert_eq!(out["receipt"]["exact_prefix_cache_hits"], 1);
    assert_eq!(out["receipt"]["test_x_accessed"], false);
    assert_eq!(
        out["representations"][2]["value"]["axis"],
        json!([1100., 1300.])
    );
    assert_ne!(
        out["representations"][0]["value"]["source"]["source_id"],
        request.dataset.source_id
    );
    for (op, payload) in spy
        .calls
        .borrow()
        .iter()
        .filter(|(op, _)| op == "preprocess_fit" || op == "preprocess_transform")
    {
        assert_eq!(payload["matrix"].as_array().unwrap().len(), 3, "{op}");
        assert!(payload["matrix"][0][0].as_f64().unwrap() < 100.);
    }
    assert_eq!(
        spy.calls
            .borrow()
            .iter()
            .filter(|(op, _)| op == "preprocess_fit")
            .count(),
        2
    );
    assert!(!out.to_string().contains("state_bytes"));
    fn no_raw_matrices(v: &Value) {
        match v {
            Value::Object(object) => {
                for (name, child) in object {
                    if name == "matrix" {
                        assert!(
                            child
                                .as_array()
                                .is_none_or(|a| a.first().is_none_or(|v| !v.is_array())),
                            "raw matrix escaped transport"
                        );
                    }
                    no_raw_matrices(child);
                }
            }
            Value::Array(items) => {
                for item in items {
                    no_raw_matrices(item);
                }
            }
            _ => {}
        }
    }
    no_raw_matrices(&out);
    let mut uncached = request.clone();
    uncached.reuse_exact_prefixes = false;
    let plain = protocol::analyze(&uncached, &Spy::default()).unwrap();
    assert_eq!(out["representations"], plain["representations"]);
    assert_eq!(
        out["reference_input_sha256"],
        plain["reference_input_sha256"]
    );
    assert_eq!(out["input_sha256"], plain["input_sha256"]);
}
#[test]
fn second_stage_rebuilds_all_reference_states_then_restores_for_actual_query_only() {
    let request = fixture();
    let frozen = protocol::analyze(&request, &Spy::default()).unwrap();
    let audit = test_audit(request, frozen);
    let spy = Spy::default();
    let out = protocol::analyze(&audit, &spy).unwrap();
    assert_eq!(out["receipt"]["test_x_accessed"], true);
    let calls = spy.calls.borrow();
    let first_restore = calls
        .iter()
        .position(|(op, _)| op == "preprocess_restore")
        .unwrap();
    assert!(calls[..first_restore]
        .iter()
        .filter(|(op, _)| op == "preprocess_fit")
        .all(|(_, r)| r["matrix"][0][0].as_f64().unwrap() < 100.));
    assert!(!calls[first_restore..]
        .iter()
        .any(|(op, _)| op == "preprocess_fit"));
    assert!(calls
        .iter()
        .filter(|(op, _)| op == "preprocess_restore")
        .all(|(_, r)| r.get("matrix").is_none()));
    assert!(calls
        .iter()
        .filter(|(op, _)| op == "pca_fit")
        .all(|(_, r)| r["matrix"][0][0].as_f64().unwrap() < 100.));
    let outer = out["receipt"]["provider_calls"].as_array().unwrap();
    for call in outer.iter().filter(|v| v["operation"] == "pca_transform") {
        let keys = call["row_keys"].as_array().unwrap();
        assert!(
            keys == &json!(["r0", "r1", "r2"]).as_array().unwrap().clone()
                || keys == &json!(["q0", "q1", "q2"]).as_array().unwrap().clone()
        );
    }
    let mut changed = audit.clone();
    changed.x.matrix[3][0] = Some(999.);
    let changed = protocol::analyze(&changed, &Spy::default()).unwrap();
    assert_eq!(
        out["reference_input_sha256"],
        changed["reference_input_sha256"]
    );
    assert_ne!(out["input_sha256"], changed["input_sha256"]);
}
#[test]
fn changed_reference_reproduction_refuses_before_any_query_transform() {
    let request = fixture();
    let frozen = protocol::analyze(&request, &Spy::default()).unwrap();
    let audit = test_audit(request, frozen);
    let spy = Spy {
        corrupt_reference: true,
        ..Spy::default()
    };
    assert!(protocol::analyze(&audit, &spy).is_err());
    assert!(!spy
        .calls
        .borrow()
        .iter()
        .any(|(op, _)| op == "preprocess_restore"));
    assert!(!spy
        .calls
        .borrow()
        .iter()
        .any(|(op, p)| op == "preprocess_transform" && p["matrix"][0][0].as_f64().unwrap() > 100.));
}
#[test]
fn malformed_access_order_targets_freeze_and_budget_refuse_before_provider() {
    let mut cases = Vec::new();
    let mut r = fixture();
    r.access.y_fields.push("Y_test".into());
    cases.push(r);
    let mut r = fixture();
    r.reference_keys.swap(0, 1);
    cases.push(r);
    let mut r = fixture();
    r.x.matrix[0][0] = None;
    cases.push(r);
    let mut r = fixture();
    r.x.row_keys.push("predict-forbidden".into());
    cases.push(r);
    let mut r = fixture();
    r.x.axis = vec![1., 3., 2.];
    cases.push(r);
    let r = fixture();
    let mut frozen = protocol::analyze(&r, &Spy::default()).unwrap();
    frozen["representations"][0]["value"]["reference_matrix_sha256"] = json!("b".repeat(64));
    cases.push(test_audit(r, frozen));
    let mut r = fixture();
    r.plan.representations = (0..16)
        .map(|i| {
            let mut s = r.plan.representations[1].clone();
            s.id = format!("rep-{i}");
            s.steps = vec![s.steps[0].clone(); 3];
            s
        })
        .collect();
    r.plan.representations[0].id = "raw".into();
    r.plan.representations[0].steps.clear();
    r.x.axis = (0..40_000).map(|i| i as f64).collect();
    r.x.matrix = vec![vec![Some(1.); 40_000]; 3];
    cases.push(r);
    for r in cases {
        let spy = Spy::default();
        assert!(protocol::analyze(&r, &spy).is_err());
        assert!(spy.calls.borrow().is_empty());
    }
    let mut wire = serde_json::to_value(fixture()).unwrap();
    wire["Y"] = json!([1., 2., 3.]);
    assert!(protocol::parse(&wire.to_string()).is_err());
}
#[test]
fn owner_and_operator_failures_stay_local_and_always_clean_up() {
    let request = fixture();
    let spy = Spy {
        fail_fit: true,
        ..Spy::default()
    };
    let out = protocol::analyze(&request, &spy).unwrap();
    assert_eq!(out["status"], "computed");
    assert_eq!(out["representations"][0]["status"], "computed");
    assert_eq!(out["representations"][1]["status"], "unavailable");
    assert!(spy
        .calls
        .borrow()
        .iter()
        .any(|(op, _)| op == "preprocess_destroy"));
    let spy = Spy {
        mutate_state: true,
        ..Spy::default()
    };
    let out = protocol::analyze(&request, &spy).unwrap();
    assert_eq!(out["representations"][1]["status"], "unavailable");
    assert!(spy.active.borrow().is_none());
    let mut r = request;
    r.plan.representations[1].steps[0].operator = "UnknownOwnerOperation".into();
    let out = protocol::analyze(&r, &Spy::default()).unwrap();
    assert_eq!(
        out["representations"][1]["reason"],
        "UNSUPPORTED_PREPROCESSOR"
    );
    assert_eq!(out["representations"][2]["status"], "computed");
}
#[test]
fn unpartitioned_and_metadata_grants_are_closed_without_changing_types() {
    let mut r = fixture();
    r.population = "unpartitioned".into();
    assert!(protocol::validate(&r).is_err());
    r.manifest.truncate(3);
    for m in &mut r.manifest {
        m.partition = nirs4all_domains::browser_scoped::PartitionRole::Unpartitioned;
    }
    assert!(protocol::validate(&r).is_ok());
    let column = json!({"name":"group","role":"group","kind":"categorical","unit":null,"origin":"M","derived_from_target":false,"evidence":"declared","row_keys":r.reference_keys,"values":[1,"1",true]});
    r.dependencies = vec![serde_json::from_value(column).unwrap()];
    r.exclusion_field = Some("group".into());
    r.access.m_fields = vec!["group".into()];
    assert!(protocol::analyze(&r, &Spy::default()).is_ok());
    r.dependencies[0].values[1] = Value::Null;
    assert!(protocol::validate(&r).is_err());
}

#[test]
fn a_selected_factor_can_also_be_a_matching_exclusion_dependency_but_conflicts_refuse() {
    let mut r = fixture();
    let column = json!({"name":"instrument","role":"instrument","kind":"categorical","unit":null,"origin":"M","derived_from_target":false,"evidence":"declared","row_keys":r.reference_keys,"values":["a","a","b"]});
    let field: nirs4all_domains::browser_factor::FactorColumn =
        serde_json::from_value(column).unwrap();
    r.factors = vec![field.clone()];
    r.dependencies = vec![field];
    r.access.m_fields = vec!["instrument".into()];
    r.exclusion_field = Some("instrument".into());
    assert!(protocol::validate(&r).is_ok());
    let frozen = protocol::analyze(&r, &Spy::default()).unwrap();
    let mut audit = test_audit(r.clone(), frozen);
    audit.dependencies[0]
        .row_keys
        .extend(audit.query_keys.clone());
    audit.dependencies[0]
        .values
        .extend([json!("a"), json!("c"), json!("c")]);
    assert!(protocol::validate(&audit).is_ok());
    r.dependencies[0].values[0] = json!("conflict");
    let spy = Spy::default();
    assert!(protocol::analyze(&r, &spy).is_err());
    assert!(spy.calls.borrow().is_empty());
    let mut bad = audit;
    bad.dependencies[0].unit = Some("conflicting-unit".into());
    assert!(protocol::validate(&bad).is_err());
}

#[test]
fn incomplete_operator_parameters_are_local_refusals_before_owner() {
    let mut request = fixture();
    request.plan.representations[1].steps[0]
        .parameters
        .remove("ddof");
    let spy = Spy::default();
    let out = protocol::analyze(&request, &spy).unwrap();
    assert_eq!(
        out["representations"][1]["reason"],
        "EXPLICIT_PREPROCESS_PARAMETERS_REQUIRED"
    );
    assert_eq!(out["representations"][2]["status"], "computed");
    assert_eq!(
        spy.calls
            .borrow()
            .iter()
            .filter(|(op, _)| op == "preprocess_fit")
            .count(),
        2
    );
}
