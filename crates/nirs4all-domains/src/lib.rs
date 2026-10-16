//! Task-specific protocols over public Preflight and Methods interfaces.
pub mod contract;
pub mod methods;
mod protocol;
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
