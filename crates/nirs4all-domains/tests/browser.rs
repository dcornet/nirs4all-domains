//! Analytical orchestration fixtures, not a second numerical backend.
use nirs4all_domains::browser::{self, BrowserRequest, PredictionIntent};
use nirs4all_preflight::*;
use std::cell::Cell;

struct Analytical {
    calls: Cell<usize>,
    self_neighbor: bool,
    failure: bool,
}
impl Analytical {
    fn tick(&self) {
        self.calls.set(self.calls.get() + 1);
    }
}
impl MethodsProvider for Analytical {
    fn capabilities(&self) -> Vec<Capability> {
        vec![]
    }
    fn pca(&self, r: &PcaRequest) -> Result<PcaDiagnostics, ProviderError> {
        self.tick();
        if self.failure {
            return Err(ProviderError::numerical("FIXTURE_PCA_FAILURE"));
        }
        assert_eq!(r.matrix, vec![vec![0.], vec![1.], vec![2.]]);
        assert_eq!(r.n_components, 1);
        Ok(PcaDiagnostics {
            eigenvalues: vec![1.],
            scores: vec![vec![-1.], vec![0.], vec![1.]],
            full_moments: [1., 1.],
            resolution: 1e-14,
            unresolved: vec![false],
            backend_version: "analytical-fixture".into(),
        })
    }
    fn repeatability(
        &self,
        _: &RepeatabilityRequest,
    ) -> Result<RepeatabilityDiagnostics, ProviderError> {
        panic!("X-only protocol must not request repeatability")
    }
    fn summary(&self, r: &SummaryRequest) -> Result<SummaryDiagnostics, ProviderError> {
        self.tick();
        assert_eq!(r.values, vec![1., 1., 1.]);
        Ok(SummaryDiagnostics {
            count: 3,
            min: 1.,
            max: 1.,
            mean: 1.,
            sample_sd: Some(0.),
            q25: 1.,
            median: 1.,
            q75: 1.,
            backend_version: "analytical-fixture".into(),
        })
    }
    fn nearest_neighbors(
        &self,
        r: &NearestNeighborsRequest,
    ) -> Result<NearestNeighborsDiagnostics, ProviderError> {
        self.tick();
        assert_eq!(r.query, r.reference);
        assert_eq!(r.query.len(), 3);
        assert_eq!(r.k, 2);
        assert_eq!(r.query_group_ids, r.reference_group_ids);
        Ok(NearestNeighborsDiagnostics {
            indices: if self.self_neighbor {
                vec![vec![0, 2], vec![0, 2], vec![1, 0]]
            } else {
                vec![vec![1, 2], vec![0, 2], vec![1, 0]]
            },
            distances: vec![
                vec![Some(1.), Some(2.)],
                vec![Some(1.), Some(1.)],
                vec![Some(1.), Some(2.)],
            ],
            backend_version: "analytical-fixture".into(),
        })
    }
    fn hdbscan(&self, _: &HdbscanRequest) -> Result<HdbscanDiagnostics, ProviderError> {
        panic!("three rows are below the frozen density setting")
    }
}
fn fixture() -> BrowserRequest {
    BrowserRequest {
        schema_version: 1,
        dataset_id: "analytical".into(),
        source_id: "x".into(),
        content_sha256: "a".repeat(64),
        observation_ids: vec!["a".into(), "b".into(), "c".into()],
        axis: vec![1000.],
        axis_unit: "nm".into(),
        spectra: vec![vec![0.], vec![1.], vec![2.]],
        group_ids: None,
        prediction_intent: PredictionIntent::Unknown,
    }
}
fn provider() -> Analytical {
    Analytical {
        calls: Cell::new(0),
        self_neighbor: false,
        failure: false,
    }
}

