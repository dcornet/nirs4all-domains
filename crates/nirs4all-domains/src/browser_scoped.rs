//! F4.0 value-projected operations. Domains assembles documentary evidence;
//! public Methods and Preflight retain numerical and intrinsic ownership.
use crate::{browser, hash};
use nirs4all_preflight::*;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::cell::RefCell;
use std::collections::{BTreeMap, BTreeSet};

pub const PROTOCOL: &str = "domains.browser_scoped_analysis.v1";
pub const RESULT_PROTOCOL: &str = "domains.browser_scoped_result.v1";

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ScopedOperation {
    IntegrityAudit,
    TrainStructure,
    MetadataFactorAudit,
    CrossPartitionMetadataAudit,
    TrainReferenceTestQuery,
    GlobalDescriptiveTransductive,
}
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum PartitionRole {
    Train,
    Test,
    Predict,
    Unpartitioned,
}
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Diagnostic {
    ExactSpectra,
    DeclaredIdentities,
}
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Fit {
    None,
    Train,
    Transductive,
}
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Representation {
    Raw,
}
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum SelectionContext {
    PreSelectionIntegrityAudit,
    PostEvaluationExplanation,
    Unspecified,
}
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum MetadataKind {
    Categorical,
    Continuous,
    Unknown,
}
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Evidence {
    Declared,
    Verified,
    Unknown,
}
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum Preset {
    #[serde(rename = "f4_fixed_raw_v1")]
    FixedRawV1,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Dataset {
    pub dataset_id: String,
    pub source_id: String,
    pub content_version: String,
    pub content_sha256: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ManifestRow {
    pub key: String,
    pub partition: PartitionRole,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Access {
    pub x: bool,
    pub m_fields: Vec<String>,
    pub y_fields: Vec<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Parameters {
    pub preset: Preset,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Spectra {
    pub row_keys: Vec<String>,
    pub matrix: Vec<Vec<Option<f64>>>,
    pub axis: Vec<f64>,
    pub axis_unit: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ScopedMetadata {
    pub name: String,
    pub role: String,
    pub kind: MetadataKind,
    pub origin: String,
    #[serde(deserialize_with = "required_nullable")]
    pub derived_from_target: Option<bool>,
    pub evidence: Evidence,
    pub row_keys: Vec<String>,
    pub values: Vec<Value>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ScopedRequest {
    pub schema_version: u32,
    pub protocol_version: String,
    pub operation: ScopedOperation,
    #[serde(deserialize_with = "required_nullable")]
    pub diagnostic: Option<Diagnostic>,
    pub dataset: Dataset,
    pub manifest: Vec<ManifestRow>,
    pub reference_keys: Vec<String>,
    pub query_keys: Vec<String>,
    pub access: Access,
    pub fit: Fit,
    pub representation: Representation,
    pub selection_context: SelectionContext,
    pub explicit_transductive: bool,
    pub parameters: Parameters,
    #[serde(deserialize_with = "required_nullable")]
    pub exclusion_field: Option<String>,
    #[serde(deserialize_with = "required_nullable")]
    pub x: Option<Spectra>,
    pub metadata: Vec<ScopedMetadata>,
}

// The wire contract requires explicit null for inapplicable fields. Serde's
// default Option handling would otherwise silently accept an absent grant.
fn required_nullable<'de, D: serde::Deserializer<'de>, T: Deserialize<'de>>(
    deserializer: D,
) -> Result<Option<T>, D::Error> {
    Option::<T>::deserialize(deserializer)
}

pub fn parse(input: &str) -> Result<ScopedRequest, String> {
    if input.len() > browser::MAX_JSON_BYTES {
        return Err("JSON_MEMORY_BUDGET_EXCEEDED".into());
    }
    let request = serde_json::from_str(input).map_err(|e| format!("INVALID_SCOPED_INPUT:{e}"))?;
    validate(&request)?;
    Ok(request)
}
fn nonempty(s: &str) -> bool {
    !s.trim().is_empty()
}
fn keys(r: &ScopedRequest, role: PartitionRole) -> Vec<String> {
    r.manifest
        .iter()
        .filter(|row| row.partition == role)
        .map(|row| row.key.clone())
        .collect()
}
fn population(r: &ScopedRequest) -> Vec<String> {
    r.reference_keys
        .iter()
        .chain(&r.query_keys)
        .cloned()
        .collect()
}
fn identity_role(role: &str) -> bool {
    matches!(
        role,
        "specimen"
            | "physical_sample_id"
            | "sample_id"
            | "observation_id"
            | "group"
            | "group_id"
            | "reference"
            | "reference_id"
            | "reference_group_id"
            | "repetition"
            | "instrument"
            | "campaign"
    )
}
fn physical_role(role: &str) -> bool {
    matches!(role, "specimen" | "physical_sample_id")
}
fn exclusion_role(role: &str) -> bool {
    identity_role(role)
}

/// Every value population and grant is closed before any provider invocation.
pub fn validate(r: &ScopedRequest) -> Result<(), String> {
    if r.schema_version != 1
        || r.protocol_version != PROTOCOL
        || !nonempty(&r.dataset.dataset_id)
        || !nonempty(&r.dataset.source_id)
        || !nonempty(&r.dataset.content_version)
        || r.dataset.content_sha256.len() != 64
        || !r
            .dataset
            .content_sha256
            .bytes()
            .all(|b| b.is_ascii_hexdigit())
    {
        return Err("INVALID_DATASET_PROTOCOL_BINDING".into());
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
        return Err("INVALID_OR_OVER_BUDGET_MANIFEST".into());
    }
    if !r.access.y_fields.is_empty() {
        return Err("Y_VALUES_FORBIDDEN".into());
    }
    let train = keys(r, PartitionRole::Train);
    let test = keys(r, PartitionRole::Test);
    let mut expected_reference = train.clone();
    let mut expected_query = Vec::new();
    let requires_x;
    let expected_fit;
    match r.operation {
        ScopedOperation::TrainStructure => {
            requires_x = true;
            expected_fit = Fit::Train;
        }
        ScopedOperation::GlobalDescriptiveTransductive => {
            if !r.explicit_transductive {
                return Err("EXPLICIT_TRANSDUCTIVE_CONSENT_REQUIRED".into());
            }
            requires_x = true;
            expected_fit = Fit::Transductive;
            expected_query = test.clone();
        }
        ScopedOperation::TrainReferenceTestQuery => {
            requires_x = true;
            expected_fit = Fit::None;
            expected_query = test.clone();
        }
        ScopedOperation::MetadataFactorAudit => {
            requires_x = false;
            expected_fit = Fit::None;
            if train.is_empty() && test.is_empty() {
                expected_reference = keys(r, PartitionRole::Unpartitioned);
            }
        }
        ScopedOperation::CrossPartitionMetadataAudit => {
            requires_x = false;
            expected_fit = Fit::None;
            expected_query = test.clone();
        }
        ScopedOperation::IntegrityAudit => {
            requires_x = match r.diagnostic {
                Some(Diagnostic::ExactSpectra) => true,
                Some(Diagnostic::DeclaredIdentities) => false,
                None => return Err("INTEGRITY_DIAGNOSTIC_REQUIRED".into()),
            };
            expected_fit = Fit::None;
            expected_query = test.clone();
        }
    }
    if r.operation != ScopedOperation::IntegrityAudit && r.diagnostic.is_some() {
        return Err("DIAGNOSTIC_NOT_APPLICABLE".into());
    }
    if r.operation != ScopedOperation::GlobalDescriptiveTransductive && r.explicit_transductive {
        return Err("TRANSDUCTIVE_CONSENT_NOT_APPLICABLE".into());
    }
    let cross = matches!(
        r.operation,
        ScopedOperation::IntegrityAudit
            | ScopedOperation::CrossPartitionMetadataAudit
            | ScopedOperation::TrainReferenceTestQuery
            | ScopedOperation::GlobalDescriptiveTransductive
    );
    if expected_reference.is_empty()
        || (cross && expected_query.is_empty())
        || r.reference_keys != expected_reference
        || r.query_keys != expected_query
    {
        return Err("COMPLETE_ORDERED_ROLE_POPULATION_REQUIRED".into());
    }
    if r.fit != expected_fit {
        return Err("FORBIDDEN_FIT_ROLE".into());
    }
    if r.access.x != r.x.is_some() || r.access.x != requires_x {
        return Err("X_GRANT_PAYLOAD_OPERATION_MISMATCH".into());
    }
    let rows = population(r);
    let fields: Vec<_> = r.metadata.iter().map(|m| m.name.clone()).collect();
    if fields != r.access.m_fields || fields.iter().collect::<BTreeSet<_>>().len() != fields.len() {
        return Err("M_GRANT_PAYLOAD_MISMATCH".into());
    }
    let mut cells = 0usize;
    for m in &r.metadata {
        if !nonempty(&m.name)
            || !nonempty(&m.role)
            || !nonempty(&m.origin)
            || m.row_keys != rows
            || m.values.len() != rows.len()
            || m.values.iter().any(|v| {
                !(v.is_null()
                    || v.is_string()
                    || v.is_boolean()
                    || v.as_f64().is_some_and(f64::is_finite))
            })
            || (m.kind == MetadataKind::Continuous
                && m.values.iter().any(|v| !v.is_null() && !v.is_number()))
        {
            return Err("INVALID_ORDERED_METADATA_PAYLOAD".into());
        }
        if m.derived_from_target == Some(true) || matches!(m.role.as_str(), "target" | "y") {
            return Err("TARGET_DERIVED_METADATA_INELIGIBLE".into());
        }
        if physical_role(&m.role)
            && m.values
                .iter()
                .any(|v| v.as_str().is_some_and(|s| !nonempty(s)))
        {
            return Err("EMPTY_DECLARED_PHYSICAL_IDENTITY".into());
        }
        cells = cells
            .checked_add(m.values.len())
            .ok_or("CELL_BUDGET_EXCEEDED")?;
    }
    let fit_or_support = matches!(
        r.operation,
        ScopedOperation::TrainStructure
            | ScopedOperation::GlobalDescriptiveTransductive
            | ScopedOperation::TrainReferenceTestQuery
    );
    if fit_or_support {
        let permitted: Vec<_> = r.exclusion_field.iter().cloned().collect();
        if fields != permitted {
            return Err("ONLY_EXPLICIT_EXCLUSION_METADATA_ALLOWED".into());
        }
    }
    if let Some(field) = &r.exclusion_field {
        let m = r
            .metadata
            .iter()
            .find(|m| &m.name == field)
            .ok_or("EXCLUSION_FIELD_NOT_GRANTED")?;
        if !fit_or_support
            || !exclusion_role(&m.role)
            || m.kind == MetadataKind::Continuous
            || m.values
                .iter()
                .any(|v| v.is_null() || v.as_str().is_some_and(|s| !nonempty(s)))
        {
            return Err("EXCLUSION_FIELD_INELIGIBLE".into());
        }
    }
    if r.operation == ScopedOperation::IntegrityAudit
        && r.metadata.iter().any(|m| !identity_role(&m.role))
    {
        return Err("ONLY_DECLARED_IDENTITY_METADATA_ALLOWED".into());
    }
    if r.operation == ScopedOperation::IntegrityAudit
        && r.metadata.iter().filter(|m| physical_role(&m.role)).count() > 1
    {
        return Err("AMBIGUOUS_PHYSICAL_IDENTITY_COLUMNS".into());
    }
    if let Some(x) = &r.x {
        let n = rows.len();
        let p = x.axis.len();
        if x.row_keys != rows
            || x.matrix.len() != n
            || p == 0
            || !nonempty(&x.axis_unit)
            || x.axis.iter().any(|v| !v.is_finite())
            || !(x.axis.windows(2).all(|w| w[0] < w[1]) || x.axis.windows(2).all(|w| w[0] > w[1]))
            || x.matrix
                .iter()
                .any(|row| row.len() != p || row.iter().flatten().any(|v| !v.is_finite()))
        {
            return Err("INVALID_ORDERED_X_PAYLOAD".into());
        }
        cells = n
            .checked_mul(p)
            .and_then(|v| cells.checked_add(v))
            .ok_or("CELL_BUDGET_EXCEEDED")?;
        if fit_or_support && x.matrix.iter().flatten().any(Option::is_none) {
            return Err("INCOMPLETE_X_UNAVAILABLE_WITHOUT_IMPUTATION".into());
        }
        // Structure retains the existing browser's separate PCA/NN/HDBSCAN
        // gates, so an expensive neighbor kernel cannot erase admissible PCA.
        // Integrity invokes no numerical provider; bound its hash/documentary
        // work by rows squared plus cells, rather than spectral pair products.
        let products = match r.operation {
            ScopedOperation::TrainReferenceTestQuery => r
                .reference_keys
                .len()
                .checked_mul(r.query_keys.len())
                .and_then(|v| v.checked_mul(p)),
            ScopedOperation::IntegrityAudit => n
                .checked_mul(n)
                .and_then(|v| n.checked_mul(p).and_then(|cells| v.checked_add(cells))),
            _ => Some(0),
        };
        if products.is_none_or(|v| v > browser::MAX_PRODUCTS) {
            return Err("OPERATION_WORK_BUDGET_EXCEEDED".into());
        }
    }
    if cells > browser::MAX_CELLS {
        return Err("CELL_BUDGET_EXCEEDED".into());
    }
    // Programmatic callers have the same serialized-memory boundary as parse.
    if serde_json::to_vec(r).map_err(|e| e.to_string())?.len() > browser::MAX_JSON_BYTES {
        return Err("JSON_MEMORY_BUDGET_EXCEEDED".into());
    }
    Ok(())
}

fn digest(value: &impl Serialize) -> String {
    // All inputs and provider results are checked before publication.
    hash(&serde_json::to_vec(value).expect("JSON serialization of validated finite evidence"))
}
fn matrix_receipt<T: Serialize>(matrix: &[Vec<T>]) -> Value {
    json!({"shape":[matrix.len(),matrix.first().map_or(0,Vec::len)],"sha256":digest(&matrix)})
}
fn computed(value: Value) -> Value {
    json!({"status":"computed","reason":null,"value":value})
}
fn unavailable(reason: &str) -> Value {
    json!({"status":"unavailable","reason":reason,"value":null})
}
fn failure(e: ProviderError) -> Value {
    json!({"status":if e.kind == ProviderErrorKind::Unsupported {"unsupported"} else {"error"},"reason":e.reason,"value":null})
}

struct RecordingProvider<'a, P> {
    inner: &'a P,
    calls: RefCell<Vec<Value>>,
}
impl<P: MethodsProvider> RecordingProvider<'_, P> {
    fn record<T>(
        &self,
        operation: &str,
        request: &impl Serialize,
        matrices: Value,
        result: &Result<T, ProviderError>,
    ) {
        self.calls.borrow_mut().push(json!({"provider":"nirs4all-methods via public Preflight MethodsProvider",
            "operation":operation,"request_sha256":digest(request),"matrices":matrices,
            "status":match result {Ok(_)=>"computed",Err(e) if e.kind == ProviderErrorKind::Unsupported=>"unsupported",Err(_)=>"error"},
            "reason":result.as_ref().err().map(|e| &e.reason)}));
    }
}
impl<P: MethodsProvider> MethodsProvider for RecordingProvider<'_, P> {
    fn capabilities(&self) -> Vec<Capability> {
        let out = self.inner.capabilities();
        self.calls.borrow_mut().push(json!({"provider":"nirs4all-methods via public Preflight MethodsProvider",
            "operation":"capabilities","request_sha256":digest(&json!({})),"matrices":{},"status":"computed","reason":null}));
        out
    }
    fn pca(&self, r: &PcaRequest) -> Result<PcaDiagnostics, ProviderError> {
        let out = self.inner.pca(r);
        self.record("pca", r, json!({"matrix":matrix_receipt(&r.matrix),"source_id":r.source_id,"sample_ids":r.sample_ids}), &out);
        out
    }
    fn hdbscan(&self, r: &HdbscanRequest) -> Result<HdbscanDiagnostics, ProviderError> {
        let out = self.inner.hdbscan(r);
        self.record(
            "hdbscan",
            r,
            json!({"matrix":matrix_receipt(&r.matrix)}),
            &out,
        );
        out
    }
    fn nearest_neighbors(
        &self,
        r: &NearestNeighborsRequest,
    ) -> Result<NearestNeighborsDiagnostics, ProviderError> {
        let out = self.inner.nearest_neighbors(r);
        self.record("nearest_neighbors",r,json!({"query":matrix_receipt(&r.query),"reference":matrix_receipt(&r.reference),
            "query_group_ids_sha256":digest(&r.query_group_ids),"reference_group_ids_sha256":digest(&r.reference_group_ids)}),&out);
        out
    }
    fn summary(&self, r: &SummaryRequest) -> Result<SummaryDiagnostics, ProviderError> {
        let out = self.inner.summary(r);
        self.record(
            "summary",
            r,
            json!({"values":{"shape":[r.values.len()],"sha256":digest(&r.values)}}),
            &out,
        );
        out
    }
    fn repeatability(
        &self,
        _: &RepeatabilityRequest,
    ) -> Result<RepeatabilityDiagnostics, ProviderError> {
        Err(ProviderError::unsupported(
            "NO_SCOPED_REPEATABILITY_PROTOCOL",
        ))
    }
}

fn documentary(r: &ScopedRequest) -> Value {
    let n_ref = r.reference_keys.len();
    let columns: Vec<_> = r.metadata.iter().map(|m| {
        let describe = |values: &[Value]| {
            let mut levels = BTreeMap::<String,(Value,usize)>::new();
            for value in values.iter().filter(|v| !v.is_null()) {
                let entry = levels.entry(value.to_string()).or_insert((value.clone(),0)); entry.1 += 1;
            }
            let level_counts: Vec<_> = levels.values().map(|(value,count)|json!({"level":value,"count":count})).collect();
            json!({"n_rows":values.len(),"missing_count":values.iter().filter(|v|v.is_null()).count(),
                "cardinality":levels.len(),"level_counts":if m.kind == MetadataKind::Continuous {Value::Null} else {json!(level_counts)}})
        };
        let a = &m.values[..n_ref]; let b = &m.values[n_ref..];
        let first: BTreeSet<_> = a.iter().filter(|v| !v.is_null()).map(Value::to_string).collect();
        let second: BTreeSet<_> = b.iter().filter(|v| !v.is_null()).map(Value::to_string).collect();
        let shared = first.intersection(&second).count();
        let reference_only:Vec<_>=first.difference(&second).collect();
        let query_only:Vec<_>=second.difference(&first).collect();
        let levels = |keys:&[&String]| keys.iter().map(|key| {
            // Keys were serialized from validated scalar Values above; this
            // only recovers their original type for documentary presentation.
            serde_json::from_str::<Value>(key).expect("serialized metadata scalar")
        }).collect::<Vec<_>>();
        json!({"name":m.name,"role":m.role,"kind":m.kind,"origin":m.origin,"evidence":m.evidence,"derived_from_target":m.derived_from_target,
            "reference":describe(a),"query":if b.is_empty() {Value::Null} else {describe(b)},
            "literal_shared_nonmissing_value_count":if b.is_empty() {Value::Null} else {json!(shared)},
            "reference_only_nonmissing_value_count":if b.is_empty() {Value::Null} else {json!(reference_only.len())},
            "query_only_nonmissing_value_count":if b.is_empty() {Value::Null} else {json!(query_only.len())},
            "reference_only_levels":if b.is_empty() || m.kind==MetadataKind::Continuous {Value::Null} else {json!(levels(&reference_only))},
            "query_only_levels":if b.is_empty() || m.kind==MetadataKind::Continuous {Value::Null} else {json!(levels(&query_only))},
            "association":unavailable("DOCUMENTARY_COUNTS_ONLY_NO_QUALIFIED_X_M_ASSOCIATION_PROTOCOL")})
    }).collect();
    json!({"assembly":"documentary counts and literal set intersection; no association test", "columns":columns})
}

fn group_ids(r: &ScopedRequest) -> Vec<i64> {
    let n = r.reference_keys.len() + r.query_keys.len();
    let Some(field) = &r.exclusion_field else {
        return (0..n as i64).collect();
    };
    let m = r
        .metadata
        .iter()
        .find(|m| &m.name == field)
        .expect("validated exclusion");
    let mut mapping = BTreeMap::new();
    m.values
        .iter()
        .map(|v| {
            let next = mapping.len() as i64;
            *mapping.entry(v.to_string()).or_insert(next)
        })
        .collect()
}
fn complete_matrix(r: &ScopedRequest) -> Vec<Vec<f64>> {
    r.x.as_ref()
        .expect("validated X grant")
        .matrix
        .iter()
        .map(|row| {
            row.iter()
                .map(|v| v.expect("validated complete matrix"))
                .collect()
        })
        .collect()
}

fn query_support(r: &ScopedRequest, provider: &impl MethodsProvider) -> Value {
    let matrix = complete_matrix(r);
    let n = r.reference_keys.len();
    let groups = group_ids(r);
    let k = 8.min(n);
    let request = NearestNeighborsRequest {
        reference: matrix[..n].to_vec(),
        query: matrix[n..].to_vec(),
        reference_group_ids: groups[..n].to_vec(),
        query_group_ids: groups[n..].to_vec(),
        k,
    };
    let raw = match provider.nearest_neighbors(&request) {
        Err(e) => failure(e),
        Ok(out) => {
            let valid = out.indices.len() == request.query.len()
                && out.distances.len() == request.query.len()
                && out.indices.iter().zip(&out.distances).enumerate().all(
                    |(i, (indices, distances))| {
                        if indices.len() != k || distances.len() != k {
                            return false;
                        }
                        let mut seen = BTreeSet::new();
                        let mut padded = false;
                        let mut previous = None;
                        indices
                            .iter()
                            .zip(distances)
                            .all(|(&index, d)| match (index, d) {
                                (-1, None) => {
                                    padded = true;
                                    true
                                }
                                (j, Some(distance))
                                    if !padded
                                        && j >= 0
                                        && (j as usize) < n
                                        && distance.is_finite()
                                        && *distance >= 0.
                                        && previous.is_none_or(|prev| *distance >= prev)
                                        && request.query_group_ids[i]
                                            != request.reference_group_ids[j as usize]
                                        && seen.insert(j) =>
                                {
                                    previous = Some(*distance);
                                    true
                                }
                                _ => false,
                            })
                    },
                );
            if valid {
                computed(json!({"n_reference":n,"n_query":request.query.len(),"k":k,
                "indices":out.indices,"distances":out.distances,"backend_version":out.backend_version,
                "reference_population_preserved":true,"approximate":false}))
            } else {
                failure(ProviderError::internal("INVALID_PROVIDER_RESPONSE"))
            }
        }
    };
    json!({"raw_neighbors":raw,"pca_support":unavailable("TRAIN_FITTED_PCA_TRANSFORM_BROWSER_PROTOCOL_UNQUALIFIED"),
        "quasi_duplicates":unavailable("NO_DECLARED_TOLERANCE_AND_QUALIFIED_BROWSER_PROTOCOL")})
}

fn exact_audit(r: &ScopedRequest) -> Result<(Value, Value), String> {
    let x = r.x.as_ref().expect("validated exact-spectra grant");
    let physical = r.metadata.iter().find(|m| physical_role(&m.role));
    let samples: Vec<_> = population(r)
        .iter()
        .enumerate()
        .map(|(i, key)| {
            // Preserve scalar type: declared number 1, string "1" and
            // boolean true must never collapse through String(value).
            let identity =
                physical.and_then(|m| (!m.values[i].is_null()).then(|| m.values[i].to_string()));
            json!({"sample_id":key,"physical_sample_id":identity,
            "partition":if i<r.reference_keys.len() {"development"} else {"retained_test"}})
        })
        .collect();
    let source = json!({"source_id":r.dataset.source_id,"observation_ids":x.row_keys,
        "sample_ids":x.row_keys,"x":x.matrix,"axis":x.axis,"axis_unit":x.axis_unit});
    let wire = json!({"schema_version":1,"sources":[source],"samples":samples,"targets":[],
        "options":{"max_cells":browser::MAX_CELLS,"max_samples":browser::MAX_ROWS,
            "snv_sensitivity":false,"validation_probe":{"enabled":false},
            "clustering":{"subsample_refit":false},"domain_shift":{"external_domain_audit":false}}});
    let input: QualificationInput =
        serde_json::from_str(&serde_json::to_string(&wire).map_err(|e| e.to_string())?)
            .map_err(|e| format!("PREFLIGHT_INPUT_CONTRACT:{e}"))?;
    // This provider is intentionally independent of the browser callback. Even
    // incidental upstream diagnostic attempts cannot perform a numerical fit.
    let report = nirs4all_preflight::analyze(&input, &UnavailableMethodsProvider);
    let metrics: Vec<_> = report
        .metrics
        .iter()
        .filter(|m| {
            matches!(
                m.metric_id.as_str(),
                "integrity.missing_cells"
                    | "integrity.axis_order"
                    | "integrity.development_observations"
                    | "integrity.cross_physical_exact_duplicate_pairs"
                    | "integrity.cross_partition_exact_duplicate_pairs"
            )
        })
        .collect();
    let execution = json!({"provider":"nirs4all-preflight@0.1.6::analyze",
        "operation":"integrity_audit","request_sha256":digest(&wire),"status":if report.validation.valid {"computed"} else {"error"},
        "reason":if report.validation.valid {Value::Null} else {json!("PREFLIGHT_INPUT_VALIDATION_FAILED")},
        "numerical_provider":"UnavailableMethodsProvider","numerical_fit_possible":false,
        "matrices":{"matrix":matrix_receipt(&x.matrix)},"sample_ids":x.row_keys});
    Ok((
        json!({"metrics":metrics,"validation":report.validation,
        "declared_identities":documentary(r),
        "quasi_duplicates":unavailable("NO_DECLARED_TOLERANCE_AND_QUALIFIED_BROWSER_PROTOCOL")}),
        execution,
    ))
}

pub fn analyze(r: &ScopedRequest, provider: &impl MethodsProvider) -> Result<Value, String> {
    validate(r)?;
    let recorder = RecordingProvider {
        inner: provider,
        calls: RefCell::new(Vec::new()),
    };
    let mut extra_calls = Vec::new();
    let mut status = "computed";
    let mut reason = Value::Null;
    let value = match r.operation {
        ScopedOperation::TrainStructure | ScopedOperation::GlobalDescriptiveTransductive => {
            let x = r.x.as_ref().expect("validated structure grant");
            if x.row_keys.len() < 3 {
                status = "unavailable";
                reason = json!("FEWER_THAN_THREE_STRUCTURE_ROWS");
                Value::Null
            } else {
                let group_ids = r.exclusion_field.as_ref().map(|field| {
                    r.metadata
                        .iter()
                        .find(|m| &m.name == field)
                        .expect("validated exclusion")
                        .values
                        .iter()
                        .map(Value::to_string)
                        .collect()
                });
                let input = browser::BrowserRequest {
                    schema_version: 1,
                    dataset_id: r.dataset.dataset_id.clone(),
                    source_id: r.dataset.source_id.clone(),
                    content_sha256: r.dataset.content_sha256.clone(),
                    observation_ids: x.row_keys.clone(),
                    spectra: complete_matrix(r),
                    axis: x.axis.clone(),
                    axis_unit: x.axis_unit.clone(),
                    group_ids,
                    prediction_intent: browser::PredictionIntent::Unknown,
                };
                json!({"structure":browser::analyze(&input,&recorder)?})
            }
        }
        ScopedOperation::TrainReferenceTestQuery => json!(query_support(r, &recorder)),
        ScopedOperation::IntegrityAudit if r.diagnostic == Some(Diagnostic::ExactSpectra) => {
            let (v, call) = exact_audit(r)?;
            if v["validation"]["valid"] != true {
                status = "error";
                reason = json!("PREFLIGHT_INPUT_VALIDATION_FAILED");
            }
            extra_calls.push(call);
            v
        }
        _ => documentary(r),
    };
    let mut calls = recorder.calls.into_inner();
    calls.extend(extra_calls);
    let requested_fit_keys = if r.fit == Fit::None {
        Vec::new()
    } else {
        population(r)
    };
    let fit_attempted = calls
        .iter()
        .any(|call| matches!(call["operation"].as_str(), Some("pca" | "hdbscan")));
    let fit_executed = value["structure"]["metrics"]["pca"]["status"] == "computed"
        && calls
            .iter()
            .any(|call| call["operation"] == "pca" && call["status"] == "computed");
    let fit_keys = if fit_attempted {
        requested_fit_keys.clone()
    } else {
        Vec::new()
    };
    let fields_read = json!({"x":r.x.as_ref().map(|x|json!({"row_keys":x.row_keys,"matrix":matrix_receipt(&x.matrix),
        "axis_sha256":digest(&x.axis),"axis_unit":x.axis_unit})),
        "m":r.metadata.iter().map(|m|json!({"name":m.name,"role":m.role,"kind":m.kind,"origin":m.origin,
            "evidence":m.evidence,"derived_from_target":m.derived_from_target,"row_keys":m.row_keys,"shape":[m.values.len()],"sha256":digest(&m.values)})).collect::<Vec<_>>(),
        "y":[]});
    let test_x_accessed = r.x.is_some() && !r.query_keys.is_empty();
    let receipt = json!({"protocol_version":PROTOCOL,"operation":r.operation,"diagnostic":r.diagnostic,
        "dataset":r.dataset,"request_sha256":digest(r),"manifest_sha256":digest(&r.manifest),
        "reference_keys":r.reference_keys,"query_keys":r.query_keys,"fit_keys":fit_keys,
        "requested_fit_keys":requested_fit_keys,"fit_attempted":fit_attempted,"fit_executed":fit_executed,
        "reference_population":{"role":if r.operation==ScopedOperation::MetadataFactorAudit && keys(r,PartitionRole::Train).is_empty() {"unpartitioned"} else {"train"},"row_keys":r.reference_keys},
        "query_population":{"role":"test","row_keys":r.query_keys},"fit":r.fit,"representation":r.representation,
        "parameters":r.parameters,"selection_context":r.selection_context,"explicit_transductive":r.explicit_transductive,
        "exclusion_field":r.exclusion_field,"fields_read":fields_read,"provider_calls":calls,
        "test_x_accessed":test_x_accessed,"y_accessed":false,"physical_independence":"unverified",
        "physical_id_encoding":"type-preserving JSON scalar of declared specimen/physical_sample_id; not verified identity"});
    let limitations = vec!["The manifest and metadata are declarations; physical and reference independence remain unverified.",
        "Unknown metadata origin or target derivation remains unknown; eligibility is not verification that a column is independent of targets.",
        "Preflight 0.1.6 intrinsic integrity is exploratory alpha evidence; availability and execution do not establish scientific qualification.",
        "A negative audit does not certify independence or future predictive performance.",
        "Inspecting test X may influence decisions; this operation performs no automatic selection or response refit.",
        "X-M association, tolerance duplicates and train-fitted PCA query projection are not qualified by this browser protocol.",
        "Embedded browser_x.v1 evidence describes exactly the wrapper receipt population; the scoped receipt determines train versus transductive use."];
    let mut claims = vec!["Documented access and owner evidence for the exact receipt population; no Y value admitted."];
    if r.fit == Fit::Transductive {
        claims.push("Explicitly consented descriptive transductive train+test fit; no prospective train-only support claim.");
    }
    let mut result = json!({"protocol_version":RESULT_PROTOCOL,"operation":r.operation,"diagnostic":r.diagnostic,
        "status":status,"reason":reason,"value":value,"receipt":receipt,"supported_claims":claims,
        "limitations":limitations,"action":"Review provenance, declared dependencies and operation limitations before changing validation or interpreting support."});
    // Failed owner validation retains its original issues as evidence. It does
    // not claim a computed scientific value, even when documentary data survive.
    if status == "error" || status == "unavailable" {
        let evidence = result["value"].take();
        result["receipt"]["noncomputed_evidence"] = evidence;
        result["value"] = Value::Null;
    }
    result["receipt"]["receipt_sha256"] = json!(digest(&result["receipt"]));
    Ok(result)
}
