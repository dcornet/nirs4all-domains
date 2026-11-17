//! Synthetic access/orchestration adversaries. Provider stubs test transport,
//! not numerical accuracy; no numerical algorithm is implemented as an oracle.
use nirs4all_domains::browser_scoped::{self as scoped, ScopedRequest};
use nirs4all_preflight::*;
use serde_json::{json, Value};
use std::cell::RefCell;

#[derive(Default)]
struct Spy {
    calls: RefCell<Vec<(String, Value)>>,
    fail_pca: bool,
    malformed_pca: bool,
    fail_neighbors: bool,
    malformed_neighbors: bool,
}
impl Spy {
    fn record(&self, name: &str, value: &impl serde::Serialize) {
        self.calls
            .borrow_mut()
            .push((name.into(), serde_json::to_value(value).unwrap()));
    }
    fn requests(&self, name: &str) -> Vec<Value> {
        self.calls
            .borrow()
            .iter()
            .filter(|(op, _)| op == name)
            .map(|(_, r)| r.clone())
            .collect()
    }
    fn assert_unused(&self) {
        assert!(self.calls.borrow().is_empty());
    }
}
impl MethodsProvider for Spy {
    fn capabilities(&self) -> Vec<Capability> {
        vec![]
    }
    fn pca(&self, r: &PcaRequest) -> Result<PcaDiagnostics, ProviderError> {
        self.record("pca", r);
        if self.fail_pca {
            return Err(ProviderError::numerical("SCOPED_FIXTURE_PCA_FAILURE"));
        }
        // Shape-valid fixed stub; these scores are deliberately not an estimate
        // of the input matrix. Only their exact transport population is tested.
        let mut out = PcaDiagnostics {
            eigenvalues: vec![1.; r.n_components],
            scores: vec![vec![42.; r.n_components]; r.matrix.len()],
            full_moments: [r.n_components as f64, r.n_components as f64],
            resolution: 1e-14,
            unresolved: vec![false; r.n_components],
            backend_version: "transport-spy".into(),
        };
        if self.malformed_pca {
            out.scores.pop();
        }
        Ok(out)
    }
    fn repeatability(
        &self,
        _: &RepeatabilityRequest,
    ) -> Result<RepeatabilityDiagnostics, ProviderError> {
        panic!("F4.0 must never request repeatability")
    }
    fn nearest_neighbors(
        &self,
        r: &NearestNeighborsRequest,
    ) -> Result<NearestNeighborsDiagnostics, ProviderError> {
        self.record("nearest_neighbors", r);
        if self.fail_neighbors {
            return Err(ProviderError::unsupported(
                "SCOPED_FIXTURE_NEIGHBORS_UNSUPPORTED",
            ));
        }
        // All-padding fixture exercises insufficient admissible neighbors
        // without introducing a distance implementation in the test.
        let mut out = NearestNeighborsDiagnostics {
            indices: vec![vec![-1; r.k]; r.query.len()],
            distances: vec![vec![None; r.k]; r.query.len()],
            backend_version: "transport-spy".into(),
        };
        if self.malformed_neighbors {
            out.indices[0][0] = 0;
        }
        Ok(out)
    }
    fn summary(&self, _: &SummaryRequest) -> Result<SummaryDiagnostics, ProviderError> {
        panic!("all-padding and all-noise fixtures have no summary population")
    }
    fn hdbscan(&self, r: &HdbscanRequest) -> Result<HdbscanDiagnostics, ProviderError> {
        self.record("hdbscan", r);
        Ok(HdbscanDiagnostics {
            labels: vec![-1; r.matrix.len()],
            membership: vec![0.; r.matrix.len()],
            outlier_scores: vec![None; r.matrix.len()],
            persistence: vec![],
            tree: vec![],
            backend_version: "transport-spy".into(),
        })
    }
}

