// SPDX-License-Identifier: CECILL-2.1 OR AGPL-3.0-or-later
// Transport only. Methods owns all preprocessing and comparison kernels.
import * as methods from '@nirs4all/methods';

const MAX_CELLS = 1_000_000;
const MAX_STATE_BYTES = 2 * 1024 * 1024;
const OPERATORS = Object.freeze({
  SNV: methods.SNV,
  MSC: methods.MSC,
  Detrend: methods.Detrend,
  SavitzkyGolay: methods.SavitzkyGolay,
  Gaussian: methods.Gaussian,
  StandardScale: methods.StandardScale,
  Normalize: methods.Normalize,
  CropTransformer: methods.CropTransformer,
});

const internal = reason => {
  throw Object.assign(new Error(reason), { kind:'internal', reason });
};

function matrix(rows) {
  if (!Array.isArray(rows) || rows.length < 1 || !Array.isArray(rows[0])) {
    internal('PREPROCESS_MATRIX_BUDGET_OR_SHAPE');
  }
  const n = rows.length, p = rows[0].length;
  if (!Number.isSafeInteger(p) || p < 1 || n * p > MAX_CELLS) {
    internal('PREPROCESS_MATRIX_BUDGET_OR_SHAPE');
  }
  const data = new Float64Array(n * p);
  for (let i = 0; i < n; i++) {
    if (!Array.isArray(rows[i]) || rows[i].length !== p) internal('PREPROCESS_MATRIX_BUDGET_OR_SHAPE');
    for (let j = 0; j < p; j++) {
      const value = rows[i][j];
      if (typeof value !== 'number' || !Number.isFinite(value)) internal('PREPROCESS_MATRIX_NONFINITE');
      data[i * p + j] = value;
    }
  }
  return { data, rows:n, cols:p };
}

function finiteOutput(value, label) {
  if (!value || !Number.isSafeInteger(value.rows) || value.rows < 1 ||
      !Number.isSafeInteger(value.cols) || value.cols < 1 ||
      value.rows * value.cols > MAX_CELLS || value.data?.length !== value.rows * value.cols) {
    internal(`${label}_SHAPE`);
  }
  for (const x of value.data) if (!Number.isFinite(x)) internal(`${label}_NONFINITE`);
  return Array.from({ length:value.rows }, (_, i) =>
    Array.from(value.data.subarray(i * value.cols, (i + 1) * value.cols)));
}

function state(estimator) {
  const bytes = estimator.toN4me();
  if (!(bytes instanceof Uint8Array) || bytes.length < 1 || bytes.length > MAX_STATE_BYTES) {
    internal('PREPROCESS_STATE_BUDGET_OR_SHAPE');
  }
  return Uint8Array.from(bytes);
}

function stateArray(bytes) {
  if (!Array.isArray(bytes) || bytes.length < 1 || bytes.length > MAX_STATE_BYTES ||
      bytes.some(x => !Number.isInteger(x) || x < 0 || x > 255)) {
    internal('PREPROCESS_STATE_BUDGET_OR_SHAPE');
  }
  return Uint8Array.from(bytes);
}

function sameBytes(a, b) {
  return a.length === b.length && a.every((x, i) => x === b[i]);
}

function labels(value, name) {
  if (!Array.isArray(value) || value.length > MAX_CELLS ||
      value.some(x => !Number.isSafeInteger(x))) {
    internal('PREPROCESS_LABEL_BUDGET_OR_SHAPE');
  }
  return value;
}

function integer(value, name, minimum = 0) {
  if (!Number.isSafeInteger(value) || value < minimum) internal(`INVALID_${name}`);
  return value;
}

function nullable(value) {
  return Number.isFinite(value) ? value : null;
}

function dispose(estimator) {
  if (estimator) estimator.dispose();
}

