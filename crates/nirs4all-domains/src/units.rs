//! Declared identity constraints and task representations. Numerical means are Methods calls.
use crate::{contract::*, hash, methods::Methods};
use nirs4all_preflight::{MethodsProvider, SummaryRequest};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

pub struct Audit {
    pub value: Value,
    pub xy_blocked: bool,
    pub unsafe_physical: BTreeSet<String>,
}

fn reference_id(row: &Observation) -> Option<&String> {
    row.reference_id.as_ref().filter(|s| !s.trim().is_empty())
}

fn links(row: &Observation) -> Vec<(&str, &str)> {
    let mut keys = vec![
        ("sample", row.sample_id.as_str()),
        ("physical", row.physical_sample_id.as_str()),
        ("group", row.independence_group.as_str()),
    ];
    for (kind, key) in [
        ("individual", &row.individual_id),
        ("reference", &row.reference_id),
        ("reference_group", &row.reference_group_id),
    ] {
        if let Some(key) = key.as_ref().filter(|s| !s.trim().is_empty()) {
            keys.push((kind, key));
        }
    }
    keys
}

pub fn context(task: &Task, row: &Observation) -> BTreeMap<String, String> {
    let mut result = BTreeMap::from([("source".into(), task.context.source_id.clone())]);
    for key in ["instrument", "campaign", "site", "lot"] {
        if let Some(value) = row.metadata.get(key).filter(|v| !v.trim().is_empty()) {
            result.insert(key.into(), value.clone());
        }
    }
    result
}

