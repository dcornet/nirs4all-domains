//! Owning F4.3 transport to public Methods 1.3.13 / ABI 2.20; no numerical kernels.
//! ABI declarations follow estimator.h, n4m.h and metrics.h at fa8ff57603ec23bce95f73d52170285e8f3e2861.
use crate::browser_support::{SupportProvider, STATE_BYTES};
use libloading::Library;
use nirs4all_preflight::ProviderError;
use serde_json::{json, Value};
use std::{
    cell::RefCell,
    ffi::{c_char, c_void, CStr, CString},
    marker::PhantomData,
    path::Path,
    rc::Rc,
};

type Destroy = unsafe extern "C" fn(*mut c_void);
type LastError = unsafe extern "C" fn(*const c_void) -> *const c_char;
#[repr(C)]
struct MatrixView {
    data: *mut c_void,
    rows: i64,
    cols: i64,
    row_stride: i64,
    col_stride: i64,
    dtype: i32,
    reserved: i32,
}
impl MatrixView {
    fn new(data: &mut [f64], rows: usize, cols: usize) -> Self {
        Self {
            data: data.as_mut_ptr().cast(),
            rows: rows as i64,
            cols: cols as i64,
            row_stride: cols as i64,
            col_stride: 1,
            dtype: 1,
            reserved: 0,
        }
    }
}
#[repr(C)]
struct FitInputs {
    struct_size: u32,
    x: *const MatrixView,
    y: *const MatrixView,
    labels: *const i64,
    n_labels: i64,
    sample_weight: *const f64,
    n_sample_weight: i64,
    groups: *const i64,
    n_groups: i64,
    feature_groups: *const i64,
    n_feature_groups: i64,
    block_sizes: *const i64,
    n_blocks: i64,
    axis: *const f64,
    n_axis: i64,
    x_target: *const MatrixView,
    fold_ids: *const i64,
    n_fold_ids: i64,
}
struct Handle {
    ptr: *mut c_void,
    destroy: Destroy,
}
impl Drop for Handle {
    fn drop(&mut self) {
        if !self.ptr.is_null() {
            // SAFETY: the handle's owner library remains loaded through this guard.
            unsafe { (self.destroy)(self.ptr) }
        }
    }
}

