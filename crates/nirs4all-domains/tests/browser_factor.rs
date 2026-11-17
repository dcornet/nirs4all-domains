//! Transport/access adversaries only. Fixed owner-shaped replies are not numerical qualification.
//! Real numerical expectations execute separately through published native/WASM Methods.
use nirs4all_domains::{browser, browser_factor as factor};
use nirs4all_preflight::*;
use serde_json::{json, Value};
use std::cell::RefCell;

const VERSION: &str = "1.3.13+abi.2.20.0";
struct Source;
impl MethodsProvider for Source {
    fn capabilities(&self) -> Vec<Capability> {
        vec![]
    }
    fn pca(&self, _: &PcaRequest) -> Result<PcaDiagnostics, ProviderError> {
        Ok(PcaDiagnostics {
            eigenvalues: vec![11.6],
            scores: vec![
                vec![-4.],
                vec![-3.],
                vec![-2.],
                vec![2.],
                vec![3.],
                vec![4.],
            ],
            full_moments: [11.6, 134.56],
            resolution: 1e-14,
            unresolved: vec![false],
            backend_version: VERSION.into(),
        })
    }
    fn repeatability(
        &self,
        _: &RepeatabilityRequest,
    ) -> Result<RepeatabilityDiagnostics, ProviderError> {
        unreachable!()
    }
    fn nearest_neighbors(
        &self,
        _: &NearestNeighborsRequest,
    ) -> Result<NearestNeighborsDiagnostics, ProviderError> {
        Err(ProviderError::unsupported("TRANSPORT_ONLY"))
    }
    fn summary(&self, _: &SummaryRequest) -> Result<SummaryDiagnostics, ProviderError> {
        unreachable!()
    }
    fn hdbscan(&self, _: &HdbscanRequest) -> Result<HdbscanDiagnostics, ProviderError> {
        Err(ProviderError::unsupported("TRANSPORT_ONLY"))
    }
}
#[derive(Default)]
struct Spy {
    calls: RefCell<Vec<(String, Value)>>,
    malformed: bool,
    fail_exact: bool,
}
impl factor::FactorProvider for Spy {
    fn version(&self) -> String {
        VERSION.into()
    }
    fn execute(&self, op: &str, r: &Value) -> Result<Value, ProviderError> {
        self.calls.borrow_mut().push((op.into(), r.clone()));
        if self.fail_exact && op.ends_with("_exact") {
            return Err(ProviderError::unsupported("EXACT_FIXTURE_UNAVAILABLE"));
        }
        let mut out = match op {
            "factor_descriptive" => {
                json!({"eta_squared":27./29.,"f_statistic":54.,"df1":1,"df2":4,"n_levels":2,"n_score_values":6,"log10_distinct_arrangements":null,"p_value":null,"n_at_least_observed":0,"n_permutations_executed":0})
            }
            "factor_exact" => {
                json!({"n_arrangements":20,"p_value":0.1,"minimum_p_value":0.1,"maximum_statistic":27./29.})
            }
            "holm_adjust" => json!({"adjusted":[0.1]}),
            _ => panic!("unexpected operation {op}"),
        };
        if self.malformed {
            out["p_value"] = json!(0.01);
            out["n_permutations_executed"] = json!(100);
        }
        out["backend_version"] = json!(VERSION);
        Ok(out)
    }
}
fn wire() -> Value {
    let keys = json!(["a", "b", "c", "d", "e", "f"]);
    let source=browser::parse(&json!({"schema_version":1,"dataset_id":"synthetic-factor-guards","source_id":"X","content_sha256":"a".repeat(64),"observation_ids":keys,"spectra":[[1.],[2.],[3.],[7.],[8.],[9.]],"axis":[1000.],"axis_unit":"nm"}).to_string()).unwrap();
    let mut report = browser::analyze(&source, &Source).unwrap();
    report.as_object_mut().unwrap().retain(|k, _| {
        [
            "schema_version",
            "protocol_version",
            "status",
            "scope",
            "metrics",
            "input_sha256",
            "evidence_sha256",
            "test_target_accessed",
            "raw_spectra_included",
        ]
        .contains(&k.as_str())
    });
    json!({"schema_version":1,"protocol_version":factor::PROTOCOL,
        "dataset":{"dataset_id":"synthetic-factor-guards","source_id":"X","content_sha256":"a".repeat(64),"content_version":"synthetic-v1"},
        "manifest":["a","b","c","d","e","f"].map(|key|json!({"key":key,"partition":"unpartitioned"})),"population":"unpartitioned",
        "pca":{"report":report,"row_keys":keys,"fit_receipt":null},
        "factors":[{"name":"batch","role":"factor","kind":"categorical","unit":null,"origin":"synthetic-by-construction","derived_from_target":false,"evidence":"verified","row_keys":keys,"values":["A","A","A","B","B","B"]}],
        "dependencies":[],"access":{"x":false,"y_fields":[],"m_fields":["batch"]},"representation":"raw","explicit_transductive":false,"components":"all_resolved","correlation_method":"pearson","inference":{"mode":"descriptive","plan":null},"parameters":{"preset":"f41_factor_pc_v1"}})
}
fn execute(w: &Value, spy: &Spy) -> Value {
    factor::analyze(&factor::parse(&w.to_string()).unwrap(), spy).unwrap()
}
fn qualify(w: &mut Value) {
    let mut unit = w["factors"][0].clone();
    unit["name"] = json!("specimen");
    unit["role"] = json!("specimen");
    unit["values"] = w["pca"]["row_keys"].clone();
    w["dependencies"] = json!([unit]);
    w["access"]["m_fields"] = json!(["batch", "specimen"]);
    w["inference"] = json!({"mode":"exact_if_qualified","plan":{"protocol_version":"domains.factor_exchangeability.v1","population":"unpartitioned","dataset_content_sha256":"a".repeat(64),"pca_evidence_sha256":w["pca"]["report"]["evidence_sha256"],"external_evidence":{"uri":"urn:synthetic-design","content_sha256":"b".repeat(64),"qualification":"externally_qualified","basis":"Independent synthetic fixture units; not a real-source qualification."},"unit_field":"specimen","unit_kind":"specimen","dependency_fields":["specimen"],"no_other_dependencies":true,"selection":"prospective","factor_ids":["batch"],"components":"all_resolved","missingness":"complete_units","null_model":"unrestricted_exchangeability_given_fitted_x"}});
}
#[test]
fn reordered_keys_bind_the_original_pc_scores_and_missingness_does_not_refit() {
    let mut w = wire();
    w["factors"][0]["row_keys"] = json!(["f", "e", "d", "c", "b", "a"]);
    w["factors"][0]["values"] = json!([null, "B", "B", "A", null, "A"]);
    let spy = Spy::default();
    let result = execute(&w, &spy);
    let calls = spy.calls.borrow();
    assert_eq!(calls.len(), 1);
    assert_eq!(calls[0].0, "factor_descriptive");
    assert_eq!(calls[0].1["scores"], json!([-4., -2., 2., 3.]));
    assert_eq!(calls[0].1["codes"], json!([0, 0, 1, 1]));
    assert_eq!(result["value"]["factors"][0]["n_used"], 4);
    assert_eq!(result["receipt"]["pca_refits"], 0);
    assert_eq!(result["receipt"]["fields_read"]["y"], json!([]));
    assert_eq!(result["receipt"]["fields_read"]["x"], false);
    assert_eq!(result, execute(&w, &Spy::default()));
}
#[test]
fn all_scope_and_target_adversaries_refuse_before_provider_access() {
    let cases: [fn(&mut Value); 10] = [
        |w| w["access"]["x"] = json!(true),
        |w| w["access"]["y_fields"] = json!(["target"]),
        |w| w["factors"][0]["derived_from_target"] = json!(true),
        |w| w["factors"][0]["row_keys"][0] = json!("test"),
        |w| w["factors"][0]["row_keys"][0] = json!("b"),
        |w| w["pca"]["report"]["evidence_sha256"] = json!("0".repeat(64)),
        |w| w["pca"]["report"]["scope"]["content_sha256"] = json!("f".repeat(64)),
        |w| w["manifest"][0]["partition"] = json!("test"),
        |w| w["population"] = json!("train"),
        |w| w["pca"]["report"]["Y_test"] = json!([1234]),
    ];
    for mutate in cases {
        let mut w = wire();
        mutate(&mut w);
        let spy = Spy::default();
        assert!(factor::parse(&w.to_string()).is_err());
        assert!(spy.calls.borrow().is_empty());
    }
    let mut unknown = wire();
    unknown["Y"] = json!([1234]);
    assert!(factor::parse(&unknown.to_string()).is_err());
}
#[test]
fn declared_independence_is_not_inferred_from_unique_groups_or_repeated_specimens() {
    let mut w = wire();
    qualify(&mut w);
    w["dependencies"][0]["values"] = json!(["s1", "s1", "s2", "s2", "s3", "s3"]);
    let spy = Spy::default();
    let r = execute(&w, &spy);
    assert_eq!(r["value"]["inference"]["level"], "unqualified");
    assert_eq!(
        r["value"]["analysis_unit"]["n_independent_units"],
        Value::Null
    );
    assert_eq!(
        r["value"]["dependency_audit"]["fields"][0]["declared_unique_unit_count"],
        3
    );
    assert_eq!(spy.calls.borrow().len(), 1);
    w["dependencies"][0]["values"] = w["pca"]["row_keys"].clone();
    w["inference"]["plan"]["external_evidence"]["qualification"] = json!("declared");
    assert_eq!(
        execute(&w, &Spy::default())["value"]["inference"]["level"],
        "unqualified"
    );
}
#[test]
fn qualified_exact_family_runs_owner_operations_and_preserves_failures_without_invented_p() {
    let mut w = wire();
    qualify(&mut w);
    let spy = Spy::default();
    let r = execute(&w, &spy);
    assert_eq!(r["value"]["inference"]["level"], "conditionally_admissible");
    assert_eq!(
        spy.calls
            .borrow()
            .iter()
            .map(|(s, _)| s.as_str())
            .collect::<Vec<_>>(),
        vec!["factor_descriptive", "factor_exact", "holm_adjust"]
    );
    let failed = execute(
        &w,
        &Spy {
            fail_exact: true,
            ..Default::default()
        },
    );
    assert_eq!(failed["value"]["inference"]["level"], "unqualified");
    assert_eq!(
        failed["value"]["factors"][0]["components"][0]["inference"]["value"],
        Value::Null
    );
    assert_eq!(
        failed["value"]["factors"][0]["components"][0]["exact_owner_evidence"]["status"],
        "unsupported"
    );
}
#[test]
fn undocumented_permutations_are_rejected_without_erasing_the_receipt() {
    let r = execute(
        &wire(),
        &Spy {
            malformed: true,
            ..Default::default()
        },
    );
    assert_eq!(
        r["value"]["factors"][0]["components"][0]["descriptive"]["status"],
        "error"
    );
    assert_eq!(
        r["receipt"]["provider_calls"][0]["operation"],
        "factor_descriptive"
    );
}
#[test]
fn literal_confounding_and_crossing_are_documentary_and_not_causal_conclusions() {
    let mut w = wire();
    let mut c = w["factors"][0].clone();
    c["name"] = json!("instrument");
    c["role"] = json!("instrument");
    c["values"] = json!(["i1", "i1", "i1", "i2", "i2", "i2"]);
    w["dependencies"] = json!([c]);
    w["access"]["m_fields"] = json!(["batch", "instrument"]);
    let r = execute(&w, &Spy::default());
    assert_eq!(
        r["value"]["dependency_audit"]["pairwise_context_tables"][0]["literal_total_confounding"],
        true
    );
    assert_eq!(
        r["value"]["dependency_audit"]["pairwise_context_tables"][0]["absent_combination_count"],
        2
    );
    w["dependencies"][0]["values"] = json!(["i1", "i2", "i1", "i2", "i1", "i2"]);
    let r = execute(&w, &Spy::default());
    assert_eq!(
        r["value"]["dependency_audit"]["pairwise_context_tables"][0]["literal_total_confounding"],
        false
    );
    assert_eq!(
        r["value"]["dependency_audit"]["pairwise_context_tables"][0]["absent_combination_count"],
        0
    );
}
