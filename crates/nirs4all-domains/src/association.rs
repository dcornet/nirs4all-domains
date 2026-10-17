//! Physical-unit descriptive association over public Methods kernels.
use crate::{comparison_task, contract::*, methods::Methods, units, validate};
use nirs4all_preflight::{MethodsProvider, SummaryRequest};
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    path::Path,
};

fn unavailable(reason: &str) -> Value {
    json!({"status":"insufficient_data","reason":reason,"value":null})
}
fn calculate(rows: &[&Observation], factor: &str, methods: &Methods) -> Result<Value, String> {
    let selected: Vec<_> = rows
        .iter()
        .copied()
        .filter(|r| r.y.is_some() && r.metadata.get(factor).is_some_and(|s| !s.trim().is_empty()))
        .collect();
    if selected.len() < 2 {
        return Ok(unavailable("FEWER_THAN_TWO_COMPLETE_FACTOR_TARGET_UNITS"));
    }
    let mut levels: BTreeMap<&str, Vec<&Observation>> = BTreeMap::new();
    for row in &selected {
        levels
            .entry(row.metadata[factor].as_str())
            .or_default()
            .push(row);
    }
    let codes: BTreeMap<_, _> = levels
        .keys()
        .enumerate()
        .map(|(i, k)| (*k, i as i64))
        .collect();
    let y: Vec<_> = selected.iter().map(|r| r.y.unwrap()).collect();
    let code: Vec<_> = selected
        .iter()
        .map(|r| codes[r.metadata[factor].as_str()])
        .collect();
    let native = methods
        .factor_association(&code, &y)
        .map_err(|e| serde_json::to_string(&e).unwrap())?;
    let summary = methods
        .provider
        .summary(&SummaryRequest { values: y })
        .map_err(|e| e.0)?;
    let variance = summary.sample_sd.unwrap_or(0.0).powi(2);
    let total = (selected.len() - 1) as f64 * variance;
    let Some(eta) = native[0] else {
        return Ok(unavailable(if levels.len() < 2 {
            "ONE_FACTOR_LEVEL"
        } else {
            "CONSTANT_TARGET_NATIVE_EFFECT_UNDEFINED"
        }));
    };
    let mut table = Vec::new();
    for (level, values) in &levels {
        let s = methods
            .provider
            .summary(&SummaryRequest {
                values: values.iter().map(|r| r.y.unwrap()).collect(),
            })
            .map_err(|e| e.0)?;
        table.push(json!({"level":level,"n":values.len(),"mean_y":s.mean,
            "components":values.iter().map(|r| &r.metadata["validation_component_id"]).collect::<BTreeSet<_>>().len()}));
    }
    let mut warnings = vec!["Exploratory; declared components do not verify biological/assay independence or precision."];
    if levels.len() as f64 / selected.len() as f64 >= 0.8 {
        warnings.push("SATURATED_OR_NEAR_SATURATED_FACTOR: high eta-squared can be trivial.");
    }
    if levels.values().any(|v| v.len() == 1) {
        warnings.push("SINGLETON_LEVELS");
    }
    if table.iter().any(|v| v["components"].as_u64().unwrap() < 3) {
        warnings.push("SPARSE_INDEPENDENT_COMPONENT_SUPPORT");
    }
    Ok(
        json!({"status":"computed","reason":null,"value":{"eta_squared":eta,
        "n_physical":selected.len(),"n_components":selected.iter().map(|r| &r.metadata["validation_component_id"]).collect::<BTreeSet<_>>().len(),
        "known_reference_units":selected.iter().filter_map(|r|r.reference_id.as_ref()).collect::<BTreeSet<_>>().len(),
        "n_levels":levels.len(),"overall_mean":summary.mean,"sample_variance":variance,
        "ss_total":total,"ss_between":eta*total,"ss_within":total-eta*total,
        "f":{"value":native[1],"reason":if native[1].is_none(){Some("NATIVE_UNDEFINED_ZERO_WITHIN_SS_OR_NO_RESIDUAL_DF")}else{None}},
        "df_between":native[2],"df_within":native[3],"levels":table,"warnings":warnings,
        "native_permutations":0}}),
    )
}