fn wire(operation: &str) -> Value {
    let train = vec!["a", "b", "c"];
    let query = if matches!(operation, "train_structure" | "metadata_factor_audit") {
        vec![]
    } else {
        vec!["t1", "t2"]
    };
    let mut rows = train.clone();
    rows.extend(&query);
    let uses_x = !matches!(
        operation,
        "metadata_factor_audit" | "cross_partition_metadata_audit"
    );
    let matrix: Vec<_> = rows
        .iter()
        .map(|key| match *key {
            "a" => json!([0.]),
            "b" => json!([1.]),
            "c" => json!([2.]),
            "t1" => json!([100.]),
            _ => json!([200.]),
        })
        .collect();
    json!({"schema_version":1,"protocol_version":scoped::PROTOCOL,"operation":operation,
        "diagnostic":if operation=="integrity_audit" {json!("exact_spectra")} else {Value::Null},
        "dataset":{"dataset_id":"synthetic-access","source_id":"synthetic-source","content_version":"v1","content_sha256":"a".repeat(64)},
        "manifest":[{"key":"a","partition":"train"},{"key":"t1","partition":"test"},
            {"key":"b","partition":"train"},{"key":"future","partition":"predict"},
            {"key":"c","partition":"train"},{"key":"t2","partition":"test"}],
        "reference_keys":train,"query_keys":query,"access":{"x":uses_x,"m_fields":[],"y_fields":[]},
        "fit":match operation {"train_structure"=>"train","global_descriptive_transductive"=>"transductive",_=>"none"},
        "representation":"raw","selection_context":"pre_selection_integrity_audit",
        "explicit_transductive":operation=="global_descriptive_transductive","parameters":{"preset":"f4_fixed_raw_v1"},
        "exclusion_field":null,"x":if uses_x {json!({"row_keys":rows,"matrix":matrix,"axis":[1000.],"axis_unit":"nm"})} else {Value::Null},"metadata":[]})
}
fn request(v: &Value) -> ScopedRequest {
    scoped::parse(&v.to_string()).unwrap()
}
fn add_metadata(v: &mut Value, name: &str, role: &str, values: Value) {
    let mut keys = v["reference_keys"].as_array().unwrap().clone();
    keys.extend(v["query_keys"].as_array().unwrap().iter().cloned());
    v["access"]["m_fields"]
        .as_array_mut()
        .unwrap()
        .push(json!(name));
    v["metadata"].as_array_mut().unwrap().push(json!({"name":name,"role":role,"kind":"categorical",
        "origin":"synthetic declaration","derived_from_target":false,"evidence":"unknown","row_keys":keys,"values":values}));
}
fn refused(v: &Value) {
    let spy = Spy::default();
    assert!(scoped::parse(&v.to_string()).is_err());
    // Deserialization-only bypass still meets the validate-before-call guard.
    if let Ok(r) = serde_json::from_value::<ScopedRequest>(v.clone()) {
        assert!(scoped::analyze(&r, &spy).is_err());
    }
    spy.assert_unused();
}

#[test]
fn complete_train_provider_population_isolated_from_test_and_prediction() {
    let spy = Spy::default();
    let v = wire("train_structure");
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    let pca = spy.requests("pca");
    assert_eq!(pca.len(), 1);
    assert_eq!(pca[0]["sample_ids"], json!(["a", "b", "c"]));
    assert_eq!(pca[0]["matrix"], json!([[0.], [1.], [2.]]));
    assert_eq!(pca[0]["source_id"], "synthetic-source");
    for neighbors in spy.requests("nearest_neighbors") {
        assert_eq!(neighbors["query"].as_array().unwrap().len(), 3);
        assert_eq!(neighbors["query"], neighbors["reference"]);
    }
    assert_eq!(result["receipt"]["fit_keys"], json!(["a", "b", "c"]));
    assert_eq!(
        result["receipt"]["requested_fit_keys"],
        json!(["a", "b", "c"])
    );
    assert_eq!(result["receipt"]["fit_attempted"], true);
    assert_eq!(result["receipt"]["fit_executed"], true);
    assert_eq!(result["receipt"]["test_x_accessed"], false);
    assert_eq!(result["receipt"]["fields_read"]["y"], json!([]));
    let calls = result["receipt"]["provider_calls"].as_array().unwrap();
    let pca = calls.iter().find(|v| v["operation"] == "pca").unwrap();
    assert_eq!(pca["matrices"]["matrix"]["shape"], json!([3, 1]));
    assert_eq!(
        pca["matrices"]["matrix"]["sha256"].as_str().unwrap().len(),
        64
    );
    assert!(pca["matrices"]["matrix"].get("values").is_none());
}

#[test]
fn hdbscan_receives_only_the_validated_train_score_population() {
    let mut v = wire("train_structure");
    let keys: Vec<_> = (0..8).map(|i| format!("tr{i}")).collect();
    v["reference_keys"] = json!(keys);
    v["manifest"] = json!(keys
        .iter()
        .map(|key| json!({"key":key,"partition":"train"}))
        .chain([
            json!({"key":"held","partition":"test"}),
            json!({"key":"future","partition":"predict"})
        ])
        .collect::<Vec<_>>());
    v["x"]["row_keys"] = json!(keys);
    v["x"]["matrix"] = json!((0..8).map(|i| vec![f64::from(i)]).collect::<Vec<_>>());
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    let pca = spy.requests("pca");
    assert_eq!(pca[0]["sample_ids"], json!(keys));
    assert_eq!(pca[0]["matrix"], v["x"]["matrix"]);
    let density = spy.requests("hdbscan");
    assert_eq!(density.len(), 1);
    assert_eq!(density[0]["matrix"], json!(vec![vec![42.]; 8]));
    assert_eq!(
        result["value"]["structure"]["metrics"]["density"]["value"]["noise_count"],
        8
    );
    assert_eq!(result["receipt"]["fit_keys"], v["reference_keys"]);
}

