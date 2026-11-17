//! F4.1 value-projected factor–PC protocol. Methods owns all numerical statistics.
use crate::browser;
use crate::browser_scoped::{Access, Dataset, Evidence, ManifestRow, MetadataKind, PartitionRole};
use crate::hash;
use nirs4all_preflight::{ProviderError, ProviderErrorKind};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::cell::RefCell;
use std::collections::{BTreeMap, BTreeSet};

pub const PROTOCOL: &str = "domains.browser_factor_association.v1";
pub const RESULT_PROTOCOL: &str = "domains.browser_factor_association_result.v1";
pub const EXACT_MAX: usize = 40_320;
const METHODS_VERSION: &str = "1.3.13+abi.2.20.0";

/// Transport seam only; no PCA/model method exists on this provider.
pub trait FactorProvider {
    fn version(&self) -> String;
    fn execute(&self, operation: &str, request: &Value) -> Result<Value, ProviderError>;
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Population {
    Train,
    Unpartitioned,
    GlobalTransductive,
}
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Correlation {
    Pearson,
    Spearman,
}
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum InferenceMode {
    Descriptive,
    ExactIfQualified,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FactorColumn {
    pub name: String,
    pub role: String,
    pub kind: MetadataKind,
    #[serde(deserialize_with = "nullable")]
    pub unit: Option<String>,
    pub origin: String,
    #[serde(deserialize_with = "nullable")]
    pub derived_from_target: Option<bool>,
    pub evidence: Evidence,
    pub row_keys: Vec<String>,
    pub values: Vec<Value>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PcaSource {
    /// Compact original browser report: scope/metrics and their original hashes.
    pub report: Value,
    pub row_keys: Vec<String>,
    #[serde(deserialize_with = "nullable")]
    pub fit_receipt: Option<Value>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExternalEvidence {
    pub uri: String,
    pub content_sha256: String,
    pub qualification: String,
    pub basis: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct InferencePlan {
    pub protocol_version: String,
    pub population: Population,
    pub dataset_content_sha256: String,
    pub pca_evidence_sha256: String,
    pub external_evidence: ExternalEvidence,
    pub unit_field: String,
    pub unit_kind: String,
    pub dependency_fields: Vec<String>,
    pub no_other_dependencies: bool,
    pub selection: String,
    pub factor_ids: Vec<String>,
    pub components: String,
    pub missingness: String,
    pub null_model: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Inference {
    pub mode: InferenceMode,
    #[serde(deserialize_with = "nullable")]
    pub plan: Option<InferencePlan>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Parameters {
    pub preset: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FactorRequest {
    pub schema_version: u32,
    pub protocol_version: String,
    pub dataset: Dataset,
    pub manifest: Vec<ManifestRow>,
    pub population: Population,
    pub pca: PcaSource,
    pub factors: Vec<FactorColumn>,
    pub dependencies: Vec<FactorColumn>,
    pub access: Access,
    pub representation: String,
    pub explicit_transductive: bool,
    pub components: String,
    pub correlation_method: Correlation,
    pub inference: Inference,
    pub parameters: Parameters,
}
fn nullable<'de, D: serde::Deserializer<'de>, T: Deserialize<'de>>(
    d: D,
) -> Result<Option<T>, D::Error> {
    Option::<T>::deserialize(d)
}
fn digest(v: &impl Serialize) -> String {
    hash(&serde_json::to_vec(v).expect("serializable finite protocol"))
}
fn nonempty(v: &str) -> bool {
    !v.trim().is_empty()
}
fn sha(v: &str) -> bool {
    v.len() == 64 && v.bytes().all(|c| c.is_ascii_hexdigit())
}
fn count(v: &Value) -> Option<usize> {
    v.as_f64()
        .filter(|n| n.is_finite() && *n >= 0. && n.fract() == 0. && *n <= 1_000_000.)
        .map(|n| n as usize)
}
fn slot(value: Value) -> Value {
    json!({"status":"computed","reason":null,"value":value})
}
fn unavailable(reason: &str) -> Value {
    json!({"status":"unavailable","reason":reason,"value":null})
}
fn failed(e: ProviderError) -> Value {
    json!({"status":if e.kind==ProviderErrorKind::Unsupported{"unsupported"}else{"error"},"reason":e.reason,"value":null})
}
fn scalar(v: &Value) -> bool {
    v.is_null() || v.is_string() || v.is_boolean() || v.as_f64().is_some_and(f64::is_finite)
}
fn scalar_key(v: &Value) -> String {
    if let Some(n) = v.as_f64() {
        format!("number:{:016x}", if n == 0. { 0 } else { n.to_bits() })
    } else {
        v.to_string()
    }
}
fn factor_role(role: &str) -> bool {
    matches!(role, "factor" | "group" | "instrument" | "campaign")
}
fn dependency_role(role: &str) -> bool {
    matches!(
        role,
        "specimen"
            | "physical_sample_id"
            | "observation_id"
            | "repetition"
            | "reference"
            | "group"
            | "factor"
            | "instrument"
            | "campaign"
    )
}
fn identity_role(role: &str) -> bool {
    matches!(
        role,
        "specimen" | "physical_sample_id" | "observation_id" | "repetition" | "reference" | "group"
    )
}

pub fn parse(input: &str) -> Result<FactorRequest, String> {
    if input.len() > browser::MAX_JSON_BYTES {
        return Err("JSON_MEMORY_BUDGET_EXCEEDED".into());
    }
    let r =
        serde_json::from_str(input).map_err(|e| format!("INVALID_FACTOR_ASSOCIATION_INPUT:{e}"))?;
    validate(&r)?;
    Ok(r)
}
fn population_keys(r: &FactorRequest) -> Vec<String> {
    let part = |p| {
        r.manifest
            .iter()
            .filter(|row| row.partition == p)
            .map(|row| row.key.clone())
            .collect::<Vec<_>>()
    };
    match r.population {
        Population::Train => part(PartitionRole::Train),
        Population::Unpartitioned => part(PartitionRole::Unpartitioned),
        Population::GlobalTransductive => {
            let mut v = part(PartitionRole::Train);
            v.extend(part(PartitionRole::Test));
            v
        }
    }
}
fn aligned(column: &FactorColumn, keys: &[String]) -> Vec<Value> {
    let positions: BTreeMap<_, _> = column
        .row_keys
        .iter()
        .enumerate()
        .map(|(i, k)| (k.clone(), i))
        .collect();
    keys.iter()
        .map(|key| column.values[positions[key]].clone())
        .collect()
}
fn scores(r: &FactorRequest) -> Result<Vec<Vec<f64>>, String> {
    serde_json::from_value(r.pca.report["metrics"]["pca"]["value"]["scores"].clone())
        .map_err(|_| "INVALID_PCA_SCORES".into())
}
fn has_raw_or_y(value: &Value) -> bool {
    match value {
        Value::Object(m) => m.iter().any(|(k, v)| {
            matches!(
                k.as_str(),
                "y" | "Y" | "Y_train" | "Y_test" | "y_train" | "y_test" | "targets" | "spectra"
            ) || has_raw_or_y(v)
        }),
        Value::Array(a) => a.iter().any(has_raw_or_y),
        _ => false,
    }
}
pub fn validate(r: &FactorRequest) -> Result<(), String> {
    if r.schema_version != 1
        || r.protocol_version != PROTOCOL
        || r.representation != "raw"
        || r.components != "all_resolved"
        || r.parameters.preset != "f41_factor_pc_v1"
        || !nonempty(&r.dataset.dataset_id)
        || !nonempty(&r.dataset.source_id)
        || !nonempty(&r.dataset.content_version)
        || !sha(&r.dataset.content_sha256)
    {
        return Err("INVALID_FACTOR_PROTOCOL_BINDING".into());
    }
    if r.access.x || !r.access.y_fields.is_empty() {
        return Err("X_AND_Y_VALUES_FORBIDDEN_IN_FACTOR_OPERATION".into());
    }
    if r.population == Population::GlobalTransductive && !r.explicit_transductive {
        return Err("EXPLICIT_TRANSDUCTIVE_ASSOCIATION_CONSENT_REQUIRED".into());
    }
    if r.population != Population::GlobalTransductive && r.explicit_transductive {
        return Err("TRANSDUCTIVE_FLAG_SCOPE_MISMATCH".into());
    }
    if r.manifest.is_empty()
        || r.manifest.len() > browser::MAX_ROWS
        || r.manifest.iter().any(|row| !nonempty(&row.key))
        || r.manifest
            .iter()
            .map(|row| &row.key)
            .collect::<BTreeSet<_>>()
            .len()
            != r.manifest.len()
    {
        return Err("INVALID_FACTOR_MANIFEST".into());
    }
    if r.population == Population::Unpartitioned
        && r.manifest
            .iter()
            .any(|row| row.partition != PartitionRole::Unpartitioned)
    {
        return Err("UNPARTITIONED_SCOPE_CANNOT_HIDE_ASSIGNED_PARTITIONS".into());
    }
    let keys = population_keys(r);
    if keys.len() < 3 || r.pca.row_keys != keys {
        return Err("PCA_FACTOR_POPULATION_MISMATCH".into());
    }
    if r.factors.is_empty() || r.factors.len() > 4 || r.dependencies.len() > 24 {
        return Err("FACTOR_FIELD_BUDGET_OR_EMPTY_SELECTION".into());
    }
    let columns: Vec<_> = r.factors.iter().chain(&r.dependencies).collect();
    let names: Vec<_> = columns.iter().map(|c| c.name.clone()).collect();
    if names.iter().collect::<BTreeSet<_>>().len() != names.len() || r.access.m_fields != names {
        return Err("FACTOR_FIELD_GRANT_MISMATCH".into());
    }
    let expected: BTreeSet<_> = keys.iter().collect();
    for (index, c) in columns.iter().enumerate() {
        if !nonempty(&c.name)
            || !nonempty(&c.origin)
            || c.derived_from_target == Some(true)
            || !dependency_role(&c.role)
            || (index < r.factors.len()
                && (!factor_role(&c.role) || c.kind == MetadataKind::Unknown))
            || c.row_keys.len() != keys.len()
            || c.values.len() != keys.len()
            || c.row_keys.iter().collect::<BTreeSet<_>>() != expected
            || c.row_keys.iter().collect::<BTreeSet<_>>().len() != c.row_keys.len()
            || c.values.iter().any(|v| !scalar(v))
            || (c.kind == MetadataKind::Continuous
                && c.values.iter().any(|v| !v.is_null() && !v.is_number()))
        {
            return Err("INELIGIBLE_OR_MISALIGNED_FACTOR_FIELD".into());
        }
    }
    let report = &r.pca.report;
    let allowed: BTreeSet<_> = [
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
    .into_iter()
    .collect();
    if report
        .as_object()
        .is_none_or(|m| m.keys().any(|k| !allowed.contains(k.as_str())))
        || has_raw_or_y(report)
        || report["status"] != "computed"
        || report["test_target_accessed"] != false
        || report["raw_spectra_included"] != false
    {
        return Err("UNKNOWN_OR_FORBIDDEN_PCA_SOURCE".into());
    }
    browser::interpret(report, browser::PredictionIntent::Unknown)?;
    let scope = &report["scope"];
    if scope["dataset_id"] != r.dataset.dataset_id
        || scope["source_id"] != r.dataset.source_id
        || scope["content_sha256"] != r.dataset.content_sha256
        || count(&scope["n_observations"]) != Some(keys.len())
        || scope["observation_ids_sha256"] != digest(&keys)
        || scope["target"] != "absent"
        || !report["input_sha256"].as_str().is_some_and(sha)
    {
        return Err("PCA_SOURCE_BINDING_MISMATCH".into());
    }
    let metrics = report["metrics"].as_object().ok_or("PCA_METRICS_MISSING")?;
    let metric_names: BTreeSet<_> = [
        "pca",
        "density",
        "raw_neighbors",
        "projected_neighbors",
        "metadata_factor_association",
        "resampling_stability",
        "parameter_sensitivity",
        "predictive_performance",
    ]
    .into_iter()
    .collect();
    if metrics.len() != metric_names.len()
        || metrics.keys().any(|k| !metric_names.contains(k.as_str()))
        || metrics["predictive_performance"]["status"] != "unavailable"
        || !metrics["predictive_performance"]["value"].is_null()
        || metrics["metadata_factor_association"]["status"] != "unavailable"
        || !metrics["metadata_factor_association"]["value"].is_null()
    {
        return Err("PCA_SOURCE_NOT_QUALIFIED_X_ONLY_REPORT".into());
    }
    let p = &metrics["pca"];
    if p["status"] != "computed" || !p["reason"].is_null() {
        return Err("PCA_ASSOCIATION_SOURCE_UNAVAILABLE".into());
    }
    let k = count(&p["value"]["n_components_resolved"]).ok_or("INVALID_PCA_COMPONENT_COUNTS")?;
    let requested =
        count(&p["value"]["n_components_requested"]).ok_or("INVALID_PCA_COMPONENT_COUNTS")?;
    let matrix = scores(r)?;
    if k == 0
        || k > 20
        || requested < k
        || requested > 20
        || matrix.len() != keys.len()
        || matrix
            .iter()
            .any(|row| row.len() != k || row.iter().any(|v| !v.is_finite()))
        || p["value"]["eigenvalues"].as_array().is_none_or(|v| {
            v.len() != k
                || v.iter()
                    .any(|x| x.as_f64().is_none_or(|a| !a.is_finite() || a < 0.))
        })
        || p["value"]["unresolved"].as_array().is_none_or(|v| {
            v.len() != requested
                || v.iter().take(k).any(|a| *a != false)
                || v.iter().skip(k).any(|a| *a != true)
        })
        || !p["value"]["backend_version"]
            .as_str()
            .is_some_and(|v| v == METHODS_VERSION)
    {
        return Err("PCA_SCORES_OR_COMPONENT_LINEAGE_INVALID".into());
    }
    match (r.population, &r.pca.fit_receipt) {
        (Population::Unpartitioned, None) => {}
        (Population::Train | Population::GlobalTransductive, Some(receipt)) => {
            let mut unsigned = receipt.clone();
            let recorded = unsigned
                .as_object_mut()
                .ok_or("INVALID_PCA_FIT_RECEIPT")?
                .remove("receipt_sha256")
                .ok_or("MISSING_PCA_FIT_RECEIPT_HASH")?;
            let op = if r.population == Population::Train {
                "train_structure"
            } else {
                "global_descriptive_transductive"
            };
            let fit = if r.population == Population::Train {
                "train"
            } else {
                "transductive"
            };
            let pca_call = receipt["provider_calls"].as_array().and_then(|calls| {
                calls
                    .iter()
                    .find(|c| c["operation"] == "pca" && c["status"] == "computed")
            });
            let forbidden_receipt = receipt.as_object().is_none_or(|m| {
                m.keys().any(|k| {
                    ![
                        "protocol_version",
                        "operation",
                        "diagnostic",
                        "dataset",
                        "request_sha256",
                        "manifest_sha256",
                        "reference_keys",
                        "query_keys",
                        "fit_keys",
                        "requested_fit_keys",
                        "fit_attempted",
                        "fit_executed",
                        "reference_population",
                        "query_population",
                        "fit",
                        "representation",
                        "parameters",
                        "selection_context",
                        "explicit_transductive",
                        "exclusion_field",
                        "fields_read",
                        "provider_calls",
                        "test_x_accessed",
                        "y_accessed",
                        "physical_independence",
                        "physical_id_encoding",
                        "receipt_sha256",
                    ]
                    .contains(&k.as_str())
                })
            });
            if forbidden_receipt
                || recorded != digest(&unsigned)
                || receipt["protocol_version"] != "domains.browser_scoped_analysis.v1"
                || receipt["operation"] != op
                || receipt["fit"] != fit
                || receipt["fit_executed"] != true
                || receipt["fit_attempted"] != true
                || receipt["dataset"]
                    != serde_json::to_value(&r.dataset).map_err(|e| e.to_string())?
                || receipt["manifest_sha256"] != digest(&r.manifest)
                || receipt["fit_keys"] != json!(keys)
                || receipt["fields_read"]["x"]["row_keys"] != json!(keys)
                || receipt["y_accessed"] != false
                || receipt["fields_read"]["y"] != json!([])
                || receipt["representation"] != "raw"
                || pca_call.is_none_or(|c| {
                    c["matrices"]["sample_ids"] != json!(keys)
                        || c["matrices"]["matrix"]["sha256"]
                            != receipt["fields_read"]["x"]["matrix"]["sha256"]
                })
                || (r.population == Population::Train
                    && (receipt["test_x_accessed"] != false || receipt["query_keys"] != json!([])))
                || (r.population == Population::GlobalTransductive
                    && receipt["explicit_transductive"] != true)
            {
                return Err("PCA_EXECUTION_RECEIPT_MISMATCH".into());
            }
        }
        _ => return Err("PCA_EXECUTION_PROVENANCE_REQUIRED".into()),
    }
    Ok(())
}

struct Recorder<'a, P> {
    provider: &'a P,
    calls: RefCell<Vec<Value>>,
    version: String,
}
impl<P: FactorProvider> Recorder<'_, P> {
    fn call(&self, operation: &str, request: Value) -> Value {
        let mut fingerprint = json!({"operation":operation,"request_sha256":digest(&request),"backend_version":self.version,
            "parameters":{"n_permutations":if operation.ends_with("descriptive"){json!(0)}else{Value::Null},"seed":if operation.ends_with("descriptive"){json!(0)}else{Value::Null},"method":request.get("method"),"max_arrangements":request.get("max_arrangements")},
            "inputs":{}});
        for key in ["scores", "values", "codes", "p_values"] {
            if let Some(values) = request.get(key) {
                fingerprint["inputs"][key] =
                    json!({"count":values.as_array().map(Vec::len),"sha256":digest(values)});
            }
        }
        let result = match self.provider.execute(operation, &request) {
            Ok(v) if v["backend_version"] == self.version => slot(v),
            Ok(_) => failed(ProviderError::internal("FACTOR_PROVIDER_VERSION_MISMATCH")),
            Err(e) => failed(e),
        };
        fingerprint["status"] = result["status"].clone();
        fingerprint["reason"] = result["reason"].clone();
        fingerprint["response_sha256"] = json!(digest(&result));
        self.calls.borrow_mut().push(fingerprint);
        result
    }
}

fn column_summary(c: &FactorColumn, keys: &[String]) -> Value {
    let values = aligned(c, keys);
    let mut levels: BTreeMap<String, (Value, usize)> = BTreeMap::new();
    for value in values.iter().filter(|v| !v.is_null()) {
        let entry = levels
            .entry(scalar_key(value))
            .or_insert((value.clone(), 0));
        entry.1 += 1;
    }
    let complete = values.iter().all(|v| !v.is_null());
    json!({"name":c.name,"role":c.role,"kind":c.kind,"unit":c.unit,"origin":c.origin,"evidence":c.evidence,"derived_from_target":c.derived_from_target,
        "n_rows":keys.len(),"n_missing":values.iter().filter(|v|v.is_null()).count(),"n_distinct_nonmissing":levels.len(),
        "n_repeated_rows_beyond_first":levels.values().map(|(_,n)|n.saturating_sub(1)).sum::<usize>(),
        "declared_unique_unit_count":if complete&&identity_role(&c.role){json!(levels.len())}else{Value::Null},
        "independent_units_established":false,
        "level_counts":if factor_role(&c.role)&&!identity_role(&c.role)&&c.kind==MetadataKind::Categorical{json!(levels.values().enumerate().map(|(i,(v,n))|json!({"level_id":format!("level-{}",i+1),"value":v,"count":n})).collect::<Vec<_>>())}else{Value::Null}})
}
fn crossing(a: &FactorColumn, b: &FactorColumn, keys: &[String]) -> Value {
    let av = aligned(a, keys);
    let bv = aligned(b, keys);
    let mut table = BTreeMap::<(String, String), usize>::new();
    let mut left = BTreeMap::<String, BTreeSet<String>>::new();
    let mut right = BTreeMap::<String, BTreeSet<String>>::new();
    for (a, b) in av
        .iter()
        .zip(&bv)
        .filter(|(a, b)| !a.is_null() && !b.is_null())
    {
        let x = scalar_key(a);
        let y = scalar_key(b);
        *table.entry((x.clone(), y.clone())).or_default() += 1;
        left.entry(x.clone()).or_default().insert(y.clone());
        right.entry(y).or_default().insert(x);
    }
    let complete: usize = table.values().sum();
    let a_nested = !left.is_empty() && left.values().all(|v| v.len() == 1);
    let b_nested = !right.is_empty() && right.values().all(|v| v.len() == 1);
    let a_ids: BTreeMap<_, _> = av
        .iter()
        .filter(|v| !v.is_null())
        .map(scalar_key)
        .collect::<BTreeSet<_>>()
        .into_iter()
        .enumerate()
        .map(|(i, k)| (k, format!("level-{}", i + 1)))
        .collect();
    let b_ids: BTreeMap<_, _> = bv
        .iter()
        .filter(|v| !v.is_null())
        .map(scalar_key)
        .collect::<BTreeSet<_>>()
        .into_iter()
        .enumerate()
        .map(|(i, k)| (k, format!("level-{}", i + 1)))
        .collect();
    let possible = left.len() * right.len();
    let mut absent = Vec::new();
    if possible <= 4096 {
        for x in left.keys() {
            for y in right.keys() {
                if !table.contains_key(&(x.clone(), y.clone())) {
                    absent.push(json!({"left_level":a_ids[x],"right_level":b_ids[y]}));
                }
            }
        }
    }
    json!({"left":a.name,"right":b.name,"n_complete_pairs":complete,"n_missing_pairs":keys.len()-complete,
        "observed_combinations":table.iter().map(|((x,y),n)|json!({"left_level":a_ids[x],"right_level":b_ids[y],"count":n})).collect::<Vec<_>>(),
        "margin_definition":"levels present among complete pairs; level IDs refer to all observed nonmissing values in each field",
        "absent_combination_count":possible-table.len(),"absent_combinations":if possible<=4096{json!(absent)}else{Value::Null},
        "absence_enumeration_reason":if possible>4096{json!("PAIRWISE_OUTPUT_BUDGET_EXCEEDED")}else{Value::Null},
        "left_nested_in_right":a_nested,"right_nested_in_left":b_nested,
        "literal_total_confounding":left.len()>1&&right.len()>1&&a_nested&&b_nested,
        "qualification":"Literal observed label combinations only; no causal attribution or completeness of relevant factors."})
}

fn inference_gate(r: &FactorRequest, keys: &[String]) -> Result<(), String> {
    if r.inference.mode == InferenceMode::Descriptive {
        return Err("DESCRIPTIVE_ONLY_NO_INFERENCE_REQUESTED".into());
    }
    let p = r
        .inference
        .plan
        .as_ref()
        .ok_or("EXCHANGEABILITY_PLAN_NOT_SUPPLIED")?;
    let ids: Vec<_> = r.factors.iter().map(|f| f.name.clone()).collect();
    if p.protocol_version != "domains.factor_exchangeability.v1"
        || p.population != r.population
        || p.dataset_content_sha256 != r.dataset.content_sha256
        || p.pca_evidence_sha256 != r.pca.report["evidence_sha256"]
        || p.factor_ids != ids
        || p.components != "all_resolved"
        || p.selection != "prospective"
        || p.missingness != "complete_units"
        || p.null_model != "unrestricted_exchangeability_given_fitted_x"
        || !p.no_other_dependencies
        || p.external_evidence.qualification != "externally_qualified"
        || !nonempty(&p.external_evidence.uri)
        || !sha(&p.external_evidence.content_sha256)
        || !nonempty(&p.external_evidence.basis)
    {
        return Err("EXCHANGEABILITY_OR_FAMILY_RECORD_NOT_QUALIFIED".into());
    }
    if keys.len() > 8 {
        return Err("EXACT_INFERENCE_OBSERVATION_BUDGET_EXCEEDED".into());
    }
    if r.factors.iter().chain(&r.dependencies).any(|c| {
        c.derived_from_target != Some(false)
            || c.origin == "unknown"
            || c.evidence == Evidence::Unknown
            || c.values.iter().any(Value::is_null)
    }) {
        return Err("INFERENCE_REQUIRES_COMPLETE_NON_TARGET_DECLARATIONS".into());
    }
    let unit = r
        .dependencies
        .iter()
        .find(|c| c.name == p.unit_field)
        .ok_or("QUALIFIED_UNIT_FIELD_MISSING")?;
    if !((p.unit_kind == "specimen"
        && matches!(unit.role.as_str(), "specimen" | "physical_sample_id"))
        || (p.unit_kind == "independent_acquisition" && unit.role == "observation_id"))
    {
        return Err("QUALIFIED_ANALYSIS_UNIT_MISMATCH".into());
    }
    let supplied: BTreeSet<_> = r
        .factors
        .iter()
        .chain(&r.dependencies)
        .filter(|c| identity_role(&c.role))
        .map(|c| c.name.clone())
        .collect();
    if p.dependency_fields.iter().cloned().collect::<BTreeSet<_>>() != supplied {
        return Err("DEPENDENCY_RECORD_INCOMPLETE".into());
    }
    for c in r.factors.iter().chain(&r.dependencies) {
        if identity_role(&c.role)
            && c.values
                .iter()
                .map(scalar_key)
                .collect::<BTreeSet<_>>()
                .len()
                != keys.len()
        {
            return Err(
                "REPEATED_OR_BLOCKED_UNITS_REQUIRE_ANOTHER_EXCHANGEABILITY_PROTOCOL".into(),
            );
        }
    }
    Ok(())
}

pub fn analyze(r: &FactorRequest, provider: &impl FactorProvider) -> Result<Value, String> {
    validate(r)?;
    let version = provider.version();
    if version != METHODS_VERSION {
        return Err("PINNED_METHODS_1_3_13_ABI_2_20_REQUIRED".into());
    }
    let recorder = Recorder {
        provider,
        calls: RefCell::new(Vec::new()),
        version,
    };
    let keys = population_keys(r);
    let matrix = scores(r)?;
    let k = matrix[0].len();
    let n_requested = count(&r.pca.report["metrics"]["pca"]["value"]["n_components_requested"])
        .expect("validated count");
    let mut factors = Vec::new();
    let mut infer_error = inference_gate(r, &keys).err();
    for f in &r.factors {
        let values = aligned(f, &keys);
        let used: Vec<_> = values
            .iter()
            .enumerate()
            .filter(|(_, v)| !v.is_null())
            .map(|(i, _)| i)
            .collect();
        let used_keys: Vec<_> = used.iter().map(|i| keys[*i].clone()).collect();
        let mut levels = BTreeMap::<String, (Value, usize)>::new();
        for i in &used {
            let entry = levels
                .entry(scalar_key(&values[*i]))
                .or_insert((values[*i].clone(), 0));
            entry.1 += 1;
        }
        let level_codes: BTreeMap<_, _> = levels
            .keys()
            .enumerate()
            .map(|(i, v)| (v.clone(), i as i64))
            .collect();
        let codes: Vec<_> = used
            .iter()
            .map(|i| level_codes[&scalar_key(&values[*i])])
            .collect();
        let numeric: Vec<_> = used.iter().map(|i| values[*i].as_f64()).collect();
        let categorical = f.kind == MetadataKind::Categorical;
        let summary = if !categorical && !used.is_empty() {
            recorder.call("summary", json!({"values":numeric}))
        } else {
            unavailable("NOT_A_CONTINUOUS_NONEMPTY_FACTOR")
        };
        let range = if summary["status"] == "computed"
            && count(&summary["value"]["count"]) == Some(used.len())
            && summary["value"]["min"].as_f64().is_some_and(f64::is_finite)
            && summary["value"]["max"].as_f64().is_some_and(f64::is_finite)
            && summary["value"]["min"].as_f64() <= summary["value"]["max"].as_f64()
        {
            slot(json!({"min":summary["value"]["min"],"max":summary["value"]["max"]}))
        } else {
            unavailable("OWNER_RANGE_UNAVAILABLE")
        };
        let saturated = categorical && levels.len() == used.len() && used.len() > 1;
        let mut warnings = Vec::new();
        if saturated {
            warnings.push("SATURATED_FACTOR_ETA_SQUARED_IS_NOT_INFORMATIVE_EXPLANATION");
        }
        if categorical && levels.values().any(|(_, n)| *n == 1) {
            warnings.push("SINGLETON_LEVELS_CAN_INFLATE_DESCRIPTIVE_SEPARATION");
        }
        if used.len() != keys.len() {
            warnings.push("PAIRWISE_COMPLETE_MISSINGNESS_MAY_BE_NONRANDOM");
        }
        if f.derived_from_target.is_none() || f.evidence == Evidence::Unknown {
            warnings.push("M_ORIGIN_OR_TARGET_DERIVATION_NOT_VERIFIED");
        }
        if saturated {
            infer_error
                .get_or_insert("SATURATED_FACTOR_HAS_NO_INFORMATIVE_INFERENTIAL_CONTRAST".into());
        }
        let mut components = Vec::new();
        for pc in 0..n_requested {
            let mut desc = if pc >= k {
                unavailable("PCA_COMPONENT_NOT_RESOLVED")
            } else if used.len() < 2 {
                unavailable("FEWER_THAN_TWO_COMPLETE_PAIRS")
            } else {
                let vector: Vec<_> = used.iter().map(|i| matrix[*i][pc]).collect();
                let payload = if categorical {
                    json!({"codes":codes,"scores":vector})
                } else {
                    json!({"values":numeric,"scores":vector,"method":r.correlation_method})
                };
                let out = recorder.call(
                    if categorical {
                        "factor_descriptive"
                    } else {
                        "correlation_descriptive"
                    },
                    payload,
                );
                if out["status"] != "computed" {
                    out
                } else {
                    let o = &out["value"];
                    let statistic = if categorical {
                        &o["eta_squared"]
                    } else {
                        &o["coefficient"]
                    };
                    if o["p_value"] != Value::Null
                        || count(&o["n_permutations_executed"]) != Some(0)
                        || count(&o["n_at_least_observed"]) != Some(0)
                    {
                        failed(ProviderError::internal(
                            "DESCRIPTIVE_PROVIDER_PERFORMED_UNQUALIFIED_INFERENCE",
                        ))
                    } else if statistic.is_null() {
                        unavailable("OWNER_DESCRIPTIVE_STATISTIC_UNDEFINED")
                    } else if statistic.as_f64().is_none_or(|x| {
                        !x.is_finite()
                            || if categorical {
                                !(0. ..=1.).contains(&x)
                            } else {
                                !(-1. ..=1.).contains(&x)
                            }
                    }) {
                        failed(ProviderError::internal("INVALID_FACTOR_PROVIDER_RESPONSE"))
                    } else {
                        slot(
                            json!({"measure":if categorical{"eta_squared"}else if r.correlation_method==Correlation::Pearson{"pearson_r"}else{"spearman_rho"},"estimate":statistic,"owner_output":o}),
                        )
                    }
                }
            };
            if pc < k && desc["status"] != "computed" {
                infer_error
                    .get_or_insert("DECLARED_FAMILY_HAS_UNAVAILABLE_DESCRIPTIVE_MEMBER".into());
            }
            if pc >= k {
                desc = unavailable("PCA_COMPONENT_NOT_RESOLVED");
            }
            components.push(json!({"component":pc+1,"n_used":used.len(),"descriptive":desc,"inference":unavailable("INFERENCE_NOT_QUALIFIED_OR_NOT_REQUESTED"),"exact_owner_evidence":unavailable("EXACT_TEST_NOT_EXECUTED")}));
        }
        factors.push(json!({"factor_id":f.name,"kind":f.kind,"role":f.role,"unit":f.unit,"origin":f.origin,"evidence":f.evidence,"derived_from_target":f.derived_from_target,
            "n_fit_observations":keys.len(),"n_used":used.len(),"n_missing":keys.len()-used.len(),"used_keys_sha256":digest(&used_keys),
            "values_sha256":digest(&values),"n_levels":if categorical{json!(levels.len())}else{Value::Null},
            "level_counts":if categorical{json!(levels.values().enumerate().map(|(i,(v,n))|json!({"level_id":format!("level-{}",i+1),"value":v,"label":if let Some(s)=v.as_str(){s.to_owned()}else{v.to_string()},"count":n})).collect::<Vec<_>>())}else{Value::Null},
            "range":range,"owner_summary":summary,"warnings":warnings,"components":components}));
    }
    let mut exact_values = Vec::new();
    let mut exact_slots = Vec::new();
    if infer_error.is_none() {
        for (fi, f) in r.factors.iter().enumerate() {
            let values = aligned(f, &keys);
            let mapping: BTreeMap<_, _> = values
                .iter()
                .map(scalar_key)
                .collect::<BTreeSet<_>>()
                .into_iter()
                .enumerate()
                .map(|(i, v)| (v, i as i64))
                .collect();
            let codes: Vec<_> = values.iter().map(|v| mapping[&scalar_key(v)]).collect();
            for pc in 0..k {
                let vector: Vec<_> = matrix.iter().map(|row| row[pc]).collect();
                let cat = f.kind == MetadataKind::Categorical;
                let payload = if cat {
                    json!({"codes":codes,"scores":vector,"max_arrangements":EXACT_MAX})
                } else {
                    json!({"values":values,"scores":vector,"method":r.correlation_method,"max_arrangements":EXACT_MAX})
                };
                let out = recorder.call(
                    if cat {
                        "factor_exact"
                    } else {
                        "correlation_exact"
                    },
                    payload,
                );
                factors[fi]["components"][pc]["exact_owner_evidence"] = out.clone();
                if out["status"] != "computed"
                    || out["value"]["p_value"]
                        .as_f64()
                        .is_none_or(|p| !p.is_finite() || p <= 0. || p > 1.)
                    || out["value"]["minimum_p_value"]
                        .as_f64()
                        .is_none_or(|p| !p.is_finite() || p <= 0. || p > 1.)
                    || out["value"]["minimum_p_value"].as_f64() > out["value"]["p_value"].as_f64()
                    || out["value"]["maximum_statistic"]
                        .as_f64()
                        .is_none_or(|p| !p.is_finite() || !(0. ..=1.).contains(&p))
                    || count(&out["value"]["n_arrangements"])
                        .is_none_or(|n| n == 0 || n > EXACT_MAX)
                {
                    infer_error = Some("OWNER_EXACT_FAMILY_INCOMPLETE_OR_UNDEFINED".into());
                } else {
                    exact_values.push(out["value"]["p_value"].as_f64().expect("finite p"));
                }
                exact_slots.push((fi, pc, out));
            }
        }
        if infer_error.is_none() {
            let corrected = recorder.call("holm_adjust", json!({"p_values":exact_values}));
            let adjusted = corrected["value"]["adjusted"].as_array();
            if corrected["status"] != "computed"
                || adjusted.is_none_or(|v| {
                    v.len() != exact_slots.len()
                        || v.iter().zip(&exact_values).any(|(p, raw)| {
                            p.as_f64().is_none_or(|v| {
                                !v.is_finite() || !(0. ..=1.).contains(&v) || v < *raw
                            })
                        })
                })
            {
                infer_error = Some("OWNER_HOLM_FAMILY_UNAVAILABLE".into());
            } else {
                for ((fi, pc, out), p) in exact_slots
                    .iter()
                    .zip(adjusted.expect("validated adjustment"))
                {
                    factors[*fi]["components"][*pc]["inference"] = slot(
                        json!({"qualification":"conditional_on_supplied_external_exchangeability_record","test":if r.factors[*fi].kind==MetadataKind::Categorical{"exact_eta_squared"}else{"exact_absolute_correlation"},"owner_exact":out["value"],"holm_adjusted_p":p,"family_size":exact_slots.len(),"external_evidence":r.inference.plan.as_ref().map(|p|&p.external_evidence)}),
                    );
                }
            }
        }
    }
    if let Some(reason) = &infer_error {
        for f in &mut factors {
            for c in f["components"].as_array_mut().expect("components") {
                c["inference"] = unavailable(reason);
            }
        }
    }
    let dep_summaries: Vec<_> = r
        .dependencies
        .iter()
        .map(|c| column_summary(c, &keys))
        .collect();
    let contextual: Vec<_> = r
        .factors
        .iter()
        .chain(&r.dependencies)
        .filter(|c| factor_role(&c.role) && c.kind == MetadataKind::Categorical)
        .collect();
    let mut crossings = Vec::new();
    for i in 0..contextual.len() {
        for j in i + 1..contextual.len() {
            crossings.push(crossing(contextual[i], contextual[j], &keys));
        }
    }
    let mut receipt = json!({"dataset":r.dataset,"request_sha256":digest(r),"manifest_sha256":digest(&r.manifest),"population":r.population,
        "fit_keys":keys,"source_pca_input_sha256":r.pca.report["input_sha256"],"source_pca_evidence_sha256":r.pca.report["evidence_sha256"],
        "source_pca_fit_receipt_sha256":r.pca.fit_receipt.as_ref().map(|v|&v["receipt_sha256"]),"scores_sha256":digest(&matrix),"scores_shape":[matrix.len(),k],
        "pca_id":digest(&json!([r.pca.report["input_sha256"],r.pca.report["evidence_sha256"],keys])),"pca_refits":0,
        "fields_read":{"x":false,"y":[],"m":r.factors.iter().chain(&r.dependencies).map(|c|json!({"name":c.name,"role":c.role,"origin":c.origin,"n_rows":c.row_keys.len(),"keys_sha256":digest(&c.row_keys),"values_sha256":digest(&c.values)})).collect::<Vec<_>>()},
        "source_pca_uses_test_x":r.population==Population::GlobalTransductive,"test_scores_accessed":r.population==Population::GlobalTransductive,
        "test_m_accessed":r.population==Population::GlobalTransductive,"test_x_accessed":false,"y_accessed":false,"explicit_transductive":r.explicit_transductive,
        "provider_version":recorder.version,"provider_calls":recorder.calls.into_inner(),"parameters":r.parameters,"components":"all_resolved","correlation_method":r.correlation_method});
    receipt["receipt_sha256"] = json!(digest(&receipt));
    Ok(
        json!({"protocol_version":RESULT_PROTOCOL,"status":"computed","reason":null,"value":{
        "population":r.population,"representation":"recorded raw-PCA scores","pca_id":receipt["pca_id"],"scores_sha256":receipt["scores_sha256"],
        "analysis_unit":{"calculation_unit":"observations/acquisitions","n_observations":keys.len(),"n_independent_units":if infer_error.is_none(){json!(keys.len())}else{Value::Null},"physical_independence_verified_by_domains":false,"qualification":"Independent-unit support, when supplied, is conditional on the external design record; uniqueness alone is insufficient."},
        "inference":{"level":if infer_error.is_none(){"conditionally_admissible"}else if r.inference.mode==InferenceMode::Descriptive{"descriptive_only"}else{"unqualified"},"reason":infer_error,"family":r.inference.plan.as_ref().map(|p|json!({"factor_ids":p.factor_ids,"components":p.components,"correction":"holm","external_evidence":p.external_evidence})),"no_global_risk_or_causal_claim":true},
        "factors":factors,"dependency_audit":{"fields":dep_summaries,"pairwise_context_tables":crossings,"qualification":"Literal metadata only; missing factors do not establish absence of confounding."}},
        "receipt":receipt,"supported_claims":["Conditional, component-specific descriptive associations for the exact recorded score/M populations."],
        "limitations":["Eta squared concerns the variance of one recorded PC score, not total spectral variance.","Signed correlation depends on PC orientation; degenerate eigenspaces can change component associations.","Association does not establish causality, leakage, poor calibrability or a preprocessing remedy.","Repeated observations are retained with acquisition weighting; no automatic pseudoreplication correction.","P-values, when available, are conditional on the supplied external unrestricted-exchangeability record, not independently authenticated by Domains.","Raw X/Y and per-row M vectors/codes are not included; factor-color exports need separate authorization."],
        "action":"Review concomitant factors, physical/reference units, acquisition design and the intended prediction population."}),
    )
}
