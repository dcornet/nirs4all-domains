//! Synthetic native/WASM protocol parity. No scientific kernel is implemented here.
use nirs4all_domains::{browser, hash};
use nirs4all_preflight::native::NativeMethodsProvider;
use serde::Deserialize;
use serde_json::{json, Value};
use std::{collections::BTreeMap, env, fs};

#[derive(Deserialize)]
struct Fixtures {
    fixtures: Vec<Fixture>,
}
#[derive(Deserialize)]
struct Fixture {
    id: String,
    input: browser::BrowserRequest,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let fixture_path = env::args().nth(1).ok_or("FIXTURE_FILE_ARGUMENT_REQUIRED")?;
    let bytes = fs::read(fixture_path)?;
    let fixtures: Fixtures = serde_json::from_slice(&bytes)?;
    let library =
        env::var_os("N4DOMAINS_METHODS_LIBRARY").ok_or("N4DOMAINS_METHODS_LIBRARY_REQUIRED")?;
    let provider = NativeMethodsProvider::load(library).map_err(|error| error.reason)?;
    let mut reports = BTreeMap::<String, Value>::new();
    for fixture in fixtures.fixtures {
        if reports.contains_key(&fixture.id) {
            return Err("DUPLICATE_PARITY_FIXTURE_ID".into());
        }
        reports.insert(fixture.id, browser::analyze(&fixture.input, &provider)?);
    }
    println!(
        "{}",
        serde_json::to_string(&json!({
            "schema_version":1,"protocol_version":"domains.browser_parity.v1",
            "backend":"native","fixture_file_sha256":hash(&bytes),"reports":reports,
            "new_real_scientific_fits":0
        }))?
    );
    Ok(())
}