#[test]
fn forbidden_y_fields_hidden_test_fit_and_grant_mismatches_have_no_calls() {
    for field in ["y", "spectra_y", "targets", "Y_test"] {
        let mut v = wire("train_structure");
        v[field] = json!(["secret"]);
        refused(&v);
    }
    let mut v = wire("train_structure");
    v["access"]["y_fields"] = json!(["target"]);
    refused(&v);
    let mut v = wire("train_structure");
    v["reference_keys"][1] = json!("t1");
    v["x"]["row_keys"][1] = json!("t1");
    refused(&v);
    let mut v = wire("train_structure");
    v["x"]["matrix"][1] = json!([null]);
    refused(&v);
    let mut v = wire("train_structure");
    v["access"]["x"] = json!(false);
    refused(&v);
    let mut v = wire("train_structure");
    v["x"]["row_keys"] = json!(["b", "a", "c"]);
    refused(&v);
    let mut v = wire("train_structure");
    v["x"]["row_keys"] = json!(["a", "a", "c"]);
    refused(&v);
    let mut v = wire("train_structure");
    v["manifest"][1]["key"] = json!("a");
    refused(&v);
    let mut v = wire("train_structure");
    v["reference_keys"] = json!(["a", "b"]);
    refused(&v);
    let mut v = wire("train_structure");
    v["parameters"]["n_components"] = json!(2);
    refused(&v);
    let mut v = wire("train_structure");
    v["parameters"]["preset"] = json!("tuned");
    refused(&v);
}

#[test]
fn all_nested_objects_deny_unknown_fields_and_only_metadata_scalars_are_admitted() {
    for field in ["diagnostic", "x", "exclusion_field"] {
        let mut v = wire("train_structure");
        v.as_object_mut().unwrap().remove(field);
        refused(&v);
    }
    for pointer in ["/dataset", "/manifest/0", "/access", "/parameters", "/x"] {
        let mut v = wire("train_structure");
        v.pointer_mut(pointer).unwrap()["Y_test"] = json!(99);
        refused(&v);
    }
    let mut v = wire("metadata_factor_audit");
    add_metadata(&mut v, "batch", "group", json!(["a", "b", "c"]));
    v["metadata"][0]["Y_test"] = json!([1, 2, 3]);
    refused(&v);
    let mut v = wire("metadata_factor_audit");
    add_metadata(&mut v, "batch", "group", json!([{}, null, "a"]));
    refused(&v);
    let mut v = wire("metadata_factor_audit");
    add_metadata(&mut v, "batch", "group", json!([[], null, "a"]));
    refused(&v);
}

#[test]
fn train_exclusion_reads_only_complete_train_metadata_and_refuses_test_values() {
    let mut v = wire("train_structure");
    add_metadata(&mut v, "unit", "group", json!(["same", "same", "other"]));
    v["exclusion_field"] = json!("unit");
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    assert_eq!(spy.requests("pca")[0]["sample_ids"], json!(["a", "b", "c"]));
    for nn in spy.requests("nearest_neighbors") {
        assert_eq!(nn["reference_group_ids"], json!([0, 0, 1]));
        assert_eq!(nn["query_group_ids"], json!([0, 0, 1]));
    }
    assert_eq!(
        result["receipt"]["fields_read"]["m"][0]["row_keys"],
        json!(["a", "b", "c"])
    );
    let mut wrong = v.clone();
    wrong["metadata"][0]["row_keys"]
        .as_array_mut()
        .unwrap()
        .push(json!("t1"));
    wrong["metadata"][0]["values"]
        .as_array_mut()
        .unwrap()
        .push(json!("test-secret"));
    refused(&wrong);
}

