//! Versioned task and report contracts; no numerical kernels.
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;

pub const PROTOCOL: &str = "domains.canonical.v0.2";
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Partition {
    Train,
    Test,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema, PartialEq, Eq, Default)]
#[serde(rename_all = "snake_case")]
pub enum AuditMode {
    #[default]
    PreTraining,
    PostEvaluation,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema, PartialEq, Eq, Default)]
#[serde(rename_all = "snake_case")]
pub enum TargetKind {
    #[default]
    Continuous,
    Categorical,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema, PartialEq, Eq, Default)]
#[serde(rename_all = "snake_case")]
pub enum Representation {
    #[default]
    Native,
    TechnicalMean,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Context {
    pub dataset_id: String,
    pub content_version: String,
    pub source_id: String,
    pub target_id: Option<String>,
    pub split_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Observation {
    pub observation_id: String,
    pub sample_id: String,
    pub physical_sample_id: String,
    pub independence_group: String,
    pub partition: Partition,
    pub x: Vec<Option<f64>>,
    #[serde(default)]
    pub y: Option<f64>,
    #[serde(default)]
    pub category: Option<String>,
    #[serde(default)]
    pub reference_id: Option<String>,
    #[serde(default)]
    pub reference_group_id: Option<String>,
    #[serde(default)]
    pub reference_status: Option<String>,
    #[serde(default)]
    pub reference_unit: Option<String>,
    #[serde(default)]
    pub individual_id: Option<String>,
    #[serde(default)]
    pub repetition_type: Option<String>,
    #[serde(default)]
    pub metadata: BTreeMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Policy {
    pub independence_unit: String,
    #[serde(default)]
    pub representation: Representation,
    #[serde(default)]
    pub audit_mode: AuditMode,
    pub seed: u64,
    pub pca_max_components: usize,
    pub pca_variance_fraction: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Task {
    pub schema_version: u32,
    pub context: Context,
    pub data_origin: String,
    pub axis: Vec<f64>,
    pub axis_unit: String,
    pub signal_unit: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_unit: Option<String>,
    #[serde(default)]
    pub target_kind: TargetKind,
    pub policy: Policy,
    pub observations: Vec<Observation>,
    #[serde(default)]
    pub provenance: BTreeMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Status {
    Computed,
    Unavailable,
    InsufficientData,
    NotIdentifiable,
    Error,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct Population {
    pub population_id: String,
    pub statistical_unit: String,
    pub n_train_observations: usize,
    pub n_test_observations: usize,
    pub n_train_physical_samples: usize,
    pub n_test_physical_samples: usize,
    pub n_train_independent_units: usize,
    pub n_test_independent_units: usize,
    pub n_effective: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct Metric {
    pub metric_id: String,
    pub protocol_version: String,
    pub context: Context,
    pub population: Population,
    pub preprocessing_view: String,
    pub status: Status,
    pub reason: Option<String>,
    pub value: Value,
    pub unit: String,
    pub parameters: Value,
    pub uncertainty: Option<Value>,
    pub provenance: BTreeMap<String, String>,
    pub observation_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct Finding {
    pub rule_id: String,
    pub severity: String,
    pub observation: String,
    pub confidence: String,
    pub calibration_consequence: String,
    pub recommended_action: String,
    pub evidence: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct Report {
    pub schema_version: u32,
    pub engine_version: String,
    pub protocol_version: String,
    pub context: Context,
    pub data_origin: String,
    pub status: String,
    pub test_target_accessed: bool,
    pub policy: Policy,
    pub provenance: BTreeMap<String, String>,
    pub fit: Option<Value>,
    pub preflight: Option<Value>,
    pub unit_audit: Value,
    pub representations: Value,
    pub metrics: Vec<Metric>,
    pub findings: Vec<Finding>,
    pub dimensions: BTreeMap<String, String>,
    pub limitations: Vec<String>,
}
