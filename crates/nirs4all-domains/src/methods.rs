//! Safe owning adapter to Methods ABI 2.18. Numerical algorithms stay upstream.
//! Preflight's public provider omits PCA loadings, so this adapter retains them.
use libloading::Library;
use nirs4all_preflight::{native::NativeMethodsProvider, MethodsProvider, SummaryRequest};
use serde::{Deserialize, Serialize};
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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FittedPca {
    pub mean: Vec<f64>,
    pub loadings: Vec<Vec<f64>>,
    pub eigenvalues: Vec<f64>,
    pub full_moments: [f64; 2],
    pub train_scores: Vec<Vec<f64>>,
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

    pub fn fit_pca(&self, x: &[Vec<f64>], k: usize) -> Result<FittedPca, String> {
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
            full_moments: moments,
            train_scores: scores.chunks(k).map(|r| r.to_vec()).collect(),
        })
    }
}
impl Drop for Methods {
    fn drop(&mut self) {
        // SAFETY: this context was created by this still-loaded library.
        unsafe { (self.destroy)(self.context) }
    }
}
