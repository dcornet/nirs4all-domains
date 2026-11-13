// Engineering fixtures only. Requires built Domains WASM and pinned published Methods.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createDomainsRuntime } from '../index.js';
import * as rust from '../native/nirs4all_domains.js';

const bytes = await readFile(new URL('../native/nirs4all_domains_bg.wasm',import.meta.url));
const runtime = await createDomainsRuntime({wasmModule:bytes});
const analytical = {schema_version:1,dataset_id:'analytical-three-row',source_id:'x',content_sha256:'a'.repeat(64),
  observation_ids:['a','b','c'],axis:[1000],axis_unit:'nm',spectra:[[0],[1],[2]],prediction_intent:'unknown'};

test('actual Domains WASM invokes published Methods PCA and neighbors',()=>{
  assert.equal(runtime.provider.version,'1.3.13+abi.2.20.0');
  assert.equal(runtime.provider.abi[0],2);
  assert.ok(runtime.provider.abi[1]>=20);
  const report=runtime.analyze(analytical);
  assert.equal(report.metrics.pca.status,'computed');
  assert.ok(Math.abs(report.metrics.pca.value.eigenvalues[0]-1)<1e-12);
  assert.equal(report.metrics.raw_neighbors.status,'computed');
  assert.equal(report.metrics.raw_neighbors.value.n_reference,3);
  assert.equal(report.metrics.raw_neighbors.value.first_neighbor_distance_summary.value.mean,1);
  assert.equal(report.metrics.density.reason,'INSUFFICIENT_ROWS_FOR_FROZEN_DENSITY_SETTING');
  const changed=runtime.analyze({...analytical,spectra:[[0],[2],[4]]});
  assert.ok(Math.abs(changed.metrics.pca.value.eigenvalues[0]-4)<1e-12);
  assert.notEqual(changed.evidence_sha256,report.evidence_sha256);
  assert.equal(changed.raw_spectra_included,false);
  assert.equal(changed.test_target_accessed,false);
  assert.equal('spectra' in changed,false);
});

test('actual density kernel sees two compact separated synthetic populations',()=>{
  const spectra=Array.from({length:32},(_,i)=>[Math.floor(i/16)*10+(i%4)*0.05,Math.floor((i%16)/4)*0.05]);
  const report=runtime.analyze({...analytical,observation_ids:spectra.map((_,i)=>`fixture-${i}`),axis:[1100,1000],spectra});
  assert.equal(report.metrics.pca.status,'computed');
  assert.equal(report.metrics.density.status,'computed');
  assert.equal(report.metrics.density.value.n_clusters,2);
  assert.equal(report.metrics.density.value.labels.length,32);
  assert.equal(report.metrics.density.value.membership.length,32);
  assert.equal(report.metrics.density.value.persistence_summary.status,'computed');
  assert.equal(report.metrics.parameter_sensitivity.reason,'NO_PARAMETER_COMPARISON');
});

test('intent changes are pure and source mutations invalidate evidence',()=>{
  const report=runtime.analyze(analytical),before=JSON.stringify(report);
  for(const intent of ['study','known_acquisitions','new_specimens','new_groups','new_context','unknown']) {
    const reading=runtime.interpret(report,intent);
    assert.equal(reading.evidence_sha256,report.evidence_sha256);
    assert.equal(reading.prediction_intent,intent);
    assert.equal(reading.execution,'not_executed');
    assert.equal(reading.conditional_scenarios.length,intent==='unknown'?3:0);
  }
  assert.equal(JSON.stringify(report),before);
  const forged=structuredClone(report);forged.scope.n_observations=4;
  assert.throws(()=>runtime.interpret(forged,'study'),/BROWSER_EVIDENCE_HASH_MISMATCH/);
});

test('callback errors and explicit provider refusals retain null reason/value states',()=>{
  const malformed=JSON.parse(rust.analyze_json(JSON.stringify(analytical),()=>'{"garbage":true}'));
  assert.equal(malformed.metrics.pca.status,'error');
  assert.equal(malformed.metrics.pca.reason,'METHODS_CALLBACK_INVALID_RESPONSE');
  assert.equal(malformed.metrics.pca.value,null);
  const refusal=JSON.parse(rust.analyze_json(JSON.stringify(analytical),operation=>JSON.stringify(operation==='capabilities'?{ok:[]}:{provider_error:{methods_status:10,message:'unsupported fixture'}})));
  assert.equal(refusal.metrics.pca.status,'unsupported');
  assert.equal(refusal.metrics.pca.reason,'METHODS_UNSUPPORTED');
  assert.equal(refusal.metrics.pca.value,null);
});

test('Y and fabricated physical identity are refused at the parser boundary',()=>{
  assert.throws(()=>runtime.analyze({...analytical,y:[1,2,3]}),/unknown field/);
  assert.throws(()=>runtime.analyze({...analytical,identity_evidence:'verified_physical_identity'}),/unknown field/);
  assert.throws(()=>runtime.analyze({...analytical,observation_ids:['a','a','c']}),/INVALID_SCOPED_BROWSER_X_INPUT/);
});

test('live reading matches the qualified Python scientific boundaries only',async()=>{
  const oracle=JSON.parse(await readFile(new URL('../../../demo/public/examples/scientific-boundary-oracle.json',import.meta.url),'utf8'));
  assert.match(oracle.qualification,/not full Python\/Rust companion parity/);
  const report=runtime.analyze(analytical);
  for(const [intent,boundary] of Object.entries(oracle.variants)) {
    const reading=runtime.interpret(report,intent);
    assert.deepEqual(reading.boundaries,boundary.required_browser_boundaries);
    assert.equal(report.scope.identity_evidence,'observation_identity_only');
    assert.equal(report.metrics.predictive_performance.status,'unavailable');
    assert.equal(reading.readiness.status,'unavailable');
  }
});
