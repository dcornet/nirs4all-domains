import test from 'node:test';
import assert from 'node:assert/strict';
import * as methods from '@nirs4all/methods';
import { createFactorCallback } from '../factor-provider.js';

await methods.loadModule();
const callback = createFactorCallback(methods.version());
const call = (op,request) => JSON.parse(callback(op,JSON.stringify(request)));
const close = (actual,expected) => assert.ok(Math.abs(actual-expected) <= 1e-10, `${actual} != ${expected}`);

test('factor callback binds the actual published owner version and ABI', () => {
  assert.equal(methods.version(),'1.5.1+abi.2.24.0');
  assert.deepEqual(Array.from(methods.abiVersion()),[2,24,0]);
  assert.throws(() => createFactorCallback('invented-version'),/METHODS_VERSION_MISMATCH/);
});

test('published Methods descriptive transport preserves B=0, undefined p and counts', () => {
  const r = call('factor_descriptive',{ codes:[0,0,0,1,1,1],scores:[1,2,3,7,8,9] }).ok;
  close(r.eta_squared,27/29);
  close(r.f_statistic,54);
  assert.equal(r.p_value,null);
  assert.equal(r.n_permutations_executed,0);
  assert.equal(r.backend_version,methods.version());
  for (const method of ['pearson','spearman']) {
    const c = call('correlation_descriptive',{ values:[1,2,3,4],scores:[-1,-2,-3,-4],method }).ok;
    close(c.coefficient,-1);
    assert.equal(c.n_distinct_factor,4);
    assert.equal(c.p_value,null);
    assert.equal(c.n_permutations_executed,0);
  }
});

test('published Methods exact, Holm and summary outputs are marshalled', () => {
  const f = call('factor_exact',{ codes:[0,0,1,1],scores:[1,2,3,4],max_arrangements:24 }).ok;
  assert.equal(f.n_arrangements,6);
  close(f.p_value,1/3);
  const c = call('correlation_exact',{ values:[1,2,3,4],scores:[1,2,3,4],method:'pearson',max_arrangements:24 }).ok;
  assert.equal(c.n_arrangements,24);
  close(c.p_value,1/12);
  assert.deepEqual(call('holm_adjust',{ p_values:[.01,.04,.03,.005] }).ok.adjusted,[.03,.06,.06,.02]);
  const s = call('summary',{ values:[1,2,3,4] }).ok;
  assert.equal(s.count,4);
  assert.equal(s.min,1);
  assert.equal(s.max,4);
  assert.equal(s.mean,2.5);
});

test('undefined slots and owner refusal retain distinct transport outcomes', () => {
  const constant = call('correlation_descriptive',{ values:[1,1,1],scores:[1,2,3],method:'pearson' }).ok;
  assert.equal(constant.coefficient,null);
  const saturated = call('factor_descriptive',{ codes:[0,1,2],scores:[1,2,3] }).ok;
  close(saturated.eta_squared,1);
  assert.equal(saturated.f_statistic,null);
  const refusal = call('correlation_descriptive',{ values:[1,1e40],scores:[1,2],method:'pearson' }).provider_error;
  assert.equal(typeof refusal.methods_status,'number');
  assert.equal(typeof refusal.message,'string');
  assert.equal(call('factor_descriptive',{ codes:[0],scores:[1,2] }).provider_error.reason,'INVALID_FACTOR_PROVIDER_REQUEST');
  assert.equal(call('unknown',{}).provider_error.kind,'unsupported');
  assert.equal(JSON.parse(callback('summary','bad json')).provider_error.kind,'internal');
});