pub struct PreprocessingMethods {
    pub version: String,
    library: Library,
    context: *mut c_void,
    destroy: Destroy,
    last_error: LastError,
    estimator: RefCell<Option<Handle>>,
    _thread_bound: PhantomData<Rc<()>>,
}
impl PreprocessingMethods {
    pub fn load(path: &Path) -> Result<Self, String> {
        // SAFETY: caller selects the library; all signatures are public pinned ABI.
        unsafe {
            let library = Library::new(path).map_err(|e| e.to_string())?;
            let compatible = library
                .get::<unsafe extern "C" fn(u32, u32) -> i32>(b"n4m_check_abi_compatibility\0")
                .map_err(|e| e.to_string())?;
            if compatible(2, 20) != 0 {
                return Err("METHODS_ABI_2_20_REQUIRED".into());
            }
            let version_fn = library
                .get::<unsafe extern "C" fn() -> *const c_char>(b"n4m_get_version_string\0")
                .map_err(|e| e.to_string())?;
            let ptr = version_fn();
            if ptr.is_null() {
                return Err("NULL_METHODS_VERSION".into());
            }
            let version = CStr::from_ptr(ptr).to_string_lossy().into_owned();
            if version != "1.3.13+abi.2.20.0" {
                return Err("PINNED_METHODS_1_3_13_ABI_2_20_REQUIRED".into());
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
            let mut context = std::ptr::null_mut();
            let status = create(&mut context);
            if status != 0 || context.is_null() {
                if !context.is_null() {
                    destroy(context);
                }
                return Err(format!("METHODS_CONTEXT_STATUS_{status}"));
            }
            Ok(Self {
                version,
                library,
                context,
                destroy,
                last_error,
                estimator: RefCell::new(None),
                _thread_bound: PhantomData,
            })
        }
    }
    fn symbol<T: Copy>(&self, name: &[u8]) -> Result<T, ProviderError> {
        // SAFETY: each caller supplies the signature from the pinned public header.
        unsafe {
            self.library
                .get::<T>(name)
                .map(|s| *s)
                .map_err(|_| ProviderError::unsupported("METHODS_PREPROCESSING_SYMBOL_UNAVAILABLE"))
        }
    }
    fn check(&self, status: i32) -> Result<(), ProviderError> {
        if status == 0 {
            return Ok(());
        }
        // SAFETY: copy the live context's error immediately after a failed owner call.
        let message = unsafe {
            let ptr = (self.last_error)(self.context);
            if ptr.is_null() {
                format!("METHODS_PREPROCESSING_STATUS_{status}")
            } else {
                CStr::from_ptr(ptr).to_string_lossy().into_owned()
            }
        };
        Err(ProviderError::from_methods_error(status, &message))
    }
    fn export(&self, ptr: *const c_void) -> Result<Vec<u8>, ProviderError> {
        type Size = unsafe extern "C" fn(*mut c_void, *const c_void, u32, *mut usize) -> i32;
        type Export = unsafe extern "C" fn(
            *mut c_void,
            *const c_void,
            u32,
            *mut c_void,
            usize,
            *mut usize,
        ) -> i32;
        let size: Size = self.symbol(b"n4m_estimator_export_size\0")?;
        let export: Export = self.symbol(b"n4m_estimator_export_to_buffer\0")?;
        let mut count = 0;
        // SAFETY: live handle, output size pointer; flags=0 forbids retained-training-row export.
        self.check(unsafe { size(self.context, ptr, 0, &mut count) })?;
        if count == 0 || count > STATE_BYTES {
            return Err(invalid("PROVIDER_STATE_BUDGET_OR_SHAPE"));
        }
        let mut bytes = vec![0; count];
        let mut written = 0;
        // SAFETY: owner-reported bounded capacity and writable byte buffer.
        self.check(unsafe {
            export(
                self.context,
                ptr,
                0,
                bytes.as_mut_ptr().cast(),
                count,
                &mut written,
            )
        })?;
        if written != count {
            return Err(invalid("PROVIDER_STATE_BUDGET_OR_SHAPE"));
        }
        Ok(bytes)
    }
    fn method_index(&self, operator: &str) -> Result<i32, ProviderError> {
        let id = CString::new(method_id(operator)?).expect("fixed manifest ID");
        type Find = unsafe extern "C" fn(*const c_char, *mut i32) -> i32;
        let find: Find = self.symbol(b"n4m_method_find\0")?;
        let mut index = 0;
        // SAFETY: fixed NUL-terminated method ID and writable index.
        self.check(unsafe { find(id.as_ptr(), &mut index) })?;
        Ok(index)
    }
    fn fit(&self, request: &Value) -> Result<Value, ProviderError> {
        exact(request, &["operator", "parameters", "matrix"])?;
        let operator = request["operator"]
            .as_str()
            .ok_or_else(|| invalid("INVALID_PREPROCESSING_OPERATOR"))?;
        let index = self.method_index(operator)?;
        let parameters = request["parameters"]
            .as_object()
            .ok_or_else(|| invalid("INVALID_PREPROCESSING_PARAMETERS"))?;
        let (mut data, rows, cols) = matrix(&request["matrix"])?;
        type Params = unsafe extern "C" fn(*mut c_void, i32, *mut *mut c_void) -> i32;
        type Validate = unsafe extern "C" fn(*mut c_void, *const c_void) -> i32;
        type Create = unsafe extern "C" fn(
            *mut c_void,
            *const c_char,
            *const c_void,
            *mut *mut c_void,
        ) -> i32;
        type Fit = unsafe extern "C" fn(*mut c_void, *mut c_void, *const FitInputs) -> i32;
        let create_params: Params = self.symbol(b"n4m_params_create\0")?;
        let validate: Validate = self.symbol(b"n4m_params_validate\0")?;
        let create: Create = self.symbol(b"n4m_estimator_create\0")?;
        let fit: Fit = self.symbol(b"n4m_estimator_fit\0")?;
        let mut params = Handle {
            ptr: std::ptr::null_mut(),
            destroy: self.symbol(b"n4m_params_destroy\0")?,
        };
        let mut candidate = Handle {
            ptr: std::ptr::null_mut(),
            destroy: self.symbol(b"n4m_estimator_destroy\0")?,
        };
        // SAFETY: live context and writable handle pointer; guard owns even partial output.
        self.check(unsafe { create_params(self.context, index, &mut params.ptr) })?;
        for (name, value) in parameters {
            self.set_parameter(params.ptr, operator, name, value)?;
        }
        let id = CString::new(method_id(operator)?).expect("fixed manifest ID");
        let view = MatrixView::new(&mut data, rows, cols);
        // SAFETY: the C-layout optional fit pointers/counts are absent; only X is supplied.
        let mut inputs: FitInputs = unsafe { std::mem::zeroed() };
        inputs.struct_size = std::mem::size_of::<FitInputs>() as u32;
        inputs.x = &view;
        // SAFETY: validated named parameters and live X-only fit inputs.
        unsafe {
            self.check(validate(self.context, params.ptr))?;
            self.check(create(
                self.context,
                id.as_ptr(),
                params.ptr,
                &mut candidate.ptr,
            ))?;
            self.check(fit(self.context, candidate.ptr, &inputs))?;
        }
        let bytes = self.export(candidate.ptr)?;
        *self.estimator.borrow_mut() = Some(candidate);
        Ok(json!({"state_bytes": bytes}))
    }
    fn set_parameter(
        &self,
        params: *mut c_void,
        operator: &str,
        name: &str,
        value: &Value,
    ) -> Result<(), ProviderError> {
        let kind = parameter_kind(operator, name)
            .ok_or_else(|| invalid("INVALID_PREPROCESSING_PARAMETERS"))?;
        let key = CString::new(name).map_err(|_| invalid("INVALID_PREPROCESSING_PARAMETERS"))?;
        // SAFETY: guarded live params, fixed whitelisted key and matching public typed setter.
        let status = unsafe {
            match kind {
                "int" => {
                    type Set = unsafe extern "C" fn(*mut c_void, *const c_char, i64) -> i32;
                    let set: Set = self.symbol(b"n4m_params_set_int\0")?;
                    set(
                        params,
                        key.as_ptr(),
                        value
                            .as_i64()
                            .ok_or_else(|| invalid("INVALID_PREPROCESSING_PARAMETERS"))?,
                    )
                }
                "double" => {
                    type Set = unsafe extern "C" fn(*mut c_void, *const c_char, f64) -> i32;
                    let set: Set = self.symbol(b"n4m_params_set_double\0")?;
                    set(
                        params,
                        key.as_ptr(),
                        value
                            .as_f64()
                            .filter(|v| v.is_finite())
                            .ok_or_else(|| invalid("INVALID_PREPROCESSING_PARAMETERS"))?,
                    )
                }
                "bool" => {
                    type Set = unsafe extern "C" fn(*mut c_void, *const c_char, i32) -> i32;
                    let set: Set = self.symbol(b"n4m_params_set_bool\0")?;
                    set(
                        params,
                        key.as_ptr(),
                        i32::from(
                            value
                                .as_bool()
                                .ok_or_else(|| invalid("INVALID_PREPROCESSING_PARAMETERS"))?,
                        ),
                    )
                }
                "enum" => {
                    type Set =
                        unsafe extern "C" fn(*mut c_void, *const c_char, *const c_char) -> i32;
                    let set: Set = self.symbol(b"n4m_params_set_enum\0")?;
                    let choice = CString::new(
                        value
                            .as_str()
                            .ok_or_else(|| invalid("INVALID_PREPROCESSING_PARAMETERS"))?,
                    )
                    .map_err(|_| invalid("INVALID_PREPROCESSING_PARAMETERS"))?;
                    set(params, key.as_ptr(), choice.as_ptr())
                }
                _ => return Err(invalid("INVALID_PREPROCESSING_PARAMETERS")),
            }
        };
        // Typed setters have no context argument and do not set its last-error string.
        // Do not misattribute a stale error from an earlier unrelated owner call.
        if status == 0 {
            Ok(())
        } else {
            Err(ProviderError::from_methods_error(
                status,
                "METHODS_PREPROCESSING_PARAMETER_REJECTED",
            ))
        }
    }
    fn transform(&self, request: &Value) -> Result<Value, ProviderError> {
        exact(request, &["matrix"])?;
        let (mut data, rows, cols) = matrix(&request["matrix"])?;
        let state = self.estimator.borrow();
        let handle = state
            .as_ref()
            .ok_or_else(|| invalid("PREPROCESSING_STATE_NOT_FITTED"))?;
        type Cols = unsafe extern "C" fn(*const c_void, *mut i64) -> i32;
        type Transform = unsafe extern "C" fn(
            *mut c_void,
            *const c_void,
            *const MatrixView,
            *mut MatrixView,
        ) -> i32;
        let width: Cols = self.symbol(b"n4m_estimator_transform_cols\0")?;
        let transform: Transform = self.symbol(b"n4m_estimator_transform\0")?;
        let mut output_cols = 0;
        // SAFETY: live estimator and scalar output.
        self.check(unsafe { width(handle.ptr, &mut output_cols) })?;
        let output_cols =
            usize::try_from(output_cols).map_err(|_| invalid("PROVIDER_MATRIX_BUDGET_OR_SHAPE"))?;
        if output_cols == 0 || rows.checked_mul(output_cols).is_none_or(|n| n > 1_000_000) {
            return Err(invalid("PROVIDER_MATRIX_BUDGET_OR_SHAPE"));
        }
        let before = self.export(handle.ptr)?;
        let input = MatrixView::new(&mut data, rows, cols);
        let mut values = vec![f64::NAN; rows * output_cols];
        let mut output = MatrixView::new(&mut values, rows, output_cols);
        // SAFETY: equal-row views and owner-reported bounded output width.
        let checked =
            self.check(unsafe { transform(self.context, handle.ptr, &input, &mut output) });
        // Copy the original error before serialization calls can overwrite the context error.
        let after = self.export(handle.ptr)?;
        if before != after {
            return Err(invalid(
                "FITTED_PREPROCESSING_STATE_CHANGED_DURING_TRANSFORM",
            ));
        }
        checked?;
        if values.iter().any(|v| !v.is_finite()) {
            return Err(invalid("PROVIDER_MATRIX_NONFINITE"));
        }
        Ok(json!({"matrix": nested(&values, rows, output_cols), "state_bytes": after}))
    }
    fn restore(&self, request: &Value) -> Result<Value, ProviderError> {
        exact(request, &["operator", "state_bytes"])?;
        let operator = request["operator"]
            .as_str()
            .ok_or_else(|| invalid("INVALID_PREPROCESSING_OPERATOR"))?;
        let expected = self.method_index(operator)?;
        let raw = request["state_bytes"]
            .as_array()
            .filter(|v| !v.is_empty() && v.len() <= STATE_BYTES)
            .ok_or_else(|| invalid("PROVIDER_STATE_BUDGET_OR_SHAPE"))?;
        let bytes: Vec<u8> = raw
            .iter()
            .map(|v| {
                v.as_u64()
                    .and_then(|v| u8::try_from(v).ok())
                    .ok_or_else(|| invalid("PROVIDER_STATE_BUDGET_OR_SHAPE"))
            })
            .collect::<Result<_, _>>()?;
        type Import =
            unsafe extern "C" fn(*mut c_void, *const c_void, usize, *mut *mut c_void) -> i32;
        type Info = unsafe extern "C" fn(*const c_void, *mut i32, *mut u64) -> i32;
        let import: Import = self.symbol(b"n4m_estimator_import_from_buffer\0")?;
        let info: Info = self.symbol(b"n4m_estimator_info\0")?;
        let mut candidate = Handle {
            ptr: std::ptr::null_mut(),
            destroy: self.symbol(b"n4m_estimator_destroy\0")?,
        };
        let (mut index, mut capabilities) = (0, 0);
        // SAFETY: bounded state bytes and guarded candidate; no live state is replaced on failure.
        unsafe {
            self.check(import(
                self.context,
                bytes.as_ptr().cast(),
                bytes.len(),
                &mut candidate.ptr,
            ))?;
            self.check(info(candidate.ptr, &mut index, &mut capabilities))?;
        }
        if index != expected {
            return Err(invalid("RESTORED_PREPROCESSING_OPERATOR_MISMATCH"));
        }
        let after = self.export(candidate.ptr)?;
        if bytes != after {
            return Err(invalid("RESTORED_PREPROCESSING_STATE_CHANGED"));
        }
        *self.estimator.borrow_mut() = Some(candidate);
        Ok(json!({"state_bytes": after}))
    }
    fn compare(&self, op: &str, request: &Value) -> Result<Value, ProviderError> {
        exact(
            request,
            if op == "adjusted_rand" {
                &["labels_a", "labels_b"]
            } else {
                &["labels_a", "labels_b", "n_clusters_a", "n_clusters_b"]
            },
        )?;
        let a = labels(&request["labels_a"])?;
        let b = labels(&request["labels_b"])?;
        if a.len() != b.len() {
            return Err(invalid("PROVIDER_LABEL_BUDGET_OR_SHAPE"));
        }
        if op == "adjusted_rand" {
            type Ari =
                unsafe extern "C" fn(*mut c_void, *const i64, *const i64, i64, *mut f64) -> i32;
            let ari: Ari = self.symbol(b"n4m_preflight_adjusted_rand_index\0")?;
            let mut result = f64::NAN;
            // SAFETY: equally sized labels; -1 remains an ordinary owner-defined ARI class.
            self.check(unsafe {
                ari(
                    self.context,
                    a.as_ptr(),
                    b.as_ptr(),
                    a.len() as i64,
                    &mut result,
                )
            })?;
            return Ok(json!({"value": nullable(result)}));
        }
        let na = count(&request["n_clusters_a"])?;
        let nb = count(&request["n_clusters_b"])?;
        let cells = na
            .checked_mul(nb)
            .filter(|n| *n <= 1_000_000)
            .ok_or_else(|| invalid("PROVIDER_LABEL_BUDGET_OR_SHAPE"))?;
        type Jaccard = unsafe extern "C" fn(
            *mut c_void,
            *const i64,
            *const i64,
            i64,
            i64,
            i64,
            *mut f64,
            *mut i64,
            *mut i64,
            *mut i64,
        ) -> i32;
        let jaccard: Jaccard = self.symbol(b"n4m_cluster_jaccard_matrix\0")?;
        let (mut overlaps, mut intersections, mut sizes_a, mut sizes_b) = (
            vec![f64::NAN; cells],
            vec![0_i64; cells],
            vec![0_i64; na],
            vec![0_i64; nb],
        );
        // SAFETY: equal-length labels and exactly sized row-major/cluster-count outputs.
        self.check(unsafe {
            jaccard(
                self.context,
                a.as_ptr(),
                b.as_ptr(),
                a.len() as i64,
                na as i64,
                nb as i64,
                overlaps.as_mut_ptr(),
                intersections.as_mut_ptr(),
                sizes_a.as_mut_ptr(),
                sizes_b.as_mut_ptr(),
            )
        })?;
        let overlap_rows: Vec<Vec<Value>> = if nb == 0 {
            vec![vec![]; na]
        } else {
            overlaps
                .chunks_exact(nb)
                .map(|v| v.iter().map(|x| nullable(*x)).collect())
                .collect()
        };
        Ok(
            json!({"jaccard":overlap_rows,"intersections":nested(&intersections,na,nb),"sizes_a":sizes_a,"sizes_b":sizes_b}),
        )
    }
}

impl SupportProvider for PreprocessingMethods {
    fn version(&self) -> String {
        self.version.clone()
    }
    fn execute(&self, op: &str, request: &Value) -> Result<Value, ProviderError> {
        let mut result = match op {
            "preprocess_fit" => self.fit(request),
            "preprocess_transform" => self.transform(request),
            "preprocess_restore" => self.restore(request),
            "preprocess_destroy" => {
                exact(request, &[])?;
                self.estimator.borrow_mut().take();
                Ok(json!({"destroyed":true}))
            }
            "adjusted_rand" | "cluster_jaccard" => self.compare(op, request),
            _ => Err(ProviderError::unsupported("UNSUPPORTED_METHODS_OPERATION")),
        }?;
        result["backend_version"] = json!(self.version);
        Ok(result)
    }
}
impl Drop for PreprocessingMethods {
    fn drop(&mut self) {
        self.estimator.get_mut().take();
        // SAFETY: estimator released first; context is owned by the still-loaded library.
        unsafe { (self.destroy)(self.context) }
    }
}
fn invalid(reason: &str) -> ProviderError {
    ProviderError::internal(reason)
}
fn nullable(v: f64) -> Value {
    if v.is_finite() {
        json!(v)
    } else {
        Value::Null
    }
}
fn exact(value: &Value, fields: &[&str]) -> Result<(), ProviderError> {
    let object = value
        .as_object()
        .ok_or_else(|| invalid("INVALID_PREPROCESSING_REQUEST"))?;
    if object.len() != fields.len() || fields.iter().any(|key| !object.contains_key(*key)) {
        return Err(invalid("INVALID_PREPROCESSING_REQUEST"));
    }
    Ok(())
}
fn method_id(operator: &str) -> Result<&'static str, ProviderError> {
    match operator {
        "SNV" => Ok("preprocessing.scatter.snv"),
        "MSC" => Ok("preprocessing.scatter.msc"),
        "Detrend" => Ok("preprocessing.baselines.detrend"),
        "SavitzkyGolay" => Ok("preprocessing.derivatives.savitzky_golay"),
        "Gaussian" => Ok("preprocessing.smoothing.gaussian"),
        "StandardScale" => Ok("preprocessing.scaling.standard_scale"),
        "Normalize" => Ok("preprocessing.scaling.normalize"),
        "CropTransformer" => Ok("preprocessing.resampling.crop"),
        _ => Err(ProviderError::unsupported(
            "PREPROCESSING_OPERATOR_NOT_WHITELISTED",
        )),
    }
}
fn parameter_kind(operator: &str, key: &str) -> Option<&'static str> {
    match (operator, key) {
        ("SNV" | "StandardScale", "with_mean" | "with_std") => Some("bool"),
        ("SNV", "ddof")
        | ("Detrend", "polyorder")
        | ("SavitzkyGolay", "window_length" | "polyorder" | "deriv")
        | ("Gaussian", "order")
        | ("CropTransformer", "start" | "end") => Some("int"),
        ("SavitzkyGolay", "delta" | "cval")
        | ("Gaussian", "sigma" | "cval" | "truncate")
        | ("Normalize", "feature_min" | "feature_max") => Some("double"),
        ("SavitzkyGolay" | "Gaussian", "mode") => Some("enum"),
        _ => None,
    }
}
fn matrix(value: &Value) -> Result<(Vec<f64>, usize, usize), ProviderError> {
    let rows = value
        .as_array()
        .filter(|v| !v.is_empty() && v.len() <= 1_000_000)
        .ok_or_else(|| invalid("PROVIDER_MATRIX_BUDGET_OR_SHAPE"))?;
    let cols = rows[0]
        .as_array()
        .map(Vec::len)
        .filter(|p| *p > 0 && rows.len().checked_mul(*p).is_some_and(|n| n <= 1_000_000))
        .ok_or_else(|| invalid("PROVIDER_MATRIX_BUDGET_OR_SHAPE"))?;
    let mut data = Vec::with_capacity(rows.len() * cols);
    for row in rows {
        let row = row
            .as_array()
            .filter(|row| row.len() == cols)
            .ok_or_else(|| invalid("PROVIDER_MATRIX_BUDGET_OR_SHAPE"))?;
        for value in row {
            data.push(
                value
                    .as_f64()
                    .filter(|v| v.is_finite())
                    .ok_or_else(|| invalid("PROVIDER_MATRIX_NONFINITE"))?,
            );
        }
    }
    Ok((data, rows.len(), cols))
}
fn labels(value: &Value) -> Result<Vec<i64>, ProviderError> {
    let values = value
        .as_array()
        .filter(|v| v.len() <= 1_000_000)
        .ok_or_else(|| invalid("PROVIDER_LABEL_BUDGET_OR_SHAPE"))?;
    values
        .iter()
        .map(|v| {
            v.as_i64()
                .ok_or_else(|| invalid("PROVIDER_LABEL_BUDGET_OR_SHAPE"))
        })
        .collect()
}
fn count(value: &Value) -> Result<usize, ProviderError> {
    value
        .as_u64()
        .and_then(|v| usize::try_from(v).ok())
        .filter(|v| *v <= 1_000_000)
        .ok_or_else(|| invalid("PROVIDER_LABEL_BUDGET_OR_SHAPE"))
}
fn nested<T: Clone>(values: &[T], rows: usize, cols: usize) -> Vec<Vec<T>> {
    if cols == 0 {
        vec![vec![]; rows]
    } else {
        values.chunks_exact(cols).map(|v| v.to_vec()).collect()
    }
}
