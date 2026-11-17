//! Replay WASM-produced public synthetic requests with the original recorded PCA scores.
//! No fit or numerical algorithm is implemented by this consumer.
use nirs4all_domains::{browser_factor, factor_methods::FactorMethods, hash};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{collections::BTreeMap, env, fs, path::Path};

#[derive(Deserialize)]
struct Replay {
    cases: Vec<Case>,
}
#[derive(Deserialize)]
struct Case {
    id: String,
    request: Value,
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let path = env::args().nth(1).ok_or("WASM_REQUEST_ARTIFACT_REQUIRED")?;
    let bytes = fs::read(path)?;
    let replay: Replay = serde_json::from_slice(&bytes)?;
    let library =
        env::var_os("N4DOMAINS_METHODS_LIBRARY").ok_or("N4DOMAINS_METHODS_LIBRARY_REQUIRED")?;
    let provider = FactorMethods::load(Path::new(&library))?;
    let mut reports = BTreeMap::new();
    for case in replay.cases {
        if reports.contains_key(&case.id) {
            return Err("DUPLICATE_FACTOR_CASE_ID".into());
        }
        let request = browser_factor::parse(&serde_json::to_string(&case.request)?)?;
        reports.insert(case.id, browser_factor::analyze(&request, &provider)?);
    }
    println!(
        "{}",
        serde_json::to_string(&json!({
            "protocol_version":"domains.factor_same_scores_native_replay.v1",
            "backend":"native", "provider_version":provider.version,
            "wasm_artifact_sha256":hash(&bytes), "reports":reports,
            "new_real_scientific_fits":0,"pca_refits":0
        }))?
    );
    Ok(())
}
