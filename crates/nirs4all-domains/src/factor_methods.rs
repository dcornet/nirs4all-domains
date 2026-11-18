//! Independent owning transport for the F4.1 public Methods ABI 2.20 kernels.
//! Historical native adapters and numerical algorithms remain unchanged.
use libloading::Library;
use nirs4all_preflight::ProviderError;
use std::{
    ffi::{c_char, c_void, CStr},
    marker::PhantomData,
    path::Path,
    rc::Rc,
};

type Destroy = unsafe extern "C" fn(*mut c_void);
type LastError = unsafe extern "C" fn(*const c_void) -> *const c_char;
type FactorAssociation = unsafe extern "C" fn(
    *mut c_void,
    *const i64,
    *const f64,
    i64,
    i32,
    i32,
    u64,
    *mut f64,
    *mut i64,
) -> i32;

/// Owns its library/context together; no handle crosses into a legacy provider.
pub struct FactorMethods {
    pub version: String,
    _library: Library,
    context: *mut c_void,
    destroy: Destroy,
    last_error: LastError,
    _thread_bound: PhantomData<Rc<()>>,
}
impl FactorMethods {
    pub fn load(path: &Path) -> Result<Self, String> {
        // SAFETY: explicitly selected owner library; public signatures are checked
        // before creating a context. No fallible initialization follows success.
        unsafe {
            let library = Library::new(path).map_err(|e| e.to_string())?;
            let compatible = library
                .get::<unsafe extern "C" fn(u32, u32) -> i32>(b"n4m_check_abi_compatibility\0")
                .map_err(|e| e.to_string())?;
            if compatible(2, 20) != 0 {
                return Err("METHODS_ABI_2_20_REQUIRED".into());
            }
            let create = *library
                .get::<unsafe extern "C" fn(*mut *mut c_void) -> i32>(b"n4m_context_create\0")
                .map_err(|e| e.to_string())?;
            let destroy = *library
                .get::<Destroy>(b"n4m_context_destroy\0")
                .map_err(|e| e.to_string())?;
            let last_error = *library
                .get::<LastError>(b"n4m_context_last_error\0")
                .map_err(|e| e.to_string())?;
            let version_fn = library
                .get::<unsafe extern "C" fn() -> *const c_char>(b"n4m_get_version_string\0")
                .map_err(|e| e.to_string())?;
            let version_ptr = version_fn();
            if version_ptr.is_null() {
                return Err("NULL_METHODS_VERSION".into());
            }
            let version = CStr::from_ptr(version_ptr).to_string_lossy().into_owned();
            if version != "1.3.13+abi.2.20.0" {
                return Err("PINNED_METHODS_1_3_13_ABI_2_20_REQUIRED".into());
            }
            let mut context = std::ptr::null_mut();
            let code = create(&mut context);
            if code != 0 || context.is_null() {
                let message = if context.is_null() {
                    "METHODS_CONTEXT_FAILED".to_owned()
                } else {
                    // Copy the context-owned error before destruction or another owner call.
                    let ptr = last_error(context);
                    let message = if ptr.is_null() {
                        "METHODS_CONTEXT_FAILED".to_owned()
                    } else {
                        CStr::from_ptr(ptr).to_string_lossy().into_owned()
                    };
                    destroy(context);
                    message
                };
                return Err(format!("METHODS_CONTEXT_STATUS_{code}:{message}"));
            }
            Ok(Self {
                version,
                _library: library,
                context,
                destroy,
                last_error,
                _thread_bound: PhantomData,
            })
        }
    }
    fn factor_transport_error(&self, code: i32) -> ProviderError {
        // SAFETY: copy the live context's error immediately after its failed call.
        let message = unsafe {
            let ptr = (self.last_error)(self.context);
            if ptr.is_null() {
                format!("METHODS_FACTOR_STATUS_{code}")
            } else {
                CStr::from_ptr(ptr).to_string_lossy().into_owned()
            }
        };
        ProviderError::from_methods_error(code, &message)
    }
}
impl Drop for FactorMethods {
    fn drop(&mut self) {
        // SAFETY: this nonnull context belongs to the still-loaded owning library.
        unsafe { (self.destroy)(self.context) }
    }
}

