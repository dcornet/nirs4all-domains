//! Representation-scoped protocol over existing public Methods/Preflight kernels.
use crate::{
    hash,
    methods::{HdbscanParameters, Methods, SelectionMethod},
    x_structure::XRequest,
};
use nirs4all_preflight::{MethodsProvider, NearestNeighborsRequest, SummaryRequest};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{collections::BTreeSet, path::Path};

pub const PROTOCOL: &str = "domains.unsupervised.v0.1";
const CALL_PRODUCTS: usize = 250_000_000;
const TOTAL_PRODUCTS: usize = 750_000_000;

#[derive(Debug, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct UnsupervisedRequest {
    pub spectral: XRequest,
    pub representation: String,
    /// Empty only for a resampling fit that requests no neighborhoods.
    pub query_ids: Vec<String>,
    pub include_neighbors: bool,
}

fn computed(value: Value) -> Value {
    json!({"status":"computed","reason":null,"value":value})
}
fn unavailable(reason: &str) -> Value {
    json!({"status":"unavailable","reason":reason,"value":null})
}

fn summary(m: &Methods, values: Vec<f64>) -> Result<Value, String> {
    if values.is_empty() {
        return Ok(unavailable("EMPTY_SUMMARY_POPULATION"));
    }
    let s = m
        .provider
        .summary(&SummaryRequest { values })
        .map_err(|e| e.0)?;
    Ok(computed(
        json!({"count":s.count,"min":s.min,"max":s.max,"mean":s.mean,
        "sd":s.sample_sd,"q25":s.q25,"median":s.median,"q75":s.q75}),
    ))
}

/// Split queries only. Every native call sees the exact same complete reference.
fn neighbors(
    m: &Methods,
    rows: &[Vec<f64>],
    selected: &[usize],
    ids: &[String],
) -> Result<Value, String> {
    let n = rows.len();
    let p = rows[0].len();
    let k = 8.min(n - 1);
    let products = selected
        .len()
        .checked_mul(n)
        .and_then(|v| v.checked_mul(p))
        .ok_or("NEIGHBOR_WORK_OVERFLOW")?;
    if products > TOTAL_PRODUCTS {
        return Err("TOTAL_NEIGHBOR_PRODUCT_BUDGET_EXCEEDED".into());
    }
    let batch = CALL_PRODUCTS.checked_div(n * p).unwrap_or(0).max(1);
    let groups = (0..n as i64).collect::<Vec<_>>();
    let mut distances = Vec::new();
    let mut indices = Vec::new();
    let mut calls = 0;
    for selection in selected.chunks(batch) {
        let r = m
            .provider
            .nearest_neighbors(&NearestNeighborsRequest {
                query: selection.iter().map(|i| rows[*i].clone()).collect(),
                reference: rows.to_vec(),
                query_group_ids: selection.iter().map(|i| *i as i64).collect(),
                reference_group_ids: groups.clone(),
                k,
            })
            .map_err(|e| e.0)?;
        if r.distances.iter().flatten().any(Option::is_none) {
            return Err("INCOMPLETE_NATIVE_NEIGHBORS".into());
        }
        distances.extend(
            r.distances
                .into_iter()
                .map(|r| r.into_iter().map(Option::unwrap).collect::<Vec<_>>()),
        );
        indices.extend(r.indices);
        calls += 1;
    }
    let mut ranks = Vec::new();
    for rank in [1, 4, 8].into_iter().filter(|rank| *rank <= k) {
        ranks.push(json!({"rank":rank,"distance_summary":summary(m,distances.iter().map(|r|r[rank-1]).collect())?}));
    }
    Ok(
        json!({"n_reference":n,"n_query":selected.len(),"query_ids":selected.iter().map(|i|&ids[*i]).collect::<Vec<_>>(),
        "query_indices":selected,"mode":if selected.len()==n {"complete_source"}else{"query_subset"},
        "k":k,"reference_indices":indices,"distances":distances,"rank_summaries":ranks,
        "native_calls":calls,"distance_products":products,"self_exclusion":"observation identity only",
        "reference_population_preserved":true,"approximate":false}),
    )
}

