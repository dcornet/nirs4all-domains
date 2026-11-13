//! WASM transport only. The provider runs synchronously in the same worker.
use crate::browser::{self, PredictionIntent};
use js_sys::Function;
use nirs4all_preflight::*;
use serde::{de::DeserializeOwned, Deserialize, Serialize};
use wasm_bindgen::prelude::*;

struct CallbackProvider<'a>(&'a Function);
#[derive(Deserialize)]
#[serde(rename_all = "snake_case")]
enum Reply<T> {
    Ok(T),
    ProviderError(WireError),
}
#[derive(Deserialize)]
#[serde(untagged)]
enum WireError {
    Methods {
        methods_status: i32,
        message: String,
    },
    Adapter(ProviderError),
}
impl CallbackProvider<'_> {
    fn invoke<T: DeserializeOwned>(
        &self,
        operation: &str,
        request: &impl Serialize,
    ) -> Result<T, ProviderError> {
        let request = serde_json::to_string(request)
            .map_err(|_| ProviderError::internal("REQUEST_SERIALIZATION_FAILED"))?;
        let result = self
            .0
            .call2(
                &JsValue::NULL,
                &JsValue::from_str(operation),
                &JsValue::from_str(&request),
            )
            .map_err(|_| ProviderError::internal("METHODS_CALLBACK_FAILED"))?;
        let text = result
            .as_string()
            .ok_or_else(|| ProviderError::internal("METHODS_CALLBACK_MUST_RETURN_JSON_STRING"))?;
        match serde_json::from_str(&text)
            .map_err(|_| ProviderError::internal("METHODS_CALLBACK_INVALID_RESPONSE"))?
        {
            Reply::Ok(value) => Ok(value),
            Reply::ProviderError(WireError::Adapter(error)) => Err(error),
            Reply::ProviderError(WireError::Methods {
                methods_status,
                message,
            }) => Err(ProviderError::from_methods_error(methods_status, &message)),
        }
    }
}
impl MethodsProvider for CallbackProvider<'_> {
    fn capabilities(&self) -> Vec<Capability> {
        self.invoke("capabilities", &serde_json::json!({}))
            .unwrap_or_default()
    }
    fn pca(&self, r: &PcaRequest) -> Result<PcaDiagnostics, ProviderError> {
        self.invoke("pca", r)
    }
    fn repeatability(
        &self,
        _: &RepeatabilityRequest,
    ) -> Result<RepeatabilityDiagnostics, ProviderError> {
        Err(ProviderError::unsupported(
            "NO_BROWSER_REPEATABILITY_PROTOCOL",
        ))
    }
    fn summary(&self, r: &SummaryRequest) -> Result<SummaryDiagnostics, ProviderError> {
        self.invoke("summary", r)
    }
    fn nearest_neighbors(
        &self,
        r: &NearestNeighborsRequest,
    ) -> Result<NearestNeighborsDiagnostics, ProviderError> {
        self.invoke("nearest_neighbors", r)
    }
    fn hdbscan(&self, r: &HdbscanRequest) -> Result<HdbscanDiagnostics, ProviderError> {
        self.invoke("hdbscan", r)
    }
}
fn js_error(error: impl ToString) -> JsValue {
    JsValue::from_str(&error.to_string())
}
#[wasm_bindgen]
pub fn analyze_json(input: &str, callback: &Function) -> Result<String, JsValue> {
    let request = browser::parse(input).map_err(js_error)?;
    let report = browser::analyze(&request, &CallbackProvider(callback)).map_err(js_error)?;
    serde_json::to_string(&report).map_err(js_error)
}
#[wasm_bindgen]
pub fn validate_json(input: &str) -> Result<String, JsValue> {
    browser::parse(input).map_err(js_error)?;
    Ok("{\"valid\":true}".into())
}
#[wasm_bindgen]
pub fn interpret_json(report: &str, intent: &str) -> Result<String, JsValue> {
    if report.len() > browser::MAX_JSON_BYTES {
        return Err(js_error("JSON_MEMORY_BUDGET_EXCEEDED"));
    }
    let report = serde_json::from_str(report).map_err(js_error)?;
    let intent: PredictionIntent = serde_json::from_str(intent).map_err(js_error)?;
    serde_json::to_string(&browser::interpret(&report, intent).map_err(js_error)?).map_err(js_error)
}
