use crate::{
    contract::*,
    hash,
    methods::{FittedPca, Methods},
    units,
};
use nirs4all_preflight::{
    self as pf, MethodsProvider, NearestNeighborsRequest, SummaryRequest,
    UnavailableMethodsProvider,
};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    path::Path,
};

fn preflight_input(task: &Task) -> Result<pf::QualificationInput, String> {
    let audit = units::audit(task);
    // Context aliases adapt Preflight's sample-level context without losing physical links.
    let aliases: Vec<_> = task
        .observations
        .iter()
        .map(|r| {
            format!(
                "context:{}",
                hash(
                    &serde_json::to_vec(&json!([
                        r.sample_id,
                        units::context(task, r),
                        if audit.unsafe_physical.contains(&r.physical_sample_id) {
                            Some(&r.observation_id)
                        } else {
                            None
                        }
                    ]))
                    .unwrap()
                )
            )
        })
        .collect();
    let mut samples = BTreeMap::new();
    for (row, alias) in task.observations.iter().zip(&aliases) {
        let sample = json!({"sample_id":alias,"physical_sample_id":row.physical_sample_id,
            "partition":if row.partition==Partition::Train {"development"} else {"retained_test"},
            "independence_group":row.independence_group,"individual_id":row.individual_id,
            "instrument":row.metadata.get("instrument"),"campaign":row.metadata.get("campaign")});
        if let Some(previous) = samples.insert(alias.clone(), sample.clone()) {
            if previous != sample {
                return Err("INCONSISTENT_SAMPLE_IDENTITY_OR_PARTITION".into());
            }
        }
    }
    // Test references are deliberately absent from the Preflight input, including
    // in post-evaluation mode. Their identity constraints are checked below without Y.
    let mut seen = BTreeSet::new();
    let mut seen_physical = BTreeSet::new();
    let values:Vec<_>=task.observations.iter().zip(&aliases).filter(|(r,_)|r.partition==Partition::Train && !audit.xy_blocked)
        .filter(|(r,_)| if task.target_kind==TargetKind::Continuous {r.y.is_some()}else{r.category.is_some()})
        .filter(|(r,_)|seen.insert(if let Some(id)=&r.reference_id {format!("reference:{id}")}else{format!("physical:{}",r.physical_sample_id)}))
        .filter(|(r,_)|seen_physical.insert(&r.physical_sample_id))
        .filter_map(|(r,alias)|match task.target_kind {
            TargetKind::Continuous=>r.y.map(|v|json!({"sample_id":alias,"value":v,"status":"exact","reference_id":r.reference_id,"reference_group_id":r.reference_group_id})),
            TargetKind::Categorical=>r.category.as_ref().map(|v|json!({"sample_id":alias,"category":v,"status":"exact","reference_id":r.reference_id,"reference_group_id":r.reference_group_id}))
        }).collect();
    let targets = task
        .context
        .target_id
        .as_ref()
        .map(|id| vec![json!({"target_id":id,"kind":task.target_kind,"values":values,"unit":task.target_unit})])
        .unwrap_or_default();
    let repetitions: Vec<_> = task
        .observations
        .iter()
        .map(|r| r.repetition_type.as_deref().unwrap_or("unknown"))
        .collect();
    serde_json::from_value(json!({"schema_version":1,"data_origin":task.data_origin,
        "sources":[{"source_id":task.context.source_id,"axis":task.axis,"axis_unit":task.axis_unit,"signal_unit":task.signal_unit,
            "x":task.observations.iter().map(|r|&r.x).collect::<Vec<_>>(),
            "sample_ids":aliases,
            "observation_ids":task.observations.iter().map(|r|&r.observation_id).collect::<Vec<_>>(),"repetition_types":repetitions}],
        "samples":samples.into_values().collect::<Vec<_>>(),"targets":targets,
        "options":{"independence_unit":"group","seed":task.policy.seed}})).map_err(|e|e.to_string())
}

