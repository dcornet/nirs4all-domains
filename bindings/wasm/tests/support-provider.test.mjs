// SPDX-License-Identifier: CECILL-2.1 OR AGPL-3.0-or-later
import assert from 'node:assert/strict';
import test from 'node:test';
import * as methods from '@nirs4all/methods';
import { createSupportCallback } from '../support-provider.js';

const backendVersion = '1.3.13+abi.2.20.0';
let callback;

test('support callback uses the pinned Methods backend', async () => {
  await methods.loadModule();
  assert.equal(methods.version(), backendVersion);
  assert.deepEqual(methods.abiVersion(), [2, 20, 0]);
  callback = createSupportCallback(backendVersion);
});

function response(operation, input = {}) {
  return JSON.parse(callback(operation, JSON.stringify(input)));
}
function call(operation, input) {
  const result = response(operation, input);
  assert.equal(result.provider_error, undefined, JSON.stringify(result.provider_error));
  assert.equal(result.ok.backend_version, backendVersion);
  return result.ok;
}
function close(actual, expected, tolerance = 1e-10) {
  assert.ok(Number.isFinite(actual), `expected finite value, got ${actual}`);
  assert.ok(Math.abs(actual - expected) <= tolerance * Math.max(1, Math.abs(expected)), `${actual} != ${expected}`);
}
function direction(scores) { return Math.sign(scores[1][0] - scores[0][0]); }

test('FlexiblePCA centers, projects queries, and preserves serialized live state', t => {
  t.after(() => { response('pca_destroy'); });
  const fit = call('pca_fit', { matrix:[[1],[2],[3]], n_components:1 });
  assert.ok(Array.isArray(fit.state_bytes) && fit.state_bytes.length > 0);
  const train = call('pca_transform', { matrix:[[1],[2],[3]] });
  const orientation = direction(train.scores);
  assert.ok(orientation === -1 || orientation === 1);
  assert.deepEqual(train.scores, [[-orientation],[0],[orientation]]);
  assert.deepEqual(train.state_bytes, fit.state_bytes);

  const query = call('pca_transform', { matrix:[[4],[5]] });
  assert.deepEqual(query.scores, [[2 * orientation],[3 * orientation]]);
  assert.deepEqual(query.state_bytes, fit.state_bytes);

  // A failed width check must leave the live estimator usable and unchanged.
  const failed = response('pca_transform', { matrix:[[1,2]] });
  assert.equal(failed.provider_error.methods_status, methods.Status.ERR_SHAPE_MISMATCH);
  const afterFailure = call('pca_transform', { matrix:[[4]] });
  assert.deepEqual(afterFailure.scores, [[2 * orientation]]);
  assert.deepEqual(afterFailure.state_bytes, fit.state_bytes);

  // Changing the training offset changes the fitted state, while scores remain
  // translation invariant. Component sign is allowed to follow SVD orientation.
  call('pca_destroy');
  const translated = call('pca_fit', { matrix:[[11],[12],[13]], n_components:1 });
  assert.notDeepEqual(translated.state_bytes, fit.state_bytes);
  const translatedScores = call('pca_transform', { matrix:[[11],[12],[13]] });
  const translatedOrientation = direction(translatedScores.scores);
  assert.deepEqual(translatedScores.scores, [[-translatedOrientation],[0],[translatedOrientation]]);
  assert.deepEqual(translatedScores.state_bytes, translated.state_bytes);
  assert.deepEqual(call('pca_destroy').destroyed, true);
  assert.equal(response('pca_transform', { matrix:[[1]] }).provider_error.reason, 'PCA_STATE_NOT_FITTED');
});

test('FlexiblePCA does not claim eigenvalue metadata supplied by preflightPca', t => {
  t.after(() => { response('pca_destroy'); });
  const X = { data:Float64Array.of(1,2,3), rows:3, cols:1 };
  const diagnostic = methods.preflightPca(X, 1);
  close(diagnostic.eigenvalues[0], 1);
  close(diagnostic.fullMoments[0], 1);
  assert.equal(diagnostic.unresolved[0], 0);

  call('pca_fit', { matrix:[[1],[2],[3]], n_components:1 });
  const projected = call('pca_transform', { matrix:[[1],[2],[3]] });
  assert.equal(projected.scores.length, 3);
  assert.equal(Object.hasOwn(projected, 'eigenvalues'), false);
  assert.equal(Object.hasOwn(projected, 'variance'), false);
  call('pca_destroy');
});

test('FlexiblePCA N4ME bytes restore a portable transform state', () => {
  const training = { data:Float64Array.of(1,2,3, 2,4,6, 3,6,9), rows:3, cols:3 };
  const query = { data:Float64Array.of(4,8,12), rows:1, cols:3 };
  let fitted;
  let restored;
  try {
    fitted = new methods.FlexiblePCA({ n_components:1 }).fit(training);
    const bytes = fitted.toN4me();
    restored = methods.NativeEstimator.fromN4me(bytes);
    const original = fitted.transform(query);
    const replay = restored.transform(query);
    assert.deepEqual(Array.from(replay.data), Array.from(original.data));
    assert.deepEqual(Array.from(fitted.toN4me()), Array.from(bytes));
    assert.deepEqual(Array.from(restored.toN4me()), Array.from(bytes));
  } finally {
    if (restored) restored.dispose();
    if (fitted) fitted.dispose();
  }
});
test('statsPcaMonitor returns full-fit eigenvalue and analytical T2/Q geometry', () => {
  // The reference is centered, rank one, and lies on the first coordinate
  // axis. Sample variance/eigenvalue is 28 / (6 - 1) = 5.6. A point at (2,0)
  // has T2=2^2/5.6; (0,5) has zero T2 and Q=25.
  const referenceRows = [[-3,0],[-2,0],[-1,0],[1,0],[2,0],[3,0]];
  const result = call('pca_monitor', {
    reference:referenceRows,
    monitored:[[2,0],[0,5]],
    max_components:1,
    n_folds:2,
    alpha:0.25,
  });
  assert.equal(result.effective_components, 1);
  close(result.eigenvalues[0], 5.6);
  close(result.monitored_t2[0], 4 / 5.6);
  close(result.monitored_t2[1], 0);
  close(result.monitored_q[0], 0);
  close(result.monitored_q[1], 25);
  assert.equal(result.n_beyond_q, 1);
  assert.equal(result.n_beyond_either, 1);
  close(result.reference_total_variance, 5.6);
  assert.ok(Number.isFinite(result.t2_limit));
  assert.ok(Number.isFinite(result.q_limit));
  assert.ok(Number.isFinite(result.eigenvalue_resolution));
});

test('summary callback maps the existing Methods summary tuple', () => {
  const result = call('summary', { values:[1,2,3,4] });
  assert.deepEqual(result, {
    count:4, min:1, max:4, mean:2.5,
    sample_sd:Math.sqrt(5/3), q25:1.75, median:2.5, q75:3.25,
    backend_version:backendVersion,
  });
});
