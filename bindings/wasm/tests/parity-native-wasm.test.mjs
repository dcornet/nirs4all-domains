// Runs the same synthetic fixtures as the native public-provider example.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile,mkdir,writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createDomainsRuntime } from '../index.js';

test('produce real WASM parity reports from the common synthetic fixtures',async()=>{
  const bytes=await readFile(new URL('../native/nirs4all_domains_bg.wasm',import.meta.url));
  const runtime=await createDomainsRuntime({wasmModule:bytes});
  assert.equal(runtime.provider.version,'1.3.13+abi.2.20.0');
  const fixtureBytes=await readFile(new URL('./parity-fixtures.json',import.meta.url));
  const fixtures=JSON.parse(fixtureBytes);
  const reports={};
  for(const fixture of fixtures.fixtures) {
    const report=runtime.analyze(fixture.input);
    assert.equal(report.metrics.pca.status,fixture.expected.pca_status,fixture.id);
    if(fixture.expected.pca_reason) assert.equal(report.metrics.pca.reason,fixture.expected.pca_reason,fixture.id);
    if(fixture.expected.n_clusters!==undefined) assert.equal(report.metrics.density.value.n_clusters,fixture.expected.n_clusters,fixture.id);
    if(fixture.expected.first_eigenvalue!==undefined) assert.ok(Math.abs(report.metrics.pca.value.eigenvalues[0]-fixture.expected.first_eigenvalue)<=1e-10,fixture.id);
    if(fixture.expected.rows_with_neighbor!==undefined) assert.equal(report.metrics.raw_neighbors.value.rows_with_neighbor,fixture.expected.rows_with_neighbor,fixture.id);
    assert.equal(report.scope.n_observations,fixture.input.spectra.length,fixture.id);
    assert.equal(report.raw_spectra_included,false);
    assert.equal(report.test_target_accessed,false);
    reports[fixture.id]=report;
  }
  const output=process.env.N4DOMAINS_WASM_PARITY_OUT ?? fileURLToPath(new URL('../../../demo/test-results/wasm-parity.json',import.meta.url));
  await mkdir(dirname(output),{recursive:true});
  await writeFile(output,JSON.stringify({schema_version:1,protocol_version:'domains.browser_parity.v1',backend:'wasm',
    fixture_file_sha256:createHash('sha256').update(fixtureBytes).digest('hex'),provider:runtime.provider,reports,new_real_scientific_fits:0})+'\n');
});
