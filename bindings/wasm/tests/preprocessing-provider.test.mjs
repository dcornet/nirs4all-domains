// SPDX-License-Identifier: CECILL-2.1 OR AGPL-3.0-or-later
import assert from 'node:assert/strict';
import test from 'node:test';
import * as methods from '@nirs4all/methods';
import { createPreprocessingCallback } from '../preprocessing-provider.js';

const backendVersion = '1.3.13+abi.2.20.0';

await methods.loadModule();

function makeProvider() {
  const callback = createPreprocessingCallback(backendVersion);
  const response = (operation, request = {}) => JSON.parse(callback(operation, JSON.stringify(request)));
  const call = (operation, request) => {
    const result = response(operation, request);
    assert.equal(result.provider_error, undefined, JSON.stringify(result.provider_error));
    assert.equal(result.ok.backend_version, backendVersion);
    return result.ok;
  };
  return { response, call };
}

function close(actual, expected, tolerance = 1e-10) {
  assert.ok(Number.isFinite(actual), `expected finite ${expected}, got ${actual}`);
  assert.ok(Math.abs(actual - expected) <= tolerance * Math.max(1, Math.abs(expected)),
    `${actual} != ${expected}`);
}

function closeRows(actual, expected, tolerance = 1e-10) {
  assert.equal(actual.length, expected.length);
  for (let i = 0; i < expected.length; i++) {
    assert.equal(actual[i].length, expected[i].length);
    for (let j = 0; j < expected[i].length; j++) close(actual[i][j], expected[i][j], tolerance);
  }
}

function destroy(call) {
  assert.deepEqual(call('preprocess_destroy'), { destroyed:true, backend_version:backendVersion });
}

test('provider pins actual Methods runtime and exposes only the frozen preprocessing whitelist', () => {
  assert.equal(methods.version(), backendVersion);
  assert.deepEqual(Array.from(methods.abiVersion()), [2, 20, 0]);
  assert.throws(() => createPreprocessingCallback('invented-version'), /METHODS_VERSION_MISMATCH/);
  const { response } = makeProvider();
  assert.equal(response('preprocess_fit', {
    operator:'FlexiblePCA', parameters:{ n_components:1 }, matrix:[[1], [2]],
  }).provider_error.reason, 'UNSUPPORTED_PREPROCESSOR');
});

test('StandardScale uses the owner population variance, freezes and restores N4ME state, and preserves it after failures', () => {
  const { call, response } = makeProvider();
  const train = [[0,7], [2,7], [4,7], [6,7]];
  const fit = call('preprocess_fit', {
    operator:'StandardScale', parameters:{ with_mean:true, with_std:true }, matrix:train,
  });
  assert.ok(fit.state_bytes.length > 0 && fit.state_bytes.length <= 2 * 1024 * 1024);
  const query = [[4,7]];
  const transformed = call('preprocess_transform', { matrix:query });
  closeRows(transformed.matrix, [[1 / Math.sqrt(5), 0]]);
  assert.deepEqual(transformed.state_bytes, fit.state_bytes);

  assert.deepEqual(call('preprocess_restore', {
    operator:'StandardScale', state_bytes:fit.state_bytes,
  }).state_bytes, fit.state_bytes);
  closeRows(call('preprocess_transform', { matrix:query }).matrix, [[1 / Math.sqrt(5), 0]]);

  const failed = response('preprocess_transform', { matrix:[[1]] });
  assert.equal(failed.provider_error.methods_status, methods.Status.ERR_SHAPE_MISMATCH);
  assert.deepEqual(call('preprocess_transform', { matrix:query }).state_bytes, fit.state_bytes);

  const failedRefit = response('preprocess_fit', {
    operator:'MSC', parameters:{}, matrix:[[1,1], [2,2]],
  });
  assert.ok(failedRefit.provider_error, 'constant-reference MSC fit is refused by Methods');
  closeRows(call('preprocess_transform', { matrix:query }).matrix, [[1 / Math.sqrt(5), 0]]);
  destroy(call);
  assert.equal(response('preprocess_transform', { matrix:query }).provider_error.reason, 'PREPROCESS_STATE_NOT_FITTED');
});

