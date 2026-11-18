//! Prospective, X-only representation sensitivity. All numerical kernels stay in Methods.
use crate::{
    browser, browser_factor as factor, browser_scoped as scoped, browser_support as support, hash,
};
use nirs4all_preflight::*;
use serde::{de::DeserializeOwned, Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    cell::RefCell,
    collections::{BTreeMap, BTreeSet},
};

pub const PROTOCOL: &str = "domains.browser_preprocessing_sensitivity.v1";
pub const RESULT_PROTOCOL: &str = "domains.browser_preprocessing_sensitivity_result.v1";
const VERSION: &str = "1.3.13+abi.2.20.0";
const MEMORY_CELLS: usize = 4_000_000;
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PreprocessingStep {
    pub operator: String,
    pub parameters: BTreeMap<String, Value>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RepresentationSpec {
    pub id: String,
    pub family: String,
    pub steps: Vec<PreprocessingStep>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SensitivityPlan {
    pub bank_id: String,
    pub kind: String,
    #[serde(deserialize_with = "nullable")]
    pub parent_plan_sha256: Option<String>,
    pub representations: Vec<RepresentationSpec>,
    pub structure: bool,
    pub compare_neighbors: bool,
    pub compare_clusters: bool,
    pub correlation_method: factor::Correlation,
    pub support: support::Parameters,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SensitivityRequest {
    pub schema_version: u32,
    pub protocol_version: String,
    pub dataset: scoped::Dataset,
    pub manifest: Vec<scoped::ManifestRow>,
    pub population: String,
    pub reference_keys: Vec<String>,
    pub query_keys: Vec<String>,
    pub x: scoped::Spectra,
    pub factors: Vec<factor::FactorColumn>,
    pub dependencies: Vec<factor::FactorColumn>,
    #[serde(deserialize_with = "nullable")]
    pub exclusion_field: Option<String>,
    pub access: scoped::Access,
    pub plan: SensitivityPlan,
    pub stage: String,
    #[serde(deserialize_with = "nullable")]
    pub frozen_reference: Option<Value>,
    pub reuse_exact_prefixes: bool,
}
fn nullable<'de, D: serde::Deserializer<'de>, T: Deserialize<'de>>(
    d: D,
) -> Result<Option<T>, D::Error> {
    Option::<T>::deserialize(d)
}
fn fingerprint(value: &impl Serialize) -> String {
    fn canonical(v: &Value) -> Value {
        match v {
            Value::Number(n) => {
                let f = n.as_f64().expect("finite JSON number");
                json!({"number":format!("{:016x}",if f==0. {0} else {f.to_bits()})})
            }
            Value::Array(a) => json!({"array":a.iter().map(canonical).collect::<Vec<_>>()}),
            Value::Object(o) => {
                json!({"object":o.iter().map(|(k,v)|(k.clone(),canonical(v))).collect::<BTreeMap<_,_>>()})
            }
            v => json!({"scalar":v}),
        }
    }
    hash(
        &serde_json::to_vec(&canonical(
            &serde_json::to_value(value).expect("finite protocol JSON"),
        ))
        .expect("serializable canonical evidence"),
    )
}
fn unavailable(reason: impl Into<String>) -> Value {
    json!({"status":"unavailable","reason":reason.into(),"value":null})
}
fn computed(value: Value) -> Value {
    json!({"status":"computed","reason":null,"value":value})
}
fn sha(s: &str) -> bool {
    s.len() == 64 && s.bytes().all(|v| v.is_ascii_hexdigit())
}
fn text(s: &str) -> bool {
    !s.trim().is_empty() && s.len() <= 256
}
fn scalar(v: &Value) -> bool {
    v.is_null()
        || v.is_boolean()
        || v.is_string()
        || v.as_f64()
            .is_some_and(|n| n.is_finite() && n.abs() <= 9_007_199_254_740_991.)
}
fn role_keys(r: &SensitivityRequest, role: scoped::PartitionRole) -> Vec<String> {
    r.manifest
        .iter()
        .filter(|m| m.partition == role)
        .map(|m| m.key.clone())
        .collect()
}
pub fn parse(input: &str) -> Result<SensitivityRequest, String> {
    if input.len() > browser::MAX_JSON_BYTES {
        return Err("JSON_MEMORY_BUDGET_EXCEEDED".into());
    }
    let r = serde_json::from_str(input).map_err(|_| "INVALID_PREPROCESSING_SENSITIVITY_INPUT")?;
    validate(&r)?;
    Ok(r)
}
fn project_column(c: &factor::FactorColumn, keys: &[String]) -> factor::FactorColumn {
    let mut result = c.clone();
    result.values = keys
        .iter()
        .map(|key| {
            c.values[c
                .row_keys
                .iter()
                .position(|k| k == key)
                .expect("validated metadata keys")]
            .clone()
        })
        .collect();
    result.row_keys = keys.to_vec();
    result
}
fn metadata(c: &factor::FactorColumn) -> scoped::ScopedMetadata {
    scoped::ScopedMetadata {
        name: c.name.clone(),
        role: c.role.clone(),
        kind: c.kind,
        origin: c.origin.clone(),
        derived_from_target: c.derived_from_target,
        evidence: c.evidence,
        row_keys: c.row_keys.clone(),
        values: c.values.clone(),
    }
}
fn raw_reference(r: &SensitivityRequest) -> Vec<Vec<f64>> {
    r.x.matrix[..r.reference_keys.len()]
        .iter()
        .map(|row| {
            row.iter()
                .map(|v| v.expect("validated complete X"))
                .collect()
        })
        .collect()
}
fn reference_input(r: &SensitivityRequest) -> String {
    fingerprint(
        &json!({"dataset":r.dataset,"manifest":r.manifest,"reference_keys":r.reference_keys,"axis":r.x.axis,"axis_unit":r.x.axis_unit,"matrix":raw_reference(r),"factors":r.factors,"dependencies":r.dependencies.iter().map(|d|project_column(d,&r.reference_keys)).collect::<Vec<_>>() }),
    )
}
fn verify_frozen(r: &SensitivityRequest) -> Result<(), String> {
    let old = r
        .frozen_reference
        .as_ref()
        .ok_or("FROZEN_REFERENCE_REQUIRED")?;
    let mut unsigned = old.clone();
    let recorded = unsigned
        .as_object_mut()
        .ok_or("INVALID_FROZEN_REFERENCE")?
        .remove("evidence_sha256")
        .ok_or("INVALID_FROZEN_REFERENCE")?;
    if recorded != fingerprint(&unsigned)
        || old["schema_version"] != 1
        || old["protocol_version"] != RESULT_PROTOCOL
        || old["status"] != "computed"
        || old["stage"] != "reference_only"
        || old["population"] != r.population
        || old["dataset"] != json!(r.dataset)
        || old["plan_sha256"] != fingerprint(&r.plan)
        || fingerprint(&old["plan"]) != fingerprint(&r.plan)
        || old["reference_input_sha256"] != reference_input(r)
        || old["receipt"]["reference_keys"] != json!(r.reference_keys)
        || old["receipt"]["query_keys"] != json!([])
        || old["receipt"]["test_x_accessed"] != false
        || old["receipt"]["provider"] != VERSION
    {
        return Err("FROZEN_REFERENCE_BINDING_OR_EVIDENCE_MISMATCH".into());
    }
    let reps = old["representations"]
        .as_array()
        .ok_or("INVALID_FROZEN_REFERENCE")?;
    if reps.len() != r.plan.representations.len()
        || reps
            .iter()
            .zip(&r.plan.representations)
            .any(|(a, b)| a["id"] != b.id)
    {
        return Err("FROZEN_REFERENCE_PANEL_MISMATCH".into());
    }
    Ok(())
}
pub fn validate(r: &SensitivityRequest) -> Result<(), String> {
    use scoped::PartitionRole::*;
    if r.schema_version != 1
        || r.protocol_version != PROTOCOL
        || !["train", "unpartitioned"].contains(&r.population.as_str())
        || !["reference_only", "test_audit"].contains(&r.stage.as_str())
        || !text(&r.dataset.dataset_id)
        || !text(&r.dataset.source_id)
        || !text(&r.dataset.content_version)
        || !sha(&r.dataset.content_sha256)
    {
        return Err("INVALID_SENSITIVITY_BINDING".into());
    }
    if r.manifest.is_empty()
        || r.manifest.len() > browser::MAX_ROWS
        || r.manifest.iter().any(|m| !text(&m.key))
        || r.manifest
            .iter()
            .map(|m| &m.key)
            .collect::<BTreeSet<_>>()
            .len()
            != r.manifest.len()
    {
        return Err("INVALID_OR_OVER_BUDGET_MANIFEST".into());
    }
    let expected = if r.population == "train" {
        role_keys(r, Train)
    } else {
        if r.manifest.iter().any(|m| m.partition != Unpartitioned) {
            return Err("UNPARTITIONED_SCOPE_CANNOT_HIDE_ASSIGNED_PARTITIONS".into());
        }
        role_keys(r, Unpartitioned)
    };
    if r.population == "train" && r.manifest.iter().any(|m| m.partition == Unpartitioned) {
        return Err("MIXED_ASSIGNED_UNPARTITIONED_POPULATION".into());
    }
    let query = if r.stage == "test_audit" {
        if r.population != "train" {
            return Err("TEST_AUDIT_REQUIRES_TRAIN_POPULATION".into());
        }
        role_keys(r, Test)
    } else {
        Vec::new()
    };
    if expected.is_empty()
        || r.reference_keys != expected
        || r.query_keys != query
        || (r.stage == "test_audit" && query.is_empty())
    {
        return Err("COMPLETE_ORDERED_ROLE_POPULATION_REQUIRED".into());
    }
    if !r.access.x || !r.access.y_fields.is_empty() {
        return Err("X_ONLY_EXPLICIT_ACCESS_REQUIRED".into());
    }
    let keys: Vec<_> = r
        .reference_keys
        .iter()
        .chain(&r.query_keys)
        .cloned()
        .collect();
    let n = keys.len();
    let p = r.x.axis.len();
    if r.x.row_keys != keys
        || r.x.matrix.len() != n
        || p == 0
        || !text(&r.x.axis_unit)
        || r.x.axis.iter().any(|v| !v.is_finite())
        || !(r.x.axis.windows(2).all(|a| a[0] < a[1]) || r.x.axis.windows(2).all(|a| a[0] > a[1]))
        || r.x
            .matrix
            .iter()
            .any(|row| row.len() != p || row.iter().any(|v| v.is_none_or(|v| !v.is_finite())))
    {
        return Err("INVALID_ORDERED_COMPLETE_X_PAYLOAD".into());
    }
    if n.checked_mul(p).is_none_or(|n| n > browser::MAX_CELLS) {
        return Err("FULL_POPULATION_BROWSER_BUDGET_EXCEEDED".into());
    }
    if r.factors.len() > 2 || r.dependencies.len() > 24 {
        return Err("METADATA_FIELD_BUDGET_EXCEEDED".into());
    }
    let columns: Vec<_> = r.factors.iter().chain(&r.dependencies).collect();
    let mut names = Vec::new();
    for c in &columns {
        if !names.contains(&c.name) {
            names.push(c.name.clone());
        }
    }
    if names != r.access.m_fields
        || r.factors
            .iter()
            .map(|c| &c.name)
            .collect::<BTreeSet<_>>()
            .len()
            != r.factors.len()
        || r.dependencies
            .iter()
            .map(|c| &c.name)
            .collect::<BTreeSet<_>>()
            .len()
            != r.dependencies.len()
    {
        return Err("M_GRANT_PAYLOAD_MISMATCH".into());
    }
    for (i, c) in columns.iter().enumerate() {
        let ck = if i < r.factors.len() {
            &r.reference_keys
        } else {
            &keys
        };
        if !text(&c.name)
            || !text(&c.role)
            || !text(&c.origin)
            || ["y", "y_train", "y_test", "targets", "target"]
                .iter()
                .any(|y| c.origin.trim().eq_ignore_ascii_case(y))
            || c.derived_from_target == Some(true)
            || c.row_keys != *ck
            || c.values.len() != ck.len()
            || c.values.iter().any(|v| !scalar(v))
            || c.kind == scoped::MetadataKind::Continuous
                && c.values.iter().any(|v| !v.is_null() && !v.is_number())
            || !matches!(
                c.role.as_str(),
                "specimen"
                    | "physical_sample_id"
                    | "observation_id"
                    | "repetition"
                    | "reference"
                    | "reference_id"
                    | "reference_group_id"
                    | "group"
                    | "group_id"
                    | "factor"
                    | "instrument"
                    | "campaign"
            )
            || i < r.factors.len()
                && (!matches!(
                    c.role.as_str(),
                    "factor" | "group" | "instrument" | "campaign"
                ) || c.kind == scoped::MetadataKind::Unknown)
        {
            return Err("INELIGIBLE_OR_MISALIGNED_METADATA_FIELD".into());
        }
    }
    for c in &r.factors {
        if let Some(d) = r.dependencies.iter().find(|d| d.name == c.name) {
            if fingerprint(c) != fingerprint(&project_column(d, &r.reference_keys)) {
                return Err("CONFLICTING_FACTOR_DEPENDENCY_FIELD".into());
            }
        }
    }
    if let Some(name) = &r.exclusion_field {
        let c = r
            .dependencies
            .iter()
            .find(|c| &c.name == name)
            .ok_or("EXCLUSION_DEPENDENCY_REQUIRED")?;
        if c.kind == scoped::MetadataKind::Continuous
            || c.values
                .iter()
                .any(|v| v.is_null() || v.as_str().is_some_and(|s| s.trim().is_empty()))
        {
            return Err("INCOMPLETE_EXCLUSION_DEPENDENCY".into());
        }
    }
    let plan = &r.plan;
    if !text(&plan.bank_id)
        || !["prospective", "exploratory_revision"].contains(&plan.kind.as_str())
        || plan.parent_plan_sha256.as_ref().is_some_and(|h| !sha(h))
        || plan.kind == "exploratory_revision" && plan.parent_plan_sha256.is_none()
        || plan.representations.is_empty()
        || plan.representations.len() > 16
        || plan.representations[0].id != "raw"
        || !plan.representations[0].steps.is_empty()
        || plan
            .representations
            .iter()
            .any(|s| !text(&s.id) || !text(&s.family) || s.steps.len() > 3)
        || plan
            .representations
            .iter()
            .map(|s| &s.id)
            .collect::<BTreeSet<_>>()
            .len()
            != plan.representations.len()
    {
        return Err("INVALID_VERSIONED_REPRESENTATION_PANEL".into());
    }
    if (plan.compare_neighbors || plan.compare_clusters) && !plan.structure {
        return Err("COMPARISON_REQUIRES_STRUCTURE_BUNDLE".into());
    }
    let nr = r.reference_keys.len();
    let cells = nr.checked_mul(p).ok_or("PANEL_MEMORY_BUDGET_EXCEEDED")?;
    let nodes: usize = plan.representations.iter().map(|s| s.steps.len()).sum();
    let state_estimate = 4096usize
        .checked_add(p.checked_mul(32).ok_or("STATE_MEMORY_BUDGET_EXCEEDED")?)
        .ok_or("STATE_MEMORY_BUDGET_EXCEEDED")?;
    if nodes > 0 && state_estimate > support::STATE_BYTES {
        return Err("STATE_MEMORY_BUDGET_EXCEEDED".into());
    }
    let memory = cells
        .checked_mul(2 + plan.representations.len() + nodes)
        .and_then(|v| v.checked_add(nodes * (state_estimate / 8 + 1)))
        .and_then(|v| v.checked_add(r.query_keys.len() * p * 2));
    if memory.is_none_or(|n| n > MEMORY_CELLS) {
        return Err("PANEL_MEMORY_BUDGET_EXCEEDED".into());
    }
    let mut products = 0usize;
    for rep in &plan.representations {
        for step in &rep.steps {
            let weight = if step.operator == "SavitzkyGolay" {
                step.parameters
                    .get("window_length")
                    .and_then(Value::as_u64)
                    .unwrap_or(11)
                    .min(1_000_000) as usize
            } else {
                4
            };
            products = products.saturating_add(n.saturating_mul(p).saturating_mul(weight.max(1)));
        }
        if plan.structure {
            let k = 20.min(p).min(nr.saturating_sub(1));
            products = products
                .saturating_add(nr.saturating_mul(nr).saturating_mul(p + k * 2))
                .saturating_add(cells.saturating_mul(nr.min(p)));
        }
        if r.stage == "test_audit" {
            products = products
                .saturating_add(cells.saturating_mul(nr.min(p)))
                .saturating_add(r.query_keys.len().saturating_mul(p).saturating_mul(20));
            let folds = plan.support.n_folds;
            let components = plan.support.max_components;
            if plan.support.monitoring
                && (2..=nr as i64).contains(&folds)
                && components > 0
                && components as usize <= p
                && components as usize
                    <= nr
                        .saturating_sub(nr.div_ceil(folds as usize))
                        .saturating_sub(1)
            {
                products = products.saturating_add(
                    (folds as usize + 1)
                        .saturating_mul(nr)
                        .saturating_mul(p)
                        .saturating_mul(components as usize),
                );
            }
        }
    }
    if products > browser::MAX_PRODUCTS {
        return Err("AGGREGATE_PANEL_WORK_BUDGET_EXCEEDED".into());
    }
    if serde_json::to_vec(r)
        .map_err(|_| "INPUT_SERIALIZATION_FAILED")?
        .len()
        > browser::MAX_JSON_BYTES
    {
        return Err("JSON_MEMORY_BUDGET_EXCEEDED".into());
    }
    if r.stage == "reference_only" {
        if r.frozen_reference.is_some() {
            return Err("FROZEN_REFERENCE_NOT_APPLICABLE".into());
        }
    } else {
        verify_frozen(r)?;
    }
    Ok(())
}

struct Bridge<'a, P> {
    provider: &'a P,
    calls: &'a RefCell<Vec<Value>>,
    id: &'a str,
    keys: &'a [String],
    query_keys: &'a [String],
    support_transforms: RefCell<usize>,
    support_matrices: RefCell<Option<(String, String)>>,
    neighbors: RefCell<Vec<Option<NearestNeighborsDiagnostics>>>,
}
impl<P: support::SupportProvider> Bridge<'_, P> {
    fn call(&self, op: &str, payload: &Value, keys: &[String]) -> Result<Value, ProviderError> {
        let result = self.provider.execute(op, payload);
        let shapes: BTreeMap<_, _> = payload
            .as_object()
            .into_iter()
            .flat_map(|o| o.iter())
            .filter_map(|(k, v)| {
                v.as_array().map(|a| {
                    (
                        k.clone(),
                        vec![
                            a.len(),
                            a.first().and_then(Value::as_array).map_or(0, Vec::len),
                        ],
                    )
                })
            })
            .collect();
        self.calls.borrow_mut().push(json!({"operation":op,"representation_id":self.id,"row_keys":keys,"reference_row_keys":if op=="pca_monitor"{Some(self.keys)}else{None},"monitored_row_keys":if op=="pca_monitor"{Some(self.query_keys)}else{None},"payload_sha256":fingerprint(payload),"request_sha256":fingerprint(payload),"shapes":shapes,"provider_success":result.is_ok()}));
        let v = result?;
        if op != "capabilities" && v["backend_version"] != VERSION {
            return Err(ProviderError::internal(
                "PREPROCESSING_PROVIDER_VERSION_MISMATCH",
            ));
        }
        Ok(v)
    }
    fn typed<T: DeserializeOwned>(
        &self,
        op: &str,
        payload: &impl Serialize,
    ) -> Result<T, ProviderError> {
        serde_json::from_value(
            self.call(
                op,
                &serde_json::to_value(payload)
                    .map_err(|_| ProviderError::internal("REQUEST_SERIALIZATION_FAILED"))?,
                self.keys,
            )?,
        )
        .map_err(|_| ProviderError::internal("INVALID_PROVIDER_RESPONSE"))
    }
    fn invoke(&self, op: &str, payload: Value, keys: &[String]) -> Result<Value, String> {
        self.call(op, &payload, keys).map_err(|e| e.reason)
    }
}
impl<P: support::SupportProvider> MethodsProvider for Bridge<'_, P> {
    fn capabilities(&self) -> Vec<Capability> {
        self.typed("capabilities", &json!({})).unwrap_or_default()
    }
    fn pca(&self, r: &PcaRequest) -> Result<PcaDiagnostics, ProviderError> {
        self.typed("pca", r)
    }
    fn repeatability(
        &self,
        _: &RepeatabilityRequest,
    ) -> Result<RepeatabilityDiagnostics, ProviderError> {
        Err(ProviderError::unsupported(
            "NO_PREPROCESSING_REPEATABILITY_PROTOCOL",
        ))
    }
    fn summary(&self, r: &SummaryRequest) -> Result<SummaryDiagnostics, ProviderError> {
        self.typed("summary", r)
    }
    fn nearest_neighbors(
        &self,
        r: &NearestNeighborsRequest,
    ) -> Result<NearestNeighborsDiagnostics, ProviderError> {
        let v: Result<NearestNeighborsDiagnostics, _> = self.typed("nearest_neighbors", r);
        self.neighbors.borrow_mut().push(v.as_ref().ok().cloned());
        v
    }
    fn hdbscan(&self, r: &HdbscanRequest) -> Result<HdbscanDiagnostics, ProviderError> {
        self.typed("hdbscan", r)
    }
}
impl<P: support::SupportProvider> factor::FactorProvider for Bridge<'_, P> {
    fn version(&self) -> String {
        self.provider.version()
    }
    fn execute(&self, op: &str, r: &Value) -> Result<Value, ProviderError> {
        self.call(op, r, self.keys)
    }
}
impl<P: support::SupportProvider> support::SupportProvider for Bridge<'_, P> {
    fn version(&self) -> String {
        self.provider.version()
    }
    fn execute(&self, op: &str, r: &Value) -> Result<Value, ProviderError> {
        let binding = self.support_matrices.borrow();
        if matches!(op, "pca_fit" | "pca_transform" | "pca_monitor") && binding.is_none() {
            return Err(ProviderError::internal("SUPPORT_MATRIX_BINDING_REQUIRED"));
        }
        if let Some((reference, query)) = &*binding {
            let valid = match op {
                "pca_fit" => fingerprint(&r["matrix"]) == *reference,
                "pca_transform" => {
                    fingerprint(&r["matrix"])
                        == if *self.support_transforms.borrow() == 0 {
                            reference.clone()
                        } else {
                            query.clone()
                        }
                }
                "pca_monitor" => {
                    fingerprint(&r["reference"]) == *reference
                        && fingerprint(&r["monitored"]) == *query
                }
                _ => true,
            };
            if !valid {
                return Err(ProviderError::internal(
                    "SUPPORT_ACTUAL_MATRIX_SCOPE_MISMATCH",
                ));
            }
        }
        let combined: Vec<_> = self.keys.iter().chain(self.query_keys).cloned().collect();
        let keys = if op == "pca_transform" {
            let mut count = self.support_transforms.borrow_mut();
            let keys = if *count == 0 {
                self.keys
            } else {
                self.query_keys
            };
            *count += 1;
            keys
        } else if op == "pca_monitor" {
            &combined
        } else if op == "pca_destroy" {
            &[]
        } else {
            self.keys
        };
        self.call(op, r, keys)
    }
}
#[derive(Clone)]
struct StageState {
    step: PreprocessingStep,
    bytes: Vec<u8>,
    input_hash: String,
    output_hash: String,
    input_axis: Vec<f64>,
    axis: Vec<f64>,
}
#[derive(Clone)]
struct Prepared {
    matrix: Vec<Vec<f64>>,
    axis: Vec<f64>,
    states: Vec<StageState>,
    structure: Value,
    factors: Vec<Value>,
    neighbors: Vec<Option<NearestNeighborsDiagnostics>>,
    source: scoped::Dataset,
}
fn state(v: &Value) -> Result<Vec<u8>, String> {
    let a = v["state_bytes"]
        .as_array()
        .filter(|v| !v.is_empty() && v.len() <= support::STATE_BYTES)
        .ok_or("INVALID_PREPROCESSING_STATE_BYTES")?;
    a.iter()
        .map(|v| {
            v.as_u64()
                .and_then(|v| u8::try_from(v).ok())
                .ok_or("INVALID_PREPROCESSING_STATE_BYTES".into())
        })
        .collect()
}
fn output(v: &Value, n: usize, p: usize) -> Result<Vec<Vec<f64>>, String> {
    let a: Vec<Vec<f64>> =
        serde_json::from_value(v["matrix"].clone()).map_err(|_| "INVALID_PREPROCESSING_MATRIX")?;
    if a.len() != n
        || p == 0
        || n.checked_mul(p).is_none_or(|v| v > browser::MAX_CELLS)
        || a.iter()
            .any(|row| row.len() != p || row.iter().any(|v| !v.is_finite()))
    {
        return Err("INVALID_PREPROCESSING_MATRIX".into());
    }
    Ok(a)
}
fn step_axis(step: &PreprocessingStep, axis: &[f64]) -> Result<Vec<f64>, String> {
    let kinds: &[(&str, &str)] = match step.operator.as_str() {
        "SNV" => &[("with_mean", "bool"), ("with_std", "bool"), ("ddof", "int")],
        "MSC" => &[],
        "Detrend" => &[("polyorder", "int")],
        "SavitzkyGolay" => &[
            ("window_length", "int"),
            ("polyorder", "int"),
            ("deriv", "int"),
            ("delta", "number"),
            ("mode", "string"),
            ("cval", "number"),
        ],
        "Gaussian" => &[
            ("sigma", "number"),
            ("order", "int"),
            ("mode", "string"),
            ("cval", "number"),
            ("truncate", "number"),
        ],
        "StandardScale" => &[("with_mean", "bool"), ("with_std", "bool")],
        "Normalize" => &[("feature_min", "number"), ("feature_max", "number")],
        "CropTransformer" => &[("start", "int"), ("end", "int")],
        _ => return Err("UNSUPPORTED_PREPROCESSOR".into()),
    };
    if step.parameters.len() != kinds.len()
        || kinds
            .iter()
            .any(|(name, _)| !step.parameters.contains_key(*name))
    {
        return Err("EXPLICIT_PREPROCESS_PARAMETERS_REQUIRED".into());
    }
    for (name, v) in &step.parameters {
        let kind = kinds
            .iter()
            .find(|(k, _)| *k == name)
            .map(|(_, t)| *t)
            .ok_or("INVALID_PREPROCESS_PARAMETERS")?;
        let valid = match kind {
            "bool" => v.is_boolean(),
            "int" => v.as_i64().is_some(),
            "number" => v.as_f64().is_some_and(f64::is_finite),
            "string" => v.as_str().is_some_and(text),
            _ => false,
        };
        if !valid {
            return Err("INVALID_PREPROCESS_PARAMETERS".into());
        }
    }
    if step.operator == "CropTransformer" {
        let start = step
            .parameters
            .get("start")
            .and_then(Value::as_u64)
            .and_then(|v| usize::try_from(v).ok())
            .ok_or("EXPLICIT_CROP_INTERVAL_REQUIRED")?;
        let end = step
            .parameters
            .get("end")
            .and_then(Value::as_u64)
            .and_then(|v| usize::try_from(v).ok())
            .ok_or("EXPLICIT_CROP_INTERVAL_REQUIRED")?;
        if start >= end || end > axis.len() {
            return Err("INVALID_EXPLICIT_CROP_INTERVAL".into());
        }
        Ok(axis[start..end].to_vec())
    } else {
        Ok(axis.to_vec())
    }
}
fn transformations(states: &[StageState]) -> Vec<Value> {
    states.iter().map(|s|json!({"operator":s.step.operator,"parameters":s.step.parameters,"fit_keys_role":"reference_only","state_sha256":hash(&s.bytes),"reference_input_sha256":s.input_hash,"reference_output_sha256":s.output_hash,"input_axis_sha256":fingerprint(&s.input_axis),"output_axis_sha256":fingerprint(&s.axis),"input_bands":s.input_axis.len(),"output_bands":s.axis.len(),"provider":VERSION,"state_unchanged_after_transform":true})).collect()
}
type TransformedRepresentation = (Vec<Vec<f64>>, Vec<f64>, Vec<StageState>);
fn pipeline<P: support::SupportProvider>(
    r: &SensitivityRequest,
    spec: &RepresentationSpec,
    b: &Bridge<P>,
    cache: &mut BTreeMap<String, (Vec<Vec<f64>>, StageState)>,
    hits: &mut usize,
) -> Result<TransformedRepresentation, String> {
    let (mut matrix, mut axis, mut states) = (raw_reference(r), r.x.axis.clone(), Vec::new());
    for step in &spec.steps {
        let next_axis = step_axis(step, &axis)?;
        let key = fingerprint(&json!([VERSION, matrix, axis, r.reference_keys, step]));
        if r.reuse_exact_prefixes {
            if let Some((saved, s)) = cache.get(&key) {
                if s.input_hash != fingerprint(&matrix)
                    || s.input_axis != axis
                    || s.output_hash != fingerprint(saved)
                    || s.axis != next_axis
                {
                    return Err("STALE_EXACT_PREFIX_CACHE".into());
                }
                matrix = saved.clone();
                axis = s.axis.clone();
                states.push(s.clone());
                *hits += 1;
                continue;
            }
        }
        let result: Result<(Vec<Vec<f64>>, Vec<u8>), String> = (|| {
            let fit = b.invoke(
                "preprocess_fit",
                json!({"operator":step.operator,"parameters":step.parameters,"matrix":matrix}),
                &r.reference_keys,
            )?;
            let bytes = state(&fit)?;
            let transformed = b.invoke(
                "preprocess_transform",
                json!({"matrix":matrix}),
                &r.reference_keys,
            )?;
            if state(&transformed)? != bytes {
                return Err("REFERENCE_TRANSFORM_CHANGED_FITTED_STATE".into());
            }
            let out = output(&transformed, r.reference_keys.len(), next_axis.len())?;
            Ok((out, bytes))
        })();
        let destroyed = b.invoke("preprocess_destroy", json!({}), &[]);
        let (out, bytes) = result?;
        if destroyed?["destroyed"] != true {
            return Err("PREPROCESSING_CLEANUP_FAILED".into());
        }
        let saved = StageState {
            step: step.clone(),
            bytes,
            input_hash: fingerprint(&matrix),
            output_hash: fingerprint(&out),
            input_axis: axis.clone(),
            axis: next_axis.clone(),
        };
        if r.reuse_exact_prefixes {
            cache.insert(key, (out.clone(), saved.clone()));
        }
        matrix = out;
        axis = next_axis;
        states.push(saved);
    }
    Ok((matrix, axis, states))
}

