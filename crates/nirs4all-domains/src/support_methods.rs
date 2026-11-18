//! Owning F4.2 transport to public Methods 1.3.13 / ABI 2.20; no numerical kernels.
//! ABI declarations follow estimator.h, n4m.h and metrics.h at fa8ff57603ec23bce95f73d52170285e8f3e2861.
use crate::browser_support::{SupportProvider, STATE_BYTES};
use libloading::Library;
use nirs4all_preflight::ProviderError;
use serde_json::{json, Value};
use std::{
    cell::RefCell,
    ffi::{c_char, c_void, CStr},
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

pub struct SupportMethods {
    pub version: String,
    library: Library,
    context: *mut c_void,
    destroy: Destroy,
    last_error: LastError,
    estimator: RefCell<Option<Handle>>,
    _thread_bound: PhantomData<Rc<()>>,
}
impl SupportMethods {
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
                .map_err(|_| ProviderError::unsupported("METHODS_SUPPORT_SYMBOL_UNAVAILABLE"))
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
                format!("METHODS_SUPPORT_STATUS_{status}")
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
    fn dispatch(&self, op: &str, r: &Value) -> Result<Value, ProviderError> {
        match op {
            "pca_fit" => {
                if self.estimator.borrow().is_some() {
                    return Err(invalid("PCA_STATE_ALREADY_FITTED"));
                }
                let (mut data, n, p) = matrix(&r["matrix"])?;
                let k = r["n_components"]
                    .as_f64()
                    .filter(|k| k.is_finite() && *k > 0.0 && (*k < 1.0 || k.fract() == 0.0))
                    .ok_or_else(|| invalid("INVALID_PCA_FIT_REQUEST"))?;
                type Find = unsafe extern "C" fn(*const c_char, *mut i32) -> i32;
                type Params = unsafe extern "C" fn(*mut c_void, i32, *mut *mut c_void) -> i32;
                type Set = unsafe extern "C" fn(*mut c_void, *const c_char, f64) -> i32;
                type Validate = unsafe extern "C" fn(*mut c_void, *const c_void) -> i32;
                type Create = unsafe extern "C" fn(
                    *mut c_void,
                    *const c_char,
                    *const c_void,
                    *mut *mut c_void,
                ) -> i32;
                type Fit = unsafe extern "C" fn(*mut c_void, *mut c_void, *const FitInputs) -> i32;
                let find: Find = self.symbol(b"n4m_method_find\0")?;
                let create_params: Params = self.symbol(b"n4m_params_create\0")?;
                let params_destroy: Destroy = self.symbol(b"n4m_params_destroy\0")?;
                let set: Set = self.symbol(b"n4m_params_set_double\0")?;
                let validate: Validate = self.symbol(b"n4m_params_validate\0")?;
                let create: Create = self.symbol(b"n4m_estimator_create\0")?;
                let estimator_destroy: Destroy = self.symbol(b"n4m_estimator_destroy\0")?;
                let fit: Fit = self.symbol(b"n4m_estimator_fit\0")?;
                let id = b"preprocessing.feature_selection.flexible_pca\0";
                let mut index = 0;
                let mut params = Handle {
                    ptr: std::ptr::null_mut(),
                    destroy: params_destroy,
                };
                let mut candidate = Handle {
                    ptr: std::ptr::null_mut(),
                    destroy: estimator_destroy,
                };
                let view = MatrixView::new(&mut data, n, p);
                // SAFETY: C-layout zeroed optional fields are absent; X is kept live for fit.
                let mut inputs: FitInputs = unsafe { std::mem::zeroed() };
                inputs.struct_size = std::mem::size_of::<FitInputs>() as u32;
                inputs.x = &view;
                // SAFETY: all pointers refer to live buffers/guards and checked public signatures.
                unsafe {
                    self.check(find(id.as_ptr().cast(), &mut index))?;
                    self.check(create_params(self.context, index, &mut params.ptr))?;
                    self.check(set(params.ptr, c"n_components".as_ptr(), k))?;
                    self.check(validate(self.context, params.ptr))?;
                    self.check(create(
                        self.context,
                        id.as_ptr().cast(),
                        params.ptr,
                        &mut candidate.ptr,
                    ))?;
                    self.check(fit(self.context, candidate.ptr, &inputs))?;
                }
                let bytes = self.export(candidate.ptr)?;
                *self.estimator.borrow_mut() = Some(candidate);
                Ok(json!({"state_bytes":bytes}))
            }
            "pca_transform" => {
                let (mut data, n, p) = matrix(&r["matrix"])?;
                let state = self.estimator.borrow();
                let handle = state
                    .as_ref()
                    .ok_or_else(|| invalid("PCA_STATE_NOT_FITTED"))?;
                type Cols = unsafe extern "C" fn(*const c_void, *mut i64) -> i32;
                type Transform = unsafe extern "C" fn(
                    *mut c_void,
                    *const c_void,
                    *const MatrixView,
                    *mut MatrixView,
                ) -> i32;
                let cols: Cols = self.symbol(b"n4m_estimator_transform_cols\0")?;
                let transform: Transform = self.symbol(b"n4m_estimator_transform\0")?;
                let mut k = 0;
                // SAFETY: live estimator and writable scalar.
                self.check(unsafe { cols(handle.ptr, &mut k) })?;
                let k =
                    usize::try_from(k).map_err(|_| invalid("PROVIDER_MATRIX_BUDGET_OR_SHAPE"))?;
                if k == 0 || n.checked_mul(k).is_none_or(|v| v > 1_000_000) {
                    return Err(invalid("PROVIDER_MATRIX_BUDGET_OR_SHAPE"));
                }
                let before = self.export(handle.ptr)?;
                let mut scores = vec![f64::NAN; n * k];
                let view = MatrixView::new(&mut data, n, p);
                let mut output = MatrixView::new(&mut scores, n, k);
                // SAFETY: owner-reported width, live views and correctly sized writable output.
                let status = unsafe { transform(self.context, handle.ptr, &view, &mut output) };
                let checked = self.check(status); // Copy owner error before any subsequent owner call.
                let after = self.export(handle.ptr)?;
                if before != after {
                    return Err(invalid("FITTED_PCA_STATE_CHANGED_DURING_TRANSFORM"));
                }
                checked?;
                if scores.iter().any(|v| !v.is_finite()) {
                    return Err(invalid("PROVIDER_MATRIX_NONFINITE"));
                }
                let scores: Vec<_> = scores.chunks_exact(k).map(|v| v.to_vec()).collect();
                Ok(json!({"scores":scores,"state_bytes":after}))
            }
            "pca_destroy" => {
                self.estimator.borrow_mut().take();
                Ok(json!({"destroyed":true}))
            }
            "summary" => {
                let values: Vec<f64> = serde_json::from_value(r["values"].clone())
                    .map_err(|_| invalid("PROVIDER_VECTOR_BUDGET_OR_SHAPE"))?;
                if values.is_empty()
                    || values.len() > 1_000_000
                    || values.iter().any(|v| !v.is_finite())
                {
                    return Err(invalid("PROVIDER_VECTOR_BUDGET_OR_SHAPE"));
                }
                type Summary =
                    unsafe extern "C" fn(*mut c_void, *const f64, *const u8, i64, *mut f64) -> i32;
                let summary: Summary = self.symbol(b"n4m_preflight_summary_compute\0")?;
                let mut out = [f64::NAN; 8];
                // SAFETY: finite input, null optional mask and eight owner-defined output slots.
                self.check(unsafe {
                    summary(
                        self.context,
                        values.as_ptr(),
                        std::ptr::null(),
                        values.len() as i64,
                        out.as_mut_ptr(),
                    )
                })?;
                Ok(fields(
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
                    &out,
                ))
            }
            "pca_monitor" => self.monitor(r),
            _ => Err(ProviderError::unsupported("UNSUPPORTED_METHODS_OPERATION")),
        }
    }
    fn monitor(&self, r: &Value) -> Result<Value, ProviderError> {
        let (mut reference, n, p) = matrix(&r["reference"])?;
        let (mut monitored, m, q) = matrix(&r["monitored"])?;
        if p != q || reference.len() + monitored.len() > 1_000_000 {
            return Err(invalid("INVALID_PCA_MONITOR_REQUEST"));
        }
        let k = r["max_components"]
            .as_i64()
            .and_then(|v| i32::try_from(v).ok())
            .filter(|v| *v > 0 && *v as usize <= p)
            .ok_or_else(|| invalid("INVALID_PCA_MONITOR_REQUEST"))?;
        let folds = r["n_folds"]
            .as_i64()
            .and_then(|v| i32::try_from(v).ok())
            .ok_or_else(|| invalid("INVALID_PCA_MONITOR_REQUEST"))?;
        let alpha = r["alpha"]
            .as_f64()
            .filter(|v| v.is_finite())
            .ok_or_else(|| invalid("INVALID_PCA_MONITOR_REQUEST"))?;
        type Monitor = unsafe extern "C" fn(
            *mut c_void,
            *const MatrixView,
            *const MatrixView,
            i32,
            i32,
            f64,
            *mut f64,
            *mut f64,
            *mut f64,
            *mut f64,
            *mut f64,
            *mut i32,
            *mut i64,
            *mut f64,
        ) -> i32;
        let monitor: Monitor = self.symbol(b"n4m_stats_pca_monitor\0")?;
        let mut eigenvalues = vec![f64::NAN; k as usize];
        let (mut rt, mut rq, mut mt, mut mq) = (
            vec![f64::NAN; n],
            vec![f64::NAN; n],
            vec![f64::NAN; m],
            vec![f64::NAN; m],
        );
        let (mut effective, mut counts, mut scalars) = (0, [0_i64; 6], [f64::NAN; 13]);
        let rv = MatrixView::new(&mut reference, n, p);
        let mv = MatrixView::new(&mut monitored, m, p);
        // SAFETY: equal-width views and arrays sized exactly to the pinned monitor contract.
        self.check(unsafe {
            monitor(
                self.context,
                &rv,
                &mv,
                k,
                folds,
                alpha,
                eigenvalues.as_mut_ptr(),
                rt.as_mut_ptr(),
                rq.as_mut_ptr(),
                mt.as_mut_ptr(),
                mq.as_mut_ptr(),
                &mut effective,
                counts.as_mut_ptr(),
                scalars.as_mut_ptr(),
            )
        })?;
        let mut out = fields(
            &[
                "t2_limit",
                "q_limit",
                "reference_total_variance",
                "monitored_total_variance",
                "centroid_distance",
                "centroid_subspace_distance",
                "centroid_residual_distance",
                "centroid_t2",
                "retained_fraction",
                "tolerance",
                "condition",
                "q_tolerance_scale",
                "eigenvalue_resolution",
            ],
            &scalars,
        );
        let object = out.as_object_mut().expect("fields produces object");
        for (name, values) in [
            ("eigenvalues", eigenvalues),
            ("reference_t2", rt),
            ("reference_q", rq),
            ("monitored_t2", mt),
            ("monitored_q", mq),
        ] {
            object.insert(
                name.into(),
                Value::Array(values.iter().map(|v| nullable(*v)).collect()),
            );
        }
        for (name, count) in [
            "n_beyond_t2",
            "n_beyond_q",
            "n_beyond_either",
            "n_near_t2",
            "n_near_q",
            "n_near_either",
        ]
        .iter()
        .zip(counts)
        {
            object.insert((*name).into(), json!(count));
        }
        object.insert("effective_components".into(), json!(effective));
        Ok(out)
    }
}
impl SupportProvider for SupportMethods {
    fn version(&self) -> String {
        self.version.clone()
    }
    fn execute(&self, op: &str, r: &Value) -> Result<Value, ProviderError> {
        // A summary/monitor error must not invalidate an independently fitted PCA.
        // Candidate guards, explicit destroy and Drop own cleanup; owner transform
        // errors preserve the fitted handle until the protocol destroys it.
        self.dispatch(op, r).map(|mut value| {
            value["backend_version"] = json!(self.version);
            value
        })
    }
}
impl Drop for SupportMethods {
    fn drop(&mut self) {
        self.estimator.get_mut().take();
        // SAFETY: estimator released first; context belongs to the still-loaded library.
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
fn fields(names: &[&str], values: &[f64]) -> Value {
    Value::Object(
        names
            .iter()
            .zip(values)
            .map(|(k, v)| ((*k).into(), nullable(*v)))
            .collect(),
    )
}
fn matrix(value: &Value) -> Result<(Vec<f64>, usize, usize), ProviderError> {
    let rows = value
        .as_array()
        .filter(|v| !v.is_empty() && v.len() <= 1_000_000)
        .ok_or_else(|| invalid("PROVIDER_MATRIX_BUDGET_OR_SHAPE"))?;
    let p = rows[0]
        .as_array()
        .map(Vec::len)
        .filter(|p| *p > 0 && rows.len().checked_mul(*p).is_some_and(|n| n <= 1_000_000))
        .ok_or_else(|| invalid("PROVIDER_MATRIX_BUDGET_OR_SHAPE"))?;
    let mut data = Vec::with_capacity(rows.len() * p);
    for row in rows {
        let row = row
            .as_array()
            .filter(|row| row.len() == p)
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
    Ok((data, rows.len(), p))
}