/// Validates the evaluation policy plus Preflight's public integrity contract.
/// Reference *identities* remain available even when test target values are hidden.
pub fn validate(task: &Task) -> Result<(), String> {
    let c = &task.context;
    if task.schema_version != 1
        || [
            &c.dataset_id,
            &c.content_version,
            &c.source_id,
            &c.split_id,
            &task.axis_unit,
            &task.signal_unit,
        ]
        .iter()
        .any(|s| s.trim().is_empty())
        || c.target_id.as_ref().is_some_and(|s| s.trim().is_empty())
        || task
            .target_unit
            .as_ref()
            .is_some_and(|s| s.trim().is_empty())
    {
        return Err("INVALID_TASK_CONTEXT_OR_SCHEMA_VERSION".into());
    }
    if !matches!(task.data_origin.as_str(), "synthetic" | "user_provided")
        || !matches!(
            task.policy.independence_unit.as_str(),
            "physical_sample" | "group"
        )
    {
        return Err("EXPLICIT_ORIGIN_AND_INDEPENDENCE_UNIT_REQUIRED".into());
    }
    let policy = &task.policy;
    if policy.pca_max_components == 0
        || policy.pca_max_components > 50
        || !policy.pca_variance_fraction.is_finite()
        || !(0.0 < policy.pca_variance_fraction && policy.pca_variance_fraction <= 1.0)
    {
        return Err("INVALID_PCA_POLICY".into());
    }
    if task
        .observations
        .len()
        .checked_mul(task.axis.len())
        .is_none_or(|n| n > 10_000_000)
    {
        return Err("CELL_BUDGET_EXCEEDED".into());
    }
    let mut roles: BTreeMap<(String, String), BTreeSet<u8>> = BTreeMap::new();
    for r in &task.observations {
        if [
            &r.observation_id,
            &r.sample_id,
            &r.physical_sample_id,
            &r.independence_group,
        ]
        .iter()
        .any(|s| s.trim().is_empty())
        {
            return Err("EXPLICIT_IDENTITIES_REQUIRED".into());
        }
        if task.policy.independence_unit == "physical_sample"
            && r.independence_group != r.physical_sample_id
        {
            return Err("PHYSICAL_UNIT_GROUP_MISMATCH".into());
        }
        for (kind, key) in [
            ("sample", Some(&r.sample_id)),
            ("group", Some(&r.independence_group)),
        ] {
            if let Some(key) = key {
                roles.entry((kind.into(), key.clone())).or_default().insert(
                    if r.partition == Partition::Train {
                        0
                    } else {
                        1
                    },
                );
            }
        }
        if r.x.iter().flatten().any(|v| !v.is_finite()) {
            return Err("NONFINITE_X".into());
        }
    }
    for ((kind, key), partitions) in roles {
        if partitions.len() > 1 {
            return Err(format!("DEPENDENCY_LEAKAGE:{kind}:{key}"));
        }
    }
    let input = preflight_input(task)?;
    let validation = pf::validate_input(&input);
    if !validation.valid {
        return Err(format!(
            "PREFLIGHT_VALIDATION:{}",
            serde_json::to_string(&validation).map_err(|e| e.to_string())?
        ));
    }
    Ok(())
}

fn population(task: &Task) -> Population {
    let rows = |part: Partition| {
        task.observations
            .iter()
            .filter(move |r| r.partition == part)
            .collect::<Vec<_>>()
    };
    let train = rows(Partition::Train);
    let test = rows(Partition::Test);
    Population {
        population_id: "train_vs_test".into(),
        statistical_unit: task.policy.independence_unit.clone(),
        n_train_observations: train.len(),
        n_test_observations: test.len(),
        n_train_physical_samples: train
            .iter()
            .map(|r| &r.physical_sample_id)
            .collect::<BTreeSet<_>>()
            .len(),
        n_test_physical_samples: test
            .iter()
            .map(|r| &r.physical_sample_id)
            .collect::<BTreeSet<_>>()
            .len(),
        n_train_independent_units: train
            .iter()
            .map(|r| &r.independence_group)
            .collect::<BTreeSet<_>>()
            .len(),
        n_test_independent_units: test
            .iter()
            .map(|r| &r.independence_group)
            .collect::<BTreeSet<_>>()
            .len(),
        n_effective: None,
    }
}

