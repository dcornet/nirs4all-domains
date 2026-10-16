//! Coverage resampling protocol; whole dependency components, conditional on the frozen train fit.
use crate::{contract::Observation, methods::Methods};
use nirs4all_preflight::{MethodsProvider, SummaryRequest};
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

pub fn coverage(
    rows: &[&Observation],
    outside: &[String],
    components: &BTreeMap<String, String>,
    methods: &Methods,
    draws: usize,
    seed: u64,
) -> Result<Value, String> {
    let outside: BTreeSet<_> = outside.iter().collect();
    let mut by_sample = BTreeMap::<String, Vec<f64>>::new();
    for row in rows {
        by_sample
            .entry(row.physical_sample_id.clone())
            .or_default()
            .push(if outside.contains(&row.observation_id) {
                1.0
            } else {
                0.0
            });
    }
    let mean = |values: Vec<f64>| {
        methods
            .provider
            .summary(&SummaryRequest { values })
            .map(|s| s.mean)
            .map_err(|e| e.0)
    };
    let mut blocks = BTreeMap::<String, Vec<f64>>::new();
    for (sample, flags) in by_sample {
        blocks
            .entry(components.get(&sample).cloned().unwrap_or(sample))
            .or_default()
            .push(mean(flags)?);
    }
    if blocks.len() < 2 {
        return Ok(
            json!({"status":"insufficient_data","reason":"TWO_HELD_OUT_COMPONENTS_REQUIRED"}),
        );
    }
    let keys: Vec<_> = blocks.keys().cloned().collect();
    let block_sizes: BTreeMap<_, _> = blocks.iter().map(|(k, v)| (k.clone(), v.len())).collect();
    let blocks: Vec<_> = blocks.into_values().collect();
    let estimate = mean(blocks.iter().flatten().copied().collect())?;
    let mut rng = ChaCha8Rng::seed_from_u64(seed);
    let mut replicates = Vec::with_capacity(draws);
    for _ in 0..draws {
        let mut values = Vec::new();
        for _ in 0..blocks.len() {
            values.extend(&blocks[rng.gen_range(0..blocks.len())]);
        }
        replicates.push(mean(values)?);
    }
    // Frozen nearest-rank order statistics define this protocol's percentile endpoints.
    let mut ordered = replicates.clone();
    ordered.sort_by(f64::total_cmp);
    let endpoint = |p: f64| {
        ordered[((p * draws as f64).ceil() as usize)
            .saturating_sub(1)
            .min(draws - 1)]
    };
    Ok(
        json!({"status":"computed","protocol_version":"domains.coverage_bootstrap.v0.1",
        "estimate":estimate,"interval_95":[endpoint(0.025),endpoint(0.975)],"draws":draws,"seed":seed,
        "resampling_unit":"whole_declared_dependency_component","statistic":"physical_sample_mean_of_acquisition_flags",
        "n_components":blocks.len(),"component_ids":keys,"physical_samples_per_component":block_sizes,
        "replicates":replicates,"rng":"rand_chacha 0.3.1 ChaCha8Rng",
        "conditional_on":"frozen train PCA and thresholds; no train-refit uncertainty estimated"}),
    )
}
