//! Train-fitted transport and interpretation. All numerical work belongs to Methods.
use crate::{browser, browser_scoped as scoped, hash};
use nirs4all_preflight::ProviderError;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

pub const PROTOCOL: &str = "domains.browser_train_fitted_support.v1";
pub const RESULT_PROTOCOL: &str = "domains.browser_train_fitted_support_result.v1";
pub const STATE_BYTES: usize = 2 * 1024 * 1024;
pub trait SupportProvider {
    fn version(&self) -> String;
    fn execute(&self, operation: &str, request: &Value) -> Result<Value, ProviderError>;
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Parameters {
    pub n_components: i64,
    pub monitoring: bool,
    pub max_components: i64,
    pub n_folds: i64,
    pub alpha: f64,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LimitPlan {
    pub protocol_version: String,
    pub dataset_content_sha256: String,
    pub reference_keys: Vec<String>,
    pub max_components: i64,
    pub n_folds: i64,
    pub alpha: f64,
    pub independent_unit_ids: Vec<String>,
    pub indivisible_dependency_fields: Vec<String>,
    pub source: String,
    pub prospective: bool,
    pub row_index_modulo_folds_authorized: bool,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SupportRequest {
    pub schema_version: u32,
    pub protocol_version: String,
    pub fit: String,
    pub scope: scoped::ScopedRequest,
    pub parameters: Parameters,
    pub dependencies: Vec<scoped::ScopedMetadata>,
    pub dependency_fields: Vec<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub external_limit_plan: Option<LimitPlan>,
}
fn required_nullable<'de, D: serde::Deserializer<'de>, T: Deserialize<'de>>(
    d: D,
) -> Result<Option<T>, D::Error> {
    Option::<T>::deserialize(d)
}
fn fingerprint(v: &impl Serialize) -> String {
    hash(&serde_json::to_vec(v).expect("validated serializable protocol evidence"))
}
fn unavailable(reason: impl Into<String>) -> Value {
    json!({"status":"unavailable","reason":reason.into(),"value":null})
}
fn computed(value: Value) -> Value {
    json!({"status":"computed","reason":null,"value":value})
}
pub fn parse(text: &str) -> Result<SupportRequest, String> {
    if text.len() > browser::MAX_JSON_BYTES {
        return Err("JSON_MEMORY_BUDGET_EXCEEDED".into());
    }
    let request = serde_json::from_str(text).map_err(|_| "INVALID_TRAIN_SUPPORT_INPUT")?;
    validate(&request)?;
    Ok(request)
}
fn physical(role: &str) -> bool {
    matches!(
        role,
        "specimen"
            | "physical_sample_id"
            | "reference"
            | "reference_id"
            | "reference_group_id"
            | "repetition"
    )
}
pub fn validate(r: &SupportRequest) -> Result<(), String> {
    if r.schema_version != 1 || r.protocol_version != PROTOCOL || r.fit != "train" {
        return Err("TRAIN_ONLY_SUPPORT_PROTOCOL_REQUIRED".into());
    }
    scoped::validate_spectral_access(&r.scope)?;
    if r.scope.operation != scoped::ScopedOperation::TrainReferenceTestQuery {
        return Err("TRAIN_REFERENCE_TEST_QUERY_ACCESS_REQUIRED".into());
    }
    let names: Vec<_> = r.dependencies.iter().map(|d| d.name.clone()).collect();
    let keys: Vec<_> = r
        .scope
        .reference_keys
        .iter()
        .chain(&r.scope.query_keys)
        .cloned()
        .collect();
    if names != r.dependency_fields
        || names.iter().collect::<BTreeSet<_>>().len() != names.len()
        || names.len() > 24
    {
        return Err("DEPENDENCY_GRANT_BUDGET_OR_MAPPING_INVALID".into());
    }
    for d in &r.dependencies {
        if d.row_keys != keys
            || d.values.len() != keys.len()
            || d.name.trim().is_empty()
            || d.origin.trim().is_empty()
            || d.derived_from_target == Some(true)
            || !matches!(
                d.role.as_str(),
                "specimen"
                    | "physical_sample_id"
                    | "reference"
                    | "reference_id"
                    | "reference_group_id"
                    | "repetition"
                    | "group"
                    | "group_id"
                    | "instrument"
                    | "campaign"
            )
            || d.values.iter().any(|v| {
                !(v.is_null()
                    || v.is_string()
                    || v.is_boolean()
                    || v.as_f64()
                        .is_some_and(|n| n.is_finite() && n.abs() <= 9_007_199_254_740_991.0))
            })
        {
            return Err("DEPENDENCY_IDENTITY_PAYLOAD_INELIGIBLE".into());
        }
    }
    if serde_json::to_vec(r)
        .map_err(|_| "INPUT_SERIALIZATION_FAILED")?
        .len()
        > browser::MAX_JSON_BYTES
    {
        return Err("JSON_MEMORY_BUDGET_EXCEEDED".into());
    }
    Ok(())
}

struct Calls<'a, P> {
    provider: &'a P,
    records: Vec<Value>,
}
impl<P: SupportProvider> Calls<'_, P> {
    fn invoke(
        &mut self,
        operation: &str,
        payload: Value,
        row_keys: &[String],
    ) -> Result<Value, String> {
        let result = self.provider.execute(operation, &payload);
        self.records.push(
            json!({"operation":operation,"row_keys":row_keys,"request_sha256":fingerprint(&payload),
            "provider_success":result.is_ok()}),
        );
        let value = result.map_err(|e| e.reason)?;
        if value["backend_version"].as_str() != Some(self.provider.version().as_str()) {
            return Err("SUPPORT_PROVIDER_VERSION_MISMATCH".into());
        }
        Ok(value)
    }
}
fn bytes(v: &Value) -> Result<Vec<u8>, String> {
    let bytes: Vec<u8> = serde_json::from_value(v["state_bytes"].clone())
        .map_err(|_| "INVALID_FITTED_STATE_BYTES")?;
    if bytes.is_empty() || bytes.len() > STATE_BYTES {
        return Err("FITTED_STATE_BYTE_BUDGET_EXCEEDED".into());
    }
    Ok(bytes)
}
fn scores(v: &Value, n: usize, width: Option<usize>) -> Result<Vec<Vec<f64>>, String> {
    let rows: Vec<Vec<f64>> =
        serde_json::from_value(v["scores"].clone()).map_err(|_| "INVALID_OWNER_SCORE_MATRIX")?;
    let k = rows.first().map_or(0, Vec::len);
    if rows.len() != n
        || k == 0
        || k > 20
        || width.is_some_and(|w| w != k)
        || rows
            .iter()
            .any(|r| r.len() != k || r.iter().any(|v| !v.is_finite()))
    {
        return Err("INVALID_OWNER_SCORE_MATRIX".into());
    }
    Ok(rows)
}
fn estimate(n: usize, p: usize, multiplier: usize) -> bool {
    n.checked_mul(p)
        .and_then(|v| v.checked_mul(n.min(p)))
        .and_then(|v| v.checked_mul(multiplier))
        .is_some_and(|v| v <= browser::MAX_PRODUCTS)
}
fn projection<P: SupportProvider>(
    r: &SupportRequest,
    train: &[Vec<f64>],
    test: &[Vec<f64>],
    calls: &mut Calls<P>,
) -> Value {
    let k = r.parameters.n_components;
    if train.len() < 2 {
        return unavailable("TRAIN_REFERENCE_TOO_SMALL");
    }
    if !(1..=20).contains(&k) {
        return unavailable("PROJECTION_COMPONENT_PARAMETER_INVALID");
    }
    let p = train[0].len();
    if !estimate(train.len(), p, 1)
        || p.checked_mul((k as usize) + 1)
            .and_then(|v| v.checked_mul(8))
            .is_none_or(|v| v > STATE_BYTES)
        || test
            .len()
            .checked_mul(p)
            .and_then(|v| v.checked_mul(k as usize))
            .is_none_or(|v| v > browser::MAX_PRODUCTS)
    {
        return unavailable("PROJECTION_NUMERICAL_BUDGET_EXCEEDED");
    }
    let result = (|| -> Result<Value, String> {
        let fit = calls.invoke(
            "pca_fit",
            json!({"matrix":train,"n_components":k}),
            &r.scope.reference_keys,
        )?;
        let state = bytes(&fit)?;
        let training = calls.invoke(
            "pca_transform",
            json!({"matrix":train}),
            &r.scope.reference_keys,
        )?;
        if bytes(&training)? != state {
            return Err("TRAIN_TRANSFORM_CHANGED_FITTED_STATE".into());
        }
        let train_scores = scores(&training, train.len(), None)?;
        let width = train_scores[0].len();
        if width > (k as usize).min(p).min(train.len()) {
            return Err("INVALID_OWNER_COMPONENT_COUNT".into());
        }
        let mut summaries = Vec::new();
        let mut display = Vec::new();
        for j in 0..width {
            let values: Vec<_> = train_scores.iter().map(|row| row[j]).collect();
            let summary =
                calls.invoke("summary", json!({"values":values}), &r.scope.reference_keys);
            let metric = match summary {
                Ok(v)
                    if v["count"].as_f64() == Some(train.len() as f64)
                        && v["min"].as_f64().is_some()
                        && v["max"].as_f64().is_some()
                        && v.as_object().is_some_and(|o| {
                            o.keys().all(|k| {
                                matches!(
                                    k.as_str(),
                                    "count"
                                        | "min"
                                        | "max"
                                        | "mean"
                                        | "sample_sd"
                                        | "q25"
                                        | "median"
                                        | "q75"
                                        | "backend_version"
                                )
                            })
                        }) =>
                {
                    if v["min"] != v["max"] && display.len() < 2 {
                        display.push(j);
                    }
                    computed(v)
                }
                Ok(_) => unavailable("INVALID_OWNER_SCORE_SUMMARY"),
                Err(e) => unavailable(e),
            };
            summaries.push(json!({"component":j,"summary":metric}));
        }
        let projected =
            calls.invoke("pca_transform", json!({"matrix":test}), &r.scope.query_keys)?;
        if bytes(&projected)? != state {
            return Err("TEST_TRANSFORM_CHANGED_FITTED_STATE".into());
        }
        let test_scores = scores(&projected, test.len(), Some(width))?;
        Ok(
            json!({"train_scores":train_scores,"test_scores":test_scores,"components":width,"display_components":display,
            "component_summaries":summaries,"fit_state_sha256":hash(&state),"fitted_state_unchanged":true,
            "fit_identity_sha256":fingerprint(&json!({"dataset":r.scope.dataset,"axis":r.scope.x.as_ref().unwrap().axis,
                "axis_unit":r.scope.x.as_ref().unwrap().axis_unit,"fit_keys":r.scope.reference_keys,"train":train,
                "n_components":k,"provider":calls.provider.version()})),
            "reference_variance":unavailable("FLEXIBLE_PCA_PUBLIC_STATE_HAS_NO_EIGENVALUES"),
            "numerical_rank":unavailable("FLEXIBLE_PCA_PUBLIC_STATE_HAS_NO_RANK_RESOLUTION"),
            "basis":"Methods FlexiblePCA centered, unscaled; independent from F4.1 preflightPca and PCA monitor"}),
        )
    })();
    let cleanup = calls.invoke("pca_destroy", json!({}), &[]);
    match (result, cleanup) {
        (Ok(v), Ok(_)) => computed(v),
        (Err(e), _) => unavailable(e),
        (_, Err(e)) => unavailable(format!("FITTED_STATE_CLEANUP_FAILED:{e}")),
    }
}
fn monitoring<P: SupportProvider>(
    r: &SupportRequest,
    train: &[Vec<f64>],
    test: &[Vec<f64>],
    calls: &mut Calls<P>,
) -> Value {
    let a = &r.parameters;
    if !a.monitoring {
        return json!({"status":"not_requested","reason":"MONITORING_NOT_REQUESTED","value":null});
    }
    if !a.alpha.is_finite()
        || a.alpha <= 0.0
        || a.alpha >= 1.0
        || a.n_folds < 2
        || a.n_folds as usize > train.len()
        || a.max_components < 1
        || a.max_components > 20
    {
        return unavailable("MONITORING_PARAMETERS_INVALID");
    }
    let folds = a.n_folds as usize;
    let minimum_fold_train = train.len() - train.len().div_ceil(folds);
    if train.len() < 3
        || a.max_components as usize >= minimum_fold_train
        || a.max_components as usize > train[0].len()
    {
        return unavailable("METHODS_MONITOR_FOLD_TRAIN_RANK_REQUIREMENT");
    }
    if !estimate(train.len(), train[0].len(), folds + 1) {
        return unavailable("MONITORING_NUMERICAL_BUDGET_EXCEEDED");
    }
    let value = calls.invoke(
        "pca_monitor",
        json!({"reference":train,"monitored":test,
        "max_components":a.max_components,"n_folds":a.n_folds,"alpha":a.alpha}),
        &r.scope.query_keys,
    );
    match value {
        Err(e) => unavailable(e),
        Ok(mut v) => {
            let valid_array = |key: &str, n: usize| {
                v[key].as_array().is_some_and(|a| {
                    a.len() == n
                        && a.iter()
                            .all(|x| x.is_null() || x.as_f64().is_some_and(f64::is_finite))
                })
            };
            let scalar_fields = [
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
            ];
            let array_fields = [
                "eigenvalues",
                "reference_t2",
                "reference_q",
                "monitored_t2",
                "monitored_q",
            ];
            let count_fields = [
                "effective_components",
                "n_beyond_t2",
                "n_beyond_q",
                "n_beyond_either",
                "n_near_t2",
                "n_near_q",
                "n_near_either",
            ];
            if !valid_array("eigenvalues", a.max_components as usize)
                || !valid_array("reference_t2", train.len())
                || !valid_array("reference_q", train.len())
                || !valid_array("monitored_t2", test.len())
                || !valid_array("monitored_q", test.len())
                || scalar_fields.iter().any(|key| {
                    v.get(key)
                        .is_none_or(|x| !(x.is_null() || x.as_f64().is_some_and(f64::is_finite)))
                })
                || v.as_object().is_none_or(|o| {
                    o.keys().any(|k| {
                        k != "backend_version"
                            && !scalar_fields.contains(&k.as_str())
                            && !array_fields.contains(&k.as_str())
                            && !count_fields.contains(&k.as_str())
                    })
                })
                || v["effective_components"]
                    .as_u64()
                    .is_none_or(|n| n > a.max_components as u64)
                || [
                    "n_beyond_t2",
                    "n_beyond_q",
                    "n_beyond_either",
                    "n_near_t2",
                    "n_near_q",
                    "n_near_either",
                ]
                .iter()
                .any(|k| v[k].as_u64().is_none_or(|n| n > test.len() as u64))
            {
                return unavailable("INVALID_METHODS_MONITOR_RESPONSE");
            }
            let undefined: BTreeMap<_, _> = v
                .as_object()
                .unwrap()
                .iter()
                .filter(|(_, v)| v.is_null())
                .map(|(k, _)| (k.clone(), "METHODS_NUMERICALLY_UNDEFINED"))
                .collect();
            v["undefined_field_reasons"] = json!(undefined);
            v["undefined_array_entries"] = json!(array_fields.iter().map(|key| (*key,
                v[key].as_array().unwrap().iter().enumerate().filter(|(_,x)| x.is_null())
                    .map(|(index,_)| json!({"index":index,"reason":"NOT_RETAINED_OR_NUMERICALLY_UNDEFINED_BY_METHODS"})).collect::<Vec<_>>()))
                .collect::<BTreeMap<_,_>>());
            v["reference_protocol"] = json!("Methods statsPcaMonitor; out-of-fold row-index-modulo reference, separate full-reference PCA for query");
            v["descriptive_fractions"] = json!([("t2","n_beyond_t2"),("q","n_beyond_q"),("either","n_beyond_either")].into_iter()
                .map(|(name,key)| (name,json!({"numerator":v[key],"denominator":test.len(),
                    "value":v[key].as_u64().unwrap() as f64 / test.len() as f64,
                    "unit":"query acquisitions; descriptive threshold exceedance, not predictive failure or independent-unit probability"})))
                .collect::<BTreeMap<_,_>>());
            computed(v)
        }
    }
}