#[test]
fn metadata_without_x_has_documentary_counts_and_no_provider_calls() {
    let mut v = wire("metadata_factor_audit");
    add_metadata(&mut v, "batch", "group", json!(["A", null, "A"]));
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    spy.assert_unused();
    let column = &result["value"]["columns"][0];
    assert_eq!(column["reference"]["n_rows"], 3);
    assert_eq!(column["reference"]["missing_count"], 1);
    assert_eq!(column["reference"]["cardinality"], 1);
    assert_eq!(
        column["reference"]["level_counts"],
        json!([{"level":"A","count":2}])
    );
    assert_eq!(column["evidence"], "unknown");
    assert_eq!(column["association"]["status"], "unavailable");
    assert!(result["receipt"]["fields_read"]["x"].is_null());
    let mut extra = v.clone();
    extra["x"] = wire("train_structure")["x"].clone();
    refused(&extra);
    let mut reordered = v.clone();
    reordered["metadata"][0]["row_keys"] = json!(["b", "a", "c"]);
    refused(&reordered);
    let mut wrong_grant = v.clone();
    wrong_grant["access"]["m_fields"] = json!(["other"]);
    refused(&wrong_grant);
    let mut derived = v.clone();
    derived["metadata"][0]["derived_from_target"] = json!(true);
    refused(&derived);
}

#[test]
fn continuous_metadata_does_not_invent_a_distribution_or_association_test() {
    let mut v = wire("metadata_factor_audit");
    add_metadata(&mut v, "age", "factor", json!([2., null, 2.]));
    v["metadata"][0]["kind"] = json!("continuous");
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    spy.assert_unused();
    let column = &result["value"]["columns"][0];
    assert_eq!(column["reference"]["missing_count"], 1);
    assert_eq!(column["reference"]["cardinality"], 1);
    assert!(column["reference"]["level_counts"].is_null());
    assert!(column.get("correlation").is_none());
    assert!(column.get("eta_squared").is_none());
}

#[test]
fn unknown_metadata_derivation_is_retained_as_null_and_never_reported_false() {
    let mut v = wire("metadata_factor_audit");
    add_metadata(&mut v, "batch", "group", json!(["A", null, "A"]));
    v["metadata"][0]["derived_from_target"] = Value::Null;
    v["metadata"][0]["origin"] = json!("unknown");
    let spy = Spy::default();
    let r = request(&v);
    assert_eq!(r.metadata[0].derived_from_target, None);
    let result = scoped::analyze(&r, &spy).unwrap();
    spy.assert_unused();
    assert!(result["value"]["columns"][0]["derived_from_target"].is_null());
    assert!(result["receipt"]["fields_read"]["m"][0]["derived_from_target"].is_null());
    assert_eq!(result["value"]["columns"][0]["origin"], "unknown");
    assert!(result["limitations"].as_array().unwrap().iter().any(|v| v
        .as_str()
        .unwrap()
        .contains("target derivation remains unknown")));
    v["metadata"][0]
        .as_object_mut()
        .unwrap()
        .remove("derived_from_target");
    refused(&v);
}

#[test]
fn cross_partition_metadata_uses_literal_sets_without_x_or_fit() {
    let mut v = wire("cross_partition_metadata_audit");
    add_metadata(&mut v, "batch", "group", json!(["A", "A", null, "A", "B"]));
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    spy.assert_unused();
    assert_eq!(
        result["value"]["columns"][0]["literal_shared_nonmissing_value_count"],
        1
    );
    assert_eq!(result["receipt"]["fit_keys"], json!([]));
    assert_eq!(
        result["value"]["columns"][0]["reference_only_nonmissing_value_count"],
        0
    );
    assert_eq!(
        result["value"]["columns"][0]["query_only_nonmissing_value_count"],
        1
    );
    assert_eq!(
        result["value"]["columns"][0]["reference_only_levels"],
        json!([])
    );
    assert_eq!(
        result["value"]["columns"][0]["query_only_levels"],
        json!(["B"])
    );
    assert_eq!(result["receipt"]["fit_attempted"], false);
    assert_eq!(result["receipt"]["fit_executed"], false);
    assert_eq!(result["receipt"]["query_keys"], json!(["t1", "t2"]));
    let mut wrong = v.clone();
    wrong["metadata"][0]["row_keys"][3] = json!("future");
    refused(&wrong);
}

#[test]
fn metadata_unpartitioned_fallback_never_overrides_assigned_train_or_test() {
    let mut v = wire("metadata_factor_audit");
    v["manifest"] =
        json!([{"key":"u1","partition":"unpartitioned"},{"key":"u2","partition":"unpartitioned"}]);
    v["reference_keys"] = json!(["u1", "u2"]);
    add_metadata(&mut v, "batch", "group", json!(["A", "B"]));
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    spy.assert_unused();
    assert_eq!(
        result["receipt"]["reference_population"]["role"],
        "unpartitioned"
    );
    v["manifest"]
        .as_array_mut()
        .unwrap()
        .push(json!({"key":"t","partition":"test"}));
    refused(&v);
}

