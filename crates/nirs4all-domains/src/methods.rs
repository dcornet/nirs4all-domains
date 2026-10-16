//! Safe owning adapter to Methods ABI 2.18. Numerical algorithms stay upstream.
//! Preflight's public provider omits PCA loadings, so this adapter retains them.
use libloading::Library;
use nirs4all_preflight::{native::NativeMethodsProvider, MethodsProvider, SummaryRequest};
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
