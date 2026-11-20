//! Bounded synthetic transport for same-input owner-API attribution, never a parity gate.
use nirs4all_domains::{
    browser_support::SupportProvider, hash, preprocessing_execution::SensitivityMethods,
};
use serde_json::{json, Value};
use std::{env, fs, path::Path};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let input = env::args().nth(1).ok_or("ISOLATION_REQUESTS_REQUIRED")?;
    let bytes = fs::read(input)?;
    if bytes.len() > 4_000_000 {
        return Err("ISOLATION_INPUT_BUDGET".into());
    }
    let source: Value = serde_json::from_slice(&bytes)?;
    if source["protocol_version"] != "domains.f43_same_input_requests.v1"
        || source["synthetic_only"] != true
        || source["provider_version"] != "1.3.13+abi.2.20.0"
    {
        return Err("EXACT_SYNTHETIC_PROVIDER_SCOPE_REQUIRED".into());
    }
    let requests = source["requests"]
        .as_array()
        .ok_or("REQUEST_ARRAY_REQUIRED")?;
    if requests.is_empty() || requests.len() > 256 {
        return Err("ISOLATION_REQUEST_BUDGET".into());
    }
    let library = env::var_os("N4DOMAINS_METHODS_LIBRARY").ok_or("METHODS_LIBRARY_REQUIRED")?;
    let provider = SensitivityMethods::load(Path::new(&library))?;
    let mut results = Vec::new();
    for item in requests {
        let operation = item["operation"].as_str().ok_or("OPERATION_REQUIRED")?;
        if ![
            "preprocess_fit",
            "preprocess_transform",
            "preprocess_destroy",
            "pca",
            "factor_descriptive",
            "correlation_descriptive",
        ]
        .contains(&operation)
        {
            return Err("ISOLATION_OPERATION_NOT_PERMITTED".into());
        }
        let mut request = item["request"].clone();
        let mut input_f64 = serde_json::Map::new();
        // Exact IEEE-754 transport avoids attributing decimal-parser differences to
        // the public numerical APIs. It changes no value or estimator parameter.
        if let Some(fields) = item["f64_fields"].as_object() {
            for (field, value) in fields {
                if !["matrix", "scores", "values"].contains(&field.as_str()) {
                    return Err("ISOLATION_FLOAT_FIELD_NOT_PERMITTED".into());
                }
                let mut encoded = Vec::new();
                request[field] = decode_f64(value, &mut encoded)?;
                input_f64.insert(field.clone(), json!(hash(&encoded)));
            }
        }
        let result = provider
            .execute(operation, &request)
            .map_err(|e| format!("{} / {operation}: {}", item["id"], e.reason))?;
        results.push(json!({"id":item["id"],"operation":operation,
            "input_f64_le_sha256":input_f64,"result":result}));
    }
    println!(
        "{}",
        serde_json::to_string(&json!({
            "protocol_version":"domains.f43_same_input_native.v1",
            "status":"diagnostic_only", "provider_version":provider.version,
            "library_sha256":hash(&fs::read(library)?),"input_sha256":hash(&bytes),
            "results":results,"new_real_scientific_fits":0
        }))?
    );
    Ok(())
}

fn decode_f64(value: &Value, bytes: &mut Vec<u8>) -> Result<Value, Box<dyn std::error::Error>> {
    if let Some(items) = value.as_array() {
        if items.len() > 25_000 || bytes.len() > 8_000_000 {
            return Err("ISOLATION_MATRIX_BUDGET".into());
        }
        return items
            .iter()
            .map(|v| decode_f64(v, bytes))
            .collect::<Result<Vec<_>, _>>()
            .map(Value::Array);
    }
    let encoded = value.as_str().ok_or("F64_HEX_REQUIRED")?;
    if encoded.len() != 16 {
        return Err("F64_HEX_WIDTH".into());
    }
    let bits = u64::from_str_radix(encoded, 16)?;
    let number = f64::from_bits(bits);
    if !number.is_finite() {
        return Err("F64_NONFINITE".into());
    }
    bytes.extend(bits.to_le_bytes());
    Ok(json!(number))
}
