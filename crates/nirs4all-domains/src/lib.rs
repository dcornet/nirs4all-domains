//! Task-specific protocols over public Preflight and Methods interfaces.
pub mod association;
mod bootstrap;
pub mod contract;
pub mod methods;
mod protocol;
pub mod structure;
mod units;
pub mod unsupervised;
pub mod x_structure;
pub use contract::*;
pub use protocol::{analyze, train_refit_stability, validate};
/// Export the exact comparison task through the same native mean and safety policy as analysis.
pub fn comparison_task(task: &Task, library: &std::path::Path) -> Result<Task, String> {
    validate(task)?;
    let mut sanitized = task.clone();
    if task.policy.audit_mode == AuditMode::PreTraining {
        for row in &mut sanitized.observations {
            if row.partition == Partition::Test {
                row.y = None;
                row.category = None;
            }
        }
    }
    let methods = methods::Methods::load(library)?;
    let audit = units::audit(&sanitized);
    let (mut view, membership) = units::representation(&sanitized, &audit, Some(&methods))?;
    view.provenance
        .insert("reference_xy_blocked".into(), audit.xy_blocked.to_string());
    for component in audit.value["dependency_components"]
        .as_array()
        .into_iter()
        .flatten()
    {
        for link in component["links"]
            .as_array()
            .into_iter()
            .flatten()
            .filter(|l| l["kind"] == "physical")
        {
            for row in &mut view.observations {
                if row.physical_sample_id == link["key"].as_str().unwrap() {
                    row.metadata.insert(
                        "validation_component_id".into(),
                        component["component_id"].as_str().unwrap().into(),
                    );
                }
            }
        }
    }
    view.provenance.insert(
        "representation_membership".into(),
        serde_json::to_string(&membership).map_err(|e| e.to_string())?,
    );
    Ok(view)
}
use sha2::{Digest, Sha256};

pub fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

/// Markdown contains the same evidence and unavailable states as JSON.
pub fn markdown(report: &Report) -> String {
    fn clean(s: &str) -> String {
        s.replace(['\n', '\r', '|'], " ")
            .replace('<', "&lt;")
            .replace('>', "&gt;")
    }
    let mut out=format!("# NIRS domains audit\n\nDataset: {} · source: {} · target: {} · split: {}\n\nStatus: **{}** · protocol: `{}` · origin: {}\n\nTest target accessed: **{}**\n\n",clean(&report.context.dataset_id),clean(&report.context.source_id),clean(report.context.target_id.as_deref().unwrap_or("absent")),clean(&report.context.split_id),report.status,report.protocol_version,clean(&report.data_origin),report.test_target_accessed);
    out.push_str("## Dimensions\n\n");
    for (dimension, status) in &report.dimensions {
        out.push_str(&format!("- {}: {}\n", clean(dimension), clean(status)));
    }
    out.push_str(
        "\n## Declared units and representation\n\n| Count | Train | Test |\n|---|---:|---:|\n",
    );
    for key in [
        "acquisitions",
        "samples",
        "physical_samples",
        "known_references",
        "missing_reference_acquisitions",
        "repeat_groups",
        "declared_independence_groups",
        "validation_groups",
        "missing_instrument_or_campaign_acquisitions",
    ] {
        out.push_str(&format!(
            "| {} | {} | {} |\n",
            key, report.unit_audit["train"][key], report.unit_audit["test"][key]
        ));
    }
    out.push_str(&format!("\nRepresentation: {}. X-Y blocked by reference audit: {}. Known references are counted by supplied ID; missing IDs remain unknown. Validation groups are declared dependency components, not verified independent laboratory units.\n",report.representations["policy"],report.unit_audit["xy_blocked"]));
    let mut exclusions = std::collections::BTreeMap::<String, usize>::new();
    if let Some(groups) = report.representations["sample_context_groups"].as_array() {
        for group in groups {
            if let Some(reason) = group["reason"].as_str() {
                *exclusions.entry(reason.into()).or_default() +=
                    group["observation_ids"].as_array().map_or(0, Vec::len);
            }
        }
    }
    for (reason, count) in exclusions {
        out.push_str(&format!(
            "\n- Ineligible for a homogeneous mean: {} acquisitions, {}.\n",
            count, reason
        ));
    }
    out.push_str("\n## Observations and actions\n\n");
    for f in &report.findings {
        out.push_str(&format!(
            "- **{}** → confidence: {} → {} → {}\n",
            clean(&f.observation),
            clean(&f.confidence),
            clean(&f.calibration_consequence),
            clean(&f.recommended_action)
        ));
    }
    out.push_str(
        "\n## Metrics\n\n| Metric | Status | Value | Unit / reason |\n|---|---|---|---|\n",
    );
    for m in &report.metrics {
        out.push_str(&format!(
            "| {} | {:?} | {} | {} |\n",
            m.metric_id,
            m.status,
            clean(&m.value.to_string()),
            clean(m.reason.as_deref().unwrap_or(&m.unit))
        ));
    }
    out.push_str("\n## Limits\n\n");
    for s in &report.limitations {
        out.push_str(&format!("- {}\n", clean(s)));
    }
    out.push_str("\nThe adjacent JSON preserves the fitted state, observation IDs, distributions, parameters, engine versions and the full Preflight report.\n");
    out
}