pub fn audit(task: &Task) -> Audit {
    let mut by_key = BTreeMap::<(String, String), Vec<usize>>::new();
    for (i, row) in task.observations.iter().enumerate() {
        for (kind, key) in links(row) {
            by_key.entry((kind.into(), key.into())).or_default().push(i);
        }
    }
    let mut adjacent = vec![Vec::new(); task.observations.len()];
    let mut issues = Vec::new();
    for ((kind, key), rows) in &by_key {
        for &i in rows.iter().skip(1) {
            adjacent[rows[0]].push(i);
            adjacent[i].push(rows[0]);
        }
        if matches!(kind.as_str(), "reference" | "reference_group") {
            let physical: BTreeSet<_> = rows
                .iter()
                .map(|&i| &task.observations[i].physical_sample_id)
                .collect();
            let train = rows
                .iter()
                .any(|&i| task.observations[i].partition == Partition::Train);
            let test = rows
                .iter()
                .any(|&i| task.observations[i].partition == Partition::Test);
            if (train && test) || (kind == "reference" && physical.len() > 1) {
                issues.push(json!({"reason":if train && test {"REFERENCE_DEPENDENCY_CROSSES_PARTITIONS"} else {"REFERENCE_SHARED_BY_PHYSICAL_SAMPLES"},
                    "kind":kind,"key":key,"observation_ids":rows.iter().map(|&i| &task.observations[i].observation_id).collect::<Vec<_>>() }));
            }
        }
    }
    let mut visited = BTreeSet::new();
    let mut components = Vec::new();
    for start in 0..task.observations.len() {
        if visited.contains(&start) {
            continue;
        }
        let mut pending = vec![start];
        let mut members = Vec::new();
        while let Some(i) = pending.pop() {
            if !visited.insert(i) {
                continue;
            }
            members.push(i);
            pending.extend(&adjacent[i]);
        }
        let mut ids: Vec<_> = members
            .iter()
            .map(|&i| task.observations[i].observation_id.clone())
            .collect();
        ids.sort();
        let component_links: BTreeSet<_> = members
            .iter()
            .flat_map(|&i| links(&task.observations[i]))
            .collect();
        let train = members
            .iter()
            .any(|&i| task.observations[i].partition == Partition::Train);
        let test = members
            .iter()
            .any(|&i| task.observations[i].partition == Partition::Test);
        components.push(
            json!({"component_id":format!("dependency:{}",hash(&serde_json::to_vec(&ids).unwrap())),
            "observation_ids":ids,"links":component_links.iter().map(|(kind,key)|json!({"kind":kind,"key":key})).collect::<Vec<_>>(),"has_train":train,"has_test":test}),
        );
    }
    components.sort_by_key(|c| c["component_id"].as_str().unwrap().to_owned());
    let mut unsafe_physical = BTreeSet::new();
    // Only allowed target values participate. Test reference identities remain usable without Y_test.
    let allowed = |r: &&Observation| {
        r.partition == Partition::Train || task.policy.audit_mode == AuditMode::PostEvaluation
    };
    let mut reference_rows = BTreeMap::<(String, String), Vec<&Observation>>::new();
    for r in &task.observations {
        let can_read_value = allowed(&r);
        if can_read_value {
            reference_rows
                .entry(("physical".into(), r.physical_sample_id.clone()))
                .or_default()
                .push(r);
            if let Some(id) = reference_id(r) {
                reference_rows
                    .entry(("reference".into(), id.clone()))
                    .or_default()
                    .push(r);
            }
        }
        let nonexact = r
            .reference_status
            .as_deref()
            .is_some_and(|s| s != "exact" && s != "unknown");
        let invalid_metadata = [&r.reference_id, &r.reference_group_id, &r.reference_unit]
            .iter()
            .any(|v| v.as_ref().is_some_and(|s| s.trim().is_empty()));
        let invalid = can_read_value
            && (r.y.is_some_and(|y| !y.is_finite())
                || (r.y.is_some() && r.category.is_some())
                || (task.target_kind == TargetKind::Continuous && r.category.is_some())
                || (task.target_kind == TargetKind::Categorical && r.y.is_some()));
        let unit_mismatch = r
            .reference_unit
            .as_ref()
            .zip(task.target_unit.as_ref())
            .is_some_and(|(a, b)| a != b);
        if nonexact || invalid || unit_mismatch || invalid_metadata {
            let reason = if invalid_metadata {
                "INVALID_REFERENCE_METADATA"
            } else if invalid {
                "INVALID_REFERENCE_VALUE"
            } else if unit_mismatch {
                "REFERENCE_UNIT_MISMATCH"
            } else {
                "NONEXACT_REFERENCE"
            };
            issues.push(json!({"reason":reason,"observation_ids":[r.observation_id]}));
            if invalid || unit_mismatch || invalid_metadata {
                unsafe_physical.insert(r.physical_sample_id.clone());
            }
        }
    }
    for ((kind, key), rows) in reference_rows {
        let values: BTreeSet<_> = rows
            .iter()
            .filter_map(|r| match task.target_kind {
                TargetKind::Continuous => r.y.map(|v| {
                    if v == 0.0 {
                        "0".into()
                    } else {
                        format!("{:016x}", v.to_bits())
                    }
                }),
                TargetKind::Categorical => r.category.clone(),
            })
            .collect();
        let units: BTreeSet<_> = rows
            .iter()
            .filter_map(|r| r.reference_unit.as_ref().or(task.target_unit.as_ref()))
            .collect();
        if values.len() > 1 || units.len() > 1 {
            issues.push(
                json!({"reason":"CONTRADICTORY_REFERENCE","kind":kind,"key":key,
                "observation_ids":rows.iter().map(|r| &r.observation_id).collect::<Vec<_>>() }),
            );
            unsafe_physical.extend(rows.iter().map(|r| r.physical_sample_id.clone()));
        }
    }
    let counts = |part: Partition| {
        let rows: Vec<_> = task
            .observations
            .iter()
            .filter(|r| r.partition == part)
            .collect();
        let mut repeat_groups = BTreeMap::new();
        for r in &rows {
            *repeat_groups
                .entry((&r.physical_sample_id, context(task, r)))
                .or_insert(0) += 1;
        }
        json!({"acquisitions":rows.len(),
            "samples":rows.iter().map(|r| &r.sample_id).collect::<BTreeSet<_>>().len(),
            "physical_samples":rows.iter().map(|r| &r.physical_sample_id).collect::<BTreeSet<_>>().len(),
            "known_references":rows.iter().filter_map(|r| reference_id(r)).collect::<BTreeSet<_>>().len(),
            "missing_reference_acquisitions":rows.iter().filter(|r| reference_id(r).is_none()).count(),
            "missing_reference_status_acquisitions":rows.iter().filter(|r| r.reference_status.as_deref().is_none_or(|s|s=="unknown")).count(),
            "missing_reference_unit_acquisitions":rows.iter().filter(|r| r.reference_unit.is_none() && task.target_unit.is_none()).count(),
            "missing_instrument_or_campaign_acquisitions":rows.iter().filter(|r| !context(task,r).contains_key("instrument") || !context(task,r).contains_key("campaign")).count(),
            "declared_independence_groups":rows.iter().map(|r| &r.independence_group).collect::<BTreeSet<_>>().len(),
            "repeat_groups":repeat_groups.values().filter(|&&n|n>1).count(),
            "validation_groups":components.iter().filter(|c| c[if part == Partition::Train {"has_train"} else {"has_test"}]==true).count()})
    };
    let xy_blocked = !issues.is_empty();
    Audit {
        value: json!({"protocol_version":"domains.units.v0.1","train":counts(Partition::Train),"test":counts(Partition::Test),
        "known_reference_ids_total":task.observations.iter().filter_map(reference_id).collect::<BTreeSet<_>>().len(),
        "validation_groups_total":components.len(),
        "excluded_native_observation_ids":task.provenance.get("excluded_observation_ids").and_then(|s|serde_json::from_str::<Vec<String>>(s).ok()),
        "dependency_components":components,"reference_issues":issues,"xy_blocked":xy_blocked,
        "independence_qualification":"declared_constraints_only_not_verified_real_world_independence",
        "reference_precision":"unavailable_no_laboratory_tolerance_supplied"}),
        xy_blocked,
        unsafe_physical,
    }
}