pub fn characterize(r: &UnsupervisedRequest, library: &Path) -> Result<Value, String> {
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
            .any(|v| v.len() != p || v.iter().any(|a| !a.is_finite()))
        || !["raw", "snv"].contains(&r.representation.as_str())
        || ![
            "verified_physical_identity",
            "declared_but_unverified_identity",
            "observation_identity_only",
            "identity_unavailable",
        ]
        .contains(&x.identity_evidence.as_str())
    {
        return Err("INVALID_UNSUPERVISED_SOURCE".into());
    }
    if n.checked_mul(p).is_none_or(|v| v > 10_000_000)
        || n.checked_mul(n)
            .and_then(|v| v.checked_mul(k))
            .is_none_or(|v| v > 250_000_000)
        || p.checked_mul(p)
            .and_then(|v| v.checked_mul(k))
            .is_none_or(|v| v > 250_000_000)
    {
        return Err("FULL_POPULATION_PCA_BUDGET_EXCEEDED".into());
    }
    let unique = r.query_ids.iter().collect::<BTreeSet<_>>();
    if unique.len() != r.query_ids.len()
        || r.query_ids.iter().any(|id| !x.observation_ids.contains(id))
        || (r.include_neighbors && r.query_ids.is_empty())
        || (!r.include_neighbors && !r.query_ids.is_empty())
    {
        return Err("DECLARED_QUERY_IDENTITIES_REQUIRED".into());
    }
    let selected = r
        .query_ids
        .iter()
        .map(|id| x.observation_ids.iter().position(|a| a == id).unwrap())
        .collect::<Vec<_>>();
    // Check work before fitting, not after an expensive native operation.
    if r.include_neighbors
        && selected
            .len()
            .checked_mul(n)
            .and_then(|v| v.checked_mul(p))
            .is_none_or(|v| v > TOTAL_PRODUCTS)
    {
        return Err("TOTAL_NEIGHBOR_PRODUCT_BUDGET_EXCEEDED".into());
    }
    let m = Methods::load(library)?;
    let fit = m.fit_flexible(&x.spectra, k)?;
    if fit.covariance_trace <= 0. {
        return Err("ZERO_SPECTRAL_VARIANCE".into());
    }
    let mut settings = Vec::new();
    for size in [8, 12] {
        let parameters = HdbscanParameters {
            min_cluster_size: size,
            min_samples: 4,
            selection_method: SelectionMethod::Eom,
            allow_single_cluster: false,
        };
        match m.hdbscan(&fit.train_scores, &parameters) {
            Ok(h) => settings.push(computed(json!({"min_cluster_size":size,"min_samples":4,
                "n_clusters":h.n_clusters,"labels":h.labels,
                "membership_summary":summary(&m,h.membership_strengths)?,
                "noise_fraction":h.labels.iter().filter(|v|**v<0).count() as f64/n as f64,
                "nonfinite_diagnostics":h.nonfinite_diagnostics}))),
            Err(e) => settings.push(unavailable(&e.reason)),
        }
    }
    let neighborhoods = if r.include_neighbors {
        computed(json!({
            "full_axis":neighbors(&m,&x.spectra,&selected,&x.observation_ids)?,
            "pca":neighbors(&m,&fit.train_scores,&selected,&x.observation_ids)?
        }))
    } else {
        unavailable("NOT_REQUESTED_FOR_RESAMPLING_FIT")
    };
    let effective = fit.full_moments.map_or_else(
        || {
            unavailable(
                fit.full_moments_unavailable_reason
                    .as_deref()
                    .unwrap_or("EXACT_FULL_MOMENTS_UNAVAILABLE"),
            )
        },
        |v| computed(json!(v[0] * v[0] / v[1])),
    );
    Ok(json!({"schema_version":1,"protocol_version":PROTOCOL,
        "source_id":x.source_id,"representation":r.representation,"n_observations":n,"n_bands":p,
        "axis_unit":x.axis_unit,"axis_sha256":hash(&serde_json::to_vec(&x.axis).unwrap()),
        "observation_ids_sha256":hash(&serde_json::to_vec(&x.observation_ids).unwrap()),
        "input_sha256":hash(&serde_json::to_vec(r).map_err(|e|e.to_string())?),
        "provider":{"version":m.version,"abi":m.abi,"binary_sha256":hash(&std::fs::read(library).map_err(|e|e.to_string())?)},
        "pca":{"full_trace":fit.covariance_trace,"eigenvalues":fit.eigenvalues,
            "retained_variance_fraction":fit.eigenvalues.iter().sum::<f64>()/fit.covariance_trace,"backend":fit.backend},
        "effective_dimension":effective,"cluster_settings":settings,"neighborhoods":neighborhoods,
        "transport_only_scores":fit.train_scores,"test_target_accessed":false,
        "predictive_dependence":unavailable("NO_SUPERVISED_EXPERIMENT_IN_ALPHA12")}))
}
