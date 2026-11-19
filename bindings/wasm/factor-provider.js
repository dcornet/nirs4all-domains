// SPDX-License-Identifier: CECILL-2.1 OR AGPL-3.0-or-later
// Transport only. Scientific eligibility and identity checks belong to Domains Rust.
import * as methods from '@nirs4all/methods';

const nullable = value => Number.isFinite(value) ? value : null;
const invalid = () => { throw Object.assign(new Error('INVALID_FACTOR_PROVIDER_REQUEST'), { kind:'internal', reason:'INVALID_FACTOR_PROVIDER_REQUEST' }); };
function vector(value, minimum = 1) {
  if (!Array.isArray(value) || value.length < minimum || value.length > 1_000_000 || value.some(x => typeof x !== 'number' || !Number.isFinite(x))) invalid();
  return Float64Array.from(value);
}
function paired(r, categorical) {
  const scores = vector(r.scores, 2);
  if (categorical) {
    if (!Array.isArray(r.codes) || r.codes.length !== scores.length || r.codes.some(x => !Number.isSafeInteger(x))) invalid();
    return [r.codes, scores];
  }
  const values = vector(r.values, 2);
  if (values.length !== scores.length || !['pearson','spearman'].includes(r.method)) invalid();
  return [values, scores];
}
function exact(o) {
  return { n_arrangements:nullable(o.nArrangements),p_value:nullable(o.pValue),minimum_p_value:nullable(o.minimumPValue),maximum_statistic:nullable(o.maximumStatistic) };
}

/** Methods must already be loaded. Every call is synchronous in the worker. */
export function createFactorCallback(backend_version) {
  const abi = methods.abiVersion();
  if (abi[0] !== 2 || abi[1] < 24) throw new Error('METHODS_ABI_2_24_REQUIRED');
  if (backend_version !== methods.version()) throw new Error('METHODS_VERSION_MISMATCH');
  function dispatch(operation, r) {
    switch (operation) {
      case 'factor_descriptive': {
        const [codes,scores] = paired(r,true);
        const o = methods.preflightFactorAssociation(codes,scores,false,0,0);
        return { eta_squared:nullable(o.effectSize),f_statistic:nullable(o.statistic),df1:nullable(o.df1),df2:nullable(o.df2),n_levels:nullable(o.nLevels),n_score_values:nullable(o.nTargetValues),log10_distinct_arrangements:nullable(o.log10DistinctPermutations),p_value:nullable(o.pValue),n_at_least_observed:o.nAtLeastObserved,n_permutations_executed:o.nPermutationsExecuted };
      }
      case 'correlation_descriptive': {
        const [values,scores] = paired(r,false);
        const o = methods.statsCorrelationTest(values,scores,r.method,0,0);
        return { coefficient:nullable(o.coefficient),n_distinct_factor:nullable(o.nDistinctX),n_distinct_score:nullable(o.nDistinctY),log10_distinct_arrangements:nullable(o.log10DistinctPermutations),p_value:nullable(o.pValue),n_at_least_observed:o.nAtLeastObserved,n_permutations_executed:o.nPermutationsExecuted };
      }
      case 'factor_exact':
      case 'correlation_exact': {
        const factor = operation === 'factor_exact';
        const [values,scores] = paired(r,factor);
        if (!Number.isSafeInteger(r.max_arrangements) || r.max_arrangements < 1 || r.max_arrangements > 10_000_000) invalid();
        return exact(factor ? methods.statsFactorAssociationExact(values,scores,false,r.max_arrangements) : methods.statsCorrelationExact(values,scores,r.method,r.max_arrangements));
      }
      case 'holm_adjust': return { adjusted:Array.from(methods.preflightHolmAdjust(vector(r.p_values)),nullable) };
      case 'summary': {
        const o = methods.preflightSummary(vector(r.values));
        return Object.fromEntries(['count','min','max','mean','sample_sd','q25','median','q75'].map((key,i) => [key,nullable(o[i])]));
      }
      default: throw Object.assign(new Error('UNSUPPORTED_METHODS_OPERATION'), { kind:'unsupported',reason:'UNSUPPORTED_METHODS_OPERATION' });
    }
  }
  return (operation,payloadJSON) => {
    try { return JSON.stringify({ ok:{ ...dispatch(operation,JSON.parse(payloadJSON)),backend_version } }); }
    catch (error) {
      return JSON.stringify({ provider_error:error instanceof methods.N4mError ? { methods_status:error.status,message:error.message } : { kind:error?.kind ?? 'internal',reason:error?.reason ?? 'METHODS_ADAPTER_FAILED' } });
    }
  };
}