test('SNV output is invariant to row offset and positive scaling', () => {
  const { call } = makeProvider();
  const base = [[1,2,4,7], [2,5,6,9]];
  const transformed = call('preprocess_fit', {
    operator:'SNV', parameters:{ with_mean:true, with_std:true, ddof:0 }, matrix:base,
  });
  const baseOutput = call('preprocess_transform', { matrix:base }).matrix;

  const shifted = base.map(row => row.map(x => 17 + 3 * x));
  call('preprocess_fit', {
    operator:'SNV', parameters:{ with_mean:true, with_std:true, ddof:0 }, matrix:shifted,
  });
  const shiftedOutput = call('preprocess_transform', { matrix:shifted }).matrix;
  closeRows(shiftedOutput, baseOutput);
  assert.ok(transformed.state_bytes.length > 0);
  destroy(call);
});

test('Detrend and Gaussian are actual Methods transforms with stable state and unchanged width', () => {
  const { call } = makeProvider();
  const X = [[0,1,4,9,16], [1,2,5,10,17]];
  for (const [operator, parameters] of [
    ['Detrend', { polyorder:1 }],
    ['Gaussian', { sigma:1, order:0, mode:'reflect', cval:0, truncate:4 }],
  ]) {
    const fit = call('preprocess_fit', { operator, parameters, matrix:X });
    const transformed = call('preprocess_transform', { matrix:X });
    assert.equal(transformed.matrix.length, 2);
    assert.ok(transformed.matrix.every(row => row.length === 5 && row.every(Number.isFinite)));
    assert.deepEqual(transformed.state_bytes, fit.state_bytes);
    call('preprocess_destroy');
  }
});

test('MSC corrects held-out affine scatter using only its fitted reference and refuses a constant reference', () => {
  const { call, response } = makeProvider();
  const train = [[1,2,4], [3,5,9], [5,8,14]];
  call('preprocess_fit', { operator:'MSC', parameters:{}, matrix:train });
  const corrected = call('preprocess_transform', { matrix:[[7,11,19]] });
  closeRows(corrected.matrix, [[3,5,9]]);
  assert.equal(response('preprocess_fit', {
    operator:'MSC', parameters:{}, matrix:[[1,1,1], [2,2,2]],
  }).provider_error.methods_status, methods.Status.ERR_NUMERICAL_FAILURE);
  closeRows(call('preprocess_transform', { matrix:[[7,11,19]] }).matrix, [[3,5,9]]);
  destroy(call);
});

test('SavitzkyGolay derivative interiors follow polynomial expectations; mirror boundaries remain owner-defined', () => {
  const { call } = makeProvider();
  const x = Array.from({ length:21 }, (_, i) => i - 10);
  const polynomial = [x.map(v => v * v)];
  const d1 = call('preprocess_fit', {
    operator:'SavitzkyGolay',
    parameters:{ window_length:11, polyorder:2, deriv:1, delta:1, mode:'mirror', cval:0 },
    matrix:polynomial,
  });
  const first = call('preprocess_transform', { matrix:polynomial }).matrix[0];
  const second = call('preprocess_fit', {
    operator:'SavitzkyGolay',
    parameters:{ window_length:11, polyorder:2, deriv:2, delta:1, mode:'mirror', cval:0 },
    matrix:polynomial,
  });
  const secondDerivative = call('preprocess_transform', { matrix:polynomial }).matrix[0];
  assert.equal(first.length, 21);
  assert.equal(secondDerivative.length, 21);
  for (let j = 5; j <= 15; j++) {
    close(first[j], 2 * x[j], 1e-10);
    close(secondDerivative[j], 2, 1e-10);
  }
  assert.ok(first.every(Number.isFinite) && secondDerivative.every(Number.isFinite));

  call('preprocess_fit', {
    operator:'SavitzkyGolay',
    parameters:{ window_length:11, polyorder:2, deriv:1, delta:1, mode:'interp', cval:0 },
    matrix:polynomial,
  });
  const interpolatedEdge = call('preprocess_transform', { matrix:polynomial }).matrix[0][0];
  assert.notEqual(first[0], interpolatedEdge, 'boundary modes must not be treated as the same oracle');
  assert.ok(d1.state_bytes.length > 0 && second.state_bytes.length > 0);
  destroy(call);
});