type CorrelationTest = unsafe extern "C" fn(
    *mut c_void,
    *const f64,
    *const f64,
    i64,
    i32,
    i32,
    u64,
    *mut f64,
    *mut i64,
) -> i32;
type FactorExact =
    unsafe extern "C" fn(*mut c_void, *const i64, *const f64, i64, i32, i64, *mut f64) -> i32;
type CorrelationExact =
    unsafe extern "C" fn(*mut c_void, *const f64, *const f64, i64, i32, i64, *mut f64) -> i32;
type HolmAdjust = unsafe extern "C" fn(*mut c_void, *const f64, i64, *mut f64) -> i32;
type FactorSummary = unsafe extern "C" fn(*mut c_void, *const f64, *const u8, i64, *mut f64) -> i32;

impl crate::browser_factor::FactorProvider for FactorMethods {
    fn version(&self) -> String {
        self.version.clone()
    }

    fn execute(
        &self,
        operation: &str,
        request: &serde_json::Value,
    ) -> Result<serde_json::Value, nirs4all_preflight::ProviderError> {
        use nirs4all_preflight::ProviderError;
        use serde_json::{json, Value};
        let invalid = || ProviderError::internal("INVALID_FACTOR_PROVIDER_REQUEST");
        let symbol_error =
            |_: libloading::Error| ProviderError::unsupported("METHODS_FACTOR_SYMBOL_UNAVAILABLE");
        let vector = |key: &str, minimum: usize| -> Result<Vec<f64>, ProviderError> {
            let values: Vec<f64> =
                serde_json::from_value(request[key].clone()).map_err(|_| invalid())?;
            if values.len() < minimum
                || values.len() > 1_000_000
                || values.iter().any(|v| !v.is_finite())
            {
                return Err(invalid());
            }
            Ok(values)
        };
        if !matches!(
            operation,
            "factor_descriptive"
                | "correlation_descriptive"
                | "factor_exact"
                | "correlation_exact"
                | "holm_adjust"
                | "summary"
        ) {
            return Err(ProviderError::unsupported("UNSUPPORTED_METHODS_OPERATION"));
        }
        // SAFETY: inspection of the loaded owner's public ABI compatibility function.
        let compatible = unsafe {
            self._library
                .get::<unsafe extern "C" fn(u32, u32) -> i32>(b"n4m_check_abi_compatibility\0")
                .map_err(symbol_error)?(2, 20)
        };
        if compatible != 0 {
            return Err(ProviderError::unsupported("METHODS_ABI_2_20_REQUIRED"));
        }
        let mut result = serde_json::Map::new();
        let mut save = |keys: &[&str], out: &[f64]| {
            for (key, value) in keys.iter().zip(out) {
                result.insert(
                    (*key).into(),
                    if value.is_finite() {
                        json!(value)
                    } else {
                        Value::Null
                    },
                );
            }
        };
        if operation == "summary" || operation == "holm_adjust" {
            let values = vector(
                if operation == "summary" {
                    "values"
                } else {
                    "p_values"
                },
                1,
            )?;
            let mut output = vec![
                f64::NAN;
                if operation == "summary" {
                    8
                } else {
                    values.len()
                }
            ];
            // SAFETY: live finite input, correctly sized owner-defined output, null optional mask.
            let code = unsafe {
                if operation == "summary" {
                    self._library
                        .get::<FactorSummary>(b"n4m_preflight_summary_compute\0")
                        .map_err(symbol_error)?(
                        self.context,
                        values.as_ptr(),
                        std::ptr::null(),
                        values.len() as i64,
                        output.as_mut_ptr(),
                    )
                } else {
                    self._library
                        .get::<HolmAdjust>(b"n4m_preflight_holm_adjust\0")
                        .map_err(symbol_error)?(
                        self.context,
                        values.as_ptr(),
                        values.len() as i64,
                        output.as_mut_ptr(),
                    )
                }
            };
            if code != 0 {
                return Err(self.factor_transport_error(code));
            }
            if operation == "summary" {
                save(
                    &[
                        "count",
                        "min",
                        "max",
                        "mean",
                        "sample_sd",
                        "q25",
                        "median",
                        "q75",
                    ],
                    &output,
                );
            } else {
                result.insert(
                    "adjusted".into(),
                    json!(output
                        .iter()
                        .map(|v| v.is_finite().then_some(*v))
                        .collect::<Vec<_>>()),
                );
            }
        } else {
            let scores = vector("scores", 2)?;
            let categorical = operation.starts_with("factor_");
            let codes: Vec<i64> = if categorical {
                serde_json::from_value(request["codes"].clone()).map_err(|_| invalid())?
            } else {
                Vec::new()
            };
            let values = if categorical {
                Vec::new()
            } else {
                vector("values", 2)?
            };
            if (categorical && codes.len() != scores.len())
                || (!categorical && values.len() != scores.len())
            {
                return Err(invalid());
            }
            let method = if categorical {
                0
            } else {
                match request["method"].as_str() {
                    Some("pearson") => 0,
                    Some("spearman") => 1,
                    _ => return Err(invalid()),
                }
            };
            let exact = operation.ends_with("_exact");
            let cap = if exact {
                request["max_arrangements"]
                    .as_i64()
                    .filter(|n| (1..=10_000_000).contains(n))
                    .ok_or_else(invalid)?
            } else {
                0
            };
            let mut output = [f64::NAN; 8];
            let mut counts = [0_i64; 2];
            // SAFETY: validated equal-length inputs, ABI 2.20 public metrics.h signatures,
            // fixed output capacities; descriptive calls always request B=0, seed=0.
            let code = unsafe {
                match (categorical, exact) {
                    (true, false) => self
                        ._library
                        .get::<FactorAssociation>(b"n4m_preflight_factor_association\0")
                        .map_err(symbol_error)?(
                        self.context,
                        codes.as_ptr(),
                        scores.as_ptr(),
                        scores.len() as i64,
                        0,
                        0,
                        0,
                        output.as_mut_ptr(),
                        counts.as_mut_ptr(),
                    ),
                    (false, false) => self
                        ._library
                        .get::<CorrelationTest>(b"n4m_stats_correlation_test\0")
                        .map_err(symbol_error)?(
                        self.context,
                        values.as_ptr(),
                        scores.as_ptr(),
                        scores.len() as i64,
                        method,
                        0,
                        0,
                        output.as_mut_ptr(),
                        counts.as_mut_ptr(),
                    ),
                    (true, true) => self
                        ._library
                        .get::<FactorExact>(b"n4m_stats_factor_association_exact\0")
                        .map_err(symbol_error)?(
                        self.context,
                        codes.as_ptr(),
                        scores.as_ptr(),
                        scores.len() as i64,
                        0,
                        cap,
                        output.as_mut_ptr(),
                    ),
                    (false, true) => self
                        ._library
                        .get::<CorrelationExact>(b"n4m_stats_correlation_exact\0")
                        .map_err(symbol_error)?(
                        self.context,
                        values.as_ptr(),
                        scores.as_ptr(),
                        scores.len() as i64,
                        method,
                        cap,
                        output.as_mut_ptr(),
                    ),
                }
            };
            if code != 0 {
                return Err(self.factor_transport_error(code));
            }
            if exact {
                save(
                    &[
                        "n_arrangements",
                        "p_value",
                        "minimum_p_value",
                        "maximum_statistic",
                    ],
                    &output[..4],
                );
            } else {
                if categorical {
                    save(
                        &[
                            "eta_squared",
                            "f_statistic",
                            "df1",
                            "df2",
                            "n_levels",
                            "n_score_values",
                            "log10_distinct_arrangements",
                            "p_value",
                        ],
                        &output,
                    );
                } else {
                    save(
                        &[
                            "coefficient",
                            "n_distinct_factor",
                            "n_distinct_score",
                            "log10_distinct_arrangements",
                            "p_value",
                        ],
                        &output[..5],
                    );
                }
                result.insert("n_at_least_observed".into(), json!(counts[0]));
                result.insert("n_permutations_executed".into(), json!(counts[1]));
            }
        }
        result.insert("backend_version".into(), json!(self.version));
        Ok(Value::Object(result))
    }
}
