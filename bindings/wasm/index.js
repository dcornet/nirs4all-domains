// SPDX-License-Identifier: CECILL-2.1 OR AGPL-3.0-or-later
// Transport only: Domains owns protocols, Preflight owns provider contracts, Methods owns kernels.
import init, * as rust from './native/nirs4all_domains.js';
import * as methods from '@nirs4all/methods';
import { createFactorCallback } from './factor-provider.js';
import { createSupportCallback } from './support-provider.js';

const nullable = value => Number.isFinite(value) ? value : null;
function matrix(rows) {
  const n = rows.length, p = rows[0]?.length ?? 0;
  if (!n || !p || n * p > 1_000_000 || rows.some(row => row.length !== p || row.some(v => !Number.isFinite(v)))) {
    throw Object.assign(new Error('PROVIDER_MATRIX_BUDGET_OR_SHAPE'), { kind: 'internal', reason: 'PROVIDER_MATRIX_BUDGET_OR_SHAPE' });
  }
  // Marshal row order verbatim; avoid an additional n*p-element flat JS array.
  const data = new Float64Array(n * p);
  rows.forEach((row, i) => data.set(row, i * p));
  return { data, rows: n, cols: p };
}
function nested(values, width) {
  return Array.from({ length: values.length / width }, (_, i) => Array.from(values.slice(i * width, (i + 1) * width)));
}
function providerError(error) {
  // Rust reuses Preflight's exact status/domain mapping, just like the upstream WASM binding.
  if (error instanceof methods.N4mError) return { methods_status:error.status,message:error.message };
  return { kind:error?.kind ?? 'internal',reason:error?.reason ?? 'METHODS_ADAPTER_FAILED' };
}

/** One Domains WASM and one Methods WASM in a worker. Cancel by terminating the worker. */
export async function createDomainsRuntime(options = {}) {
  const lifecycle=options.onLifecycle??(()=>{});
  lifecycle('DOMAINS_RUNTIME_LOADING','domains');
  try { await init(options.wasmModule ? { module_or_path: options.wasmModule } : undefined); }
  catch(error) { throw Object.assign(error instanceof Error?error:new Error(String(error)),{code:error?.code??'DOMAINS_INITIALIZATION_FAILED',component:'domains',phase:'DOMAINS_RUNTIME_LOADING'}); }
  lifecycle('DOMAINS_RUNTIME_READY','domains');
  lifecycle('METHODS_RUNTIME_LOADING','methods');
  try { await methods.loadModule(); }
  catch(error) { throw Object.assign(error instanceof Error?error:new Error(String(error)),{code:error?.code??'METHODS_INITIALIZATION_FAILED',component:'methods',phase:'METHODS_RUNTIME_LOADING'}); }
  const abi = methods.abiVersion();
  if (abi[0] !== 2 || abi[1] < 20) throw Object.assign(new Error('METHODS_ABI_2_20_REQUIRED'),{code:'WASM_ABI_MISMATCH',component:'methods',phase:'METHODS_RUNTIME_LOADING'});
  lifecycle('METHODS_RUNTIME_READY','methods');
  const backend_version = methods.version();
  const factorCallback = createFactorCallback(backend_version);
  const supportCallback = createSupportCallback(backend_version);
  const capabilities = ['pca','summary','nearest_neighbors','hdbscan'].map(id => ({ capability_id:`methods.${id}`,available:true,qualified:false,reason:`${backend_version}; bounded browser protocol` }));
  function dispatch(operation, payload) {
    const r = JSON.parse(payload);
    switch (operation) {
      case 'capabilities': return capabilities;
      case 'pca': {
        const o = methods.preflightPca(matrix(r.matrix),r.n_components);
        return { eigenvalues:Array.from(o.eigenvalues),scores:nested(o.scores.data,o.scores.cols),full_moments:Array.from(o.fullMoments),resolution:o.resolution,unresolved:Array.from(o.unresolved,Boolean),backend_version };
      }
      case 'summary': {
        const o = methods.preflightSummary(Float64Array.from(r.values));
        return { count:o[0],min:o[1],max:o[2],mean:o[3],sample_sd:nullable(o[4]),q25:o[5],median:o[6],q75:o[7],backend_version };
      }
      case 'nearest_neighbors': {
        const o = methods.preflightNearestNeighbors(matrix(r.query),matrix(r.reference),r.k,r.query_group_ids,r.reference_group_ids);
        return { indices:nested(o.indices,o.k),distances:nested(Array.from(o.distances,nullable),o.k),backend_version };
      }
      case 'hdbscan': {
        const o = methods.clusterHdbscan(matrix(r.matrix),{ minClusterSize:r.min_cluster_size,minSamples:r.min_samples,selection:r.selection,allowSingleCluster:r.allow_single_cluster });
        return { labels:o.labels,membership:Array.from(o.membership),outlier_scores:Array.from(o.outlierScores,nullable),persistence:Array.from(o.persistence),tree:o.tree.map(node => ({parent:node.parent<0?null:node.parent,size:node.size,label:node.label<0?null:node.label,birth_distance:node.parent<0?null:1/node.lambdaBirth,death_distance:1/node.lambdaDeath,stability:nullable(node.stability)})),backend_version };
      }
      default: throw Object.assign(new Error('UNSUPPORTED_METHODS_OPERATION'),{kind:'unsupported',reason:'UNSUPPORTED_METHODS_OPERATION'});
    }
  }
  const callback = (operation,payload) => {
    try { return JSON.stringify({ok:dispatch(operation,payload)}); }
    catch(error) { return JSON.stringify({provider_error:providerError(error)}); }
  };
  return {
    analyzeSupport: input => JSON.parse(rust.analyze_support_json(JSON.stringify(input),supportCallback,backend_version)),
    analyzeSupportJson: text => rust.analyze_support_json(text,supportCallback,backend_version),
    analyzeFactor: input => JSON.parse(rust.analyze_factor_json(JSON.stringify(input),factorCallback,backend_version)),
    analyzeFactorJson: text => rust.analyze_factor_json(text,factorCallback,backend_version),
    analyzeScoped: input => JSON.parse(rust.analyze_scoped_json(JSON.stringify(input),callback)),
    analyzeScopedJson: text => rust.analyze_scoped_json(text,callback),
    analyze: input => JSON.parse(rust.analyze_json(JSON.stringify(input),callback)),
    analyzeJson: text => rust.analyze_json(text,callback),
    validate: input => JSON.parse(rust.validate_json(JSON.stringify(input))),
    interpret: (report,intent) => interpret(report,intent),
    capabilities: () => capabilities.map(c => ({...c})),
    provider: { name:'Methods',version:backend_version,abi:Array.from(abi) },
  };
}
/** Pure reading of existing evidence. Does not initialize Methods or run any fit. */
export function interpret(report,intent) {
  return JSON.parse(rust.interpret_json(JSON.stringify(report),JSON.stringify(intent)));
}
