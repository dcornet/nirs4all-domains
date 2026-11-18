//! Replay the recorded public synthetic requests; restore only backend-own frozen evidence.
use nirs4all_domains::{browser_preprocessing, hash, preprocessing_execution::SensitivityMethods};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    env, fs,
    path::Path,
};

#[derive(Deserialize)]
struct Artifact {
    protocol_version: String,
    provider: Value,
    fixture_sha256: String,
    descriptor_bank_sha256: String,
    schema_validation: Value,
    cases: Vec<Case>,
    refusals: Vec<Refusal>,
    new_real_scientific_fits: u64,
}
#[derive(Deserialize)]
struct Case {
    id: String,
    request: Value,
    #[serde(default)]
    reference_case_id: Option<String>,
}
#[derive(Deserialize)]
struct Refusal {
    id: String,
    #[serde(default)]
    request: Option<Value>,
    #[serde(default)]
    request_json: Option<String>,
    reason: String,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let input = env::args().nth(1).ok_or("WASM_ARTIFACT_REQUIRED")?;
    let bytes = fs::read(input)?;
    let source: Artifact = serde_json::from_slice(&bytes)?;
    if source.protocol_version != "domains.browser_preprocessing_sensitivity_wasm.v1"
        || source.provider["version"] != "1.3.13+abi.2.20.0"
        || source.new_real_scientific_fits != 0
    {
        return Err("PINNED_PUBLIC_SYNTHETIC_WASM_ARTIFACT_REQUIRED".into());
    }
    if source.fixture_sha256
        != hash(include_bytes!(
            "../../../bindings/wasm/tests/preprocessing-fixtures.json"
        ))
        || source.descriptor_bank_sha256
            != hash(include_bytes!("../../../bindings/wasm/aom-bank.json"))
    {
        return Err("EXACT_QUALIFIED_FIXTURE_AND_BANK_REQUIRED".into());
    }
    let fixtures: Vec<Value> = serde_json::from_slice(include_bytes!(
        "../../../bindings/wasm/tests/preprocessing-fixtures.json"
    ))?;
    let computed: Vec<_> = fixtures
        .iter()
        .filter(|v| v["expect_refusal"] != true)
        .collect();
    let refused: Vec<_> = fixtures
        .iter()
        .filter(|v| v["expect_refusal"] == true)
        .collect();
    if source.cases.iter().map(|v| v.id.as_str()).ne(computed
        .iter()
        .map(|v| v["id"].as_str().expect("fixture ID")))
        || source.refusals.iter().map(|v| v.id.as_str()).ne(refused
            .iter()
            .map(|v| v["id"].as_str().expect("fixture ID")))
        || source.schema_validation["available"] != true
        || source.schema_validation["valid_inputs"] != source.cases.len()
        || source.schema_validation["valid_results"] != source.cases.len()
    {
        return Err("COMPLETE_SCHEMA_VALIDATED_FIXTURE_SET_REQUIRED".into());
    }
    for (case, fixture) in source.cases.iter().zip(computed) {
        if case.reference_case_id.as_deref() != fixture["reference_case_id"].as_str() {
            return Err("FIXTURE_REFERENCE_ANCESTOR_CHANGED".into());
        }
    }
    let library =
        env::var_os("N4DOMAINS_METHODS_LIBRARY").ok_or("N4DOMAINS_METHODS_LIBRARY_REQUIRED")?;
    let provider = SensitivityMethods::load(Path::new(&library))?;
    let library_sha256 = hash(&fs::read(&library)?);
    let (mut ids, mut reference_results, mut cases, mut refusals) = (
        BTreeSet::new(),
        BTreeMap::<String, Value>::new(),
        Vec::new(),
        Vec::new(),
    );
    for case in source.cases {
        if !ids.insert(case.id.clone()) {
            return Err("DUPLICATE_PREPROCESSING_CASE_ID".into());
        }
        let original = case.request;
        let mut actual = original.clone();
        if let Some(ancestor) = &case.reference_case_id {
            if actual["stage"] != "test_audit" {
                return Err("REFERENCE_ANCESTOR_ONLY_FOR_TEST_AUDIT".into());
            }
            actual["frozen_reference"] = reference_results
                .get(ancestor)
                .ok_or("EARLIER_NATIVE_REFERENCE_CASE_REQUIRED")?
                .clone();
        } else if actual["stage"] != "reference_only" || !actual["frozen_reference"].is_null() {
            return Err("EXPLICIT_NATIVE_REFERENCE_ANCESTOR_REQUIRED".into());
        }
        let request = browser_preprocessing::parse(&serde_json::to_string(&actual)?)?;
        let before = provider.call_count();
        let result = browser_preprocessing::analyze(&request, &provider)?;
        let result_json = serde_json::to_string(&result)?;
        let calls = provider.call_count() - before;
        if request.stage == "reference_only" {
            reference_results.insert(case.id.clone(), result.clone());
        }
        cases.push(json!({"id":case.id,"original_wasm_request":original,"request":actual,"reference_case_id":case.reference_case_id,"provider_calls":calls,"result":result,"result_json_sha256":hash(result_json.as_bytes()),"result_json":result_json}));
    }
    for case in source.refusals {
        if !ids.insert(case.id.clone()) {
            return Err("DUPLICATE_PREPROCESSING_CASE_ID".into());
        }
        let raw = match (&case.request_json, &case.request) {
            (Some(raw), None) => raw.clone(),
            (None, Some(v)) => serde_json::to_string(v)?,
            _ => return Err("EXACT_REFUSAL_REQUEST_REQUIRED".into()),
        };
        let before = provider.call_count();
        let reason = browser_preprocessing::parse(&raw)
            .and_then(|r| browser_preprocessing::analyze(&r, &provider))
            .err()
            .ok_or("GLOBAL_PRE_PROVIDER_REFUSAL_EXPECTED")?;
        if provider.call_count() != before {
            return Err("REFUSAL_EXECUTED_PROVIDER".into());
        }
        if reason != case.reason {
            return Err(format!("REFUSAL_REASON_MISMATCH:{}:{reason}", case.id).into());
        }
        refusals.push(json!({"id":case.id,"request":case.request,"request_json":case.request_json,"reason":reason,"provider_calls":0}));
    }
    println!(
        "{}",
        serde_json::to_string(
            &json!({"protocol_version":"domains.browser_preprocessing_sensitivity_native.v1","provider_version":provider.version,"library_sha256":library_sha256,"example_source_sha256":hash(include_bytes!("browser_preprocessing_qualification.rs")),"wasm_artifact_sha256":hash(&bytes),"fixture_sha256":source.fixture_sha256,"descriptor_bank_sha256":source.descriptor_bank_sha256,"cases":cases,"refused_before_provider":refusals,"new_real_scientific_fits":0,"request_policy":"Original requests/plans unchanged; only frozen_reference is replaced with the identified earlier native result."})
        )?
    );
    Ok(())
}