#[test]
fn global_fit_requires_a_separate_explicit_consent_and_receipt() {
    let mut v = wire("global_descriptive_transductive");
    let spy = Spy::default();
    v["explicit_transductive"] = json!(false);
    refused(&v);
    v["explicit_transductive"] = json!(true);
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    assert_eq!(
        spy.requests("pca")[0]["sample_ids"],
        json!(["a", "b", "c", "t1", "t2"])
    );
    assert_eq!(
        spy.requests("pca")[0]["matrix"],
        json!([[0.], [1.], [2.], [100.], [200.]])
    );
    assert_eq!(result["receipt"]["fit"], "transductive");
    assert_eq!(result["receipt"]["test_x_accessed"], true);
    assert_eq!(
        result["receipt"]["fit_keys"],
        json!(["a", "b", "c", "t1", "t2"])
    );
    let mut v = wire("train_structure");
    v["fit"] = json!("transductive");
    refused(&v);
    let mut v = wire("train_structure");
    v["explicit_transductive"] = json!(true);
    refused(&v);
}

#[test]
fn test_query_has_distinct_complete_train_references_and_never_refits_pca() {
    let v = wire("train_reference_test_query");
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    assert_eq!(spy.requests("pca").len(), 0);
    assert_eq!(spy.requests("hdbscan").len(), 0);
    let nn = spy.requests("nearest_neighbors");
    assert_eq!(nn.len(), 1);
    assert_eq!(nn[0]["query"], json!([[100.], [200.]]));
    assert_eq!(nn[0]["reference"], json!([[0.], [1.], [2.]]));
    assert_eq!(nn[0]["query_group_ids"], json!([3, 4]));
    assert_eq!(nn[0]["reference_group_ids"], json!([0, 1, 2]));
    assert_eq!(result["value"]["pca_support"]["status"], "unavailable");
    assert_eq!(result["receipt"]["fit_keys"], json!([]));
    let mut wrong = v.clone();
    wrong["query_keys"] = json!(["t2", "t1"]);
    refused(&wrong);
    let mut wrong = v.clone();
    wrong["fit"] = json!("train");
    refused(&wrong);
    let mut wrong = v.clone();
    wrong["x"]["matrix"][3] = json!([null]);
    refused(&wrong);
}

#[test]
fn declared_group_exclusions_keep_reference_and_query_roles_and_unknown_evidence() {
    let mut v = wire("train_reference_test_query");
    add_metadata(
        &mut v,
        "unit",
        "group",
        json!(["same", "b", "c", "same", "d"]),
    );
    v["exclusion_field"] = json!("unit");
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    let nn = spy.requests("nearest_neighbors");
    assert_eq!(nn[0]["reference_group_ids"], json!([0, 1, 2]));
    assert_eq!(nn[0]["query_group_ids"], json!([0, 3]));
    assert_eq!(
        result["receipt"]["fields_read"]["m"][0]["evidence"],
        "unknown"
    );
    let mut no_explicit = v.clone();
    no_explicit["exclusion_field"] = Value::Null;
    refused(&no_explicit);
    let mut derived = v.clone();
    derived["metadata"][0]["derived_from_target"] = json!(true);
    refused(&derived);
    let mut missing = v.clone();
    missing["metadata"][0]["values"][0] = Value::Null;
    refused(&missing);
    let mut extra = v.clone();
    add_metadata(&mut extra, "other", "factor", json!([1, 2, 3, 4, 5]));
    refused(&extra);
}

#[test]
fn provider_failure_preserves_other_evidence_and_explicit_status_reason_value() {
    let spy = Spy {
        fail_pca: true,
        ..Spy::default()
    };
    let result = scoped::analyze(&request(&wire("train_structure")), &spy).unwrap();
    let metrics = &result["value"]["structure"]["metrics"];
    assert_eq!(metrics["raw_neighbors"]["status"], "computed");
    assert_eq!(metrics["pca"]["status"], "error");
    assert_eq!(metrics["pca"]["reason"], "SCOPED_FIXTURE_PCA_FAILURE");
    assert!(metrics["pca"]["value"].is_null());
    assert_eq!(result["receipt"]["fit_attempted"], true);
    assert_eq!(result["receipt"]["fit_executed"], false);
    assert_eq!(result["receipt"]["fit_keys"], json!(["a", "b", "c"]));
    assert_eq!(spy.requests("hdbscan").len(), 0);
    let calls = result["receipt"]["provider_calls"].as_array().unwrap();
    assert_eq!(
        calls.iter().find(|v| v["operation"] == "pca").unwrap()["status"],
        "error"
    );
    let bad = Spy {
        fail_neighbors: true,
        ..Spy::default()
    };
    let result = scoped::analyze(&request(&wire("train_reference_test_query")), &bad).unwrap();
    assert_eq!(result["value"]["raw_neighbors"]["status"], "unsupported");
    assert!(result["value"]["raw_neighbors"]["value"].is_null());
    let malformed = Spy {
        malformed_neighbors: true,
        ..Spy::default()
    };
    let result =
        scoped::analyze(&request(&wire("train_reference_test_query")), &malformed).unwrap();
    assert_eq!(
        result["value"]["raw_neighbors"]["reason"],
        "INVALID_PROVIDER_RESPONSE"
    );
}

