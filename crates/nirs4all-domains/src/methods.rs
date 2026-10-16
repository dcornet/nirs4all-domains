//! Safe owning adapter to Methods ABI 2.18. Numerical algorithms stay upstream.
//! Preflight's public provider omits PCA loadings, so this adapter retains them.
use libloading::Library;
use nirs4all_preflight::{native::NativeMethodsProvider, MethodsProvider, SummaryRequest};
use schemars::JsonSchema;
use serde::Deserialize;
use serde::Serialize;
use std::{
    ffi::{c_char, c_void, CStr},
    marker::PhantomData,
    path::Path,
    rc::Rc,
};

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
        assert_eq!(data.len(), rows * cols);
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
type Destroy = unsafe extern "C" fn(*mut c_void);
type Pca = unsafe extern "C" fn(
    *mut c_void,
    *const MatrixView,
    i32,
    *const MatrixView,
    *const MatrixView,
    *mut f64,
    *mut f64,
) -> i32;
type FlexCreate = unsafe extern "C" fn(*mut *mut c_void, f64) -> i32;
type FlexFit = unsafe extern "C" fn(*mut c_void, MatrixView) -> i32;
type FlexTransform = unsafe extern "C" fn(*const c_void, MatrixView, MatrixView) -> i32;
type FlexCols = unsafe extern "C" fn(*const c_void, *mut i64) -> i32;
type Hdbscan = unsafe extern "C" fn(
    *mut c_void,
    *const MatrixView,
    i64,
    i64,
    i32,
    i32,
    *mut i64,
    *mut f64,
    *mut f64,
    *mut i64,
    *mut f64,
    *mut i64,
    *mut i64,
    *mut i64,
    *mut i64,
    *mut f64,
    *mut f64,
    *mut f64,
) -> i32;
type Ari = unsafe extern "C" fn(*mut c_void, *const i64, *const i64, i64, *mut f64) -> i32;

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum SelectionMethod {
    Eom,
    Leaf,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct HdbscanParameters {
    pub min_cluster_size: usize,
    pub min_samples: usize,
    pub selection_method: SelectionMethod,
    pub allow_single_cluster: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct NativeFailure {
    pub status_code: Option<i32>,
    pub reason: String,
    pub native_message: Option<String>,
}
impl NativeFailure {
    pub fn transport(reason: impl Into<String>) -> Self {
        Self {
            status_code: None,
            reason: reason.into(),
            native_message: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct NonfiniteDiagnostic {
    pub field: String,
    pub index: usize,
    pub native_value: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct HdbscanNode {
    pub parent: i64,
    pub size: i64,
    pub label: i64,
    pub lambda_birth: Option<f64>,
    pub lambda_death: Option<f64>,
    pub stability: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct HdbscanOutput {
    pub native_status: i32,
    pub noise_label: i64,
    pub labels: Vec<i64>,
    pub membership_strengths: Vec<f64>,
    pub outlier_scores: Vec<Option<f64>>,
    pub cluster_persistence: Vec<Option<f64>>,
    pub n_clusters: usize,
    pub hierarchy: Vec<HdbscanNode>,
    pub nonfinite_diagnostics: Vec<NonfiniteDiagnostic>,
}

#[derive(Debug, Serialize)]
pub struct FittedPca<'a> {
    pub mean: Vec<f64>,
    pub loadings: Vec<Vec<f64>>,
    pub eigenvalues: Vec<f64>,
    pub full_moments: Option<[f64; 2]>,
    pub full_moments_unavailable_reason: Option<String>,
    pub covariance_trace: f64,
    pub backend: String,
    pub train_scores: Vec<Vec<f64>>,
    #[serde(skip)]
    pub flexible: Option<FlexibleProjection<'a>>,
}

#[derive(Debug)]
pub struct FlexibleProjection<'a> {
    handle: *mut c_void,
    transform: FlexTransform,
    destroy: Destroy,
    p: usize,
    k: usize,
    _owner: PhantomData<&'a Methods>,
}
impl Drop for FlexibleProjection<'_> {
    fn drop(&mut self) {
        // SAFETY: the lifetime binds this handle to the still-loaded owning library.
        unsafe { (self.destroy)(self.handle) }
    }
}
impl FlexibleProjection<'_> {
    pub fn transform(&self, x: &[Vec<f64>]) -> Result<Vec<Vec<f64>>, String> {
        if x.is_empty()
            || x.iter()
                .any(|r| r.len() != self.p || r.iter().any(|v| !v.is_finite()))
        {
            return Err("INVALID_FLEXIBLE_PCA_TRANSFORM".into());
        }
        let mut input: Vec<_> = x.iter().flatten().copied().collect();
        let mut output = vec![0.0; x.len() * self.k];
        // SAFETY: finite row-major matrices own precisely the declared buffers.
        let status = unsafe {
            (self.transform)(
                self.handle,
                MatrixView::new(&mut input, x.len(), self.p),
                MatrixView::new(&mut output, x.len(), self.k),
            )
        };
        if status != 0 || output.iter().any(|v| !v.is_finite()) {
            return Err(format!("FLEXIBLE_PCA_TRANSFORM_STATUS_{status}"));
        }
        Ok(output.chunks(self.k).map(|r| r.to_vec()).collect())
    }
}

pub struct Methods {
    pub provider: NativeMethodsProvider,
    pub version: String,
    pub abi: String,
    _library: Library,
    context: *mut c_void,
    destroy: Destroy,
    pca: Pca,
    _thread_bound: PhantomData<Rc<()>>,
}

impl Methods {
    pub fn clustering_capability(&self) -> Result<(), NativeFailure> {
        self.require_clustering_abi()?;
        // SAFETY: symbol inspection only, with public ABI signatures.
        unsafe {
            self._library
                .get::<Hdbscan>(b"n4m_cluster_hdbscan\0")
                .map_err(|e| {
                    NativeFailure::transport(format!("METHODS_HDBSCAN_SYMBOL_UNAVAILABLE:{e}"))
                })?;
            self._library
                .get::<Ari>(b"n4m_preflight_adjusted_rand_index\0")
                .map_err(|e| {
                    NativeFailure::transport(format!("METHODS_ARI_SYMBOL_UNAVAILABLE:{e}"))
                })?;
        }
        Ok(())
    }
    fn require_clustering_abi(&self) -> Result<(), NativeFailure> {
        // SAFETY: checked public version function on the owning loaded library.
        let compatible = unsafe {
            self._library
                .get::<unsafe extern "C" fn(u32, u32) -> i32>(b"n4m_check_abi_compatibility\0")
                .map_err(|e| NativeFailure::transport(e.to_string()))?(2, 19)
        };
        if compatible != 0 {
            return Err(NativeFailure::transport("METHODS_ABI_2_19_REQUIRED"));
        }
        Ok(())
    }
    fn native_failure(&self, operation: &str, code: i32) -> NativeFailure {
        // SAFETY: copy the context-owned error immediately, before another native call.
        let native_message = unsafe {
            self._library
                .get::<unsafe extern "C" fn(*const c_void) -> *const c_char>(
                    b"n4m_context_last_error\0",
                )
                .ok()
                .and_then(|f| {
                    let p = f(self.context);
                    (!p.is_null()).then(|| CStr::from_ptr(p).to_string_lossy().into_owned())
                })
        };
        NativeFailure {
            status_code: Some(code),
            reason: format!("{operation}_STATUS_{code}"),
            native_message,
        }
    }
    pub fn hdbscan(
        &self,
        x: &[Vec<f64>],
        parameters: &HdbscanParameters,
    ) -> Result<HdbscanOutput, NativeFailure> {
        self.require_clustering_abi()?;
        let n = x.len();
        let p = x.first().map_or(0, Vec::len);
        if n < 2
            || p == 0
            || parameters.min_cluster_size < 2
            || parameters.min_samples < 1
            || parameters.min_samples > n
            || x.iter()
                .any(|r| r.len() != p || r.iter().any(|v| !v.is_finite()))
            || n.checked_mul(n)
                .and_then(|v| v.checked_mul(p))
                .is_none_or(|v| v > 2_500_000_000)
            || n.checked_mul(p).is_none_or(|v| v > 10_000_000)
        {
            return Err(NativeFailure::transport(
                "INVALID_HDBSCAN_REQUEST_OR_BUDGET",
            ));
        }
        // Every output has the public X.rows capacity; counts are validated before truncation.
        let mut input: Vec<_> = x.iter().flatten().copied().collect();
        let mut labels = vec![0; n];
        let mut strengths = vec![0.; n];
        let mut outliers = vec![0.; n];
        let mut persistence = vec![0.; n];
        let mut count = 0i64;
        let mut nodes = 0i64;
        let mut parent = vec![0; n];
        let mut size = vec![0; n];
        let mut tree_label = vec![0; n];
        let mut birth = vec![0.; n];
        let mut death = vec![0.; n];
        let mut stability = vec![0.; n];
        // SAFETY: exact metrics.h signature, live finite row-major input and n-capacity outputs.
        let code = unsafe {
            let call = self
                ._library
                .get::<Hdbscan>(b"n4m_cluster_hdbscan\0")
                .map_err(|e| NativeFailure::transport(e.to_string()))?;
            call(
                self.context,
                &MatrixView::new(&mut input, n, p),
                parameters.min_cluster_size as i64,
                parameters.min_samples as i64,
                if parameters.selection_method == SelectionMethod::Eom {
                    0
                } else {
                    1
                },
                i32::from(parameters.allow_single_cluster),
                labels.as_mut_ptr(),
                strengths.as_mut_ptr(),
                outliers.as_mut_ptr(),
                &mut count,
                persistence.as_mut_ptr(),
                &mut nodes,
                parent.as_mut_ptr(),
                size.as_mut_ptr(),
                tree_label.as_mut_ptr(),
                birth.as_mut_ptr(),
                death.as_mut_ptr(),
                stability.as_mut_ptr(),
            )
        };
        if code != 0 {
            return Err(self.native_failure("METHODS_HDBSCAN", code));
        }
        if count < 0
            || count as usize > n
            || nodes < 0
            || nodes as usize > n
            || labels.iter().any(|&v| v < -1 || v >= count)
            || strengths
                .iter()
                .any(|v| !v.is_finite() || !(0. ..=1.).contains(v))
        {
            return Err(NativeFailure::transport("INVALID_HDBSCAN_OUTPUT_CONTRACT"));
        }
        let mut diagnostics = Vec::new();
        let mut finite = |value: f64, field: &str, index: usize| {
            if value.is_finite() {
                Some(value)
            } else {
                diagnostics.push(NonfiniteDiagnostic {
                    field: field.into(),
                    index,
                    native_value: if value.is_nan() {
                        "undefined_nan"
                    } else if value.is_sign_positive() {
                        "positive_infinity"
                    } else {
                        "negative_infinity"
                    }
                    .into(),
                });
                None
            }
        };
        let outlier_scores = outliers
            .iter()
            .enumerate()
            .map(|(i, &v)| finite(v, "outlier_scores", i))
            .collect();
        let cluster_persistence = persistence[..count as usize]
            .iter()
            .enumerate()
            .map(|(i, &v)| finite(v, "cluster_persistence", i))
            .collect();
        let hierarchy = (0..nodes as usize)
            .map(|i| HdbscanNode {
                parent: parent[i],
                size: size[i],
                label: tree_label[i],
                lambda_birth: finite(birth[i], "hierarchy.lambda_birth", i),
                lambda_death: finite(death[i], "hierarchy.lambda_death", i),
                stability: finite(stability[i], "hierarchy.stability", i),
            })
            .collect();
        Ok(HdbscanOutput {
            native_status: code,
            noise_label: -1,
            labels,
            membership_strengths: strengths,
            outlier_scores,
            cluster_persistence,
            n_clusters: count as usize,
            hierarchy,
            nonfinite_diagnostics: diagnostics,
        })
    }
    pub fn adjusted_rand_index(&self, a: &[i64], b: &[i64]) -> Result<Option<f64>, NativeFailure> {
        self.require_clustering_abi()?;
        if a.len() != b.len() || a.len() > 100_000 {
            return Err(NativeFailure::transport("INVALID_ARI_REQUEST_OR_BUDGET"));
        }
        let mut value = f64::NAN;
        // SAFETY: equal live label slices, exact metrics.h signature; empty slices are never dereferenced.
        let code = unsafe {
            self._library
                .get::<Ari>(b"n4m_preflight_adjusted_rand_index\0")
                .map_err(|e| NativeFailure::transport(e.to_string()))?(
                self.context,
                a.as_ptr(),
                b.as_ptr(),
                a.len() as i64,
                &mut value,
            )
        };
        if code != 0 {
            return Err(self.native_failure("METHODS_ARI", code));
        }
        Ok(value.is_finite().then_some(value))
    }
    pub fn load(path: &Path) -> Result<Self, String> {
        let provider = NativeMethodsProvider::load(path).map_err(|e| e.0)?;
        // SAFETY: explicit user-selected library; ABI and every symbol checked
        // before constructing a context. No handle crosses provider instances.
        unsafe {
            let library = Library::new(path).map_err(|e| e.to_string())?;
            let compat = library
                .get::<unsafe extern "C" fn(u32, u32) -> i32>(b"n4m_check_abi_compatibility\0")
                .map_err(|e| e.to_string())?;
            if compat(2, 18) != 0 {
                return Err("METHODS_ABI_2_18_REQUIRED".into());
            }
            let create = *library
                .get::<unsafe extern "C" fn(*mut *mut c_void) -> i32>(b"n4m_context_create\0")
                .map_err(|e| e.to_string())?;
            let destroy = *library
                .get::<Destroy>(b"n4m_context_destroy\0")
                .map_err(|e| e.to_string())?;
            let pca = *library
                .get::<Pca>(b"n4m_preflight_pca_compute\0")
                .map_err(|e| e.to_string())?;
            let version_fn = library
                .get::<unsafe extern "C" fn() -> *const c_char>(b"n4m_get_version_string\0")
                .map_err(|e| e.to_string())?;
            let ptr = version_fn();
            if ptr.is_null() {
                return Err("NULL_METHODS_VERSION".into());
            }
            let version = CStr::from_ptr(ptr).to_string_lossy().into_owned();
            let major = library
                .get::<unsafe extern "C" fn() -> u32>(b"n4m_get_abi_version_major\0")
                .map_err(|e| e.to_string())?();
            let minor = library
                .get::<unsafe extern "C" fn() -> u32>(b"n4m_get_abi_version_minor\0")
                .map_err(|e| e.to_string())?();
            let patch = library
                .get::<unsafe extern "C" fn() -> u32>(b"n4m_get_abi_version_patch\0")
                .map_err(|e| e.to_string())?();
            let mut context = std::ptr::null_mut();
            if create(&mut context) != 0 || context.is_null() {
                return Err("METHODS_CONTEXT_FAILED".into());
            }
            Ok(Self {
                provider,
                version,
                abi: format!("{major}.{minor}.{patch}"),
                _library: library,
                context,
                destroy,
                pca,
                _thread_bound: PhantomData,
            })
        }
    }

    pub fn fit_pca(&self, x: &[Vec<f64>], k: usize) -> Result<FittedPca<'_>, String> {
        let n = x.len();
        let p = x.first().map_or(0, Vec::len);
        if n < 2
            || p == 0
            || k == 0
            || k > p.min(n - 1)
            || x.iter()
                .any(|r| r.len() != p || r.iter().any(|v| !v.is_finite()))
            || n.checked_mul(p).is_none_or(|v| v > 10_000_000)
        {
            return Err("INVALID_PCA_REQUEST_OR_BUDGET".into());
        }
        if n.min(p)
            .checked_mul(n.min(p))
            .and_then(|m| m.checked_mul(n.max(p)))
            .is_none_or(|m| m > 250_000_000)
        {
            return self.fit_flexible(x, k);
        }
        let mean = (0..p)
            .map(|j| {
                self.provider
                    .summary(&SummaryRequest {
                        values: x.iter().map(|r| r[j]).collect(),
                    })
                    .map(|s| s.mean)
                    .map_err(|e| e.0)
            })
            .collect::<Result<Vec<_>, _>>()?;
        let mut input = x.iter().flatten().copied().collect::<Vec<_>>();
        let mut scores = vec![0.0; n * k];
        let mut loadings = vec![0.0; k * p];
        let mut eigenvalues = vec![0.0; k];
        let mut moments = [0.0; 2];
        let xv = MatrixView::new(&mut input, n, p);
        let sv = MatrixView::new(&mut scores, n, k);
        let lv = MatrixView::new(&mut loadings, k, p);
        // SAFETY: all row-major f64 buffers have exactly the declared capacity;
        // owned allocations remain live throughout this synchronous call.
        let status = unsafe {
            (self.pca)(
                self.context,
                &xv,
                k as i32,
                &sv,
                &lv,
                eigenvalues.as_mut_ptr(),
                moments.as_mut_ptr(),
            )
        };
        if status != 0 {
            return Err(format!("METHODS_PCA_STATUS_{status}"));
        }
        if scores
            .iter()
            .chain(&loadings)
            .chain(&eigenvalues)
            .chain(&moments)
            .any(|v| !v.is_finite())
        {
            return Err("NONFINITE_PCA_OUTPUT".into());
        }
        Ok(FittedPca {
            mean,
            loadings: loadings.chunks(p).map(|r| r.to_vec()).collect(),
            eigenvalues,
            full_moments: Some(moments),
            full_moments_unavailable_reason: None,
            covariance_trace: moments[0],
            backend: "Methods preflight PCA + full moments".into(),
            flexible: None,
            train_scores: scores.chunks(k).map(|r| r.to_vec()).collect(),
        })
    }

    /// Public FlexiblePCA fit/transform. Full squared covariance trace stays optional.
    pub fn fit_flexible(&self, x: &[Vec<f64>], k: usize) -> Result<FittedPca<'_>, String> {
        let n = x.len();
        let p = x.first().map_or(0, Vec::len);
        if n < 2
            || p == 0
            || k == 0
            || k > p.min(n - 1)
            || x.iter()
                .any(|r| r.len() != p || r.iter().any(|v| !v.is_finite()))
            || n.checked_mul(p).is_none_or(|v| v > 10_000_000)
            || p.checked_mul(p)
                .and_then(|v| v.checked_mul(k))
                .is_none_or(|v| v > 250_000_000)
        {
            return Err("FLEXIBLE_PCA_REQUEST_OR_AFFINE_QUERY_BUDGET".into());
        }
        let summaries = (0..p)
            .map(|j| {
                self.provider
                    .summary(&SummaryRequest {
                        values: x.iter().map(|r| r[j]).collect(),
                    })
                    .map_err(|e| e.0)
            })
            .collect::<Result<Vec<_>, _>>()?;
        let mean = summaries.iter().map(|s| s.mean).collect();
        let covariance_trace = self
            .provider
            .summary(&SummaryRequest {
                values: summaries
                    .iter()
                    .map(|s| s.sample_sd.unwrap_or(0.0).powi(2))
                    .collect(),
            })
            .map_err(|e| e.0)?
            .mean
            * p as f64;
        let state = unsafe {
            // SAFETY: the public ABI signatures and owning handle lifecycle match decomposition.h.
            let create = *self
                ._library
                .get::<FlexCreate>(b"n4m_decomposition_flexible_pca_create\0")
                .map_err(|e| e.to_string())?;
            let fit = *self
                ._library
                .get::<FlexFit>(b"n4m_decomposition_flexible_pca_fit\0")
                .map_err(|e| e.to_string())?;
            let transform = *self
                ._library
                .get::<FlexTransform>(b"n4m_decomposition_flexible_pca_transform\0")
                .map_err(|e| e.to_string())?;
            let destroy = *self
                ._library
                .get::<Destroy>(b"n4m_decomposition_flexible_pca_destroy\0")
                .map_err(|e| e.to_string())?;
            let cols = *self
                ._library
                .get::<FlexCols>(b"n4m_decomposition_flexible_pca_output_cols\0")
                .map_err(|e| e.to_string())?;
            let mut handle = std::ptr::null_mut();
            let status = create(&mut handle, k as f64);
            if status != 0 || handle.is_null() {
                return Err(format!("FLEXIBLE_PCA_CREATE_STATUS_{status}"));
            }
            let mut state = FlexibleProjection {
                handle,
                transform,
                destroy,
                p,
                k,
                _owner: PhantomData,
            };
            let mut input: Vec<_> = x.iter().flatten().copied().collect();
            let status = fit(handle, MatrixView::new(&mut input, n, p));
            if status != 0 {
                return Err(format!("FLEXIBLE_PCA_FIT_STATUS_{status}"));
            }
            let mut actual = 0;
            let status = cols(handle, &mut actual);
            if status != 0 || actual <= 0 || actual > k as i64 {
                return Err("FLEXIBLE_PCA_OUTPUT_WIDTH".into());
            }
            state.k = actual as usize;
            state
        };
        let train_scores = state.transform(x)?;
        let eigenvalues = (0..state.k)
            .map(|j| {
                self.provider
                    .summary(&SummaryRequest {
                        values: train_scores.iter().map(|r| r[j]).collect(),
                    })
                    .map(|s| s.sample_sd.unwrap_or(0.0).powi(2))
                    .map_err(|e| e.0)
            })
            .collect::<Result<Vec<_>, _>>()?;
        // Recover the fitted affine operator through public transforms, never private struct access.
        // Transforming zero and coordinate vectors cannot fit or change the retained state.
        let offset = state.transform(&[vec![0.0; p]])?.remove(0);
        let mut loadings = vec![vec![0.0; p]; state.k];
        for start in (0..p).step_by(128) {
            let count = 128.min(p - start);
            let mut basis = vec![vec![0.0; p]; count];
            for (i, row) in basis.iter_mut().enumerate() {
                row[start + i] = 1.0;
            }
            let transformed = state.transform(&basis)?;
            for (i, row) in transformed.iter().enumerate() {
                for j in 0..state.k {
                    loadings[j][start + i] = row[j] - offset[j];
                }
            }
        }
        let (moments, moment_reason) = if n
            .min(p)
            .checked_mul(n.min(p))
            .and_then(|m| m.checked_mul(n.max(p)))
            .is_some_and(|m| m <= 250_000_000)
        {
            match self.fit_pca(x, 1) {
                Ok(fitted) => (fitted.full_moments, None),
                Err(reason) => (
                    None,
                    Some(format!("EXACT_COVARIANCE_MOMENTS_UNAVAILABLE:{reason}")),
                ),
            }
        } else {
            (
                None,
                Some("EXACT_SQUARED_COVARIANCE_TRACE_EXCEEDS_PUBLIC_MOMENT_BUDGET".into()),
            )
        };
        Ok(FittedPca{mean,loadings,eigenvalues,full_moments:moments,full_moments_unavailable_reason:moment_reason,covariance_trace,train_scores,backend:"Methods FlexiblePCA public fit/transform; affine operator via coordinate queries; variances via Methods summaries".into(),flexible:Some(state)})
    }
}
impl Drop for Methods {
    fn drop(&mut self) {
        // SAFETY: this context was created by this still-loaded library.
        unsafe { (self.destroy)(self.context) }
    }
}
