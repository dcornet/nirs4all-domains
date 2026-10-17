//! Observation-scoped descriptive X evidence; no physical identity is inferred.
use crate::{
    hash,
    methods::{HdbscanParameters, Methods, SelectionMethod},
};
use nirs4all_preflight::{MethodsProvider, NearestNeighborsRequest, SummaryRequest};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{collections::BTreeSet, path::Path};

pub const PROTOCOL: &str = "domains.adaptive_structure.v0.1";

#[derive(Debug, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct XRequest {
    pub source_id: String,
    pub observation_ids: Vec<String>,
    pub identity_evidence: String,
    pub axis: Vec<f64>,
    pub axis_unit: String,
    pub spectra: Vec<Vec<f64>>,
}

fn unavailable(reason: &str) -> Value {
    json!({"status":"unavailable","reason":reason,"value":null})
}
fn computed(value: Value) -> Value {
    json!({"status":"computed","reason":null,"value":value})
}

pub fn characterize(request: &XRequest, library: &Path) -> Result<Value, String> {
    let n = request.spectra.len();
    let p = request.axis.len();
    let k = 20.min(p).min(n.saturating_sub(1));
    if n < 3
        || p == 0
        || request.observation_ids.len() != n
        || request.observation_ids.iter().any(String::is_empty)
        || request
            .observation_ids
            .iter()
            .collect::<BTreeSet<_>>()
            .len()
            != n
        || request.axis.iter().any(|v| !v.is_finite())
        || request.axis.windows(2).any(|w| w[0] >= w[1])
        || request
            .spectra
            .iter()
            .any(|r| r.len() != p || r.iter().any(|v| !v.is_finite()))
        || ![
            "verified_physical_identity",
            "declared_but_unverified_identity",
            "observation_identity_only",
            "identity_unavailable",
        ]
        .contains(&request.identity_evidence.as_str())
    {
        return Err("INVALID_SCOPED_SPECTRAL_INPUT".into());
    }
    if n.checked_mul(p).is_none_or(|v| v > 10_000_000)
        || n.checked_mul(n)
            .and_then(|v| v.checked_mul(k))
            .is_none_or(|v| v > 250_000_000)
        || p.checked_mul(p)
            .and_then(|v| v.checked_mul(k))
            .is_none_or(|v| v > 250_000_000)
    {
        return Err("FULL_POPULATION_GEOMETRY_BUDGET_EXCEEDED".into());
    }
    let m = Methods::load(library)?;
    let fit = m.fit_flexible(&request.spectra, k)?;
    if fit.covariance_trace <= 0.0 {
        return Err("ZERO_SPECTRAL_VARIANCE".into());
    }
    let summary = |values: Vec<f64>| -> Result<Value, String> {
        let s = m
            .provider
            .summary(&SummaryRequest { values })
            .map_err(|e| e.0)?;
        Ok(
            json!({"count":s.count,"min":s.min,"max":s.max,"mean":s.mean,"sd":s.sample_sd,"q25":s.q25,"median":s.median,"q75":s.q75}),
        )
    };
    let neighbors = |rows: Vec<Vec<f64>>| -> Result<Vec<f64>, String> {
        let codes = (0..n as i64).collect::<Vec<_>>();
        let result = m
            .provider
            .nearest_neighbors(&NearestNeighborsRequest {
                query: rows.clone(),
                reference: rows,
                query_group_ids: codes.clone(),
                reference_group_ids: codes,
                k: 1,
            })
            .map_err(|e| e.0)?;
        result
            .distances
            .into_iter()
            .map(|r| r[0].ok_or_else(|| "NO_OTHER_OBSERVATION".into()))
            .collect()
    };
    let projected = neighbors(fit.train_scores.clone())?;
    let raw = if n
        .checked_mul(n)
        .and_then(|v| v.checked_mul(p))
        .is_some_and(|v| v <= 250_000_000)
    {
        let distances = neighbors(request.spectra.clone())?;
        let scale = fit.covariance_trace.sqrt();
        computed(
            json!({"definition":"Euclidean original complete-axis spectra; self observation excluded",
            "summary":summary(distances.clone())?,"normalization":"sqrt(full covariance trace)","scale":scale,
            "tolerance_sensitivity":([1e-10,1e-8,1e-6].map(|t|json!({"relative_tolerance":t,"absolute_tolerance":t*scale,
                "n_observations_with_close_neighbor":distances.iter().filter(|v|**v<=t*scale).count()})))}),
        )
    } else {
        unavailable("RAW_NEIGHBOR_PRODUCT_BUDGET_EXCEEDED")
    };
    let mut clustering = Vec::new();
    for size in [8, 12] {
        let params = HdbscanParameters {
            min_cluster_size: size,
            min_samples: 4,
            selection_method: SelectionMethod::Eom,
            allow_single_cluster: false,
        };
        match m.hdbscan(&fit.train_scores, &params) {
            Ok(f) => clustering.push(computed(
                json!({"min_cluster_size":size,"min_samples":4,"labels":f.labels,
                    "membership_summary":summary(f.membership_strengths.clone())?,
                "n_clusters":f.labels.iter().filter(|v|**v>=0).collect::<BTreeSet<_>>().len(),
                "noise_fraction":f.labels.iter().filter(|v|**v<0).count() as f64/n as f64}),
            )),
            Err(e) => clustering.push(unavailable(&e.reason)),
        }
    }
    let agreement = if clustering.iter().all(|v| v["status"] == "computed") {
        let labels = |i: usize| {
            clustering[i]["value"]["labels"]
                .as_array()
                .unwrap()
                .iter()
                .map(|v| v.as_i64().unwrap())
                .collect::<Vec<_>>()
        };
        match m
            .adjusted_rand_index(&labels(0), &labels(1))
            .map_err(|e| e.reason)?
        {
            Some(v) => computed(json!(v)),
            None => unavailable("UNDEFINED_NATIVE_ARI"),
        }
    } else {
        unavailable("CLUSTERING_UNAVAILABLE")
    };
    Ok(
        json!({"schema_version":1,"protocol_version":PROTOCOL,"source_id":request.source_id,
        "input_sha256":hash(&serde_json::to_vec(request).map_err(|e|e.to_string())?),
        "identity_evidence":request.identity_evidence,"n_observations":n,"n_bands":p,
        "axis_unit":request.axis_unit,"axis_sha256":hash(&serde_json::to_vec(&request.axis).unwrap()),
        "observation_ids_sha256":hash(&serde_json::to_vec(&request.observation_ids).unwrap()),
        "provider":{"name":"Methods","version":m.version,"abi":m.abi,"binary_sha256":hash(&std::fs::read(library).map_err(|e|e.to_string())?)},
        "x_structure":computed(json!({"full_trace":fit.covariance_trace,"eigenvalues":fit.eigenvalues,
            "retained_variance_fraction":fit.eigenvalues.iter().sum::<f64>()/fit.covariance_trace,"backend":fit.backend})),
        "effective_dimension":fit.full_moments.map_or_else(||unavailable(fit.full_moments_unavailable_reason.as_deref().unwrap_or("FULL_MOMENTS_UNAVAILABLE")),|v|computed(json!(v[0]*v[0]/v[1]))),
        "spectral_neighborhood_concentration":computed(json!({"definition":"Euclidean retained PCA scores, all returned components, self observation excluded","summary":summary(projected)?})),
        "near_duplicate_proximity":raw,"cluster_settings":clustering,"parameter_ari_including_noise":agreement,
        "structural_stability":unavailable("NO_COMPONENT_RESAMPLING_IN_BROAD_SCREEN; PARAMETER_AGREEMENT_IS_NOT_STABILITY"),
        "target_structure_association":unavailable("X_ONLY_INPUT_HAS_NO_TARGET"),
        "predictive_structural_dependence":unavailable("X_STRUCTURE_DOES_NOT_ESTABLISH_MODEL_RELIANCE"),
        "test_target_accessed":false,"limitations":["Observation-scoped descriptive population; no physical independence or nuisance mechanism inferred.",
            "PCA proximity may conceal omitted-axis differences. Raw proximity is separately budgeted.","No-cluster or missing-metadata outcomes do not establish low structural dependence."]}),
    )
}