test('Normalize default is fitted column L2, custom range is fit on columns, and crop uses half-open indices', () => {
  const { call } = makeProvider();
  const X = [[1,2,4], [2,4,8]];
  call('preprocess_fit', { operator:'Normalize', parameters:{ feature_min:-1, feature_max:1 }, matrix:X });
  const normalized = call('preprocess_transform', { matrix:X }).matrix;
  closeRows(normalized, [[1 / Math.sqrt(5), 2 / Math.sqrt(20), 4 / Math.sqrt(80)],
    [2 / Math.sqrt(5), 4 / Math.sqrt(20), 8 / Math.sqrt(80)]]);
  closeRows(call('preprocess_transform', { matrix:[[3,6,12]] }).matrix,
    [[3 / Math.sqrt(5), 6 / Math.sqrt(20), 12 / Math.sqrt(80)]]);

  const cropInput = [[0,1,2,3,4], [10,11,12,13,14]];
  call('preprocess_fit', {
    operator:'CropTransformer', parameters:{ start:1, end:4 }, matrix:cropInput,
  });
  assert.deepEqual(call('preprocess_transform', { matrix:cropInput }).matrix, [[1,2,3], [11,12,13]]);
  destroy(call);
});

test('ARI and cluster Jaccard preserve provider undefined and unassigned-label semantics', () => {
  const { call } = makeProvider();
  assert.equal(call('adjusted_rand', {
    labels_a:[0,0,1,1], labels_b:[99,99,42,42],
  }).value, 1);
  assert.equal(call('adjusted_rand', {
    labels_a:[0,0,0], labels_b:[8,8,8],
  }).value, null);

  const overlap = call('cluster_jaccard', {
    labels_a:[0,0,1,1,-1], labels_b:[1,1,0,0,-1], n_clusters_a:2, n_clusters_b:2,
  });
  assert.deepEqual(overlap.intersections, [[0,2], [2,0]]);
  assert.deepEqual(overlap.sizes_a, [2,2]);
  assert.deepEqual(overlap.sizes_b, [2,2]);
  assert.deepEqual(overlap.jaccard, [[0,1], [1,0]]);
});

test('matrix, label and state bounds fail locally with deterministic provider errors', () => {
  const { response } = makeProvider();
  assert.equal(response('preprocess_fit', {
    operator:'SNV', parameters:{ with_mean:true, with_std:true, ddof:0 }, matrix:[[1,2], [3]],
  }).provider_error.reason, 'PREPROCESS_MATRIX_BUDGET_OR_SHAPE');
  assert.equal(response('preprocess_fit', {
    operator:'SNV', parameters:{ with_mean:true, with_std:true, ddof:0 }, matrix:[[1, null]],
  }).provider_error.reason, 'PREPROCESS_MATRIX_NONFINITE');
  assert.equal(response('preprocess_fit', {
    operator:'SNV', parameters:{ with_mean:true, with_std:true, ddof:0 }, matrix:[[1,2]], y:[99],
  }).provider_error.reason, 'PREPROCESS_Y_NOT_ALLOWED');
  assert.equal(response('adjusted_rand', { labels_a:[0,1], labels_b:[0] }).provider_error.reason,
    'PREPROCESS_LABEL_LENGTH_MISMATCH');
  const invalidState = response('preprocess_restore', {
    operator:'SNV', state_bytes:[78,52,77,69],
  }).provider_error;
  assert.ok(invalidState && (typeof invalidState.methods_status === 'number' || typeof invalidState.reason === 'string'));
  assert.equal(response('unknown', {}).provider_error.kind, 'unsupported');
});