/// Sanitize held-out labels before validation; repeat/reference audit precedes physical reduction.
pub fn group_target_association(
    task: &Task,
    factor: &str,
    library: &Path,
    draws: usize,
    seed: u64,
) -> Result<Value, String> {
    if factor.trim().is_empty() || draws > 1000 {
        return Err("INVALID_ASSOCIATION_CONFIG".into());
    }
    let mut task = task.clone();
    task.policy.audit_mode = AuditMode::PreTraining;
    for r in &mut task.observations {
        if r.partition == Partition::Test {
            r.y = None;
            r.category = None;
        }
    }
    validate(&task)?;
    if task.policy.representation != Representation::TechnicalMean {
        return Err("TECHNICAL_MEAN_REQUIRED".into());
    }
    let audit = units::audit(&task);
    if audit.xy_blocked {
        return Ok(
            json!({"protocol_version":"domains.structural_dependence.v0.1","factor":factor,"test_target_accessed":false,"association":unavailable("REFERENCE_AUDIT_BLOCKS_XY"),"bootstrap":null}),
        );
    }
    let view = comparison_task(&task, library)?;
    let mut rows: Vec<_> = view
        .observations
        .iter()
        .filter(|r| r.partition == Partition::Train)
        .collect();
    rows.sort_by_key(|r| &r.physical_sample_id);
    if rows.len() > 10_000 || rows.len().checked_mul(draws).is_none_or(|n| n > 2_000_000) {
        return Err("ASSOCIATION_RESAMPLING_BUDGET_EXCEEDED".into());
    }
    let ids: BTreeSet<_> = rows.iter().map(|r| &r.physical_sample_id).collect();
    if ids.len() != rows.len() {
        return Err("MULTIPLE_CONTEXTS_PER_PHYSICAL_UNIT".into());
    }
    // A mean cannot silently take the first of conflicting acquisition metadata values.
    for id in &ids {
        let values: BTreeSet<_> = task
            .observations
            .iter()
            .filter(|r| r.partition == Partition::Train && &r.physical_sample_id == *id)
            .map(|r| r.metadata.get(factor))
            .collect();
        if values.len() > 1 {
            return Err("CONFLICTING_FACTOR_WITHIN_PHYSICAL_UNIT".into());
        }
    }
    let methods = Methods::load(library)?;
    let association = calculate(&rows, factor, &methods)?;
    let mut components: BTreeMap<_, Vec<_>> = BTreeMap::new();
    for r in &rows {
        components
            .entry(r.metadata["validation_component_id"].clone())
            .or_default()
            .push(*r);
    }
    let keys: Vec<_> = components.keys().cloned().collect();
    let mut rng = ChaCha8Rng::seed_from_u64(seed);
    let mut replicas = Vec::new();
    let mut values = Vec::new();
    for draw in 0..draws {
        if keys.is_empty() {
            break;
        }
        let sampled: Vec<_> = (0..keys.len())
            .map(|_| keys[rng.gen_range(0..keys.len())].clone())
            .collect();
        let sample: Vec<_> = sampled
            .iter()
            .flat_map(|k| components[k].iter().copied())
            .collect();
        let result = calculate(&sample, factor, &methods)
            .unwrap_or_else(|e| json!({"status":"error","reason":e,"value":null}));
        let value = result["value"]["eta_squared"].as_f64();
        if let Some(v) = value {
            values.push(v);
        }
        replicas.push(
            json!({"draw":draw,"components":sampled,"value":value,"reason":result["reason"]}),
        );
    }
    values.sort_by(f64::total_cmp);
    let interval = if values.len() >= 100 && keys.len() >= 10 {
        json!([
            values[(0.025 * values.len() as f64).ceil() as usize - 1],
            values[(0.975 * values.len() as f64).ceil() as usize - 1]
        ])
    } else {
        Value::Null
    };
    Ok(
        json!({"protocol_version":"domains.structural_dependence.v0.1","factor":factor,
        "context":task.context,"target_unit":task.target_unit,"test_target_accessed":false,
        "methods_version":methods.version,"methods_abi":methods.abi,
        "population_ids":ids,"excluded_missing_y_ids":rows.iter().filter(|r|r.y.is_none()).map(|r|&r.physical_sample_id).collect::<Vec<_>>(),
        "excluded_missing_factor_ids":rows.iter().filter(|r|!r.metadata.get(factor).is_some_and(|s|!s.trim().is_empty())).map(|r|&r.physical_sample_id).collect::<Vec<_>>(),
        "association":association,"bootstrap":{"seed":seed,"requested":draws,"successful":values.len(),
            "failed":replicas.len()-values.len(),"interval_95":interval,"interval_reason":if interval.is_null(){Some("REQUIRES_100_SUCCESSFUL_DRAWS_AND_10_COMPONENTS")}else{None},
            "unit":"whole declared dependency components with replacement; multiplicity retained; conditional observed-design uncertainty","draws":replicas}}),
    )
}