fn scope(
    r: &SensitivityRequest,
    source: &scoped::Dataset,
    matrix: &[Vec<f64>],
    axis: &[f64],
    query: Option<&[Vec<f64>]>,
) -> scoped::ScopedRequest {
    let keys: Vec<_> = r
        .reference_keys
        .iter()
        .chain(if query.is_some() {
            r.query_keys.iter()
        } else {
            [].iter()
        })
        .cloned()
        .collect();
    let columns: Vec<_> = r
        .exclusion_field
        .iter()
        .filter_map(|name| r.dependencies.iter().find(|c| &c.name == name))
        .map(|c| metadata(&project_column(c, &keys)))
        .collect();
    let values: Vec<_> = matrix.iter().chain(query.unwrap_or(&[])).cloned().collect();
    serde_json::from_value(json!({"schema_version":1,"protocol_version":scoped::PROTOCOL,"operation":if query.is_some(){"train_reference_test_query"}else{"train_structure"},"diagnostic":null,"dataset":source,"manifest":r.manifest,"reference_keys":r.reference_keys,"query_keys":if query.is_some(){r.query_keys.clone()}else{vec![]},"access":{"x":true,"m_fields":columns.iter().map(|c|c.name.clone()).collect::<Vec<_>>(),"y_fields":[]},"fit":if query.is_some(){"none"}else{"train"},"representation":"raw","selection_context":"unspecified","explicit_transductive":false,"parameters":{"preset":"f4_fixed_raw_v1"},"exclusion_field":r.exclusion_field,"x":{"row_keys":keys,"matrix":values,"axis":axis,"axis_unit":r.x.axis_unit},"metadata":columns})).expect("constructed scoped wire")
}
fn diagnostics<P: support::SupportProvider>(
    r: &SensitivityRequest,
    source: &scoped::Dataset,
    matrix: &[Vec<f64>],
    axis: &[f64],
    b: &Bridge<P>,
) -> (Value, Vec<Value>) {
    if !r.plan.structure {
        return (
            unavailable("STRUCTURE_NOT_REQUESTED"),
            r.factors
                .iter()
                .map(|_| unavailable("STRUCTURE_NOT_REQUESTED"))
                .collect(),
        );
    }
    let result = if r.population == "train" {
        scoped::analyze(&scope(r, source, matrix, axis, None), b).map(|s| {
            if s["status"] == "computed" {
                computed(json!({"report":s["value"]["structure"],"scoped":s}))
            } else {
                unavailable(s["reason"].as_str().unwrap_or("STRUCTURE_UNAVAILABLE"))
            }
        })
    } else {
        let group_ids = r
            .exclusion_field
            .as_ref()
            .and_then(|name| r.dependencies.iter().find(|c| &c.name == name))
            .map(|c| {
                project_column(c, &r.reference_keys)
                    .values
                    .iter()
                    .map(Value::to_string)
                    .collect()
            });
        browser::analyze(
            &browser::BrowserRequest {
                schema_version: 1,
                dataset_id: source.dataset_id.clone(),
                source_id: source.source_id.clone(),
                content_sha256: source.content_sha256.clone(),
                observation_ids: r.reference_keys.clone(),
                axis: axis.to_vec(),
                axis_unit: r.x.axis_unit.clone(),
                spectra: matrix.to_vec(),
                group_ids,
                prediction_intent: browser::PredictionIntent::Unknown,
            },
            b,
        )
        .map(|v| computed(json!({"report":v,"scoped":null})))
    }
    .unwrap_or_else(unavailable);
    let mut factors = Vec::new();
    for column in &r.factors {
        let report = &result["value"]["report"];
        if report["metrics"]["pca"]["status"] != "computed" {
            factors.push(unavailable("PCA_ASSOCIATION_SOURCE_UNAVAILABLE"));
            continue;
        }
        let compact: serde_json::Map<String, Value> = [
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
        .iter()
        .map(|k| ((*k).into(), report[*k].clone()))
        .collect();
        let deps: Vec<_> = r
            .dependencies
            .iter()
            .filter(|d| !r.factors.iter().any(|f| f.name == d.name))
            .map(|d| project_column(d, &r.reference_keys))
            .collect();
        let mut fields = vec![column.name.clone()];
        fields.extend(deps.iter().map(|d| d.name.clone()));
        let input = factor::FactorRequest {
            schema_version: 1,
            protocol_version: factor::PROTOCOL.into(),
            dataset: source.clone(),
            manifest: r.manifest.clone(),
            population: if r.population == "train" {
                factor::Population::Train
            } else {
                factor::Population::Unpartitioned
            },
            pca: factor::PcaSource {
                report: Value::Object(compact),
                row_keys: r.reference_keys.clone(),
                fit_receipt: if r.population == "train" {
                    Some(result["value"]["scoped"]["receipt"].clone())
                } else {
                    None
                },
            },
            factors: vec![column.clone()],
            dependencies: deps,
            access: scoped::Access {
                x: false,
                m_fields: fields,
                y_fields: vec![],
            },
            representation: "raw".into(),
            explicit_transductive: false,
            components: "all_resolved".into(),
            correlation_method: r.plan.correlation_method,
            inference: factor::Inference {
                mode: factor::InferenceMode::Descriptive,
                plan: None,
            },
            parameters: factor::Parameters {
                preset: "f41_factor_pc_v1".into(),
            },
        };
        factors.push(factor::analyze(&input, b).unwrap_or_else(unavailable));
    }
    (result, factors)
}
fn query_pipeline<P: support::SupportProvider>(
    r: &SensitivityRequest,
    p: &Prepared,
    b: &Bridge<P>,
) -> Result<Vec<Vec<f64>>, String> {
    let mut matrix: Vec<Vec<f64>> = r.x.matrix[r.reference_keys.len()..]
        .iter()
        .map(|row| {
            row.iter()
                .map(|v| v.expect("validated complete X"))
                .collect()
        })
        .collect();
    for s in &p.states {
        let result = (|| {
            let restored = b.invoke(
                "preprocess_restore",
                json!({"operator":s.step.operator,"state_bytes":s.bytes}),
                &[],
            )?;
            if state(&restored)? != s.bytes {
                return Err("RESTORED_PREPROCESSING_STATE_CHANGED".into());
            }
            let transformed = b.invoke(
                "preprocess_transform",
                json!({"matrix":matrix}),
                &r.query_keys,
            )?;
            if state(&transformed)? != s.bytes {
                return Err("QUERY_TRANSFORM_CHANGED_FITTED_STATE".into());
            }
            output(&transformed, r.query_keys.len(), s.axis.len())
        })();
        let destroyed = b.invoke("preprocess_destroy", json!({}), &[]);
        matrix = result?;
        if destroyed?["destroyed"] != true {
            return Err("PREPROCESSING_CLEANUP_FAILED".into());
        }
    }
    Ok(matrix)
}
fn neighbor_comparison<P: support::SupportProvider>(
    r: &SensitivityRequest,
    raw: &Prepared,
    p: &Prepared,
    index: usize,
    b: &Bridge<P>,
) -> Value {
    let metric = if index == 0 {
        "raw_neighbors"
    } else {
        "projected_neighbors"
    };
    if raw.structure["value"]["report"]["metrics"][metric]["status"] != "computed"
        || p.structure["value"]["report"]["metrics"][metric]["status"] != "computed"
    {
        return unavailable("MATCHING_NEIGHBOR_EVIDENCE_UNAVAILABLE");
    }
    let Some(a) = raw.neighbors.get(index).and_then(Option::as_ref) else {
        return unavailable("RAW_NEIGHBOR_IDENTITIES_UNAVAILABLE");
    };
    let Some(other) = p.neighbors.get(index).and_then(Option::as_ref) else {
        return unavailable("REPRESENTATION_NEIGHBOR_IDENTITIES_UNAVAILABLE");
    };
    if a.indices.len() != r.reference_keys.len() || other.indices.len() != a.indices.len() {
        return unavailable("NEIGHBOR_POPULATION_MISMATCH");
    }
    let mut rows = Vec::new();
    let mut fractions = Vec::new();
    for (i, (a, c)) in a.indices.iter().zip(&other.indices).enumerate() {
        let aa: BTreeSet<_> = a.iter().filter(|v| **v >= 0).copied().collect();
        let cc: BTreeSet<_> = c.iter().filter(|v| **v >= 0).copied().collect();
        let shared = aa.intersection(&cc).count();
        let fraction = if aa.is_empty() {
            None
        } else {
            Some(shared as f64 / aa.len() as f64)
        };
        if let Some(f) = fraction {
            fractions.push(f);
        }
        rows.push(json!({"row_key":r.reference_keys[i],"shared_count":shared,"raw_count":aa.len(),"representation_count":cc.len(),"fraction":fraction,"reason":if fraction.is_none(){Some("EMPTY_RAW_NEIGHBORHOOD")}else{None}}));
    }
    let summary = if fractions.is_empty() {
        unavailable("NO_AVAILABLE_NEIGHBOR_FRACTIONS")
    } else {
        match b.typed::<SummaryDiagnostics>(
            "summary",
            &SummaryRequest {
                values: fractions.clone(),
            },
        ) {
            Ok(s)
                if s.count == fractions.len()
                    && [s.min, s.max, s.mean, s.q25, s.median, s.q75]
                        .iter()
                        .all(|v| v.is_finite())
                    && s.sample_sd.is_none_or(|v| v.is_finite() && v >= 0.) =>
            {
                computed(json!(s))
            }
            _ => unavailable("NEIGHBOR_FRACTION_SUMMARY_UNAVAILABLE"),
        }
    };
    computed(
        json!({"rows":rows,"summary":summary,"n_reference":r.reference_keys.len(),"n_available":fractions.len(),"n_unavailable":r.reference_keys.len()-fractions.len(),"rule":"shared identities / raw returned identities; same ordered rows and exclusions; distances are not compared"}),
    )
}
fn cluster_comparison<P: support::SupportProvider>(
    raw: &Prepared,
    p: &Prepared,
    b: &Bridge<P>,
) -> Value {
    let a = &raw.structure["value"]["report"]["metrics"]["density"];
    let c = &p.structure["value"]["report"]["metrics"]["density"];
    if a["status"] != "computed" || c["status"] != "computed" {
        return unavailable("MATCHING_DENSITY_EVIDENCE_UNAVAILABLE");
    }
    let Ok(aa) = serde_json::from_value::<Vec<i64>>(a["value"]["labels"].clone()) else {
        return unavailable("INVALID_DENSITY_LABELS");
    };
    let Ok(cc) = serde_json::from_value::<Vec<i64>>(c["value"]["labels"].clone()) else {
        return unavailable("INVALID_DENSITY_LABELS");
    };
    if aa.len() != cc.len() {
        return unavailable("DENSITY_POPULATION_MISMATCH");
    }
    let joint: Vec<_> = aa
        .iter()
        .zip(&cc)
        .filter(|(a, c)| **a >= 0 && **c >= 0)
        .map(|(a, c)| (*a, *c))
        .collect();
    let ja: Vec<_> = joint.iter().map(|(a, _)| *a).collect();
    let jb: Vec<_> = joint.iter().map(|(_, b)| *b).collect();
    let joint_keys: Vec<_> = aa
        .iter()
        .zip(&cc)
        .enumerate()
        .filter(|(_, (a, b))| **a >= 0 && **b >= 0)
        .map(|(i, _)| b.keys[i].clone())
        .collect();
    let ari = match b.invoke(
        "adjusted_rand",
        json!({"labels_a":ja,"labels_b":jb}),
        &joint_keys,
    ) {
        Ok(v)
            if v["value"]
                .as_f64()
                .is_some_and(|v| v.is_finite() && (-1.0..=1.0).contains(&v)) =>
        {
            computed(json!({"value":v["value"],"n_joint":joint.len(),"provider":VERSION}))
        }
        Ok(v) if v["value"].is_null() => unavailable("OWNER_ARI_UNDEFINED"),
        Ok(_) => unavailable("INVALID_OWNER_ARI"),
        Err(e) => unavailable(e),
    };
    let na = a["value"]["n_clusters"].as_u64().unwrap_or(0) as usize;
    let nb = c["value"]["n_clusters"].as_u64().unwrap_or(0) as usize;
    let jaccard = match b.invoke(
        "cluster_jaccard",
        json!({"labels_a":aa,"labels_b":cc,"n_clusters_a":na,"n_clusters_b":nb}),
        b.keys,
    ) {
        Ok(v) if valid_jaccard(&v, na, nb, aa.len()) => {
            if na == 0 || nb == 0 {
                unavailable("NO_ASSIGNED_CLUSTER_PAIRS")
            } else {
                computed(
                    json!({"jaccard":v["jaccard"],"intersections":v["intersections"],"sizes_a":v["sizes_a"],"sizes_b":v["sizes_b"],"provider":VERSION,"negative_labels":"unassigned; excluded by owner Jaccard kernel"}),
                )
            }
        }
        Ok(_) => unavailable("INVALID_OWNER_CLUSTER_JACCARD"),
        Err(e) => unavailable(e),
    };
    computed(
        json!({"ari":ari,"cluster_jaccard":jaccard,"n_total":aa.len(),"n_joint":joint.len(),"raw_noise_count":aa.iter().filter(|v|**v<0).count(),"representation_noise_count":cc.iter().filter(|v|**v<0).count(),"both_noise_count":aa.iter().zip(&cc).filter(|(a,b)|**a<0&&**b<0).count(),"raw_noise_to_assigned_count":aa.iter().zip(&cc).filter(|(a,b)|**a<0&&**b>=0).count(),"raw_assigned_to_noise_count":aa.iter().zip(&cc).filter(|(a,b)|**a>=0&&**b<0).count(),"qualification":"Descriptive same-population partitions; ARI uses joint assigned intersection; all noise counts retained"}),
    )
}
fn valid_jaccard(v: &Value, na: usize, nb: usize, n: usize) -> bool {
    let counts = |a: &Value, len: usize| {
        a.as_array().is_some_and(|a| {
            a.len() == len && a.iter().all(|v| v.as_u64().is_some_and(|v| v <= n as u64))
        })
    };
    counts(&v["sizes_a"], na)
        && counts(&v["sizes_b"], nb)
        && v["intersections"]
            .as_array()
            .is_some_and(|a| a.len() == na && a.iter().all(|row| counts(row, nb)))
        && v["jaccard"].as_array().is_some_and(|a| {
            a.len() == na
                && a.iter().all(|row| {
                    row.as_array().is_some_and(|row| {
                        row.len() == nb
                            && row.iter().all(|v| {
                                v.is_null()
                                    || v.as_f64()
                                        .is_some_and(|v| v.is_finite() && (0.0..=1.0).contains(&v))
                            })
                    })
                })
        })
}
pub fn analyze(
    r: &SensitivityRequest,
    provider: &impl support::SupportProvider,
) -> Result<Value, String> {
    validate(r)?;
    if provider.version() != VERSION {
        return Err("PINNED_METHODS_1_3_13_ABI_2_20_REQUIRED".into());
    }
    let calls = RefCell::new(Vec::new());
    let (mut cache, mut hits, mut prepared, mut failures) =
        (BTreeMap::new(), 0usize, Vec::new(), Vec::new());
    let plan_hash = fingerprint(&r.plan);
    let reference_hash = reference_input(r);
    for spec in &r.plan.representations {
        let bridge = Bridge {
            provider,
            calls: &calls,
            id: &spec.id,
            keys: &r.reference_keys,
            query_keys: &r.query_keys,
            support_transforms: RefCell::new(0),
            support_matrices: RefCell::new(None),
            neighbors: RefCell::new(Vec::new()),
        };
        match pipeline(r, spec, &bridge, &mut cache, &mut hits) {
            Ok((matrix, axis, states)) => {
                let identity = format!("{}::f43::{}::{}", r.dataset.source_id, plan_hash, spec.id);
                let source = scoped::Dataset {
                    dataset_id: format!(
                        "{}::f43::{}::{}",
                        r.dataset.dataset_id, plan_hash, spec.id
                    ),
                    source_id: identity,
                    content_version: "derived-reference-v1".into(),
                    content_sha256: fingerprint(
                        &json!({"parent":r.dataset.content_sha256,"reference_matrix":matrix,"axis":axis,"plan":plan_hash}),
                    ),
                };
                let (structure, factors) = diagnostics(r, &source, &matrix, &axis, &bridge);
                prepared.push(Some(Prepared {
                    matrix,
                    axis,
                    states,
                    structure,
                    factors,
                    neighbors: bridge.neighbors.into_inner(),
                    source,
                }));
                failures.push(None);
            }
            Err(e) => {
                prepared.push(None);
                failures.push(Some(e));
            }
        }
    }
    // Every reference pipeline is reproduced and checked before any query owner transform.
    if r.stage == "test_audit" {
        let frozen = &r.frozen_reference.as_ref().expect("validated freeze")["representations"];
        for (i, p) in prepared.iter().enumerate() {
            let old = &frozen[i];
            match p {
                Some(p)
                    if old["status"] == "computed"
                        && old["value"]["reference_matrix_sha256"] == fingerprint(&p.matrix)
                        && old["value"]["source"] == json!(p.source)
                        && fingerprint(&old["value"]["axis"]) == fingerprint(&p.axis)
                        && fingerprint(&old["value"]["transformations"])
                            == fingerprint(&transformations(&p.states)) => {}
                None if old["status"] == "unavailable" => {}
                _ => return Err("FROZEN_REFERENCE_REPRODUCTION_FAILED".into()),
            }
        }
    }
    let mut representations = Vec::new();
    for (i, spec) in r.plan.representations.iter().enumerate() {
        let Some(p) = &prepared[i] else {
            representations.push(json!({"id":spec.id,"family":spec.family,"steps":spec.steps,"status":"unavailable","reason":failures[i],"value":null}));
            continue;
        };
        let bridge = Bridge {
            provider,
            calls: &calls,
            id: &spec.id,
            keys: &r.reference_keys,
            query_keys: &r.query_keys,
            support_transforms: RefCell::new(0),
            support_matrices: RefCell::new(None),
            neighbors: RefCell::new(Vec::new()),
        };
        let (mut query_hash, mut support_result) = (None, unavailable("TEST_AUDIT_NOT_REQUESTED"));
        if r.stage == "test_audit" {
            match query_pipeline(r, p, &bridge) {
                Ok(query) => {
                    *bridge.support_matrices.borrow_mut() =
                        Some((fingerprint(&p.matrix), fingerprint(&query)));
                    query_hash = Some(fingerprint(&query));
                    let scope = scope(r, &p.source, &p.matrix, &p.axis, Some(&query));
                    let deps: Vec<_> = r.dependencies.iter().map(metadata).collect();
                    let request = support::SupportRequest {
                        schema_version: 1,
                        protocol_version: support::PROTOCOL.into(),
                        fit: "train".into(),
                        scope,
                        parameters: r.plan.support.clone(),
                        dependency_fields: deps.iter().map(|d| d.name.clone()).collect(),
                        dependencies: deps,
                        external_limit_plan: None,
                    };
                    support_result = match support::analyze(&request, &bridge) {
                        Ok(v) => computed(v),
                        Err(e) => unavailable(e),
                    };
                }
                Err(e) => {
                    representations.push(json!({"id":spec.id,"family":spec.family,"steps":spec.steps,"status":"unavailable","reason":e,"value":null}));
                    continue;
                }
            }
        }
        let comparisons = if let Some(raw) = &prepared[0] {
            json!({"pca":unavailable("NO_QUALIFIED_SUBSPACE_COMPARISON_API"),"neighbors":if r.plan.compare_neighbors{computed(json!({"raw_space":neighbor_comparison(r,raw,p,0,&bridge),"pca_space":neighbor_comparison(r,raw,p,1,&bridge)}))}else{unavailable("NEIGHBOR_COMPARISON_NOT_REQUESTED")},"clusters":if r.plan.compare_clusters{cluster_comparison(raw,p,&bridge)}else{unavailable("CLUSTER_COMPARISON_NOT_REQUESTED")}})
        } else {
            json!({"pca":unavailable("NO_QUALIFIED_SUBSPACE_COMPARISON_API"),"neighbors":unavailable("RAW_REFERENCE_EVIDENCE_UNAVAILABLE"),"clusters":unavailable("RAW_REFERENCE_EVIDENCE_UNAVAILABLE")})
        };
        representations.push(json!({"id":spec.id,"family":spec.family,"steps":spec.steps,"status":"computed","reason":null,"value":{"source":p.source,"axis":p.axis,"axis_unit":r.x.axis_unit,"original_axis_sha256":fingerprint(&r.x.axis),"reference_matrix_sha256":fingerprint(&p.matrix),"query_matrix_sha256":query_hash,"transformations":transformations(&p.states),"structure":p.structure,"factors":p.factors,"support":support_result,"comparisons":comparisons}}));
    }
    let catalog: Value =
        serde_json::from_slice(include_bytes!("../../../bindings/wasm/aom-bank.json"))
            .expect("checked-in descriptor catalog JSON");
    let raw_query: Vec<_> = r.x.matrix[r.reference_keys.len()..].to_vec();
    let input_hash = fingerprint(
        &json!({"reference_input_sha256":reference_hash,"plan_sha256":plan_hash,"stage":r.stage,"query_keys":r.query_keys,"query_matrix":raw_query,"dependencies":r.dependencies}),
    );
    let mut result = json!({"schema_version":1,"protocol_version":RESULT_PROTOCOL,"status":"computed","reason":null,"dataset":r.dataset,"population":r.population,"stage":r.stage,"plan":r.plan,"plan_sha256":plan_hash,"reference_input_sha256":reference_hash,"input_sha256":input_hash,"representations":representations,
        "receipt":{"provider":VERSION,"reference_keys":r.reference_keys,"query_keys":r.query_keys,"test_x_accessed":r.stage=="test_audit","y_accessed":false,"x_predict_accessed":false,"query_raw_sha256":if r.stage=="test_audit"{Some(fingerprint(&raw_query))}else{None},"provider_calls":calls.into_inner(),"exact_prefix_reuse_enabled":r.reuse_exact_prefixes,"exact_prefix_cache_hits":hits,"descriptor_catalog_sha256":hash(include_bytes!("../../../bindings/wasm/aom-bank.json")),"aom_source":catalog["aom_source"],"derived_source_semantics":"Inner raw refers only to the declared derived source; original-source results are preserved.","frozen_reference_sha256":r.frozen_reference.as_ref().map(|v|v["evidence_sha256"].clone())},
        "findings":[{"observation":"The prospectively declared representations were processed in order; unavailable entries remain visible.","confidence":"Conditional on the preserved owner outputs and declared populations.","consequence":"Persistence and change describe representation sensitivity; neither establishes chemistry, causality or predictive quality.","action":"Review each diagnostic, population, unavailable reason and experimental dependency without selecting a favorable representation."}],
        "limitations":["No Y, predict spectrum, test fit or preprocessing outcome ranking is admitted.","Axes, ordered acquisitions and declared exclusions are preserved; independence is not certified.","Derivatives with delta=1 use feature-index coordinates, including on irregular physical axes.","No paired-PCA subspace comparison API is qualified; coordinates and absolute distances are not compared.","AOM supplies descriptor provenance only; numerical equivalence to AOM implementations is not claimed.","Inspecting test X may influence later decisions; the test audit is descriptive after a frozen reference plan."]});
    result["evidence_sha256"] = json!(fingerprint(&result));
    Ok(result)
}