fn metric(
    report: &Report,
    pop: &Population,
    id: &str,
    status: Status,
    value: Value,
    unit: &str,
    reason: Option<&str>,
) -> Metric {
    Metric {
        metric_id: id.into(),
        protocol_version: PROTOCOL.into(),
        context: report.context.clone(),
        population: pop.clone(),
        preprocessing_view: format!(
            "canonical:{}:center_train:pca",
            if report.policy.representation == Representation::Native {
                "native"
            } else {
                "technical_mean"
            }
        ),
        status,
        reason: reason.map(str::to_owned),
        value,
        unit: unit.into(),
        parameters: json!({"representation":report.policy.representation,"seed":report.policy.seed,"pca_variance_fraction":report.policy.pca_variance_fraction,"pca_max_components":report.policy.pca_max_components}),
        uncertainty: None,
        provenance: report.provenance.clone(),
        observation_ids: vec![],
    }
}

pub fn analyze(task: &Task, library: Option<&Path>) -> Report {
    let mut sanitized = task.clone();
    if task.policy.audit_mode == AuditMode::PreTraining {
        for r in &mut sanitized.observations {
            if r.partition == Partition::Test {
                r.y = None;
                r.category = None;
            }
        }
    }
    let mut provenance = task.provenance.clone();
    provenance.insert("domains".into(), VERSION.into());
    provenance.insert("preflight".into(), "0.1.0-alpha.1".into());
    provenance.insert(
        "sanitized_task_sha256".into(),
        hash(&serde_json::to_vec(&sanitized).unwrap_or_default()),
    );
    let mut report=Report {schema_version:1,engine_version:VERSION.into(),protocol_version:PROTOCOL.into(),context:task.context.clone(),
        data_origin:task.data_origin.clone(),status:"partial".into(),test_target_accessed:false,policy:task.policy.clone(),provenance,
        fit:None,preflight:None,unit_audit:Value::Null,representations:Value::Null,metrics:vec![],findings:vec![],dimensions:["integrity","measurement","coverage","structure","xy_relationship","generalization"].iter().map(|s|(s.to_string(),"unavailable".into())).collect(),
        limitations:vec!["Exploratory descriptive audit; no calibrated statistical test or prediction-performance claim.".into(),
        "Coverage thresholds use train-only Tukey fences; these are heuristics, not failure probabilities.".into(),
        "No clustering, confounding inference, nested PLS/PCR probe, AOM, MMD, energy or C2ST protocol is implemented.".into(),
        "Technical means require declared homogeneous contexts; ambiguous and cross-context units are explicitly excluded from pooled geometry.".into(),
        "Counts of physical samples and groups are not an estimator of effective sample size.".into(),
        "Physical, group and reference IDs are supplied by the host; structural checks do not independently verify real-world identities or laboratory provenance.".into()]};
    let pop = population(task);
    let audit = units::audit(&sanitized);
    report.unit_audit = audit.value.clone();
    report.test_target_accessed =
        task.policy.audit_mode == AuditMode::PostEvaluation && task.context.target_id.is_some();
    if report.test_target_accessed {
        report.findings.push(Finding{rule_id:"domains.test_target_access.v1".into(),severity:"warning".into(),observation:"Post-evaluation audit accessed test target fields.".into(),confidence:"high".into(),calibration_consequence:"A strategy change after this audit requires a new independent evaluation.".into(),recommended_action:"Freeze the completed evaluation and reserve a new independent test before modifying the strategy.".into(),evidence:vec!["unit_audit".into(),"target.test_summary".into()]});
    }
    if let Err(reason) = validate(task) {
        report.status = "failed".into();
        report.dimensions.insert("integrity".into(), "error".into());
        report.metrics.push(metric(
            &report,
            &pop,
            "task.validation",
            Status::Error,
            Value::Null,
            "",
            Some(&reason),
        ));
        report.findings.push(Finding {
            rule_id: "domains.invalid_task.v1".into(),
            severity: "blocking".into(),
            observation: reason,
            confidence: "high".into(),
            calibration_consequence: "The declared evaluation plan cannot be audited safely."
                .into(),
            recommended_action:
                "Correct identities, source shape or evaluation policy before fitting.".into(),
            evidence: vec!["task.validation".into()],
        });
        return report;
    }
    let input = preflight_input(task).expect("validated preflight contract");
    let methods = match library.map(Methods::load).transpose() {
        Ok(m) => m,
        Err(reason) => {
            report.preflight = Some(
                serde_json::to_value(pf::analyze(&input, &UnavailableMethodsProvider))
                    .expect("report serializable"),
            );
            report.dimensions.insert(
                "integrity".into(),
                "computed (Preflight exploratory alpha)".into(),
            );
            report.metrics.push(metric(
                &report,
                &pop,
                "engine.methods",
                Status::Error,
                Value::Null,
                "",
                Some(&reason),
            ));
            report.status = "failed".into();
            return report;
        }
    };
    if let Some(m) = &methods {
        report
            .provenance
            .insert("methods".into(), m.version.clone());
        report
            .provenance
            .insert("methods_abi".into(), m.abi.clone());
        if let Some(path) = library {
            if let Ok(bytes) = std::fs::read(path) {
                report
                    .provenance
                    .insert("methods_binary_sha256".into(), hash(&bytes));
            }
        }
    }
    report.preflight = Some(
        serde_json::to_value(match &methods {
            Some(m) => pf::analyze(&input, &m.provider),
            None => pf::analyze(&input, &UnavailableMethodsProvider),
        })
        .expect("finite upstream report"),
    );
    report.dimensions.insert(
        "integrity".into(),
        "computed (Preflight exploratory alpha)".into(),
    );
    report.dimensions.insert(
        "measurement".into(),
        "see Preflight availability per metric".into(),
    );
    report.metrics.push(metric(&report,&pop,"reference.xy_eligibility",
        if audit.xy_blocked {Status::NotIdentifiable} else {Status::Computed},
        if audit.xy_blocked {Value::Null} else {json!({"status":"descriptive_only","reference_identity_complete":task.observations.iter().all(|r|r.reference_id.is_some())})},
        "",if audit.xy_blocked {Some("REFERENCE_ANOMALY_XY_BLOCKED_X_RETAINED")}else{None}));
    if audit.xy_blocked {
        report.findings.push(Finding{rule_id:"domains.reference_safety.v0.1".into(),severity:"high".into(),
            observation:"Reference dependencies or anomalies block X-Y qualification; native X analysis remains available.".into(),confidence:"high".into(),
            calibration_consequence:"Reference rows cannot be treated as independent exact outcomes.".into(),recommended_action:"Resolve the reference issues and reserve whole dependency components for validation.".into(),evidence:vec!["unit_audit.reference_issues".into()]});
    }
    for (id, reason) in [
        ("structure.clustering", "CLUSTER_PROTOCOL_DEFERRED"),
        ("xy.nested_probe", "NESTED_GROUP_VALIDATION_DEFERRED"),
        (
            "explainability.conditional_effects",
            "CONDITIONAL_FACTOR_PROTOCOL_DEFERRED",
        ),
    ] {
        report.metrics.push(metric(
            &report,
            &pop,
            id,
            Status::Unavailable,
            Value::Null,
            "",
            Some(reason),
        ));
    }
    let representation = units::representation(&sanitized, &audit, methods.as_ref());
    let mut comparison_pop = pop.clone();
    let geometry = match representation {
        Ok((view, inventory)) => {
            report.representations = inventory;
            let view_pop = population(&view);
            comparison_pop = view_pop.clone();
            match &methods {
                Some(m) => geometry(&view, m, &mut report, &view_pop),
                None => Err((
                    Status::Unavailable,
                    "METHODS_PROVIDER_NOT_CONFIGURED".into(),
                )),
            }
        }
        Err(reason) => Err((Status::Error, reason)),
    };
    if let Err((status, reason)) = geometry {
        for id in [
            "coverage.test_outside_fraction",
            "domain.centroid_distance",
            "domain.dispersion_ratio",
        ] {
            report.metrics.push(metric(
                &report,
                &comparison_pop,
                id,
                status.clone(),
                Value::Null,
                "",
                Some(&reason),
            ));
        }
    }
    target_audit(task, methods.as_ref(), &mut report, &pop);
    if let Some(pf) = &report.preflight {
        if let Some(findings) = pf["findings"].as_array() {
            for f in findings {
                report.findings.push(Finding {
                    rule_id: format!("preflight:{}", f["rule_id"].as_str().unwrap_or("unknown")),
                    severity: f["severity"].as_str().unwrap_or("warning").into(),
                    observation: f["message"]
                        .as_str()
                        .unwrap_or("See Preflight report")
                        .into(),
                    confidence: f["confidence"].as_str().unwrap_or("unknown").into(),
                    calibration_consequence:
                        "Review measurement integrity and independence before calibration.".into(),
                    recommended_action: f["action"]
                        .as_str()
                        .unwrap_or("Inspect Preflight evidence")
                        .into(),
                    evidence: vec!["preflight.findings".into()],
                });
            }
        }
    }
    report
}