fn dependencies(r: &SupportRequest) -> (Value, Value) {
    let n = r.scope.reference_keys.len();
    let folds = usize::try_from(r.parameters.n_folds).unwrap_or(0);
    let mut records = Vec::new();
    let mut contradicted = false;
    for d in &r.dependencies {
        let mut units: BTreeMap<String, (BTreeSet<usize>, usize, bool)> = BTreeMap::new();
        let mut missing = 0;
        for (i, v) in d.values.iter().enumerate() {
            if v.is_null() || v.as_str().is_some_and(|s| s.trim().is_empty()) {
                missing += 1;
                continue;
            }
            let entry = units.entry(v.to_string()).or_default();
            if i < n {
                entry.1 += 1;
                if folds > 0 {
                    entry.0.insert(i % folds);
                }
            } else {
                entry.2 = true;
            }
        }
        let repeated = units.values().filter(|v| v.1 > 1).count();
        let crossing = units.values().filter(|v| v.0.len() > 1).count();
        let shared = units.values().filter(|v| v.1 > 0 && v.2).count();
        let indivisible = physical(&d.role)
            || r.external_limit_plan
                .as_ref()
                .is_some_and(|p| p.indivisible_dependency_fields.contains(&d.name));
        if indivisible && (repeated > 0 || shared > 0) {
            contradicted = true;
        }
        records.push(json!({"field":d.name,"role":d.role,"evidence":d.evidence,"origin":d.origin,"missing":missing,
            "distinct_declared_values":units.len(),"train_repeated_identities":repeated,"train_cross_fold_identities":crossing,
            "train_test_shared_identities":shared,"treated_as_declared_indivisible":indivisible}));
    }
    let mut reasons = Vec::new();
    let mut qualified = false;
    let mut source = None;
    if let Some(p) = &r.external_limit_plan {
        let a = &r.parameters;
        let valid = p.protocol_version == "domains.monitor_indexed_folds_design.v1"
            && p.dataset_content_sha256 == r.scope.dataset.content_sha256
            && p.reference_keys == r.scope.reference_keys
            && p.max_components == a.max_components
            && p.n_folds == a.n_folds
            && p.alpha == a.alpha
            && p.independent_unit_ids.len() == n
            && p.independent_unit_ids.iter().all(|s| !s.trim().is_empty())
            && p.independent_unit_ids.iter().collect::<BTreeSet<_>>().len() == n
            && p.indivisible_dependency_fields
                .iter()
                .all(|s| r.dependency_fields.contains(s))
            && !p.source.trim().is_empty()
            && p.prospective
            && p.row_index_modulo_folds_authorized;
        if valid {
            qualified = true;
            source = Some(p.source.clone());
        } else {
            reasons.push("EXTERNAL_INDEXED_FOLD_PLAN_BINDING_OR_UNITS_UNQUALIFIED");
        }
    } else {
        reasons.push("NO_EXTERNAL_EVIDENCE_OF_INDEPENDENT_REFERENCE_UNITS");
    }
    if contradicted {
        qualified = false;
        reasons.push(
            "DECLARED_PHYSICAL_REFERENCE_OR_INDIVISIBLE_DEPENDENCIES_CONTRADICT_ROW_INDEPENDENCE",
        );
    }
    let status = if qualified {
        "conditional_external"
    } else if contradicted || r.external_limit_plan.is_some() {
        "not_qualified"
    } else {
        "unknown"
    };
    (
        json!({"fields":records,"physical_independence_inferred_from_unique_ids":false,
        "context_categories_alone_require_no_group_split":true}),
        json!({"status":status,"reasons":reasons,"source":source,"fold_scheme":"row_index_modulo_n_folds",
        "independent_units_certified":false,"interpretation":"Empirical indexed-fold reference values; conditional on external assumptions, never a prediction-failure probability"}),
    )
}
pub fn analyze(r: &SupportRequest, provider: &impl SupportProvider) -> Result<Value, String> {
    validate(r)?;
    if provider.version() != "1.5.0+abi.2.24.0" {
        return Err("PINNED_METHODS_1_5_0_ABI_2_24_REQUIRED".into());
    }
    let x = r.scope.x.as_ref().unwrap();
    let n = r.scope.reference_keys.len();
    let matrix: Vec<Vec<f64>> = x
        .matrix
        .iter()
        .map(|row| row.iter().map(|v| v.unwrap()).collect())
        .collect();
    let (train, test) = matrix.split_at(n);
    let mut calls = Calls {
        provider,
        records: Vec::new(),
    };
    let projection = projection(r, train, test, &mut calls);
    let monitoring = monitoring(r, train, test, &mut calls);
    let (dependence, mut qualification) = dependencies(r);
    let p = projection["status"] == "computed";
    let m = monitoring["status"] == "computed";
    if m && monitoring["value"]["effective_components"] == 0 {
        qualification["status"] = json!("not_qualified");
        qualification["reasons"]
            .as_array_mut()
            .unwrap()
            .push(json!("MONITORING_REFERENCE_HAS_NO_RESOLVED_COMPONENT"));
    }
    if !m {
        if qualification["status"] == "conditional_external" {
            qualification["status"] = json!("not_qualified");
        }
        qualification["reasons"]
            .as_array_mut()
            .unwrap()
            .push(json!("MONITORING_VALUES_AND_LIMITS_NOT_AVAILABLE"));
    }
    let mut supported_claims = Vec::new();
    if p {
        supported_claims.push("Position in this train-fitted FlexiblePCA coordinate system");
    }
    if m {
        supported_claims
            .push("Separate descriptive indexed-fold reference and monitored T2/Q values");
    }
    let status = if p && (m || !r.parameters.monitoring) {
        "computed"
    } else if p || m {
        "partial"
    } else {
        "unavailable"
    };
    let receipt = json!({"dataset":r.scope.dataset,"fit_keys":r.scope.reference_keys,"query_keys":r.scope.query_keys,
        "fit_population":"train","query_population":"test","representation":"raw","axis_sha256":fingerprint(&json!([x.axis,x.axis_unit])),
        "parameters":r.parameters,"train_spectra_sha256":fingerprint(&train),"query_spectra_sha256":fingerprint(&test),
        "source_request_sha256":fingerprint(r),"provider":provider.version(),"provider_calls":calls.records,
        "x_test_accessed":true,"y_train_accessed":false,"y_test_accessed":false,"x_predict_accessed":false,
        "f41_pca_reused":false,"monitoring_and_projection_same_fitted_object":false});
    let mut result = json!({"protocol_version":RESULT_PROTOCOL,"status":status,
        "reason":if status=="computed" {None}else{Some("READ_INDIVIDUAL_OPERATION_STATUSES")},
        "projection":projection,"monitoring":monitoring,"limit_qualification":qualification,"dependence":dependence,"receipt":receipt,
        "supported_claims":supported_claims,
        "limitations":["No predictive validation, leakage probability or non-calibrability conclusion follows from distances or limit crossings",
            "Physical/reference independence and external design authenticity are not certified",
            "FlexiblePCA, historical preflightPca and statsPcaMonitor have separate fitted bases and provenance",
            "Unknown and dependent units prevent an independently calibrated coverage claim",
            "Raw neighbors remain an independent F4.0 operation; no universal support threshold is introduced",
            "FlexiblePCA publishes no eigenvalues or numerical-rank resolution; tiny nonzero score dispersion may be numerical",
            "No raw X/Y, serialized model state or observation-level M values are exported"]});
    result["evidence_sha256"] = json!(fingerprint(&result));
    Ok(result)
}
