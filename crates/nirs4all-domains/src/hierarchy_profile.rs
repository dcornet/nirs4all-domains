//! One bounded X-only hierarchy fit using existing public Methods kernels.
//! Separate from the byte-frozen historical unsupervised transport.
use crate::{
    hash,
    methods::{HdbscanParameters, Methods},
    x_structure::XRequest,
};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{collections::BTreeSet, path::Path};

pub const PROTOCOL: &str = "domains.hierarchy_profile.v1";

#[derive(Debug, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct HierarchyRequest {
    pub spectral: XRequest,
    /// Supplied representation; callers apply public Methods SNV upstream.
    pub representation: String,
    pub parameters: HdbscanParameters,
}

pub fn characterize(r: &HierarchyRequest, library: &Path) -> Result<Value, String> {
    let x = &r.spectral;
    let n = x.spectra.len();
    let p = x.axis.len();
    let k = 20.min(p).min(n.saturating_sub(1));
    if n < 3
        || p == 0
        || x.observation_ids.len() != n
        || x.observation_ids.iter().any(String::is_empty)
        || x.observation_ids.iter().collect::<BTreeSet<_>>().len() != n
        || x.axis.iter().any(|v| !v.is_finite())
        || x.axis.windows(2).any(|v| v[0] >= v[1])
        || x.spectra
            .iter()
            .any(|row| row.len() != p || row.iter().any(|v| !v.is_finite()))
        || !["raw", "snv"].contains(&r.representation.as_str())
        || ![
            "verified_physical_identity",
            "declared_but_unverified_identity",
            "observation_identity_only",
            "identity_unavailable",
        ]
        .contains(&x.identity_evidence.as_str())
        || r.parameters.min_cluster_size < 2
        || r.parameters.min_samples < 1
        || r.parameters.min_samples > n
    {
        return Err("INVALID_HIERARCHY_PROFILE_REQUEST".into());
    }
    if n.checked_mul(p).is_none_or(|v| v > 10_000_000)
        || n.checked_mul(n)
            .and_then(|v| v.checked_mul(k))
            .is_none_or(|v| v > 250_000_000)
        || p.checked_mul(p)
            .and_then(|v| v.checked_mul(k))
            .is_none_or(|v| v > 250_000_000)
    {
        return Err("FULL_POPULATION_HIERARCHY_BUDGET_EXCEEDED".into());
    }
    let methods = Methods::load(library)?;
    let fit = methods.fit_flexible(&x.spectra, k)?;
    if fit.covariance_trace <= 0. {
        return Err("ZERO_SPECTRAL_VARIANCE".into());
    }
    let hierarchy = methods
        .hdbscan(&fit.train_scores, &r.parameters)
        .map_err(|f| f.reason)?;
    Ok(json!({"schema_version":1,"protocol_version":PROTOCOL,
        "source_id":x.source_id,"representation":r.representation,
        "identity_evidence":x.identity_evidence,"n_observations":n,"n_bands":p,
        "axis_unit":x.axis_unit,
        "axis_sha256":hash(&serde_json::to_vec(&x.axis).map_err(|e|e.to_string())?),
        "observation_ids_sha256":hash(&serde_json::to_vec(&x.observation_ids).map_err(|e|e.to_string())?),
        "input_sha256":hash(&serde_json::to_vec(r).map_err(|e|e.to_string())?),
        "provider":{"version":methods.version,"abi":methods.abi,
            "binary_sha256":hash(&std::fs::read(library).map_err(|e|e.to_string())?)},
        "pca":{"full_trace":fit.covariance_trace,"eigenvalues":fit.eigenvalues,
            "retained_variance_fraction":fit.eigenvalues.iter().sum::<f64>()/fit.covariance_trace,
            "backend":fit.backend},
        "parameters":r.parameters,"hdbscan":hierarchy,"test_target_accessed":false}))
}