type ProtocolFailure = (Status, String);
type ProtocolResult = Result<(), ProtocolFailure>;
type Projection = (Vec<Vec<f64>>, Vec<f64>);
fn err(s: String) -> (Status, String) {
    (Status::Error, s)
}
fn numeric_rows(rows: &[&Observation]) -> Result<Vec<Vec<f64>>, (Status, String)> {
    rows.iter()
        .map(|r| {
            r.x.iter()
                .map(|v| {
                    v.filter(|x| x.is_finite()).ok_or_else(|| {
                        (
                            Status::Unavailable,
                            "MISSING_X_NO_IMPUTATION_PROTOCOL".into(),
                        )
                    })
                })
                .collect()
        })
        .collect()
}
fn project(pca: &FittedPca, x: &[Vec<f64>], d: usize) -> Result<Projection, ProtocolFailure> {
    let mut scores = Vec::new();
    let mut residuals = Vec::new();
    for row in x {
        // Applying the Methods-fitted affine PCA transform; no decomposition or
        // refitting occurs here. Loadings are k x p as specified by the C ABI.
        let centered: Vec<_> = row.iter().zip(&pca.mean).map(|(x, m)| x - m).collect();
        let score: Vec<f64> = pca.loadings[..d]
            .iter()
            .map(|l| l.iter().zip(&centered).map(|(a, b)| a * b).sum())
            .collect();
        let q: f64 = centered
            .iter()
            .enumerate()
            .map(|(j, c)| {
                let reconstruction: f64 = (0..d).map(|k| score[k] * pca.loadings[k][j]).sum();
                (c - reconstruction).powi(2)
            })
            .sum();
        if !q.is_finite() || score.iter().any(|s| !s.is_finite()) {
            return Err(err("NONFINITE_PROJECTION".into()));
        }
        scores.push(score);
        residuals.push(q);
    }
    Ok((scores, residuals))
}