#[test]
fn exact_audit_calls_public_preflight_only_and_preserves_its_missing_and_zero_conventions() {
    let mut v = wire("integrity_audit");
    v["x"]["axis"] = json!([1000., 1100.]);
    v["x"]["matrix"] = json!([[0., null], [1., 2.], [3., 4.], [-0., null], [null, null]]);
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    spy.assert_unused();
    let metrics = result["value"]["metrics"].as_array().unwrap();
    assert!(metrics
        .iter()
        .all(|m| m["metric_id"].as_str().unwrap().starts_with("integrity.")));
    let cross = metrics
        .iter()
        .find(|m| m["metric_id"] == "integrity.cross_partition_exact_duplicate_pairs")
        .unwrap();
    assert_eq!(cross["status"], "computed");
    assert_eq!(cross["value"], 1);
    assert_eq!(
        cross["parameters"]["test_access"],
        "X_only_integrity_no_fit_no_Y"
    );
    assert_eq!(
        cross["parameters"]["normalization"],
        "f64_bits_with_negative_zero_normalized_and_masked_cell_sentinel"
    );
    let missing = metrics
        .iter()
        .find(|m| m["metric_id"] == "integrity.missing_cells")
        .unwrap();
    assert_eq!(missing["value"], 4);
    let calls = result["receipt"]["provider_calls"].as_array().unwrap();
    assert_eq!(calls.len(), 1);
    assert_eq!(calls[0]["numerical_provider"], "UnavailableMethodsProvider");
    assert_eq!(calls[0]["numerical_fit_possible"], false);
    assert_eq!(result["receipt"]["fit_keys"], json!([]));
}

