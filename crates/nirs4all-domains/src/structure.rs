//! Frozen task-specific PCA/HDBSCAN stability; all numerical kernels belong to Methods.
use crate::{
    contract::*,
    hash,
    methods::{HdbscanOutput, HdbscanParameters, Methods, NativeFailure},
    units, validate,
};
use nirs4all_preflight::{MethodsProvider, SummaryRequest};
use rand::{seq::SliceRandom, SeedableRng};
use rand_chacha::ChaCha8Rng;
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    path::Path,
};

pub const STRUCTURE_PROTOCOL: &str = "domains.structure.v0.1";

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct StructureConfig {
    pub schema_version: u32,
    pub seed: u64,
    pub pca_max_components: usize,
    pub pca_variance_fraction: f64,
    pub replicates: usize,
    pub component_fraction: f64,
    pub primary: HdbscanParameters,
    pub sensitivity: Vec<HdbscanParameters>,
    pub compare_native: bool,
}
impl StructureConfig {
    pub fn validate(&self) -> Result<(), String> {
        if self.schema_version != 1
            || !(1..=200).contains(&self.replicates)
            || self.sensitivity.len() > 4
            || !(1..=50).contains(&self.pca_max_components)
            || !self.pca_variance_fraction.is_finite()
            || !(0. ..=1.).contains(&self.pca_variance_fraction)
            || self.pca_variance_fraction == 0.
            || !self.component_fraction.is_finite()
            || !(0.5..=0.9).contains(&self.component_fraction)
            || std::iter::once(&self.primary)
                .chain(&self.sensitivity)
                .any(|p| {
                    p.min_cluster_size < 2
                        || p.min_cluster_size > 10000
                        || p.min_samples < 1
                        || p.min_samples > 10000
                })
        {
            return Err("INVALID_BOUNDED_STRUCTURE_CONFIG".into());
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum StructuralClassification {
    RobustStructure,
    FragileStructure,
    Continuum,
    InsufficientInformation,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct ScalarEvidence {
    pub status: Status,
    pub reason: Option<String>,
    pub value: Option<f64>,
    pub physical_sample_ids: Vec<String>,
    pub n_dependency_components: usize,
}
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct PartitionComparison {
    pub common_physical_sample_ids: Vec<String>,
    pub ari_including_noise: ScalarEvidence,
    pub ari_excluding_noise: ScalarEvidence,
    pub noise_status_agreement: Option<f64>,
}
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct StructureFit {
    pub observation_ids: Vec<String>,
    pub physical_sample_ids: Vec<String>,
    pub dependency_component_ids: Vec<String>,
    pub pca: Value,
    pub scores: Vec<Vec<f64>>,
    pub hdbscan: HdbscanOutput,
    pub noise_fraction: f64,
}
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct StructureReplicate {
    pub draw: usize,
    pub selected_components: Vec<String>,
    pub physical_sample_ids: Vec<String>,
    pub status: Status,
    pub reason: Option<String>,
    pub failure: Option<NativeFailure>,
    pub fit: Option<StructureFit>,
    pub comparison: Option<PartitionComparison>,
}
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct StructureSetting {
    pub parameters: HdbscanParameters,
    pub status: Status,
    pub reason: Option<String>,
    pub failure: Option<NativeFailure>,
    pub reference: Option<StructureFit>,
    pub comparison_to_primary: Option<PartitionComparison>,
    pub replicates: Vec<StructureReplicate>,
    pub stability: Value,
}
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct StructureReport {
    pub schema_version: u32,
    pub protocol_version: String,
    pub engine_version: String,
    pub context: Context,
    pub data_origin: String,
    pub input_provenance: BTreeMap<String, String>,
    pub status: Status,
    pub reason: Option<String>,
    pub provider: Option<Value>,
    pub configuration: StructureConfig,
    pub population: Value,
    pub representation: Value,
    pub settings: Vec<StructureSetting>,
    pub classification: StructuralClassification,
    pub classification_evidence: Value,
    pub native_comparison: Value,
    pub held_out_assignment: Value,
    pub shortcut_risk_evidence: Value,
    pub test_target_accessed: bool,
    pub limitations: Vec<String>,
}

fn labels(f: &StructureFit) -> BTreeMap<String, i64> {
    f.physical_sample_ids
        .iter()
        .cloned()
        .zip(f.hdbscan.labels.iter().copied())
        .collect()
}

/// ID-matched public Methods ARI; positional comparisons are deliberately not accepted.
pub fn compare_partitions(
    methods: &Methods,
    a: &BTreeMap<String, i64>,
    b: &BTreeMap<String, i64>,
    components: &BTreeMap<String, String>,
    reference_size: usize,
) -> Result<PartitionComparison, NativeFailure> {
    let common: Vec<_> = a.keys().filter(|id| b.contains_key(*id)).cloned().collect();
    if common.iter().any(|id| !components.contains_key(id)) {
        return Err(NativeFailure::transport(
            "MATCHED_ID_HAS_NO_DEPENDENCY_COMPONENT",
        ));
    }
    let evidence = |ids: Vec<String>| -> Result<ScalarEvidence, NativeFailure> {
        let ncomponents = ids
            .iter()
            .map(|id| &components[id])
            .collect::<BTreeSet<_>>()
            .len();
        let av: Vec<_> = ids.iter().map(|id| a[id]).collect();
        let bv: Vec<_> = ids.iter().map(|id| b[id]).collect();
        let nontrivial = |v: &Vec<i64>| {
            let k = v.iter().collect::<BTreeSet<_>>().len();
            k >= 2 && k < v.len()
        };
        let reason = if ids.len() < 20 || ids.len() * 2 < reference_size || ncomponents < 10 {
            Some("INSUFFICIENT_COMMON_PHYSICAL_IDS_OR_COMPONENTS")
        } else if !nontrivial(&av) || !nontrivial(&bv) {
            Some("TRIVIAL_MATCHED_PARTITION")
        } else {
            None
        };
        let value = if reason.is_none() {
            methods.adjusted_rand_index(&av, &bv)?
        } else {
            None
        };
        Ok(ScalarEvidence {
            status: if value.is_some() {
                Status::Computed
            } else {
                Status::InsufficientData
            },
            reason: if value.is_some() {
                None
            } else {
                Some(reason.unwrap_or("NATIVE_ARI_UNDEFINED").into())
            },
            value,
            physical_sample_ids: ids,
            n_dependency_components: ncomponents,
        })
    };
    let agreement = if common.is_empty() {
        None
    } else {
        Some(
            common
                .iter()
                .filter(|id| (a[*id] < 0) == (b[*id] < 0))
                .count() as f64
                / common.len() as f64,
        )
    };
    let clustered = common
        .iter()
        .filter(|id| a[*id] >= 0 && b[*id] >= 0)
        .cloned()
        .collect();
    Ok(PartitionComparison {
        common_physical_sample_ids: common.clone(),
        ari_including_noise: evidence(common)?,
        ari_excluding_noise: evidence(clustered)?,
        noise_status_agreement: agreement,
    })
}

struct Projection {
    pca: Value,
    scores: Vec<Vec<f64>>,
}
fn projection(
    methods: &Methods,
    rows: &[&Observation],
    task: &Task,
    cfg: &StructureConfig,
    keep_state: bool,
) -> Result<Projection, NativeFailure> {
    let x = rows
        .iter()
        .map(|r| {
            r.x.iter()
                .map(|v| {
                    v.filter(|v| v.is_finite())
                        .ok_or_else(|| NativeFailure::transport("INCOMPLETE_TRAIN_X"))
                })
                .collect::<Result<Vec<_>, _>>()
        })
        .collect::<Result<Vec<_>, _>>()?;
    let k = cfg
        .pca_max_components
        .min(task.axis.len())
        .min(rows.len().saturating_sub(1));
    let fitted = if task.policy.pca_backend == PcaBackend::Flexible {
        methods.fit_flexible(&x, k)
    } else {
        methods.fit_pca(&x, k)
    }
    .map_err(NativeFailure::transport)?;
    if !fitted.covariance_trace.is_finite() {
        return Err(NativeFailure::transport("NONFINITE_TRAIN_PCA_TRACE"));
    }
    if fitted.covariance_trace <= 0. {
        return Err(NativeFailure::transport("DEGENERATE_TRAIN_PCA_ZERO_TRACE"));
    }
    let mut d = 0;
    let mut cumulative = 0.;
    for e in &fitted.eigenvalues {
        d += 1;
        cumulative += e;
        if cumulative / fitted.covariance_trace >= cfg.pca_variance_fraction {
            break;
        }
    }
    if !(cumulative / fitted.covariance_trace).is_finite() {
        return Err(NativeFailure::transport(
            "NONFINITE_RETAINED_PCA_VARIANCE_FRACTION",
        ));
    }
    let scores = fitted
        .train_scores
        .iter()
        .map(|r| r[..d].to_vec())
        .collect();
    let state = json!({"mean":fitted.mean,"loadings":fitted.loadings[..d],"eigenvalues":fitted.eigenvalues[..d]});
    let mut pca = json!({"fit_partition":"train","fit_x_sha256":hash(&serde_json::to_vec(&x).unwrap()),
        "state_sha256":hash(&serde_json::to_vec(&state).unwrap()),"n_components":d,"retained_variance_fraction":cumulative/fitted.covariance_trace,
        "requested_variance_reached":cumulative/fitted.covariance_trace>=cfg.pca_variance_fraction,
        "covariance_trace":fitted.covariance_trace,"full_moments":fitted.full_moments,
        "full_moments_unavailable_reason":fitted.full_moments_unavailable_reason,"backend":fitted.backend,
        "preprocessing":"Methods train centering; no whitening or autoscaling",
        "solver":"Methods automatic solver; solver flag not exposed; deterministic row order"});
    if keep_state {
        pca["fitted_state"] = state;
    }
    Ok(Projection { pca, scores })
}
fn cluster(
    methods: &Methods,
    rows: &[&Observation],
    components: &BTreeMap<String, String>,
    pca: &Projection,
    parameters: &HdbscanParameters,
) -> Result<StructureFit, NativeFailure> {
    let hdbscan = methods.hdbscan(&pca.scores, parameters)?;
    let noise_fraction =
        hdbscan.labels.iter().filter(|&&v| v < 0).count() as f64 / rows.len() as f64;
    Ok(StructureFit {
        observation_ids: rows.iter().map(|r| r.observation_id.clone()).collect(),
        physical_sample_ids: rows.iter().map(|r| r.physical_sample_id.clone()).collect(),
        dependency_component_ids: rows
            .iter()
            .map(|r| components[&r.physical_sample_id].clone())
            .collect(),
        pca: pca.pca.clone(),
        scores: pca.scores.clone(),
        hdbscan,
        noise_fraction,
    })
}
fn summary(methods: &Methods, values: Vec<f64>) -> Result<Value, NativeFailure> {
    if values.is_empty() {
        return Ok(
            json!({"status":"insufficient_data","reason":"NO_ELIGIBLE_VALUES","value":null}),
        );
    }
    let result = methods
        .provider
        .summary(&SummaryRequest {
            values: values.clone(),
        })
        .map_err(|e| NativeFailure::transport(e.0))?;
    let mut ordered = values;
    ordered.sort_by(f64::total_cmp);
    let p10 = ordered[((ordered.len() as f64 * 0.1).ceil() as usize).saturating_sub(1)];
    Ok(json!({"status":"computed","reason":null,"value":result,"p10_nearest_rank":p10}))
}
fn summarize_setting(
    methods: &Methods,
    setting: &StructureSetting,
) -> Result<Value, NativeFailure> {
    let Some(reference) = &setting.reference else {
        return Ok(json!({"status":"unavailable","reason":"REFERENCE_FIT_FAILED","value":null}));
    };
    let ref_labels = labels(reference);
    let successful: Vec<_> = setting
        .replicates
        .iter()
        .filter(|r| r.fit.is_some())
        .collect();
    let mut inclusion: BTreeMap<_, usize> = ref_labels.keys().map(|id| (id.clone(), 0)).collect();
    let mut pairs = BTreeMap::<(String, String), (usize, usize)>::new();
    let mut counts = BTreeMap::<usize, usize>::new();
    for r in &successful {
        let fit = r.fit.as_ref().unwrap();
        *counts.entry(fit.hdbscan.n_clusters).or_default() += 1;
        let map = labels(fit);
        let ids: Vec<_> = map.keys().collect();
        for id in &ids {
            *inclusion.get_mut(*id).unwrap() += 1;
        }
        for i in 0..ids.len() {
            for j in i + 1..ids.len() {
                let pair = pairs.entry((ids[i].clone(), ids[j].clone())).or_default();
                pair.0 += 1;
                if map[ids[i]] >= 0 && map[ids[i]] == map[ids[j]] {
                    pair.1 += 1;
                }
            }
        }
    }
    let mut clusters = BTreeMap::new();
    for c in 0..reference.hdbscan.n_clusters as i64 {
        let ids: Vec<_> = ref_labels
            .iter()
            .filter(|(_, v)| **v == c)
            .map(|(id, _)| id.clone())
            .collect();
        let mut support = Vec::new();
        let mut missing = 0;
        for i in 0..ids.len() {
            for j in i + 1..ids.len() {
                match pairs.get(&(ids[i].clone(), ids[j].clone())) {
                    Some(&(n, k)) if n > 0 => support.push(k as f64 / n as f64),
                    _ => missing += 1,
                }
            }
        }
        clusters.insert(c.to_string(),json!({"physical_sample_ids":ids,"pair_support":summary(methods,support)?,"unobserved_pairs":missing}));
    }
    let including = successful
        .iter()
        .filter_map(|r| r.comparison.as_ref()?.ari_including_noise.value)
        .collect::<Vec<_>>();
    let excluding = successful
        .iter()
        .filter_map(|r| r.comparison.as_ref()?.ari_excluding_noise.value)
        .collect::<Vec<_>>();
    Ok(
        json!({"successful_draws":successful.len(),"attempted_draws":setting.replicates.len(),
        "eligible_ari_including_noise":including.len(),"eligible_ari_excluding_noise":excluding.len(),
        "ari_including_noise":summary(methods,including)?,"ari_excluding_noise":summary(methods,excluding)?,
        "noise_status_agreement":summary(methods,successful.iter().filter_map(|r|r.comparison.as_ref()?.noise_status_agreement).collect())?,
        "noise_fraction":summary(methods,successful.iter().map(|r|r.fit.as_ref().unwrap().noise_fraction).collect())?,
        "cluster_count_distribution":counts,"sample_successful_inclusions":inclusion,"reference_clusters":clusters,
        "co_membership_pairs":pairs.into_iter().map(|((a,b),(n,k))|json!({"physical_ids":[a,b],"successful_joint_inclusions":n,"same_nonnoise_cluster":k,"support":k as f64/n as f64})).collect::<Vec<_>>(),
        "support_interpretation":"Conditional descriptive co-membership frequency, not a calibrated membership probability"}),
    )
}

fn stable(setting: &StructureSetting) -> bool {
    let Some(r) = &setting.reference else {
        return false;
    };
    let s = &setting.stability;
    let n = setting.replicates.len() as f64;
    let minimum = s["sample_successful_inclusions"]
        .as_object()
        .and_then(|v| v.values().filter_map(Value::as_u64).min())
        .unwrap_or(0);
    r.hdbscan.n_clusters >= 2
        && r.noise_fraction <= 0.4
        && s["eligible_ari_including_noise"].as_u64().unwrap_or(0) as f64 >= 0.9 * n
        && s["ari_including_noise"]["value"]["median"]
            .as_f64()
            .unwrap_or(-1.)
            >= 0.9
        && s["ari_including_noise"]["p10_nearest_rank"]
            .as_f64()
            .unwrap_or(-1.)
            >= 0.8
        && s["noise_status_agreement"]["p10_nearest_rank"]
            .as_f64()
            .unwrap_or(-1.)
            >= 0.9
        && minimum >= 10
        && s["reference_clusters"].as_object().is_some_and(|m| {
            m.values().all(|c| {
                c["unobserved_pairs"] == 0
                    && c["pair_support"]["value"]["median"].as_f64().unwrap_or(-1.) >= 0.8
            })
        })
}
fn classify(methods: &Methods, report: &mut StructureReport) -> Result<(), NativeFailure> {
    let complete = report.configuration.replicates >= 20
        && report.settings.iter().all(|s| {
            s.reference.is_some()
                && s.stability["successful_draws"].as_u64().unwrap_or(0) as f64
                    >= 0.9 * report.configuration.replicates as f64
        });
    let stable_settings = report.settings.iter().map(stable).collect::<Vec<_>>();
    let grid_agreement = report.settings.iter().skip(1).all(|s| {
        s.comparison_to_primary.as_ref().is_some_and(|c| {
            c.ari_including_noise.value.is_some_and(|v| v >= 0.8)
                && c.noise_status_agreement.is_some_and(|v| v >= 0.9)
        })
    });
    let overlap = report.settings.iter().any(|s| {
        s.stability["eligible_ari_including_noise"]
            .as_u64()
            .unwrap_or(0) as f64
            >= 0.9 * report.configuration.replicates as f64
    });
    let nontrivial = report.settings.iter().any(|s| {
        s.reference
            .as_ref()
            .is_some_and(|r| r.hdbscan.n_clusters >= 2)
            || s.replicates
                .iter()
                .any(|r| r.fit.as_ref().is_some_and(|f| f.hdbscan.n_clusters >= 2))
    });
    let feasible_scales = report.settings.iter().all(|s| {
        let enough = |f: &StructureFit| {
            s.parameters.min_cluster_size.saturating_mul(2) <= f.physical_sample_ids.len()
        };
        s.reference.as_ref().is_some_and(enough)
            && s.replicates
                .iter()
                .filter_map(|r| r.fit.as_ref())
                .all(enough)
    });
    let mut continuum = false;
    let mut gap_evidence = Value::Null;
    if let Some(reference) = report.settings.first().and_then(|s| s.reference.as_ref()) {
        if reference.pca["n_components"] == 1
            && reference.pca["requested_variance_reached"] == true
            && reference.scores.len() >= 50
        {
            let mut positions = reference.scores.iter().map(|r| r[0]).collect::<Vec<_>>();
            positions.sort_by(f64::total_cmp);
            let gaps = positions
                .windows(2)
                .map(|v| v[1] - v[0])
                .collect::<Vec<_>>();
            let s = summary(methods, gaps)?;
            let v = &s["value"];
            continuum = feasible_scales
                && !nontrivial
                && v["min"].as_f64().unwrap_or(0.) > 0.
                && v["max"].as_f64().unwrap_or(f64::INFINITY)
                    <= 3. * v["median"].as_f64().unwrap_or(0.)
                && v["q75"].as_f64().unwrap_or(f64::INFINITY)
                    <= 1.5 * v["q25"].as_f64().unwrap_or(0.);
            gap_evidence = s;
        }
    }
    report.classification = if !complete {
        StructuralClassification::InsufficientInformation
    } else if stable_settings.iter().all(|v| *v) && grid_agreement {
        StructuralClassification::RobustStructure
    } else if continuum {
        StructuralClassification::Continuum
    } else if nontrivial && overlap {
        StructuralClassification::FragileStructure
    } else {
        StructuralClassification::InsufficientInformation
    };
    report.classification_evidence = json!({"adequate_execution":complete,"tested_scales_allow_multiple_clusters":feasible_scales,"stable_by_setting":stable_settings,"sensitivity_reference_agreement":grid_agreement,
        "adequate_nontrivial_ari_overlap_in_any_setting":overlap,"nontrivial_partition_detected":nontrivial,
        "regular_one_dimensional_gap_evidence":gap_evidence,"continuum_compatibility_gate":continuum,
        "interpretation":"Exploratory operational classification at frozen scales; no target association or causal shortcut conclusion"});
    Ok(())
}

fn native_comparison(
    methods: &Methods,
    task: &Task,
    mean: &StructureFit,
    components: &BTreeMap<String, String>,
    cfg: &StructureConfig,
) -> Result<Value, NativeFailure> {
    let wanted = mean.physical_sample_ids.iter().collect::<BTreeSet<_>>();
    let mut rows = task
        .observations
        .iter()
        .filter(|r| r.partition == Partition::Train && wanted.contains(&r.physical_sample_id))
        .collect::<Vec<_>>();
    rows.sort_by_key(|r| (&r.physical_sample_id, &r.observation_id));
    let mut groups = BTreeMap::<String, Vec<usize>>::new();
    for (i, r) in rows.iter().enumerate() {
        groups
            .entry(r.physical_sample_id.clone())
            .or_default()
            .push(i);
    }
    let counts = groups.values().map(Vec::len).collect::<BTreeSet<_>>();
    if counts.len() != 1 {
        return Ok(
            json!({"status":"unavailable","reason":"UNEQUAL_REPEAT_MULTIPLICITY_NATIVE_DENSITY_NOT_QUALIFIED","value":null}),
        );
    }
    let m = *counts.first().unwrap();
    let mut params = cfg.primary.clone();
    params.min_cluster_size *= m;
    params.min_samples = 1 + m * (params.min_samples - 1);
    let pca = projection(methods, &rows, task, cfg, true)?;
    let fit = cluster(methods, &rows, components, &pca, &params)?;
    let mut consensus = BTreeMap::new();
    let mut excluded = Vec::new();
    for (id, indices) in &groups {
        let values = indices
            .iter()
            .map(|&i| fit.hdbscan.labels[i])
            .collect::<BTreeSet<_>>();
        if values.len() == 1 {
            consensus.insert(id.clone(), *values.first().unwrap());
        } else {
            excluded.push(json!({"physical_sample_id":id,"acquisition_ids":indices.iter().map(|&i|&fit.observation_ids[i]).collect::<Vec<_>>(),"labels":values,"reason":"MIXED_ACQUISITION_CLUSTER_OR_NOISE_LABELS"}));
        }
    }
    let comparison = compare_partitions(
        methods,
        &labels(mean),
        &consensus,
        components,
        mean.physical_sample_ids.len(),
    )?;
    Ok(
        json!({"status":"computed","reason":null,"value":{"repeat_multiplicity":m,"scaled_parameters":params,"acquisition_fit":fit,
        "physical_consensus":consensus,"excluded_mixed_assignments":excluded,"comparison":comparison,
        "consensus_rule":"Unanimous labels including noise; mixed assignments excluded",
        "limitation":"Descriptive acquisition density with scaled nominal masses, not exact weighted HDBSCAN; no independent acquisition votes"}}),
    )
}

/// Separate structural report: canonical coverage/predictive report semantics are preserved.
pub fn characterize_structure(
    task: &Task,
    cfg: &StructureConfig,
    library: Option<&Path>,
) -> StructureReport {
    let mut report=StructureReport{schema_version:1,protocol_version:STRUCTURE_PROTOCOL.into(),engine_version:VERSION.into(),context:task.context.clone(),
        data_origin:task.data_origin.clone(),input_provenance:task.provenance.clone(),
        status:Status::Unavailable,reason:Some("METHODS_PROVIDER_NOT_CONFIGURED".into()),provider:None,configuration:cfg.clone(),
        population:Value::Null,representation:Value::Null,settings:vec![],classification:StructuralClassification::InsufficientInformation,
        classification_evidence:Value::Null,native_comparison:json!({"status":"unavailable","reason":"NATIVE_COMPARISON_NOT_REQUESTED_OR_REFERENCE_UNAVAILABLE","value":null}),
        held_out_assignment:json!({"status":"unavailable","reason":"NO_PUBLIC_QUALIFIED_HDBSCAN_OUT_OF_SAMPLE_ASSIGNMENT","value":null}),
        shortcut_risk_evidence:json!({"status":"unavailable","reason":"UNSUPERVISED_X_STRUCTURE_DOES_NOT_MEASURE_PREDICTIVE_RELIANCE","value":null}),
        test_target_accessed:false,limitations:vec!["Exploratory operational structural classification, not a universal taxonomy or shortcut probability.".into(),
            "Declared components do not independently establish biological or laboratory independence.".into(),
            "Native MST ties and PCA solver depend on deterministic canonical order; label values are arbitrary.".into(),
            "Membership strengths and resampling support are not calibrated probabilities.".into(),
            "All noise or a trivial cluster cannot establish robust structure. Test PCA projection does not assign HDBSCAN membership.".into()]};
    // Structural characterization is always pre-training, even for a host task
    // originally authored for post-evaluation. Hide targets before validation too.
    let mut scoped = task.clone();
    scoped.policy.audit_mode = AuditMode::PreTraining;
    for row in &mut scoped.observations {
        if row.partition == Partition::Test {
            row.y = None;
            row.category = None;
        }
    }
    if let Err(e) = cfg.validate().and_then(|()| validate(&scoped)) {
        report.status = Status::Error;
        report.reason = Some(e);
        return report;
    }
    let Some(path) = library else {
        return report;
    };
    let methods = match Methods::load(path) {
        Ok(m) => m,
        Err(e) => {
            report.reason = Some(e);
            return report;
        }
    };
    report.provider = Some(
        json!({"name":"nirs4all-methods","version":methods.version,"abi":methods.abi,
        "binary_sha256":std::fs::read(path).ok().map(|v|hash(&v)),"kernels":["FlexiblePCA or preflight PCA","n4m_cluster_hdbscan","n4m_preflight_adjusted_rand_index","n4m_preflight_summary_compute"]}),
    );
    if let Err(failure) = methods.clustering_capability() {
        report.reason = Some(failure.reason.clone());
        report.classification_evidence = json!({"failure":failure});
        return report;
    }
    match execute(&scoped, cfg, &methods, &mut report) {
        Ok(()) => {
            report.status = Status::Computed;
            report.reason = None;
        }
        Err(e) => {
            report.status =
                if e.reason.starts_with("INSUFFICIENT") || e.reason.starts_with("DEGENERATE") {
                    Status::InsufficientData
                } else {
                    Status::Error
                };
            report.reason = Some(e.reason.clone());
            report.classification_evidence = json!({"failure":e});
        }
    }
    report
}

fn execute(
    task: &Task,
    cfg: &StructureConfig,
    methods: &Methods,
    report: &mut StructureReport,
) -> Result<(), NativeFailure> {
    let mut sanitized = task.clone();
    sanitized.policy.audit_mode = AuditMode::PreTraining;
    sanitized.policy.representation = Representation::TechnicalMean;
    for r in &mut sanitized.observations {
        if r.partition == Partition::Test {
            r.y = None;
            r.category = None;
        }
    }
    sanitized
        .observations
        .sort_by_key(|r| (r.physical_sample_id.clone(), r.observation_id.clone()));
    let audit = units::audit(&sanitized);
    let (view, membership) = units::representation(&sanitized, &audit, Some(methods))
        .map_err(NativeFailure::transport)?;
    report.representation = membership;
    let mut rows = view
        .observations
        .iter()
        .filter(|r| r.partition == Partition::Train)
        .collect::<Vec<_>>();
    rows.sort_by_key(|r| &r.physical_sample_id);
    let mut components = BTreeMap::new();
    for c in audit.value["dependency_components"]
        .as_array()
        .into_iter()
        .flatten()
    {
        for link in c["links"]
            .as_array()
            .into_iter()
            .flatten()
            .filter(|l| l["kind"] == "physical")
        {
            components.insert(
                link["key"].as_str().unwrap().to_owned(),
                c["component_id"].as_str().unwrap().to_owned(),
            );
        }
    }
    let groups = rows
        .iter()
        .map(|r| components[&r.physical_sample_id].clone())
        .collect::<BTreeSet<_>>();
    report.population = json!({"input_representation":task.policy.representation,"selected_representation":"technical_mean","partition":"train",
        "n_physical_samples":rows.len(),"n_dependency_components":groups.len(),"n_native_train_acquisitions":task.observations.iter().filter(|r|r.partition==Partition::Train).count(),
        "physical_sample_ids":rows.iter().map(|r|&r.physical_sample_id).collect::<Vec<_>>(),"physical_sample_components":rows.iter().map(|r|(&r.physical_sample_id,&components[&r.physical_sample_id])).collect::<BTreeMap<_,_>>(),
        "axis_sha256":hash(&serde_json::to_vec(&task.axis).unwrap()),"n_bands":task.axis.len(),"axis_unit":task.axis_unit,"signal_unit":task.signal_unit,
        "independent_unit_definition":"Whole connected declared physical/sample/individual/reference/group dependency component; conditional real-world independence"});
    if rows.len() < 30 || groups.len() < 20 {
        return Err(NativeFailure::transport(
            "INSUFFICIENT_30_PHYSICAL_SAMPLES_AND_20_COMPONENTS_REQUIRED",
        ));
    }
    if rows
        .iter()
        .map(|r| &r.physical_sample_id)
        .collect::<BTreeSet<_>>()
        .len()
        != rows.len()
    {
        return Err(NativeFailure::transport(
            "NONUNIQUE_PHYSICAL_COMPARISON_ROWS",
        ));
    }
    if rows.len() > 1000
        || rows
            .len()
            .checked_mul(rows.len())
            .and_then(|v| v.checked_mul(cfg.pca_max_components))
            .and_then(|v| v.checked_mul(cfg.replicates + 1))
            .and_then(|v| v.checked_mul(cfg.sensitivity.len() + 1))
            .is_none_or(|v| v > 2_500_000_000)
    {
        return Err(NativeFailure::transport(
            "STRUCTURAL_EXPERIMENT_WORK_BUDGET_EXCEEDED",
        ));
    }
    let reference_projection = projection(methods, &rows, &sanitized, cfg, true)?;
    for params in std::iter::once(&cfg.primary).chain(&cfg.sensitivity) {
        let result = cluster(methods, &rows, &components, &reference_projection, params);
        let mut setting = StructureSetting {
            parameters: params.clone(),
            status: Status::Computed,
            reason: None,
            failure: None,
            reference: None,
            comparison_to_primary: None,
            replicates: vec![],
            stability: Value::Null,
        };
        match result {
            Ok(f) => setting.reference = Some(f),
            Err(e) => {
                setting.status = Status::Error;
                setting.reason = Some(e.reason.clone());
                setting.failure = Some(e);
            }
        }
        report.settings.push(setting);
    }
    let keys = groups.into_iter().collect::<Vec<_>>();
    let mut rng = ChaCha8Rng::seed_from_u64(cfg.seed);
    let selected_count = (keys.len() as f64 * cfg.component_fraction).ceil() as usize;
    for draw in 0..cfg.replicates {
        let mut selected = keys.clone();
        selected.shuffle(&mut rng);
        selected.truncate(selected_count);
        selected.sort();
        let subset = rows
            .iter()
            .copied()
            .filter(|r| {
                selected
                    .binary_search(&components[&r.physical_sample_id])
                    .is_ok()
            })
            .collect::<Vec<_>>();
        let pca = projection(methods, &subset, &sanitized, cfg, false);
        for setting in &mut report.settings {
            let mut replicate = StructureReplicate {
                draw,
                selected_components: selected.clone(),
                physical_sample_ids: subset
                    .iter()
                    .map(|r| r.physical_sample_id.clone())
                    .collect(),
                status: Status::Computed,
                reason: None,
                failure: None,
                fit: None,
                comparison: None,
            };
            let fit = match &pca {
                Ok(p) => cluster(methods, &subset, &components, p, &setting.parameters),
                Err(e) => Err(e.clone()),
            };
            match fit {
                Ok(f) => {
                    if let Some(reference) = &setting.reference {
                        replicate.comparison = Some(compare_partitions(
                            methods,
                            &labels(reference),
                            &labels(&f),
                            &components,
                            rows.len(),
                        )?);
                    }
                    replicate.fit = Some(f);
                }
                Err(e) => {
                    replicate.status = Status::Error;
                    replicate.reason = Some(e.reason.clone());
                    replicate.failure = Some(e);
                }
            }
            setting.replicates.push(replicate);
        }
    }
    let primary = report.settings[0].reference.as_ref().map(labels);
    for setting in &mut report.settings {
        setting.stability = summarize_setting(methods, setting)?;
        if let (Some(a), Some(f)) = (&primary, &setting.reference) {
            setting.comparison_to_primary = Some(compare_partitions(
                methods,
                a,
                &labels(f),
                &components,
                rows.len(),
            )?);
        }
    }
    if report.settings[0].reference.is_none() {
        return Err(report.settings[0]
            .failure
            .clone()
            .unwrap_or_else(|| NativeFailure::transport("PRIMARY_REFERENCE_HDBSCAN_FAILED")));
    }
    classify(methods, report)?;
    if cfg.compare_native {
        if let Some(reference) = &report.settings[0].reference {
            report.native_comparison =
                match native_comparison(methods, &sanitized, reference, &components, cfg) {
                    Ok(v) => v,
                    Err(e) => {
                        json!({"status":"unavailable","reason":e.reason,"value":null,"failure":e})
                    }
                };
        }
    }
    Ok(())
}

pub fn structure_markdown(report: &StructureReport) -> String {
    let classification = serde_json::to_value(&report.classification).unwrap();
    let mut out=format!("# Structural characterization\n\nDataset: `{}` · source: `{}` · split: `{}`\n\nProtocol: `{}` · status: `{:?}` · classification: `{}`\n\nTrain physical samples: {} · dependency components: {}\n\n",
        report.context.dataset_id.replace(['\n','\r','`']," "),report.context.source_id,report.context.split_id,report.protocol_version,
        report.status,classification.as_str().unwrap(),report.population["n_physical_samples"],report.population["n_dependency_components"]);
    out.push_str("| Setting | Clusters | Noise fraction | Successful draws | Median ARI incl. noise | Median ARI excl. noise |\n|---|---:|---:|---:|---:|---:|\n");
    for (i, s) in report.settings.iter().enumerate() {
        out.push_str(&format!(
            "| {} | {} | {} | {} | {} | {} |\n",
            i,
            s.reference
                .as_ref()
                .map_or(Value::Null, |f| json!(f.hdbscan.n_clusters)),
            s.reference
                .as_ref()
                .map_or(Value::Null, |f| json!(f.noise_fraction)),
            s.stability["successful_draws"],
            s.stability["ari_including_noise"]["value"]["median"],
            s.stability["ari_excluding_noise"]["value"]["median"]
        ));
    }
    if let Some(reason) = &report.reason {
        out.push_str(&format!("\nAvailability reason: `{reason}`\n"));
    }
    out.push_str("\nHeld-out HDBSCAN assignment: unavailable (no qualified public API).\n\nX structure alone does not establish target association, predictive reliance or causality.\n");
    for limitation in &report.limitations {
        out.push_str(&format!("\n- {limitation}\n"));
    }
    out
}
