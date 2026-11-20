//! Composite owner transport for the F4.3 consumer; no numerical implementation.
use crate::{
    browser_support::SupportProvider, factor_methods::FactorMethods,
    preprocessing_methods::PreprocessingMethods, support_methods::SupportMethods,
};
use nirs4all_preflight::{native::NativeMethodsProvider, MethodsProvider, ProviderError};
use serde::{de::DeserializeOwned, Serialize};
use serde_json::{json, Value};
use std::{cell::Cell, path::Path};

pub struct SensitivityMethods {
    pub version: String,
    diagnostics: NativeMethodsProvider,
    factor: FactorMethods,
    support: SupportMethods,
    preprocessing: PreprocessingMethods,
    calls: Cell<usize>,
}
impl SensitivityMethods {
    pub fn load(path: &Path) -> Result<Self, String> {
        let preprocessing = PreprocessingMethods::load(path)?;
        let support = SupportMethods::load(path)?;
        let factor = FactorMethods::load(path)?;
        let diagnostics = NativeMethodsProvider::load(path).map_err(|e| e.reason)?;
        Ok(Self {
            version: preprocessing.version.clone(),
            diagnostics,
            factor,
            support,
            preprocessing,
            calls: Cell::new(0),
        })
    }
    pub fn call_count(&self) -> usize {
        self.calls.get()
    }
}
fn decode<T: DeserializeOwned>(value: &Value) -> Result<T, ProviderError> {
    serde_json::from_value(value.clone())
        .map_err(|_| ProviderError::internal("INVALID_F43_OWNER_REQUEST"))
}
fn encode<T: Serialize>(value: Result<T, ProviderError>) -> Result<Value, ProviderError> {
    serde_json::to_value(value?).map_err(|_| ProviderError::internal("INVALID_F43_OWNER_RESPONSE"))
}
impl SupportProvider for SensitivityMethods {
    fn version(&self) -> String {
        self.version.clone()
    }
    fn execute(&self, operation: &str, request: &Value) -> Result<Value, ProviderError> {
        self.calls.set(self.calls.get() + 1);
        match operation {
            "capabilities" => Ok(json!(["pca", "summary", "nearest_neighbors", "hdbscan"]
                .map(|id| json!({
                "capability_id":format!("methods.{id}"),"available":true,"qualified":false,
                "reason":format!("{}; bounded browser protocol",self.version)})))),
            "pca" => encode(self.diagnostics.pca(&decode(request)?)),
            "nearest_neighbors" => encode(self.diagnostics.nearest_neighbors(&decode(request)?)),
            "hdbscan" => encode(self.diagnostics.hdbscan(&decode(request)?)),
            "summary" => encode(self.diagnostics.summary(&decode(request)?)),
            "pca_fit" | "pca_transform" | "pca_destroy" | "pca_monitor" => {
                self.support.execute(operation, request)
            }
            "factor_descriptive"
            | "correlation_descriptive"
            | "factor_exact"
            | "correlation_exact"
            | "holm_adjust" => {
                crate::browser_factor::FactorProvider::execute(&self.factor, operation, request)
            }
            _ => self.preprocessing.execute(operation, request),
        }
    }
}