fn geometry(
    task: &Task,
    methods: &Methods,
    report: &mut Report,
    pop: &Population,
) -> ProtocolResult {
    let train: Vec<_> = task
        .observations
        .iter()
        .filter(|r| r.partition == Partition::Train)
        .collect();
    let test: Vec<_> = task
        .observations
        .iter()
        .filter(|r| r.partition == Partition::Test)
        .collect();
    if train.len() < 3 || test.is_empty() {
        return Err((
            Status::InsufficientData,
            "AT_LEAST_THREE_TRAIN_AND_ONE_TEST_REQUIRED".into(),
        ));
    }
    if train.len() != pop.n_train_physical_samples || test.len() != pop.n_test_physical_samples {
        return Err((
            Status::NotIdentifiable,
            "REPEATED_UNITS_REQUIRE_AGGREGATION_PROTOCOL".into(),
        ));
    }
    // Bound the brute-force train and test neighbor workloads before allocation.
    let dmax = task
        .axis
        .len()
        .min(train.len() - 1)
        .min(task.policy.pca_max_components);
    if train
        .len()
        .checked_mul(train.len() + test.len())
        .and_then(|n| n.checked_mul(dmax))
        .is_none_or(|n| n > 250_000_000)
    {
        return Err((Status::Unavailable, "NEIGHBOR_WORK_BUDGET_EXCEEDED".into()));
    }
    let xtrain = numeric_rows(&train)?;
    let xtest = numeric_rows(&test)?;
    let pca = methods.fit_pca(&xtrain, dmax).map_err(err)?;
    if pca.full_moments[0] <= 0.0 || pca.full_moments[1] <= 0.0 {
        return Err((Status::InsufficientData, "ZERO_TRAIN_VARIANCE".into()));
    }
    let mut d = 0;
    let mut cumulative = 0.0;
    for e in &pca.eigenvalues {
        d += 1;
        cumulative += e;
        if cumulative / pca.full_moments[0] >= task.policy.pca_variance_fraction {
            break;
        }
    }
    let (train_scores, train_q) = project(&pca, &xtrain, d)?;
    let (test_scores, test_q) = project(&pca, &xtest, d)?;
    let group_codes: BTreeMap<_, _> = task
        .observations
        .iter()
        .map(|r| r.independence_group.clone())
        .collect::<BTreeSet<_>>()
        .into_iter()
        .enumerate()
        .map(|(i, g)| (g, i as i64))
        .collect();
    let groups = |rows: &[&Observation]| {
        rows.iter()
            .map(|r| group_codes[&r.independence_group])
            .collect::<Vec<_>>()
    };
    let train_groups = groups(&train);
    let test_groups = groups(&test);
    let neighbors = |query: Vec<Vec<f64>>, query_groups: Vec<i64>| {
        methods
            .provider
            .nearest_neighbors(&NearestNeighborsRequest {
                query,
                reference: train_scores.clone(),
                query_group_ids: query_groups,
                reference_group_ids: train_groups.clone(),
                k: 1,
            })
            .map_err(|e| err(e.0))
    };
    let train_nn = neighbors(train_scores.clone(), train_groups.clone())?;
    let test_nn = neighbors(test_scores.clone(), test_groups)?;
    let distances = |rows: Vec<Vec<Option<f64>>>| {
        rows.into_iter()
            .map(|r| {
                r[0].ok_or_else(|| (Status::InsufficientData, "NO_INDEPENDENT_NEIGHBOR".into()))
            })
            .collect::<Result<Vec<_>, _>>()
    };
    let train_dist = distances(train_nn.distances)?;
    let test_dist = distances(test_nn.distances)?;
    let summary = |values: Vec<f64>| {
        methods
            .provider
            .summary(&SummaryRequest { values })
            .map_err(|e| err(e.0))
    };
    let nn_summary = summary(train_dist.clone())?;
    let q_summary = summary(train_q.clone())?;
    let nn_threshold = nn_summary.q75 + 1.5 * (nn_summary.q75 - nn_summary.q25);
    let scale = pca.mean.iter().map(|v| v * v).sum::<f64>() + pca.full_moments[0];
    let q_threshold = q_summary.q75 + 1.5 * (q_summary.q75 - q_summary.q25) + 1e-12 * (1.0 + scale);
    let mut centroid_squared = 0.0;
    let mut train_variance = 0.0;
    let mut test_variance = 0.0;
    for j in 0..d {
        let a = summary(train_scores.iter().map(|r| r[j]).collect())?;
        let b = summary(test_scores.iter().map(|r| r[j]).collect())?;
        centroid_squared += (a.mean - b.mean).powi(2);
        train_variance += a.sample_sd.unwrap_or(0.0).powi(2);
        test_variance += b.sample_sd.unwrap_or(0.0).powi(2);
    }
    let dimension = pca.full_moments[0].powi(2) / pca.full_moments[1];
    if train_variance > 0.0 && !(test_variance / train_variance).is_finite() {
        return Err(err("NONFINITE_DISPERSION_RATIO".into()));
    }
    if [
        centroid_squared,
        train_variance,
        test_variance,
        dimension,
        nn_threshold,
        q_threshold,
    ]
    .iter()
    .any(|v| !v.is_finite())
    {
        return Err(err("NONFINITE_DOMAIN_METRIC".into()));
    }
    let outside: Vec<_> = test
        .iter()
        .enumerate()
        .filter(|(i, _)| test_dist[*i] > nn_threshold || test_q[*i] > q_threshold)
        .map(|(_, r)| r.observation_id.clone())
        .collect();
    report.fit = Some(
        json!({"fit_partition":"train","fit_observation_ids":train.iter().map(|r|&r.observation_id).collect::<Vec<_>>(),
        "fit_x_sha256":hash(&serde_json::to_vec(&xtrain).expect("finite matrix")),"mean":pca.mean,"loadings":pca.loadings[..d],"eigenvalues":pca.eigenvalues[..d],
        "full_moments":pca.full_moments,"n_components":d,"retained_variance_fraction":cumulative/pca.full_moments[0],"requested_variance_reached":cumulative/pca.full_moments[0]>=task.policy.pca_variance_fraction,
        "solver":"Methods automatic; exact or deterministic approximate depending on matrix shape; solver flag not exposed by ABI",
        "nn_threshold":nn_threshold,"reconstruction_squared_threshold":q_threshold,"threshold_rule":"train q75 + 1.5 IQR; residual numerical floor 1e-12*(1+mean_norm_squared+trace)"}),
    );
    report.metrics.push(metric(
        report,
        pop,
        "coverage.effective_dimension",
        Status::Computed,
        json!(dimension),
        "dimensions",
        None,
    ));
    report.metrics.push(metric(
        report,
        pop,
        "domain.centroid_distance",
        Status::Computed,
        json!(centroid_squared.sqrt()),
        &task.signal_unit,
        None,
    ));
    let dispersion = if test.len() < 2 {
        (
            Status::InsufficientData,
            Value::Null,
            Some("TWO_TEST_ROWS_REQUIRED"),
        )
    } else if train_variance == 0.0 {
        (
            Status::InsufficientData,
            Value::Null,
            Some("ZERO_PROJECTED_TRAIN_VARIANCE"),
        )
    } else {
        (
            Status::Computed,
            json!(test_variance / train_variance),
            None,
        )
    };
    report.metrics.push(metric(
        report,
        pop,
        "domain.dispersion_ratio",
        dispersion.0,
        dispersion.1,
        "variance ratio",
        dispersion.2,
    ));
    let mut coverage = metric(
        report,
        pop,
        "coverage.test_outside_fraction",
        Status::Computed,
        json!(outside.len() as f64 / test.len() as f64),
        "fraction",
        None,
    );
    coverage.observation_ids = outside.clone();
    coverage.parameters["denominator"] = json!(test.len());
    coverage.parameters["test_population"] = json!(test.iter().map(|r|json!({"representation_observation_id":r.observation_id,"physical_sample_id":r.physical_sample_id,"independence_group":r.independence_group})).collect::<Vec<_>>());
    coverage.parameters["population_membership"] = json!("representations.sample_context_groups maps every representation row to native acquisition IDs");
    report.metrics.push(coverage);
    for (id, value, unit) in [
        (
            "coverage.train_neighbor_distances",
            json!(train_dist),
            task.signal_unit.as_str(),
        ),
        (
            "coverage.test_neighbor_distances",
            json!(test_dist),
            task.signal_unit.as_str(),
        ),
        (
            "coverage.train_reconstruction_squared",
            json!(train_q),
            "signal squared",
        ),
        (
            "coverage.test_reconstruction_squared",
            json!(test_q),
            "signal squared",
        ),
    ] {
        let mut m = metric(report, pop, id, Status::Computed, value, unit, None);
        m.observation_ids = if id.contains(".train_") {
            train.iter().map(|r| r.observation_id.clone()).collect()
        } else {
            test.iter().map(|r| r.observation_id.clone()).collect()
        };
        report.metrics.push(m);
    }
    report
        .dimensions
        .insert("coverage".into(), "computed, exploratory".into());
    report.dimensions.insert(
        "generalization".into(),
        "spectral comparison computed; predictive risk unvalidated".into(),
    );
    if !outside.is_empty() {
        report.findings.push(Finding{rule_id:"domains.coverage.v0.1".into(),severity:"warning".into(),observation:format!("{} of {} test observations exceed a train-only coverage heuristic.",outside.len(),test.len()),confidence:"low".into(),calibration_consequence:"Possible spectral extrapolation; this does not establish a loss of predictive performance.".into(),recommended_action:"Inspect the listed observations and verify the intended application domain with independent evaluation.".into(),evidence:vec!["coverage.test_outside_fraction".into()]});
    }
    Ok(())
}