#[test]
fn physical_identity_cross_partition_owner_validation_is_preserved_without_fallback_rerun() {
    let mut v = wire("integrity_audit");
    v["x"]["matrix"][3] = json!([0.]);
    add_metadata(
        &mut v,
        "specimen",
        "specimen",
        json!(["same", "b", "c", "same", "other"]),
    );
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    spy.assert_unused();
    assert_eq!(result["status"], "error");
    assert_eq!(result["reason"], "PREFLIGHT_INPUT_VALIDATION_FAILED");
    assert!(result["value"].is_null());
    let evidence = &result["receipt"]["noncomputed_evidence"];
    assert_eq!(evidence["validation"]["valid"], false);
    assert!(evidence["validation"]["issues"]
        .as_array()
        .unwrap()
        .iter()
        .any(|v| v["code"] == "IDENTITY_LEAKAGE"));
    assert!(evidence["metrics"].as_array().unwrap().is_empty());
    assert_eq!(
        evidence["declared_identities"]["columns"][0]["literal_shared_nonmissing_value_count"],
        1
    );
    assert_eq!(
        result["receipt"]["provider_calls"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
    // The same label declared merely as an observation identity must not be
    // promoted into an upstream physical identity or suppress an exact pair.
    v["metadata"][0]["role"] = json!("observation_id");
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    assert_eq!(result["status"], "computed");
    let cross = result["value"]["metrics"]
        .as_array()
        .unwrap()
        .iter()
        .find(|m| m["metric_id"] == "integrity.cross_partition_exact_duplicate_pairs")
        .unwrap();
    assert_eq!(cross["value"], 1);
}

#[test]
fn declared_identity_audit_needs_no_x_and_preserves_unknown_physical_status() {
    let mut v = wire("integrity_audit");
    v["diagnostic"] = json!("declared_identities");
    v["access"]["x"] = json!(false);
    v["x"] = Value::Null;
    add_metadata(
        &mut v,
        "reference",
        "reference_id",
        json!(["R", "S", null, "R", "T"]),
    );
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    spy.assert_unused();
    assert_eq!(
        result["value"]["columns"][0]["literal_shared_nonmissing_value_count"],
        1
    );
    assert_eq!(result["receipt"]["physical_independence"], "unverified");
    assert_eq!(result["receipt"]["provider_calls"], json!([]));
    assert_eq!(result["receipt"]["test_x_accessed"], false);
    let mut bad = v.clone();
    add_metadata(&mut bad, "age", "factor", json!([1, 2, 3, 4, 5]));
    refused(&bad);
}

#[test]
fn numeric_string_and_boolean_declared_identities_are_never_conflated() {
    let mut v = wire("integrity_audit");
    v["x"]["matrix"][3] = json!([0.]);
    add_metadata(
        &mut v,
        "specimen",
        "specimen",
        json!([1, true, "third", "1", "true"]),
    );
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    spy.assert_unused();
    assert_eq!(result["status"], "computed");
    assert_eq!(
        result["value"]["declared_identities"]["columns"][0]
            ["literal_shared_nonmissing_value_count"],
        0
    );
    let cross = result["value"]["metrics"]
        .as_array()
        .unwrap()
        .iter()
        .find(|m| m["metric_id"] == "integrity.cross_partition_exact_duplicate_pairs")
        .unwrap();
    assert_eq!(cross["value"], 1);
    assert_eq!(result["receipt"]["physical_id_encoding"],"type-preserving JSON scalar of declared specimen/physical_sample_id; not verified identity");
    v["metadata"][0]["values"][3] = json!(1);
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    spy.assert_unused();
    assert_eq!(result["status"], "error");
    let mut group = wire("train_reference_test_query");
    add_metadata(
        &mut group,
        "unit",
        "group",
        json!([1, true, "third", "1", "true"]),
    );
    group["exclusion_field"] = json!("unit");
    let result = scoped::analyze(&request(&group), &spy).unwrap();
    let nn = spy.requests("nearest_neighbors");
    assert_eq!(nn[0]["reference_group_ids"], json!([0, 1, 2]));
    assert_eq!(nn[0]["query_group_ids"], json!([3, 4]));
    assert_eq!(
        result["receipt"]["fields_read"]["m"][0]["evidence"],
        "unknown"
    );
}

#[test]
fn original_descending_axis_is_preserved_and_axis_or_budget_refusal_precedes_calls() {
    let mut v = wire("train_structure");
    v["x"]["axis"] = json!([1100., 1000.]);
    v["x"]["matrix"] = json!([[0., 1.], [1., 2.], [2., 3.]]);
    // Only validation is needed: the provider fixture is not a numerical
    // oracle for this two-band input.
    let r = request(&v);
    assert_eq!(r.x.unwrap().axis, vec![1100., 1000.]);
    v["x"]["axis"] = json!([1000., 1000.]);
    refused(&v);
    let mut large = wire("train_structure");
    large["x"]["axis"] = json!((0..400_000).collect::<Vec<_>>());
    large["x"]["matrix"] = json!(vec![vec![0.; 400_000]; 3]);
    refused(&large);
}

#[test]
fn selection_context_does_not_change_numerical_provider_requests_or_embedded_evidence() {
    let a = wire("train_structure");
    let mut b = a.clone();
    b["selection_context"] = json!("post_evaluation_explanation");
    let p = Spy::default();
    let q = Spy::default();
    let first = scoped::analyze(&request(&a), &p).unwrap();
    let second = scoped::analyze(&request(&b), &q).unwrap();
    assert_eq!(*p.calls.borrow(), *q.calls.borrow());
    assert_eq!(first["value"], second["value"]);
    assert_ne!(
        first["receipt"]["request_sha256"],
        second["receipt"]["request_sha256"]
    );
}

#[test]
fn per_kernel_neighbor_budget_preserves_complete_admissible_pca_population() {
    let mut v = wire("train_structure");
    let keys: Vec<_> = (0..1000).map(|i| format!("tr{i}")).collect();
    v["reference_keys"] = json!(keys);
    v["manifest"] = json!(keys
        .iter()
        .map(|key| json!({"key":key,"partition":"train"}))
        .chain([
            json!({"key":"held","partition":"test"}),
            json!({"key":"future","partition":"predict"})
        ])
        .collect::<Vec<_>>());
    v["x"]["row_keys"] = json!(keys);
    v["x"]["axis"] = json!((0..40).map(f64::from).collect::<Vec<_>>());
    v["x"]["matrix"] = json!(vec![vec![0.; 40]; 1000]);
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    let pca = spy.requests("pca");
    assert_eq!(pca.len(), 1);
    assert_eq!(pca[0]["sample_ids"], json!(keys));
    assert_eq!(pca[0]["matrix"], v["x"]["matrix"]);
    let metrics = &result["value"]["structure"]["metrics"];
    assert_eq!(
        metrics["raw_neighbors"]["reason"],
        "FULL_REFERENCE_NEIGHBOR_WORK_BUDGET_EXCEEDED"
    );
    assert_eq!(metrics["pca"]["status"], "computed");
    // The qualified existing protocol can still request score-space neighbors
    // and HDBSCAN at their own work budgets. Neither may drop any row.
    for nn in spy.requests("nearest_neighbors") {
        assert_eq!(nn["reference"].as_array().unwrap().len(), 1000);
        assert_eq!(nn["query"].as_array().unwrap().len(), 1000);
    }
    assert_eq!(
        spy.requests("hdbscan")[0]["matrix"]
            .as_array()
            .unwrap()
            .len(),
        1000
    );
    assert_eq!(result["receipt"]["fit_keys"], json!(keys));
}

#[test]
fn exact_hash_audit_does_not_charge_a_numerical_spectral_pair_kernel() {
    let mut v = wire("integrity_audit");
    let train: Vec<_> = (0..500).map(|i| format!("tr{i}")).collect();
    let test: Vec<_> = (0..500).map(|i| format!("te{i}")).collect();
    let rows: Vec<_> = train.iter().chain(&test).cloned().collect();
    v["reference_keys"] = json!(train);
    v["query_keys"] = json!(test);
    v["manifest"] = json!(train
        .iter()
        .map(|key| json!({"key":key,"partition":"train"}))
        .chain(test.iter().map(|key| json!({"key":key,"partition":"test"})))
        .collect::<Vec<_>>());
    v["x"]["row_keys"] = json!(rows);
    v["x"]["axis"] = json!((0..40).map(f64::from).collect::<Vec<_>>());
    v["x"]["matrix"] = json!(vec![vec![0.; 40]; 1000]);
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    spy.assert_unused();
    assert_eq!(result["status"], "computed");
    let cross = result["value"]["metrics"]
        .as_array()
        .unwrap()
        .iter()
        .find(|m| m["metric_id"] == "integrity.cross_partition_exact_duplicate_pairs")
        .unwrap();
    assert_eq!(cross["value"], 250_000);
    assert_eq!(
        result["receipt"]["provider_calls"][0]["matrices"]["matrix"]["shape"],
        json!([1000, 40])
    );
    assert_eq!(result["receipt"]["reference_keys"], json!(train));
    assert_eq!(result["receipt"]["query_keys"], json!(test));
}

#[test]
fn skipped_or_malformed_pca_never_claims_an_executed_fit() {
    let malformed = Spy {
        malformed_pca: true,
        ..Spy::default()
    };
    let result = scoped::analyze(&request(&wire("train_structure")), &malformed).unwrap();
    assert_eq!(result["receipt"]["fit_attempted"], true);
    assert_eq!(result["receipt"]["fit_executed"], false);
    assert_eq!(
        result["value"]["structure"]["metrics"]["pca"]["reason"],
        "INVALID_PROVIDER_RESPONSE"
    );
    let pca = result["receipt"]["provider_calls"]
        .as_array()
        .unwrap()
        .iter()
        .find(|v| v["operation"] == "pca")
        .unwrap();
    assert_eq!(pca["status"], "computed");
    let mut v = wire("train_structure");
    let keys: Vec<_> = (0..400).map(|i| format!("tr{i}")).collect();
    v["reference_keys"] = json!(keys);
    v["manifest"] = json!(keys
        .iter()
        .map(|key| json!({"key":key,"partition":"train"}))
        .chain([
            json!({"key":"held","partition":"test"}),
            json!({"key":"future","partition":"predict"})
        ])
        .collect::<Vec<_>>());
    v["x"]["row_keys"] = json!(keys);
    v["x"]["axis"] = json!((0..300).map(f64::from).collect::<Vec<_>>());
    v["x"]["matrix"] = json!(vec![vec![0.; 300]; 400]);
    let spy = Spy::default();
    let result = scoped::analyze(&request(&v), &spy).unwrap();
    spy.assert_unused();
    assert_eq!(
        result["value"]["structure"]["metrics"]["pca"]["reason"],
        "PCA_WORK_BUDGET_EXCEEDED"
    );
    assert_eq!(result["receipt"]["fit_attempted"], false);
    assert_eq!(result["receipt"]["fit_executed"], false);
    assert_eq!(result["receipt"]["fit_keys"], json!([]));
    assert_eq!(result["receipt"]["requested_fit_keys"], json!(keys));
    assert_eq!(
        result["receipt"]["fields_read"]["x"]["matrix"]["shape"],
        json!([400, 300])
    );
}
