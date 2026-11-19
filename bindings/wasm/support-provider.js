// SPDX-License-Identifier: CECILL-2.1 OR AGPL-3.0-or-later
// Transport only. Domains owns the admission protocol; Methods owns the numerical kernels.
import * as methods from '@nirs4all/methods';

const MAX_CELLS = 1_000_000;
const MAX_STATE_BYTES = 2 * 1024 * 1024;
const nullable = value => Number.isFinite(value) ? value : null;
const invalid = reason => {
  throw Object.assign(new Error(reason), { kind:'internal', reason });
};
function matrix(rows, maxCells = MAX_CELLS) {
  if (!Array.isArray(rows) || rows.length < 1 || rows.length > maxCells || !Array.isArray(rows[0])) {
    invalid('PROVIDER_MATRIX_BUDGET_OR_SHAPE');
  }
  const n = rows.length, p = rows[0].length;
  if (!Number.isSafeInteger(p) || p < 1 || n * p > maxCells) invalid('PROVIDER_MATRIX_BUDGET_OR_SHAPE');
  const data = new Float64Array(n * p);
  for (let i = 0; i < n; i++) {
    const row = rows[i];
    if (!Array.isArray(row) || row.length !== p) invalid('PROVIDER_MATRIX_BUDGET_OR_SHAPE');
    for (let j = 0; j < p; j++) {
      const value = row[j];
      if (typeof value !== 'number' || !Number.isFinite(value)) invalid('PROVIDER_MATRIX_NONFINITE');
      data[i * p + j] = value;
    }
  }
  return { data, rows:n, cols:p };
}
function vector(values) {
  if (!Array.isArray(values) || values.length < 1 || values.length > MAX_CELLS || values.some(x => typeof x !== 'number' || !Number.isFinite(x))) {
    invalid('PROVIDER_VECTOR_BUDGET_OR_SHAPE');
  }
  return Float64Array.from(values);
}
function nested(data, rows, cols) {
  return Array.from({ length:rows }, (_, i) => Array.from(data.subarray(i * cols, (i + 1) * cols)));
}
function sameBytes(a, b) {
  return a.length === b.length && a.every((value, i) => value === b[i]);
}
function dispose(estimator) {
  if (estimator) estimator.dispose();
}