fn target_audit(task: &Task, methods: Option<&Methods>, report: &mut Report, pop: &Population) {
    if task.context.target_id.is_none() {
        report.metrics.push(metric(
            report,
            pop,
            "target.train_summary",
            Status::Unavailable,
            Value::Null,
            "",
            Some("TARGET_ABSENT"),
        ));
        return;
    }
    if report.unit_audit["xy_blocked"] == true {
        report.dimensions.insert(
            "xy_relationship".into(),
            "blocked by reference audit; X retained".into(),
        );
        report.metrics.push(metric(
            report,
            pop,
            "target.train_summary",
            Status::NotIdentifiable,
            Value::Null,
            "",
            Some("REFERENCE_ANOMALY_XY_BLOCKED_X_RETAINED"),
        ));
        report.metrics.push(metric(
            report,
            pop,
            if task.policy.audit_mode == AuditMode::PreTraining {
                "target.test_shift"
            } else {
                "target.test_summary"
            },
            if task.policy.audit_mode == AuditMode::PreTraining {
                Status::Unavailable
            } else {
                Status::NotIdentifiable
            },
            Value::Null,
            "",
            Some(if task.policy.audit_mode == AuditMode::PreTraining {
                "Y_TEST_FORBIDDEN_PRE_TRAINING"
            } else {
                "REFERENCE_ANOMALY_XY_BLOCKED_X_RETAINED"
            }),
        ));
        return;
    }
    // Preflight already summarizes eligible train targets, including categories.
    report.dimensions.insert(
        "xy_relationship".into(),
        "train target description in Preflight; predictability unavailable".into(),
    );
    if task.policy.audit_mode == AuditMode::PreTraining {
        report.metrics.push(metric(
            report,
            pop,
            "target.test_shift",
            Status::Unavailable,
            Value::Null,
            "",
            Some("Y_TEST_FORBIDDEN_PRE_TRAINING"),
        ));
        return;
    }
    let test: Vec<_> = task
        .observations
        .iter()
        .filter(|r| r.partition == Partition::Test)
        .collect();
    if test.len() != pop.n_test_physical_samples && test.iter().any(|r| r.reference_id.is_none()) {
        report.metrics.push(metric(
            report,
            pop,
            "target.test_summary",
            Status::NotIdentifiable,
            Value::Null,
            "",
            Some("REPEATED_TARGET_UNITS_REQUIRE_REFERENCE_PROTOCOL"),
        ));
        return;
    }
    let mut seen = BTreeSet::new();
    let test: Vec<_> = test
        .into_iter()
        .filter(|r| {
            seen.insert(
                r.reference_id
                    .as_ref()
                    .map(|id| format!("reference:{id}"))
                    .unwrap_or_else(|| format!("physical:{}", r.physical_sample_id)),
            )
        })
        .collect();
    if task.target_kind == TargetKind::Categorical {
        let mut counts = BTreeMap::<String, usize>::new();
        for r in &test {
            if let Some(v) = &r.category {
                *counts.entry(v.clone()).or_default() += 1;
            }
        }
        report.metrics.push(metric(
            report,
            pop,
            "target.test_summary",
            if counts.is_empty() {
                Status::InsufficientData
            } else {
                Status::Computed
            },
            if counts.is_empty() {
                Value::Null
            } else {
                json!(counts)
            },
            "observations",
            if counts.is_empty() {
                Some("NO_TEST_TARGET_VALUES")
            } else {
                None
            },
        ));
        return;
    }
    let values: Vec<_> = test.iter().filter_map(|r| r.y).collect();
    let (status, value, reason) = if values.iter().any(|v| !v.is_finite()) {
        (
            Status::Error,
            Value::Null,
            Some("NONFINITE_TEST_TARGET".to_string()),
        )
    } else if values.is_empty() {
        (
            Status::InsufficientData,
            Value::Null,
            Some("NO_TEST_TARGET_VALUES".into()),
        )
    } else if let Some(m) = methods {
        match m.provider.summary(&SummaryRequest { values }) {
            Ok(summary) => (Status::Computed, json!(summary), None),
            Err(e) => (Status::Error, Value::Null, Some(e.0)),
        }
    } else {
        (
            Status::Unavailable,
            Value::Null,
            Some("METHODS_PROVIDER_NOT_CONFIGURED".into()),
        )
    };
    report.metrics.push(metric(
        report,
        pop,
        "target.test_summary",
        status,
        value,
        task.target_unit
            .as_deref()
            .unwrap_or("target units (unspecified)"),
        reason.as_deref(),
    ));
}
