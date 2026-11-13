//! Bounded, X-only browser protocol. All numerical kernels are public Preflight providers.
//! This additive transport does not replay or replace historical Domains protocols.
use crate::hash;
use nirs4all_preflight::{
    ClusterSelection, HdbscanRequest, MethodsProvider, NearestNeighborsRequest, PcaRequest,
    ProviderError, ProviderErrorKind, SummaryRequest,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

pub const PROTOCOL: &str = "domains.browser_x.v1";
pub const MAX_CELLS: usize = 1_000_000;
pub const MAX_ROWS: usize = 2_000;
pub const MAX_PRODUCTS: usize = 25_000_000;
pub const MAX_JSON_BYTES: usize = 32 * 1024 * 1024;

#[derive(Debug, Clone, Copy, Default, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum PredictionIntent {
    Study,
    KnownAcquisitions,
    NewSpecimens,
    NewGroups,
    NewContext,
    #[default]
    Unknown,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BrowserRequest {
    pub schema_version: u32,
    pub dataset_id: String,
    pub source_id: String,
    /// Declared hash of the exact source bytes; never inferred from the dataset name.
    pub content_sha256: String,
    pub observation_ids: Vec<String>,
    pub axis: Vec<f64>,
    pub axis_unit: String,
    pub spectra: Vec<Vec<f64>>,
    /// Declared groups are preserved as exclusions, never certified as independent units.
    #[serde(default)]
    pub group_ids: Option<Vec<String>>,
    #[serde(default)]
    pub prediction_intent: PredictionIntent,
}

pub fn parse(input: &str) -> Result<BrowserRequest, String> {
    if input.len() > MAX_JSON_BYTES {
        return Err("JSON_MEMORY_BUDGET_EXCEEDED".into());
    }
    let request = serde_json::from_str(input).map_err(|e| format!("INVALID_BROWSER_INPUT:{e}"))?;
    validate(&request)?;
    Ok(request)
}

pub fn validate(r: &BrowserRequest) -> Result<(), String> {
    let n = r.spectra.len();
    let p = r.axis.len();
    if r.schema_version != 1
        || r.dataset_id.trim().is_empty()
        || r.source_id.trim().is_empty()
        || r.axis_unit.trim().is_empty()
        || r.content_sha256.len() != 64
        || !r.content_sha256.bytes().all(|b| b.is_ascii_hexdigit())
        || n < 3
        || p == 0
        || r.observation_ids.len() != n
        || r.observation_ids.iter().any(|v| v.trim().is_empty())
        || r.observation_ids.iter().collect::<BTreeSet<_>>().len() != n
        || r.axis.iter().any(|v| !v.is_finite())
        || !(r.axis.windows(2).all(|w| w[0] < w[1]) || r.axis.windows(2).all(|w| w[0] > w[1]))
        || r.spectra
            .iter()
            .any(|row| row.len() != p || row.iter().any(|v| !v.is_finite()))
        || r.group_ids
            .as_ref()
            .is_some_and(|g| g.len() != n || g.iter().any(|v| v.trim().is_empty()))
    {
        return Err("INVALID_SCOPED_BROWSER_X_INPUT".into());
    }
    if n > MAX_ROWS || n.checked_mul(p).is_none_or(|cells| cells > MAX_CELLS) {
        return Err("FULL_POPULATION_BROWSER_BUDGET_EXCEEDED".into());
    }
    Ok(())
}

fn computed(value: Value) -> Value {
    json!({"status":"computed","reason":null,"value":value})
}
fn unavailable(reason: &str) -> Value {
    json!({"status":"unavailable","reason":reason,"value":null})
}
fn failure(error: ProviderError) -> Value {
    let status = if error.kind == ProviderErrorKind::Unsupported {
        "unsupported"
    } else {
        "error"
    };
    json!({"status":status,"reason":error.reason,"value":null})
}
fn malformed() -> Value {
    failure(ProviderError::internal("INVALID_PROVIDER_RESPONSE"))
}
/// JavaScript writes 1.0 as 1 and -0.0 as 0. Normalize numeric encoding
/// before hashing, without changing scientific output values.
fn evidence_hash(scope: &Value, metrics: &Value) -> Result<String, String> {
    fn canonical(value: &Value) -> Result<Value, String> {
        Ok(match value {
            Value::Number(number) => {
                let number = number.as_f64().ok_or("INVALID_EVIDENCE_NUMBER")?;
                let bits = if number == 0. { 0 } else { number.to_bits() };
                json!({"number":format!("{bits:016x}")})
            }
            Value::Array(items) => {
                json!({"array":items.iter().map(canonical).collect::<Result<Vec<_>, _>>()?})
            }
            Value::Object(items) => json!({"object":items
                    .iter()
                    .map(|(key, value)| Ok((key.clone(), canonical(value)?)))
                    .collect::<Result<serde_json::Map<String,Value>, String>>()?}),
            value => json!({"scalar":value}),
        })
    }
    serde_json::to_vec(&canonical(&json!({"scope":scope,"metrics":metrics}))?)
        .map(|bytes| hash(&bytes))
        .map_err(|e| e.to_string())
}
fn summary(provider: &impl MethodsProvider, values: Vec<f64>) -> Value {
    if values.is_empty() {
        return unavailable("EMPTY_SUMMARY_POPULATION");
    }
    match provider.summary(&SummaryRequest {
        values: values.clone(),
    }) {
        Ok(s)
            if s.count == values.len()
                && [s.min, s.max, s.mean, s.q25, s.median, s.q75]
                    .iter()
                    .all(|v| v.is_finite())
                && s.sample_sd.is_none_or(|v| v.is_finite() && v >= 0.) =>
        {
            computed(json!(s))
        }
        Ok(_) => malformed(),
        Err(e) => failure(e),
    }
}
fn groups(r: &BrowserRequest) -> Vec<i64> {
    let mut mapping = BTreeMap::<&str, i64>::new();
    r.group_ids.as_ref().map_or_else(
        || (0..r.spectra.len() as i64).collect(),
        |ids| {
            ids.iter()
                .map(|id| {
                    let next = mapping.len() as i64;
                    *mapping.entry(id.as_str()).or_insert(next)
                })
                .collect()
        },
    )
}

fn neighbors(provider: &impl MethodsProvider, rows: &[Vec<f64>], group_ids: &[i64]) -> Value {
    let n = rows.len();
    let p = rows[0].len();
    if n.checked_mul(n)
        .and_then(|v| v.checked_mul(p))
        .is_none_or(|v| v > MAX_PRODUCTS)
    {
        return unavailable("FULL_REFERENCE_NEIGHBOR_WORK_BUDGET_EXCEEDED");
    }
    let k = 8.min(n - 1);
    match provider.nearest_neighbors(&NearestNeighborsRequest {
        query: rows.to_vec(),
        reference: rows.to_vec(),
        query_group_ids: group_ids.to_vec(),
        reference_group_ids: group_ids.to_vec(),
        k,
    }) {
        Err(e) => failure(e),
        Ok(v) => {
            if v.indices.len() != n
                || v.distances.len() != n
                || v.indices.iter().any(|r| r.len() != k)
                || v.distances.iter().any(|r| r.len() != k)
            {
                return malformed();
            }
            let mut distances = Vec::new();
            for (i, (indices, values)) in v.indices.iter().zip(&v.distances).enumerate() {
                let mut seen = BTreeSet::new();
                for (&index, distance) in indices.iter().zip(values) {
                    match (index, distance) {
                        (-1, None) => {}
                        (j, Some(d))
                            if j >= 0
                                && (j as usize) < n
                                && *d >= 0.
                                && d.is_finite()
                                && group_ids[i] != group_ids[j as usize]
                                && seen.insert(j) => {}
                        _ => return malformed(),
                    }
                }
                if let Some(d) = values[0] {
                    distances.push(d);
                }
            }
            computed(
                json!({"n_reference":n,"n_query":n,"k":k,"approximate":false,
                "reference_population_preserved":true,"rows_with_neighbor":distances.len(),
                "first_neighbor_distance_summary":summary(provider,distances),
                "exclusion":"equal declared group, otherwise observation self", "backend_version":v.backend_version}),
            )
        }
    }
}

/// Descriptive full-source fit, with no Y field and no predictive train/test claim.
pub fn analyze(r: &BrowserRequest, provider: &impl MethodsProvider) -> Result<Value, String> {
    validate(r)?;
    let n = r.spectra.len();
    let p = r.axis.len();
    let k = 20.min(p).min(n - 1);
    let scope = json!({"dataset_id":r.dataset_id,"source_id":r.source_id,
        "content_sha256":r.content_sha256,"n_observations":n,"n_bands":p,
        "axis_unit":r.axis_unit,"axis_sha256":hash(&serde_json::to_vec(&r.axis).map_err(|e|e.to_string())?),
        "observation_ids_sha256":hash(&serde_json::to_vec(&r.observation_ids).map_err(|e|e.to_string())?),
        "population":"complete imported source; descriptive full-X fit",
        "split":"none; no predictive evaluation","target":"absent",
        "identity_evidence":"observation_identity_only",
        "groups":"declared exclusions only; independent physical/reference units unverified",
        "metadata_coverage":"not carried by this live protocol; original availability unknown",
        "n_declared_groups":r.group_ids.as_ref().map(|ids|ids.iter().collect::<BTreeSet<_>>().len()),
        "policy":"no imputation, aggregation, resampling or axis transformation"});
    // Intent does not enter the numerical fingerprint or any provider request.
    let mut numerical_input = r.clone();
    numerical_input.prediction_intent = PredictionIntent::Unknown;
    let input_sha256 = hash(&serde_json::to_vec(&numerical_input).map_err(|e| e.to_string())?);
    let raw_neighbors = neighbors(provider, &r.spectra, &groups(r));
    let pca;
    let mut projected_neighbors = unavailable("PCA_UNAVAILABLE");
    let mut density = unavailable("PCA_UNAVAILABLE");
    // Include full-moment/SVD work, rather than counting only retained score columns.
    let pca_products = n.checked_mul(p).and_then(|v| v.checked_mul(n.min(p)));
    if pca_products.is_none_or(|v| v > MAX_PRODUCTS) {
        pca = unavailable("PCA_WORK_BUDGET_EXCEEDED");
    } else {
        match provider.pca(&PcaRequest {
            source_id: r.source_id.clone(),
            sample_ids: r.observation_ids.clone(),
            matrix: r.spectra.clone(),
            n_components: k,
        }) {
            Err(e) => pca = failure(e),
            Ok(fit) => {
                if fit.eigenvalues.len() != k
                    || fit.unresolved.len() != k
                    || fit.scores.len() != n
                    || fit
                        .scores
                        .iter()
                        .any(|row| row.len() != k || row.iter().any(|v| !v.is_finite()))
                    || fit.eigenvalues.iter().any(|v| !v.is_finite() || *v < 0.)
                    || fit.full_moments.iter().any(|v| !v.is_finite() || *v < 0.)
                    || !fit.resolution.is_finite()
                    || fit.resolution < 0.
                {
                    pca = malformed();
                } else if fit.full_moments[0] <= 0. || fit.full_moments[1] <= 0. {
                    pca = unavailable("ZERO_SPECTRAL_VARIANCE");
                } else {
                    let resolved = fit.resolved();
                    if resolved.eigenvalues.is_empty() {
                        pca = unavailable("NO_RESOLVED_PCA_COMPONENT");
                    } else {
                        pca = computed(
                            json!({"eigenvalues":resolved.eigenvalues,"scores":resolved.scores,
                            "full_moments":fit.full_moments,"resolution":fit.resolution,"unresolved":fit.unresolved,
                            "n_components_requested":k,"n_components_resolved":resolved.eigenvalues.len(),
                            "backend_version":fit.backend_version,
                            "scope":"full imported X; not a held-out projection"}),
                        );
                        projected_neighbors = neighbors(provider, &resolved.scores, &groups(r));
                        let min_cluster_size = 8;
                        let min_samples = 4;
                        density = if n < min_cluster_size {
                            unavailable("INSUFFICIENT_ROWS_FOR_FROZEN_DENSITY_SETTING")
                        } else if n
                            .checked_mul(n)
                            .and_then(|v| v.checked_mul(resolved.eigenvalues.len()))
                            .is_none_or(|v| v > MAX_PRODUCTS)
                        {
                            unavailable("DENSITY_WORK_BUDGET_EXCEEDED")
                        } else {
                            match provider.hdbscan(&HdbscanRequest {
                                matrix: resolved.scores,
                                min_cluster_size,
                                min_samples,
                                selection: ClusterSelection::Eom,
                                allow_single_cluster: false,
                            }) {
                                Err(e) => failure(e),
                                Ok(d) => {
                                    let clusters: BTreeSet<_> =
                                        d.labels.iter().copied().filter(|v| *v >= 0).collect();
                                    if d.labels.len() != n
                                        || d.membership.len() != n
                                        || d.outlier_scores.len() != n
                                        || d.labels.iter().any(|v| *v < -1)
                                        || clusters.iter().copied().ne(0..clusters.len() as i64)
                                        || d.persistence.len() != clusters.len()
                                        || d.membership
                                            .iter()
                                            .any(|v| !v.is_finite() || !(0. ..=1.).contains(v))
                                        || d.persistence
                                            .iter()
                                            .any(|v| !v.is_finite() || !(0. ..=1.).contains(v))
                                        || d.outlier_scores
                                            .iter()
                                            .flatten()
                                            .any(|v| !v.is_finite() || !(0. ..=1.).contains(v))
                                    {
                                        malformed()
                                    } else {
                                        computed(
                                            json!({"labels":d.labels,"membership":d.membership,
                                            "n_clusters":clusters.len(),"noise_count":d.labels.iter().filter(|v|**v<0).count(),
                                            "persistence":d.persistence,"persistence_summary":summary(provider,d.persistence.clone()),
                                            "min_cluster_size":min_cluster_size,"min_samples":min_samples,
                                            "selection":"eom","allow_single_cluster":false,
                                            "backend_version":d.backend_version,
                                            "qualification":"one-fit descriptor; not D1 companion or resampling stability",
                                            "support_unit":"observation; independent physical/reference support unknown"}),
                                        )
                                    }
                                }
                            }
                        };
                    }
                }
            }
        }
    }
    let metrics = json!({"pca":pca,"raw_neighbors":raw_neighbors,"projected_neighbors":projected_neighbors,
        "density":density,"metadata_factor_association":unavailable("NO_QUALIFIED_BROWSER_METADATA_PROTOCOL"),
        "resampling_stability":unavailable("NO_RESAMPLING_RUN"),
        "parameter_sensitivity":unavailable("NO_PARAMETER_COMPARISON"),
        "predictive_performance":unavailable("X_ONLY_NO_PREDICTIVE_EVALUATION")});
    let mut findings = vec![
        json!({"observation":format!("Complete imported population: {n} observations and {p} original bands."),
        "confidence":"exact validated input counts","consequence":"Counts describe observations, not independent physical or reference units.",
        "action":"Confirm specimen, reference and context identities before designing predictive evaluation."}),
    ];
    if metrics["pca"]["status"] == "computed" {
        findings.push(json!({"observation":format!("PCA returned {} resolved components from the full imported X population.",metrics["pca"]["value"]["n_components_resolved"]),
            "confidence":"computed by Methods; scope conditional on this representation",
            "consequence":"A projection describes spectral geometry and can hide differences in omitted axes.",
            "action":"Read original-axis and projected neighborhoods separately; do not infer predictive transfer from the projection."}));
    }
    if metrics["density"]["status"] == "computed" {
        let count = metrics["density"]["value"]["n_clusters"]
            .as_u64()
            .unwrap_or(0);
        findings.push(json!({"observation":format!("One density setting returned {count} clusters and {} noise observations.",metrics["density"]["value"]["noise_count"]),
            "confidence":"within-fit descriptive evidence; resampling and parameter sensitivity unavailable",
            "consequence":if count==0 {"No selected cluster does not establish low structural dependence."} else {"Selected groups and membership strengths do not identify biological mechanisms or calibrated probabilities."},
            "action":"Corroborate any spectral groups with source metadata and declared independent units before interpretation."}));
    } else {
        findings.push(json!({"observation":"Density evidence was not computed for this imported source.",
            "confidence":"explicit provider or prerequisite state","consequence":"Missing density evidence supports neither structure nor low-risk certification.",
            "action":"Read the preserved density reason before considering another separately specified analysis."}));
    }
    let evidence_sha256 = evidence_hash(&scope, &metrics)?;
    let mut report = json!({"schema_version":1,"protocol_version":PROTOCOL,"engine_version":env!("CARGO_PKG_VERSION"),
        "status":"computed","scope":scope,"input_sha256":input_sha256,"evidence_sha256":evidence_sha256,
        "metrics":metrics,"findings":findings,"capabilities":provider.capabilities(),"test_target_accessed":false,
        "raw_spectra_included":false,"interpretation":null,
        "limitations":["Full-source descriptive fit is transductive and establishes no held-out performance.",
            "Declared groups exclude neighbors but do not establish independent physical or reference units.",
            "Density membership is a strength, not a probability. No cluster does not establish low risk.",
            "Live interpretation is a bounded browser reading, not the saved D1-D6.1 companion APIs."]});
    report["interpretation"] = interpret(&report, r.prediction_intent)?;
    Ok(report)
}

/// Pure interpretation: preserves the exact numerical evidence and performs no provider calls.
pub fn interpret(report: &Value, intent: PredictionIntent) -> Result<Value, String> {
    if report["protocol_version"] != PROTOCOL || report["schema_version"] != 1 {
        return Err("INCOMPATIBLE_BROWSER_REPORT".into());
    }
    let expected = evidence_hash(&report["scope"], &report["metrics"])?;
    if report["evidence_sha256"] != expected {
        return Err("BROWSER_EVIDENCE_HASH_MISMATCH".into());
    }
    let (question, action) = match intent {
        PredictionIntent::Study => ("Within-experiment relation", "Preserve repeats and reference dependencies in any future evaluation."),
        PredictionIntent::KnownAcquisitions => ("New acquisitions in a known context", "Declare whether acquisitions share specimens and references before a split."),
        PredictionIntent::NewSpecimens => ("Prediction for new specimens", "Obtain specimen and reference dependency identities before specimen holdout."),
        PredictionIntent::NewGroups => ("Prediction for unseen declared groups", "Verify group meaning and indivisible dependencies before group holdout."),
        PredictionIntent::NewContext => ("Prediction outside the experimental context", "Declare the unseen context and obtain compatible external or context holdout evidence."),
        PredictionIntent::Unknown => ("Prediction objective unspecified", "Declare the intended population; keep conditional interpretations separate."),
    };
    let conditional_scenarios = if intent == PredictionIntent::Unknown {
        vec![
            json!({"intended_use":"study","question":"If the objective is a within-experiment study, which repeats and references must remain together?", "not_established":"Predictive performance and independent support are not established by X-only geometry."}),
            json!({"intended_use":"new_specimens","question":"If the objective is new specimens, are their physical and reference identities available for a compatible holdout?", "not_established":"New-specimen performance and dependency separation have not been tested."}),
            json!({"intended_use":"new_context","question":"If the objective is an unseen context, which context must be excluded and which evidence matches it?", "not_established":"External-context transfer and a universally preferable split are not established."}),
        ]
    } else {
        vec![]
    };
    Ok(
        json!({"protocol_version":"domains.browser_reading.v1","prediction_intent":intent,
        "declaration_only":true,"evidence_sha256":expected,"scope":report["scope"],
        "conditional_scenarios":conditional_scenarios,
        "boundaries":{"physical_independence_verified":false,"predictive_performance_established":false,
            "universally_preferred_split":null,"authorization_granted":false,"new_execution":false},
        "observation":question,"confidence":"conditional descriptive evidence",
        "consequence":"X-only geometry does not establish predictive transfer, causal mechanism or independent support.",
        "action":action,"readiness":{"status":"unavailable","reason":"NO_VERIFIED_INPUTS_PROTOCOL_AUTHORIZATION_OR_EXECUTION_RECEIPT","value":null},
        "execution":"not_executed","qualification":"bounded live reading; not D2/D6/D6.1 companion parity"}),
    )
}