/** Methods must already be loaded. Each callback owns at most one fitted estimator. */
export function createPreprocessingCallback(backend_version) {
  const abi = methods.abiVersion();
  if (abi[0] !== 2 || abi[1] < 20) throw new Error('METHODS_ABI_2_20_REQUIRED');
  if (backend_version !== methods.version()) throw new Error('METHODS_VERSION_MISMATCH');

  let estimator = null;

  function dispatch(operation, request) {
    switch (operation) {
      case 'preprocess_fit': {
        const Cls = OPERATORS[request.operator];
        if (!Object.hasOwn(OPERATORS, request.operator) || !Cls) internal('UNSUPPORTED_PREPROCESSOR');
        if (Object.hasOwn(request, 'y') || Object.hasOwn(request, 'Y') || Object.hasOwn(request, 'labels')) {
          internal('PREPROCESS_Y_NOT_ALLOWED');
        }
        if (!request.parameters || typeof request.parameters !== 'object' || Array.isArray(request.parameters)) {
          internal('INVALID_PREPROCESS_PARAMETERS');
        }
        const X = matrix(request.matrix);
        let candidate;
        try {
          candidate = new Cls(request.parameters);
          candidate.fit(X);
          const bytes = state(candidate);
          const old = estimator;
          estimator = candidate;
          candidate = null;
          dispose(old);
          return { state_bytes:Array.from(bytes) };
        } finally { dispose(candidate); }
      }
      case 'preprocess_transform': {
        if (!estimator) internal('PREPROCESS_STATE_NOT_FITTED');
        const X = matrix(request.matrix);
        const before = state(estimator);
        let transformed;
        try {
          transformed = estimator.transform(X);
        } catch (error) {
          const afterFailure = state(estimator);
          if (!sameBytes(before, afterFailure)) {
            let restored;
            try {
              restored = methods.NativeEstimator.fromN4me(before);
              if (restored.methodId !== estimator.methodId) internal('PREPROCESS_STATE_RESTORE_MISMATCH');
              const changed = estimator;
              estimator = restored;
              restored = null;
              dispose(changed);
            } finally { dispose(restored); }
          }
          throw error;
        }
        const after = state(estimator);
        if (!sameBytes(before, after)) {
          let restored;
          try {
            restored = methods.NativeEstimator.fromN4me(before);
            if (restored.methodId !== estimator.methodId) internal('PREPROCESS_STATE_RESTORE_MISMATCH');
            const changed = estimator;
            estimator = restored;
            restored = null;
            dispose(changed);
          } finally { dispose(restored); }
          internal('PREPROCESS_STATE_CHANGED_DURING_TRANSFORM');
        }
        const output = finiteOutput(transformed, 'PREPROCESS_OUTPUT');
        return { matrix:output, state_bytes:Array.from(after) };
      }
      case 'preprocess_restore': {
        const Cls = OPERATORS[request.operator];
        if (!Object.hasOwn(OPERATORS, request.operator) || !Cls) internal('UNSUPPORTED_PREPROCESSOR');
        const bytes = stateArray(request.state_bytes);
        let candidate;
        try {
          candidate = methods.NativeEstimator.fromN4me(bytes);
          if (candidate.methodId !== new Cls().methodId) internal('PREPROCESS_STATE_OPERATOR_MISMATCH');
          const exported = state(candidate);
          if (!sameBytes(bytes, exported)) internal('PREPROCESS_STATE_ROUNDTRIP_MISMATCH');
          const old = estimator;
          estimator = candidate;
          candidate = null;
          dispose(old);
          return { state_bytes:Array.from(exported) };
        } finally { dispose(candidate); }
      }
      case 'preprocess_destroy': {
        dispose(estimator);
        estimator = null;
        return { destroyed:true };
      }
      case 'adjusted_rand': {
        const a = labels(request.labels_a, 'labels_a');
        const b = labels(request.labels_b, 'labels_b');
        if (a.length !== b.length) internal('PREPROCESS_LABEL_LENGTH_MISMATCH');
        return { value:nullable(methods.preflightAdjustedRandIndex(a, b)) };
      }
      case 'cluster_jaccard': {
        const a = labels(request.labels_a, 'labels_a');
        const b = labels(request.labels_b, 'labels_b');
        if (a.length !== b.length) internal('PREPROCESS_LABEL_LENGTH_MISMATCH');
        const nA = integer(request.n_clusters_a, 'CLUSTER_COUNT_A');
        const nB = integer(request.n_clusters_b, 'CLUSTER_COUNT_B');
        if (nA * nB > MAX_CELLS) internal('PREPROCESS_JACCARD_BUDGET');
        const result = methods.clusterJaccardMatrix(a, b, nA, nB);
        return {
          jaccard:Array.from({ length:result.jaccard.rows }, (_, i) =>
            Array.from(result.jaccard.data.subarray(i * result.jaccard.cols, (i + 1) * result.jaccard.cols), nullable)),
          intersections:Array.from({ length:result.jaccard.rows }, (_, i) =>
            result.intersections.slice(i * result.jaccard.cols, (i + 1) * result.jaccard.cols)),
          sizes_a:result.sizesA,
          sizes_b:result.sizesB,
        };
      }
      default:
        throw Object.assign(new Error('UNSUPPORTED_METHODS_OPERATION'), {
          kind:'unsupported', reason:'UNSUPPORTED_METHODS_OPERATION',
        });
    }
  }

  return (operation, payloadJSON) => {
    try {
      return JSON.stringify({ ok:{ ...dispatch(operation, JSON.parse(payloadJSON)), backend_version } });
    } catch (error) {
      return JSON.stringify({ provider_error:error instanceof methods.N4mError
        ? { methods_status:error.status, message:error.message, backend_version }
        : { kind:error?.kind ?? 'internal', reason:error?.reason ?? 'PREPROCESSING_ADAPTER_FAILED', backend_version } });
    }
  };
}