#[test]
fn analytical_full_population_and_pure_intent() {
    let p = provider();
    let r = browser::analyze(&fixture(), &p).unwrap();
    assert_eq!(r["metrics"]["pca"]["status"], "computed");
    assert!(
        (r["metrics"]["pca"]["value"]["eigenvalues"][0]
            .as_f64()
            .unwrap()
            - 1.)
            .abs()
            < 1e-12
    );
    assert_eq!(r["scope"]["n_observations"], 3);
    assert_eq!(r["metrics"]["raw_neighbors"]["value"]["n_reference"], 3);
    assert_eq!(
        r["metrics"]["density"]["reason"],
        "INSUFFICIENT_ROWS_FOR_FROZEN_DENSITY_SETTING"
    );
    assert_eq!(r["scope"]["identity_evidence"], "observation_identity_only");
    assert_eq!(r["raw_spectra_included"], false);
    assert!(r.get("spectra").is_none());
    let before = serde_json::to_string(&r["metrics"]).unwrap();
    let calls = p.calls.get();
    for intent in [
        PredictionIntent::Study,
        PredictionIntent::KnownAcquisitions,
        PredictionIntent::NewSpecimens,
        PredictionIntent::NewGroups,
        PredictionIntent::NewContext,
        PredictionIntent::Unknown,
    ] {
        let reading = browser::interpret(&r, intent).unwrap();
        assert_eq!(reading["execution"], "not_executed");
        assert_eq!(reading["evidence_sha256"], r["evidence_sha256"]);
        assert_eq!(
            reading["conditional_scenarios"].as_array().unwrap().len(),
            if intent == PredictionIntent::Unknown {
                3
            } else {
                0
            }
        );
    }
    assert_eq!(p.calls.get(), calls);
    assert_eq!(serde_json::to_string(&r["metrics"]).unwrap(), before);
    let mut changed = fixture();
    changed.prediction_intent = PredictionIntent::NewContext;
    let second = browser::analyze(&changed, &provider()).unwrap();
    assert_eq!(r["metrics"], second["metrics"]);
    assert_eq!(r["input_sha256"], second["input_sha256"]);
    // JavaScript spells integral floats as integers and normalizes signed zero.
    let transported = serde_json::to_string(&r)
        .unwrap()
        .replace("1.0", "1")
        .replace("0.0", "0");
    let transported = serde_json::from_str(&transported).unwrap();
    assert!(browser::interpret(&transported, PredictionIntent::Study).is_ok());
}
#[test]
fn reject_leakage_identity_axis_and_nonfinite_inputs_before_provider() {
    let r = fixture();
    let mut bad = r.clone();
    bad.observation_ids[1] = "a".into();
    assert!(browser::validate(&bad).is_err());
    let provider = provider();
    assert!(browser::analyze(&bad, &provider).is_err());
    assert_eq!(provider.calls.get(), 0);
    bad = r.clone();
    bad.spectra[0][0] = f64::NAN;
    assert!(browser::validate(&bad).is_err());
    bad = r.clone();
    bad.group_ids = Some(vec!["shared".into()]);
    assert!(browser::validate(&bad).is_err());
    bad = r.clone();
    bad.axis = vec![1., 1.];
    bad.spectra = vec![vec![1., 2.]; 3];
    assert!(browser::validate(&bad).is_err());
    bad.axis = vec![2., 1.];
    assert!(browser::validate(&bad).is_ok());
    let mut value = serde_json::to_value(&r).unwrap();
    value["y"] = serde_json::json!([1, 2, 3]);
    assert!(browser::parse(&value.to_string()).is_err());
    value.as_object_mut().unwrap().remove("y");
    value["identity_evidence"] = "verified_physical_identity".into();
    assert!(browser::parse(&value.to_string()).is_err());
}
#[test]
fn malformed_neighbors_and_provider_failure_remain_null() {
    let mut p = provider();
    p.self_neighbor = true;
    let r = browser::analyze(&fixture(), &p).unwrap();
    assert_eq!(r["metrics"]["raw_neighbors"]["status"], "error");
    assert!(r["metrics"]["raw_neighbors"]["value"].is_null());
    let mut p = provider();
    p.failure = true;
    let r = browser::analyze(&fixture(), &p).unwrap();
    assert_eq!(r["metrics"]["pca"]["reason"], "FIXTURE_PCA_FAILURE");
    assert_eq!(r["metrics"]["pca"]["status"], "error");
    assert!(r["metrics"]["pca"]["value"].is_null());
}
#[test]
fn shared_groups_and_forged_evidence_are_rejected() {
    let mut input = fixture();
    input.group_ids = Some(vec!["shared".into(), "shared".into(), "other".into()]);
    let r = browser::analyze(&input, &provider()).unwrap();
    assert_eq!(
        r["metrics"]["raw_neighbors"]["reason"],
        "INVALID_PROVIDER_RESPONSE"
    );
    let mut forged = browser::analyze(&fixture(), &provider()).unwrap();
    forged["metrics"]["pca"]["value"]["scores"][0][0] = 100.into();
    assert_eq!(
        browser::interpret(&forged, PredictionIntent::Study).unwrap_err(),
        "BROWSER_EVIDENCE_HASH_MISMATCH"
    );
}