/// Inventory all native and context-linked rows, including exclusions. Mean only explicitly eligible groups.
pub fn representation(
    task: &Task,
    audit: &Audit,
    methods: Option<&Methods>,
) -> Result<(Task, Value), String> {
    let mut groups = BTreeMap::new();
    for row in &task.observations {
        groups
            .entry((
                row.physical_sample_id.clone(),
                context(task, row),
                if row.partition == Partition::Train {
                    0
                } else {
                    1
                },
            ))
            .or_insert_with(Vec::new)
            .push(row);
    }
    let mut contexts = BTreeMap::<String, usize>::new();
    for (physical, _, _) in groups.keys() {
        *contexts.entry(physical.clone()).or_default() += 1;
    }
    let mut result = task.clone();
    result.observations.clear();
    let mut inventory = Vec::new();
    for ((physical, context, _), mut rows) in groups {
        rows.sort_by_key(|r| &r.observation_id);
        let types: BTreeSet<_> = rows
            .iter()
            .map(|r| r.repetition_type.as_deref().unwrap_or("unknown"))
            .collect();
        let sample_ids: BTreeSet<_> = rows.iter().map(|r| &r.sample_id).collect();
        let reason = if contexts[&physical] > 1 {
            Some("CROSS_CONTEXT_REQUIRES_PAIRED_PROTOCOL")
        } else if rows.len() > 1
            && (!context.contains_key("instrument") || !context.contains_key("campaign"))
        {
            Some("MISSING_REPEAT_CONTEXT")
        } else if rows.len() > 1
            && (types.len() != 1
                || !types
                    .iter()
                    .all(|t| matches!(*t, "rescan" | "repositioning" | "repreparation")))
        {
            Some("NONTECHNICAL_UNKNOWN_OR_MIXED_REPEAT_TYPE")
        } else if rows.len() > 1 && sample_ids.len() != 1 {
            Some("AMBIGUOUS_SAMPLE_KEYS")
        } else if rows.len() > 1 && audit.unsafe_physical.contains(&physical) {
            Some("CONTRADICTORY_REFERENCE_NO_AGGREGATION")
        } else if rows.iter().any(|r| r.x.iter().any(Option::is_none)) {
            Some("INCOMPLETE_X")
        } else {
            None
        };
        let ids: Vec<_> = rows.iter().map(|r| r.observation_id.clone()).collect();
        let mut output = rows[0].clone();
        if reason.is_none()
            && rows.len() > 1
            && task.policy.representation == Representation::TechnicalMean
        {
            output.observation_id = format!("mean:{}", hash(&serde_json::to_vec(&ids).unwrap()));
            if let Some(methods) = methods {
                output.x = (0..task.axis.len())
                    .map(|c| {
                        methods
                            .provider
                            .summary(&SummaryRequest {
                                values: rows.iter().map(|r| r.x[c].unwrap()).collect(),
                            })
                            .map(|s| Some(s.mean))
                            .map_err(|e| e.0)
                    })
                    .collect::<Result<_, _>>()?;
            }
        }
        inventory.push(json!({"physical_sample_id":physical,"sample_ids":sample_ids,"partition":rows[0].partition,
            "context":context,"observation_ids":ids,"repeat_types":types,
            "eligible":reason.is_none(),"reason":reason,"weight":if reason.is_none(){json!(1)}else{Value::Null},
            "representation_observation_id":if reason.is_none(){json!(output.observation_id)}else{Value::Null}}));
        if reason.is_none() {
            result.observations.push(output);
        }
    }
    if task.policy.representation == Representation::Native {
        result = task.clone();
    }
    // Preserve acquisition order for singleton-only tasks: alpha.2 and alpha.3 solver inputs match exactly.
    if task.policy.representation == Representation::TechnicalMean
        && inventory
            .iter()
            .all(|g| g["eligible"] == true && g["observation_ids"].as_array().unwrap().len() == 1)
    {
        result.observations = task.observations.clone();
    }
    let value = json!({"policy":task.policy.representation,"mean_execution":if methods.is_some(){"available"}else{"unavailable_no_provider"},"native_observation_ids":task.observations.iter().map(|r|&r.observation_id).collect::<Vec<_>>(),
        "sample_context_groups":inventory,"weighting":if task.policy.representation==Representation::TechnicalMean{"one_vote_per_eligible_physical_sample"}else{"native_acquisitions_geometry_requires_one_per_physical_sample"},
        "selected_population":{"train_observation_ids":result.observations.iter().filter(|r|r.partition==Partition::Train).map(|r|&r.observation_id).collect::<Vec<_>>(),
            "test_observation_ids":result.observations.iter().filter(|r|r.partition==Partition::Test).map(|r|&r.observation_id).collect::<Vec<_>>(),
            "excluded_acquisitions":task.observations.len()-inventory.iter().filter(|g|g["eligible"]==true || task.policy.representation==Representation::Native).map(|g|g["observation_ids"].as_array().unwrap().len()).sum::<usize>()},
        "cross_context":"linked_native_observations_retained_no_implicit_mean",
        "mean_backend":"Methods public summary; no local numerical mean kernel"});
    Ok((result, value))
}
