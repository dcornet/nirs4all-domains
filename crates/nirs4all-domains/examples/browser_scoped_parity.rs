//! Replay the public synthetic scoped wire fixtures through the native owner.
//! This example contains no numerical kernel or alternative scientific oracle.
use nirs4all_domains::{browser_scoped, hash};
use nirs4all_preflight::native::NativeMethodsProvider;
use serde::Deserialize;
use serde_json::{json, Value};
use std::{collections::BTreeMap, env, fs};

#[derive(Deserialize)]
struct Fixtures {
    schema_version: u32,
    protocol_version: String,
    source_content_utf8: String,
    source_content_sha256: String,
    fixtures: Vec<Fixture>,
}
#[derive(Deserialize)]
struct Fixture {
    id: String,
    input: browser_scoped::ScopedRequest,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let fixture_path = env::args().nth(1).ok_or("FIXTURE_FILE_ARGUMENT_REQUIRED")?;
    let bytes = fs::read(fixture_path)?;
    let fixtures: Fixtures = serde_json::from_slice(&bytes)?;
    if fixtures.schema_version != 1
        || fixtures.protocol_version != "domains.browser_scoped_parity_fixtures.v1"
        || hash(fixtures.source_content_utf8.as_bytes()) != fixtures.source_content_sha256
    {
        return Err("INVALID_SYNTHETIC_SCOPED_FIXTURE_BINDING".into());
    }
    let library =
        env::var_os("N4DOMAINS_METHODS_LIBRARY").ok_or("N4DOMAINS_METHODS_LIBRARY_REQUIRED")?;
    let provider = NativeMethodsProvider::load(library).map_err(|error| error.reason)?;
    let mut reports = BTreeMap::<String, Value>::new();
    for fixture in fixtures.fixtures {
        if reports.contains_key(&fixture.id) {
            return Err("DUPLICATE_SCOPED_PARITY_FIXTURE_ID".into());
        }
        if fixture.input.dataset.content_sha256 != fixtures.source_content_sha256 {
            return Err("SCOPED_FIXTURE_SOURCE_CONTENT_MISMATCH".into());
        }
        reports.insert(
            fixture.id,
            browser_scoped::analyze(&fixture.input, &provider)?,
        );
    }
    println!(
        "{}",
        serde_json::to_string(&json!({
            "schema_version":1,"protocol_version":"domains.browser_scoped_parity.v1",
            "backend":"native","fixture_file_sha256":hash(&bytes),
            "source_content_sha256":fixtures.source_content_sha256,
            "provider_contract":"nirs4all_preflight::native::NativeMethodsProvider",
            "synthetic_operation_count":reports.len(),"reports":reports,
            "new_real_scientific_fits":0
        }))?
    );
    Ok(())
}
