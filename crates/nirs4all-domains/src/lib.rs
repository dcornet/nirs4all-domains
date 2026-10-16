//! Task-specific protocols over public Preflight and Methods interfaces.
pub mod contract;
pub mod methods;
mod protocol;
mod units;
pub use contract::*;
pub use protocol::{analyze, validate};
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