/** Methods must already be loaded. Calls are synchronous and use only pinned public APIs. */
export function createSupportCallback(backend_version) {
  const abi = methods.abiVersion();
  if (abi[0] !== 2 || abi[1] < 24) throw new Error('METHODS_ABI_2_24_REQUIRED');
  if (backend_version !== methods.version()) throw new Error('METHODS_VERSION_MISMATCH');

  let estimator = null;

  function dispatch(operation, r) {
    switch (operation) {
      case 'pca_fit': {
        if (estimator) invalid('PCA_STATE_ALREADY_FITTED');
        const X = matrix(r.matrix);
        if (typeof r.n_components !== 'number' || !Number.isFinite(r.n_components) || r.n_components <= 0 ||
            (r.n_components >= 1 && !Number.isSafeInteger(r.n_components))) invalid('INVALID_PCA_FIT_REQUEST');
        let candidate;
        try {
          candidate = new methods.FlexiblePCA({ n_components:r.n_components }).fit(X);
          const bytes = candidate.toN4me();
          if (bytes.length > MAX_STATE_BYTES) invalid('PROVIDER_STATE_BUDGET_OR_SHAPE');
          estimator = candidate;
          candidate = undefined;
          return { state_bytes:Array.from(bytes) };
        } finally { dispose(candidate); }
      }
      case 'pca_transform': {
        if (!estimator) invalid('PCA_STATE_NOT_FITTED');
        const X = matrix(r.matrix);
        const before = estimator.toN4me();
        let scores;
        try {
          scores = estimator.transform(X);
        } catch (error) {
          if (!sameBytes(before, estimator.toN4me())) invalid('FITTED_PCA_STATE_CHANGED_DURING_TRANSFORM');
          throw error;
        }
        const after = estimator.toN4me();
        if (!sameBytes(before, after)) invalid('FITTED_PCA_STATE_CHANGED_DURING_TRANSFORM');
        return {
          scores:nested(scores.data, scores.rows, scores.cols),
          state_bytes:Array.from(after),
        };
      }
      case 'pca_destroy': {
        if (estimator) dispose(estimator);
        estimator = null;
        return { destroyed:true };
      }      case 'pca_monitor': {
        const referenceRows = r.reference;
        const monitoredRows = r.monitored;
        if (!Array.isArray(referenceRows) || !Array.isArray(monitoredRows) || !referenceRows.length || !monitoredRows.length) {
          invalid('PROVIDER_MATRIX_BUDGET_OR_SHAPE');
        }
        const p = referenceRows[0]?.length ?? 0;
        if ((referenceRows.length + monitoredRows.length) * p > MAX_CELLS) invalid('PROVIDER_MATRIX_BUDGET_OR_SHAPE');
        const reference = matrix(referenceRows);
        const monitored = matrix(monitoredRows);
        if (reference.cols !== monitored.cols) invalid('INVALID_PCA_MONITOR_REQUEST');
        if (!Number.isSafeInteger(r.max_components) || !Number.isSafeInteger(r.n_folds) ||
            typeof r.alpha !== 'number' || !Number.isFinite(r.alpha)) invalid('INVALID_PCA_MONITOR_REQUEST');
        const o = methods.statsPcaMonitor(reference, monitored, r.max_components, r.n_folds, r.alpha);
        return {
          eigenvalues:Array.from(o.eigenvalues, nullable),
          effective_components:o.effectiveComponents,
          reference_t2:Array.from(o.referenceT2, nullable),
          reference_q:Array.from(o.referenceQ, nullable),
          monitored_t2:Array.from(o.monitoredT2, nullable),
          monitored_q:Array.from(o.monitoredQ, nullable),
          n_beyond_t2:o.nBeyondT2,
          n_beyond_q:o.nBeyondQ,
          n_beyond_either:o.nBeyondEither,
          n_near_t2:o.nNearT2,
          n_near_q:o.nNearQ,
          n_near_either:o.nNearEither,
          t2_limit:nullable(o.t2Limit),
          q_limit:nullable(o.qLimit),
          tolerance:nullable(o.tolerance),
          condition:nullable(o.condition),
          q_tolerance_scale:nullable(o.qToleranceScale),
          eigenvalue_resolution:nullable(o.eigenvalueResolution),
          reference_total_variance:nullable(o.referenceTotalVariance),
          monitored_total_variance:nullable(o.monitoredTotalVariance),
          centroid_distance:nullable(o.centroidDistance),
          centroid_subspace_distance:nullable(o.centroidSubspaceDistance),
          centroid_residual_distance:nullable(o.centroidResidualDistance),
          centroid_t2:nullable(o.centroidT2),
          retained_fraction:nullable(o.retainedFraction),
        };
      }
      case 'summary': {
        const o = methods.preflightSummary(vector(r.values));
        return Object.fromEntries(['count','min','max','mean','sample_sd','q25','median','q75']
          .map((key, i) => [key, nullable(o[i])]));
      }
      default: throw Object.assign(new Error('UNSUPPORTED_METHODS_OPERATION'), { kind:'unsupported', reason:'UNSUPPORTED_METHODS_OPERATION' });
    }
  }

  return (operation, payloadJSON) => {
    try { return JSON.stringify({ ok:{ ...dispatch(operation, JSON.parse(payloadJSON)), backend_version } }); }
    catch (error) {
      return JSON.stringify({ provider_error:error instanceof methods.N4mError
        ? { methods_status:error.status, message:error.message }
        : { kind:error?.kind ?? 'internal', reason:error?.reason ?? 'METHODS_ADAPTER_FAILED' } });
    }
  };
}
