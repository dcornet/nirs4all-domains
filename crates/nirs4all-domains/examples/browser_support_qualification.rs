//! Execute the exact public synthetic WASM requests through the pinned native owner.
use nirs4all_domains::{browser_support, hash, support_methods::SupportMethods};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{collections::BTreeSet, env, fs, path::Path};

#[derive(Deserialize)]
struct Replay {
    fixture_sha256: String,
    cases: Vec<Case>,
    refusals: Vec<Refusal>,
}
#[derive(Deserialize)]
struct Case {
    id: String,
    request: Value,
}
#[derive(Deserialize)]
struct Refusal {
    id: String,
    request: Value,
    reason: String,
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let path = env::args().nth(1).ok_or("WASM_REQUEST_ARTIFACT_REQUIRED")?;
    let bytes = fs::read(path)?;
    let replay: Replay = serde_json::from_slice(&bytes)?;
    let library =
        env::var_os("N4DOMAINS_METHODS_LIBRARY").ok_or("N4DOMAINS_METHODS_LIBRARY_REQUIRED")?;
    let provider = SupportMethods::load(Path::new(&library))?;
    let mut ids = BTreeSet::new();
    let mut cases = Vec::new();
    let mut refused = Vec::new();
    for case in replay.cases {
        if !ids.insert(case.id.clone()) {
            return Err("DUPLICATE_SUPPORT_CASE_ID".into());
        }
        let request = browser_support::parse(&serde_json::to_string(&case.request)?)?;
        let result = browser_support::analyze(&request, &provider)?;
        cases.push(json!({"id":case.id,"request":case.request,"result":result}));
    }
    for case in replay.refusals {
        if !ids.insert(case.id.clone()) {
            return Err("DUPLICATE_SUPPORT_CASE_ID".into());
        }
        let raw = case
            .request
            .as_str()
            .map(str::to_owned)
            .unwrap_or(serde_json::to_string(&case.request)?);
        let reason = browser_support::parse(&raw)
            .err()
            .ok_or("ADMISSION_REFUSAL_EXPECTED")?;
        if !reason.contains(&case.reason) {
            return Err(format!("{}:{reason}", case.id).into());
        }
        refused
            .push(json!({"id":case.id,"reason":reason,"provider_calls":0,"request":case.request}));
    }
    println!(
        "{}",
        serde_json::to_string(&json!({
        "protocol_version":"domains.browser_train_fitted_support_native.v1","provider_version":provider.version,
        "wasm_artifact_sha256":hash(&bytes),"fixture_sha256":replay.fixture_sha256,
        "cases":cases,"refused_before_provider":refused,"pca_refits":0,"new_real_scientific_fits":0,
        "scope":"Same frozen train-only synthetic protocol executed once per request; no additional selection/refit"}))?
    );
    Ok(())
}
