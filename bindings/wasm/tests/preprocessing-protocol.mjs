// SPDX-License-Identifier: CECILL-2.1 OR AGPL-3.0-or-later
// Deterministic synthetic F4.3 qualification through the compiled Domains WASM.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import { createDomainsRuntime } from '../index.js';
import * as rust from '../native/nirs4all_domains.js';

const BACKEND = '1.3.13+abi.2.20.0';
const MAX_ROWS = 2_000;
const MAX_CELLS = 1_000_000;
const sha = value => createHash('sha256').update(value).digest('hex');
const clone = value => structuredClone(value);
const hashPattern = /^[0-9a-f]{64}$/;

const fixtureBytes = await readFile(new URL('./preprocessing-fixtures.json', import.meta.url));
const fixtures = JSON.parse(fixtureBytes);
const bankBytes = await readFile(new URL('../aom-bank.json', import.meta.url));
const bank = JSON.parse(bankBytes);
assert.ok(fixtures.length >= 40, 'prospective fixture bank must contain at least 40 cases');
assert.equal(new Set(fixtures.map(x => x.id)).size, fixtures.length, 'fixture IDs must be unique');
assert.equal(bank.bank_id, 'aom_methods_balanced_v1');
assert.equal(bank.default_representations[0].id, 'raw');

const planBase = {
  bank_id:bank.bank_id,
  kind:'prospective',
  parent_plan_sha256:null,
  representations:clone(bank.default_representations),
  structure:true,
  compare_neighbors:true,
  compare_clusters:true,
  correlation_method:'pearson',
  support:{ n_components:2, max_components:2, n_folds:5, alpha:0.05, monitoring:true },
};

const EXPECTED_REFUSALS = {
  unauthorized_y:'X_ONLY_EXPLICIT_ACCESS_REQUIRED',
  fit_on_test:'COMPLETE_ORDERED_ROLE_POPULATION_REQUIRED',
  raw_row_order:'INVALID_ORDERED_COMPLETE_X_PAYLOAD',
  duplicate_key:'INVALID_OR_OVER_BUDGET_MANIFEST',
  mixed_population:'MIXED_ASSIGNED_UNPARTITIONED_POPULATION',
  manifest_2001:'INVALID_OR_OVER_BUDGET_MANIFEST',
  matrix_over_1m_cells:'FULL_POPULATION_BROWSER_BUDGET_EXCEEDED',
  nonmonotone_axis:'INVALID_ORDERED_COMPLETE_X_PAYLOAD',
  test_without_query:'COMPLETE_ORDERED_ROLE_POPULATION_REQUIRED',
  missing_frozen_reference:'FROZEN_REFERENCE_REQUIRED',
  frozen_source_fingerprint:'FROZEN_REFERENCE_BINDING_OR_EVIDENCE_MISMATCH',
  frozen_plan_fingerprint:'FROZEN_REFERENCE_BINDING_OR_EVIDENCE_MISMATCH',
  frozen_matrix_fingerprint:'FROZEN_REFERENCE_BINDING_OR_EVIDENCE_MISMATCH',
  frozen_factor:'FROZEN_REFERENCE_BINDING_OR_EVIDENCE_MISMATCH',
  frozen_evidence_hash:'FROZEN_REFERENCE_BINDING_OR_EVIDENCE_MISMATCH',
  unpartitioned_query:'TEST_AUDIT_REQUIRES_TRAIN_POPULATION',
  predict_key_in_reference:'COMPLETE_ORDERED_ROLE_POPULATION_REQUIRED',
  axis_width_mismatch:'INVALID_ORDERED_COMPLETE_X_PAYLOAD',
  missing_x_value:'INVALID_ORDERED_COMPLETE_X_PAYLOAD',
  nonfinite_json_number:'INVALID_PREPROCESSING_SENSITIVITY_INPUT',
};

const nTrain = 24, nTest = 4, nPredict = 1, nFeatures = 25;
const trainKeys = scenario => Array.from({ length:nTrain }, (_, i) => `${scenario}-train-${i}`);
const testKeys = scenario => Array.from({ length:nTest }, (_, i) => `${scenario}-test-${i}`);
const predictKeys = scenario => Array.from({ length:nPredict }, (_, i) => `${scenario}-predict-${i}`);

function axisFor(desc) {
  const axis = Array.from({ length:nFeatures }, (_, j) => 900 + 2 * j);
  if (desc.axis === 'irregular_monotone') return axis.map((x, j) => x + 0.03 * j * j);
  if (desc.axis === 'decreasing') return axis.map((_, j) => 1_000 - 2 * j);
  return axis;
}

function factorLevels(scenario, originalIndex) {
  if (scenario === 'confounded') {
    const same = originalIndex < 12 ? 0 : 1;
    return { instrument:same, lot:same, temperature:18 + 3 * same };
  }
  const instrument = originalIndex % 2;
  const lot = Math.floor(originalIndex / 3) % 4;
  let temperature = 18 + ((originalIndex * 5) % 9);
  if (scenario === 'independent_factor') temperature = 18 + ((originalIndex * 7 + 3) % 11);
  return { instrument, lot, temperature };
}

function spectrum(desc, originalIndex, role) {
  const i = desc.scenario === 'repeated_acquisition' ? originalIndex % 6 : originalIndex;
  const levels = factorLevels(desc.scenario, originalIndex);
  const out = Array.from({ length:nFeatures }, (_, j) => {
    const t = j - 12;
    let value = 8 + 0.04 * j + 0.0007 * t * t + 0.4 * Math.sin(0.24 * j) +
      0.15 * Math.cos(0.11 * j + 0.08 * i) + 0.025 * (i - 11.5) * t;
    if (desc.scenario === 'offset') value += 2 + (originalIndex % 4) * 1.5;
    if (desc.scenario === 'positive_multiplier') value *= 0.8 + 0.1 * (originalIndex % 5);
    if (desc.scenario === 'slope') value += (originalIndex % 5 - 2) * 0.025 * j;
    if (desc.scenario === 'low_frequency') value += 0.5 * Math.sin(0.09 * j + 0.2 * originalIndex);
    if (desc.scenario === 'high_frequency') value += 0.15 * Math.sin(1.65 * j + 0.61 * originalIndex);
    if (desc.scenario === 'local_peak') value += 1.3 * Math.exp(-((j - 13) ** 2) / 2);
    if (desc.scenario === 'smooth_drift') value += 0.0012 * t * t + 0.01 * t;
    if (desc.scenario === 'instrument_shift') value += levels.instrument * (0.5 + 0.01 * j);
    if (desc.scenario === 'lot_shift') value += levels.lot * (0.25 + 0.006 * j);
    if (desc.scenario === 'confounded') value += levels.instrument * (0.5 + 0.01 * j);
    if (desc.scenario === 'independent_factor') value += 0.002 * levels.temperature * Math.sin(j * 0.18);
    if (desc.scenario === 'repeated_acquisition') value += 0.0001 * (originalIndex % 4) * Math.sin(j * 0.3);
    if (desc.scenario === 'independent_replicate') value += 0.0005 * Math.sin(originalIndex * 1.3 + j * 0.7);
    if (desc.scenario === 'dispersed') value += 4 * Math.sin(originalIndex * 13 + j * 7.1);
    if (desc.scenario === 'constant_band' && j === 12) value = 7;
    if (desc.scenario === 'constant_matrix') value = 5;
    if (desc.scenario === 'principal_query' && role === 'test') value += 2.5 * t / 12;
    if (desc.scenario === 'residual_query' && role === 'test') value += 0.6 * Math.sin(j * 1.9 + originalIndex);
    if (desc.scenario === 'batch_query' && role === 'test') value += 8;
    if (desc.scenario === 'extreme_high') value *= 1e70;
    if (desc.scenario === 'extreme_low') value *= 1e-70;
    if (desc.scenario === 'domain_boundary') value *= 1e30;
    return value;
  });
  return out;
}

function sourceRows(desc) {
  const trainOrder = Array.from({ length:nTrain }, (_, i) => i);
  if (desc.scenario === 'row_permutation') trainOrder.reverse();
  const rows = trainOrder.map((original, position) => ({
    key:`${desc.scenario}-train-${position}`, partition:desc.population === 'unpartitioned' ? 'unpartitioned' : 'train',
    original, role:'reference',
  }));
  if (desc.population !== 'unpartitioned') {
    for (let i = 0; i < nTest; i++) rows.push({ key:`${desc.scenario}-test-${i}`, partition:'test', original:nTrain + i, role:'test' });
    for (let i = 0; i < nPredict; i++) rows.push({ key:`${desc.scenario}-predict-${i}`, partition:'predict', original:nTrain + nTest + i, role:'predict' });
  }
  return rows;
}

function buildPlan(desc) {
  const plan = clone(planBase);
  if (desc.panel === 'crop') plan.representations.push(clone(bank.entries.find(x => x.spec.id === 'crop_1_10').spec));
  if (desc.panel === 'quadratic_detrend') plan.representations.push(clone(bank.entries.find(x => x.spec.id === 'detrend_2').spec));
  if (desc.panel === 'invalid_sg') {
    const spec = plan.representations.find(x => x.id === 'sg_d1_11_2');
    spec.steps[0].parameters.window_length = 10;
  }
  return plan;
}

function buildRequest(desc, frozenReference = null) {
  const rows = sourceRows(desc);
  const allMatrix = rows.map(row => spectrum(desc, row.original, row.role));
  const axis = axisFor(desc);
  const manifest = rows.map(({ key, partition }) => ({ key, partition }));
  const referenceRows = rows.filter(x => x.role === 'reference');
  const queryRows = desc.stage === 'test_audit' ? rows.filter(x => x.role === 'test') : [];
  const selectedRows = [...referenceRows, ...queryRows];
  const referenceKeys = referenceRows.map(x => x.key);
  const queryKeys = queryRows.map(x => x.key);
  const allContent = { manifest, axis, axis_unit:'nm', matrix:allMatrix };
  const dataset = {
    dataset_id:`f43-synthetic-${desc.scenario}`,
    source_id:`deterministic-generator-${desc.scenario}`,
    content_version:'f4.3-synthetic-fixtures-v1',
    content_sha256:sha(JSON.stringify(allContent)),
  };
  const factorColumn = (name, role, kind, unit, values, selected) => ({
    name, role, kind, unit, origin:'synthetic-declared', derived_from_target:false,
    evidence:'declared', row_keys:selected.map(row => row.key), values:selected.map(row => values(row.original)),
  });
  const factors = [
    factorColumn('instrument', 'instrument', 'categorical', null,
      i => `instrument-${factorLevels(desc.scenario, i).instrument}`, referenceRows),
    factorColumn('temperature', 'factor', 'continuous', 'degC',
      i => factorLevels(desc.scenario, i).temperature, referenceRows),
  ];
  const dependencies = [
    factorColumn('acquisition_group', 'group', 'categorical', null,
      i => `group-${Math.floor(i / 4)}`, selectedRows),
    factorColumn('repetition', 'repetition', 'categorical', null,
      i => `rep-${i % 3}`, selectedRows),
  ];
  const request = {
    schema_version:1,
    protocol_version:'domains.browser_preprocessing_sensitivity.v1',
    dataset,
    manifest,
    population:desc.population ?? 'train',
    reference_keys:referenceKeys,
    query_keys:queryKeys,
    x:{
      row_keys:selectedRows.map(row => row.key),
      matrix:selectedRows.map(row => allMatrix[rows.indexOf(row)]),
      axis,
      axis_unit:'nm',
    },
    factors,
    dependencies,
    exclusion_field:'acquisition_group',
    access:{x:true,m_fields:['instrument','temperature','acquisition_group','repetition'],y_fields:[]},
    plan:buildPlan(desc),
    stage:desc.stage,
    frozen_reference:frozenReference ? clone(frozenReference) : null,
    reuse_exact_prefixes:desc.reuse_exact_prefixes,
  };
  applyMutation(desc, request, rows, allMatrix);
  return request;
}

function oversizedCellRequest(desc) {
  const n = MAX_ROWS, p = 501;
  const referenceKeys = Array.from({ length:n }, (_, i) => `large-train-${i}`);
  const axis = Array.from({ length:p }, (_, j) => 900 + 2 * j);
  return {
    schema_version:1,
    protocol_version:'domains.browser_preprocessing_sensitivity.v1',
    dataset:{dataset_id:'f43-oversized-cells',source_id:'synthetic-generator',content_version:'f4.3-v1',content_sha256:'a'.repeat(64)},
    manifest:referenceKeys.map(key => ({key,partition:'train'})),
    population:'train',reference_keys:referenceKeys,query_keys:[],
    x:{row_keys:referenceKeys,matrix:Array.from({length:n},()=>Array(p).fill(0)),axis,axis_unit:'nm'},
    factors:[],dependencies:[],exclusion_field:null,access:{x:true,m_fields:[],y_fields:[]},
    plan:buildPlan(desc),stage:'reference_only',frozen_reference:null,reuse_exact_prefixes:true,
  };
}

function applyMutation(desc, request, rows, allMatrix) {
  switch (desc.mutation) {
    case undefined: return;
    case 'unauthorized_y': request.access.y_fields = ['target']; return;
    case 'fit_on_test': request.reference_keys[0] = rows.find(x => x.partition === 'test').key; return;
    case 'raw_row_order': [request.x.row_keys[0], request.x.row_keys[1]] = [request.x.row_keys[1], request.x.row_keys[0]]; return;
    case 'duplicate_key': request.manifest[1].key = request.manifest[0].key; return;
    case 'mixed_population': request.manifest[0].partition = 'unpartitioned'; return;
    case 'manifest_2001':
      for (let i = request.manifest.length; i < 2001; i++) request.manifest.push({key:`extra-${i}`,partition:'train'});
      return;
    case 'matrix_over_1m_cells': return;
    case 'nonmonotone_axis': request.x.axis[12] = request.x.axis[11] - 1; return;
    case 'test_without_query': request.stage = 'test_audit'; request.query_keys = []; request.x.row_keys = request.reference_keys.slice(); request.x.matrix = request.x.matrix.slice(0, request.reference_keys.length); return;
    case 'missing_frozen_reference': request.frozen_reference = null; return;
    case 'frozen_source_fingerprint': request.dataset.content_sha256 = '0'.repeat(64); return;
    case 'frozen_plan_fingerprint': request.plan.support.alpha = 0.1; return;
    case 'frozen_matrix_fingerprint': request.x.matrix[0][0] += 0.125; return;
    case 'frozen_factor': request.factors.find(x => x.name === 'temperature').values[0] += 0.25; return;
    case 'frozen_evidence_hash': request.frozen_reference.evidence_sha256 = '0'.repeat(64); return;
    case 'unpartitioned_query': request.stage = 'test_audit'; request.population = 'unpartitioned'; request.query_keys = []; request.frozen_reference = null; return;
    case 'predict_key_in_reference': {
      const predict = rows.find(x => x.role === 'predict');
      request.reference_keys.push(predict.key);
      request.x.row_keys.push(predict.key);
      request.x.matrix.push(allMatrix[rows.indexOf(predict)]);
      return;
    }
    case 'axis_width_mismatch': request.x.axis.pop(); return;
    case 'missing_x_value': request.x.matrix[0][0] = null; return;
    case 'nonfinite_json_number': request.x.matrix[0][0] = 987654321.123; return;
    default: throw new Error(`unknown fixture mutation ${desc.mutation}`);
  }
}

function findReason(errorOrResult) {
  if (typeof errorOrResult === 'string') {
    const match = errorOrResult.match(/[A-Z][A-Z0-9_]{5,}/g);
    return match?.at(-1) ?? errorOrResult;
  }
  if (errorOrResult && typeof errorOrResult.reason === 'string') return errorOrResult.reason;
  return 'REFUSAL_REASON_NOT_RETURNED';
}

function finite(value, path = 'result') {
  if (typeof value === 'number') assert.ok(Number.isFinite(value), `${path} contains non-finite number`);
  else if (Array.isArray(value)) value.forEach((x, i) => finite(x, `${path}[${i}]`));
  else if (value && typeof value === 'object') {
    for (const [key, child] of Object.entries(value)) finite(child, `${path}.${key}`);
  }
}

function noRawProviderState(value, path = 'result') {
  if (Array.isArray(value)) return value.forEach((x, i) => noRawProviderState(x, `${path}[${i}]`));
  if (!value || typeof value !== 'object') return;
  for (const [key, child] of Object.entries(value)) {
    if (key === 'y' && path.endsWith('.fields_read')) {
      assert.deepEqual(child, [], `${path}.y must remain an empty access receipt`);
      continue;
    }
    if (key === 'matrix' && (path.endsWith('.fields_read.x') || path.endsWith('.matrices'))) {
      assert.deepEqual(Object.keys(child).sort(), ['sha256','shape']);
      assert.match(child.sha256, hashPattern);
      assert.ok(Array.isArray(child.shape) && child.shape.length === 2 && child.shape.every(x => Number.isSafeInteger(x) && x >= 0));
      continue;
    }
    if (path.endsWith('.shapes') && ['matrix','state_bytes'].includes(key)) {
      assert.ok(Array.isArray(child) && child.length === 2 && child.every(x => Number.isSafeInteger(x) && x >= 0),
        `${path}.${key} must contain only a dimension tuple`);
      continue;
    }
    assert.ok(!['state_bytes','n4me_bytes','raw_state','training_rows','matrix','raw_X','raw_y','spectra','Y','y'].includes(key),
      `${path}.${key} must not be exported`);
    noRawProviderState(child, `${path}.${key}`);
  }
}

function providerCalls(result) {
  const calls = result?.receipt?.provider_calls;
  return Array.isArray(calls) ? calls : [];
}

function stableNumericResult(result) {
  const omit = new Set(['receipt','evidence_sha256','input_sha256','reference_input_sha256','plan_sha256',
    'reference_matrix_sha256','query_matrix_sha256','original_axis_sha256','state_sha256',
    'input_axis_sha256','output_axis_sha256','payload_sha256','request_sha256','reference_raw_sha256',
    'query_raw_sha256','exact_prefix_cache_hits','reuse_exact_prefixes','reuse_exact_prefixes_enabled']);
  const visit = value => {
    if (Array.isArray(value)) return value.map(visit);
    if (!value || typeof value !== 'object') return value;
    return Object.fromEntries(Object.entries(value).filter(([key]) => !omit.has(key)).map(([key, child]) => [key, visit(child)]));
  };
  return visit(result);
}

async function validateSchemas(requests, results) {
  const paths = ['report.schema.json','scoped-input.schema.json','scoped-result.schema.json',
    'factor-input.schema.json','factor-result.schema.json','support-input.schema.json','support-result.schema.json',
    'preprocessing-input.schema.json','preprocessing-result.schema.json'];
  const schemas = [];
  for (const name of paths) {
    try { schemas.push({ name, value:JSON.parse(await readFile(new URL(`../${name}`, import.meta.url), 'utf8')) }); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  if (!schemas.length) return { available:false, reason:'PREPROCESSING_SCHEMAS_NOT_PRESENT' };
  const { default:Ajv2020 } = await import('../../../demo/node_modules/ajv/dist/2020.js');
  const ajv = new Ajv2020({ strict:true, strictTypes:false, allErrors:true });
  function legacyDeclarations(value) {
    if (!value || typeof value !== 'object') return;
    if (Array.isArray(value)) { value.forEach(legacyDeclarations); return; }
    for (const key of value.required ?? []) {
      if (value.properties?.[key]) continue;
      assert.notEqual(value.additionalProperties, false, 'Never relax a closed legacy contract');
      (value.properties ??= {})[key] = {}; // Already-permitted required field; validation is unchanged.
    }
    Object.values(value).forEach(legacyDeclarations);
  }
  for (const {value} of schemas) {
    if (!value.$id.startsWith('domains.browser_preprocessing_')) legacyDeclarations(value);
    ajv.addSchema(value);
  }
  const validators = new Map(schemas.map(({name,value}) => [name,ajv.getSchema(value.$id)]));
  const inputValidator = validators.get('preprocessing-input.schema.json');
  const resultValidator = validators.get('preprocessing-result.schema.json');
  const checkedInputs = inputValidator ? requests.filter(x => !x.refused).map(x => x.request) : [];
  const checkedResults = resultValidator ? results.map(x => x.result) : [];
  for (const request of checkedInputs) assert.ok(inputValidator(request), JSON.stringify(inputValidator.errors));
  for (const result of checkedResults) assert.ok(resultValidator(result), JSON.stringify(resultValidator.errors));
  return {
    available:true,
    schemas:schemas.map(x => x.name),
    valid_inputs:checkedInputs.length,
    valid_results:checkedResults.length,
  };
}

async function run(output) {
  const wasm = await readFile(new URL('../native/nirs4all_domains_bg.wasm', import.meta.url));
  const runtime = await createDomainsRuntime({ wasmModule:wasm });
  assert.equal(runtime.provider.version, BACKEND);
  assert.deepEqual(runtime.provider.abi.slice(0, 2), [2, 20]);
  assert.equal(typeof runtime.analyzeSensitivity, 'function', 'F4.3 Domains WASM must expose analyzeSensitivity');
  const resultById = new Map();
  const cases = [], refusals = [], schemaRows = [];

  for (const fixture of fixtures) {
    const frozen = fixture.reference_case_id ? resultById.get(fixture.reference_case_id) : null;
    if (fixture.reference_case_id) assert.ok(frozen, `${fixture.id} requires prior actual reference ${fixture.reference_case_id}`);
    let request = buildRequest(fixture, frozen ?? null);
    if (fixture.mutation === 'matrix_over_1m_cells') request = oversizedCellRequest(fixture);
    let raw = JSON.stringify(request);
    if (fixture.mutation === 'nonfinite_json_number') raw = raw.replace('987654321.123', 'NaN');
    schemaRows.push({ id:fixture.id, request, refused:!!fixture.expect_refusal });

    if (fixture.expect_refusal) {
      let calls = 0;
      const spy = () => {
        calls++;
        return JSON.stringify({ provider_error:{ kind:'internal', reason:'UNEXPECTED_PROVIDER_CALL' } });
      };
      let result, thrown = null;
      try {
        const rawResult = rust.analyze_preprocessing_json(raw, spy, runtime.provider.version);
        result = typeof rawResult === 'string' ? JSON.parse(rawResult) : rawResult;
      } catch (error) { thrown = String(error); }
      assert.equal(calls, 0, `${fixture.id} must refuse before any Methods provider call`);
      const reason = findReason(thrown ?? result);
      const expected = EXPECTED_REFUSALS[fixture.mutation];
      if (expected) assert.ok(String(thrown ?? reason).includes(expected), `${fixture.id}: expected ${expected}, got ${thrown ?? reason}`);
      refusals.push({ id:fixture.id, ...(fixture.mutation === 'nonfinite_json_number' ? { request_json:raw } : { request }), reason, thrown, provider_calls:calls });
      continue;
    }

    const resultJson = runtime.analyzeSensitivityJson(JSON.stringify(request));
    const result = JSON.parse(resultJson);
    finite(result, fixture.id);
    noRawProviderState(result, fixture.id);
    assert.equal(result.protocol_version, 'domains.browser_preprocessing_sensitivity_result.v1', fixture.id);
    assert.equal(result.status, 'computed', fixture.id);
    assert.equal(result.stage, fixture.stage, fixture.id);
    assert.deepEqual(result.receipt.reference_keys, request.reference_keys, `${fixture.id} reference keys`);
    assert.deepEqual(result.receipt.query_keys, request.query_keys, `${fixture.id} query keys`);
    assert.equal(result.receipt.test_x_accessed, fixture.stage === 'test_audit', fixture.id);
    assert.equal(result.receipt.y_accessed, false, fixture.id);
    assert.equal(result.receipt.x_predict_accessed, false, fixture.id);
    assert.match(result.evidence_sha256, hashPattern, `${fixture.id} evidence hash`);
    assert.equal(result.receipt.provider, runtime.provider.version);
    const calls = providerCalls(result);
    assert.ok(calls.length > 0, `${fixture.id} should record actual Methods owner calls`);
    assert.ok(calls.every(call => typeof call.provider_success === 'boolean' && typeof call.operation === 'string'),
      `${fixture.id} provider receipts must retain each call status`);
    assert.ok(calls.some(call => call.operation === 'preprocess_destroy'), `${fixture.id} must record cleanup`);
    assert.ok(calls.filter(call => call.operation === 'preprocess_fit').every(call =>
      JSON.stringify(call.row_keys) === JSON.stringify(request.reference_keys)), `${fixture.id} fitted outside reference keys`);

    const rawRep = result.representations.find(rep => rep.id === 'raw');
    if (rawRep?.status === 'computed') {
      assert.deepEqual(rawRep.value.axis, request.x.axis, `${fixture.id} raw axis/order`);
      assert.equal(rawRep.value.reference_matrix_sha256.length, 64);
    }
    for (const rep of result.representations) {
      if (rep.status !== 'computed') continue;
      assert.equal(rep.value.transformations.every(step => step.state_unchanged_after_transform === true), true, `${fixture.id}/${rep.id} fitted-state immutability`);
      if (!rep.steps.some(step => step.operator === 'CropTransformer')) {
        assert.deepEqual(rep.value.axis, request.x.axis, `${fixture.id}/${rep.id} shape-preserving axis`);
      }
      for (const step of rep.value.transformations) assert.match(step.state_sha256, hashPattern);
    }
    if (fixture.panel === 'crop') {
      const crop = result.representations.find(rep => rep.id === 'crop_1_10');
      if (crop?.status === 'computed') assert.deepEqual(crop.value.axis, request.x.axis.slice(1, 10));
    }
    if (fixture.panel === 'invalid_sg') {
      assert.equal(rawRep?.status, 'computed', `${fixture.id} raw result remains available`);
      const invalid = result.representations.find(rep => rep.id === 'sg_d1_11_2');
      assert.equal(invalid?.status, 'unavailable', `${fixture.id} invalid SG fails locally`);
      assert.ok(invalid.reason);
    }
    if (fixture.stage === 'reference_only') {
      assert.equal(result.receipt.test_x_accessed, false);
      assert.deepEqual(result.receipt.query_keys, []);
    } else {
      assert.ok(calls.some(call => call.operation === 'preprocess_restore'), `${fixture.id} test uses restored reference state`);
      assert.ok(calls.every(call => call.operation !== 'preprocess_fit' ||
        JSON.stringify(call.row_keys) === JSON.stringify(request.reference_keys)), `${fixture.id} test rows were not fit`);
      assert.equal(result.receipt.frozen_reference_sha256, frozen.evidence_sha256);
    }

    const row = { id:fixture.id, request, result, result_json:resultJson,
      result_json_sha256:sha(resultJson), ...(fixture.reference_case_id ? { reference_case_id:fixture.reference_case_id } : {}) };
    cases.push(row);
    if (fixture.stage === 'reference_only') resultById.set(fixture.id, result);
  }

  const cacheOn = cases.find(x => x.id === 'cache-enabled-reference');
  const cacheOff = cases.find(x => x.id === 'cache-disabled-reference');
  assert.ok(cacheOn && cacheOff);
  assert.deepEqual(stableNumericResult(cacheOn.result), stableNumericResult(cacheOff.result),
    'cached and uncached computations must preserve the same numerical result');

  const schemaValidation = await validateSchemas(schemaRows, cases);
  const artifact = {
    protocol_version:'domains.browser_preprocessing_sensitivity_wasm.v1',
    provider:runtime.provider,
    fixture_sha256:sha(fixtureBytes),
    descriptor_bank_sha256:sha(bankBytes),
    tolerance:{ absolute:1e-10, relative:1e-10 },
    schema_validation:schemaValidation,
    cases,
    refusals,
    new_real_scientific_fits:0,
  };
  await mkdir(dirname(output), { recursive:true });
  await writeFile(output, JSON.stringify(artifact) + '\n');
  console.log(`Preprocessing WASM: ${cases.length} computed requests; ${refusals.length} pre-provider refusals`);
}

async function benchmark(output) {
  const started=performance.now();
  const wasm=await readFile(new URL('../native/nirs4all_domains_bg.wasm',import.meta.url));
  const runtime=await createDomainsRuntime({wasmModule:wasm});
  assert.equal(runtime.provider.version,BACKEND);
  const initialization_ms=performance.now()-started;
  const enabled=buildRequest(fixtures.find(f=>f.id==='cache-enabled-reference'),null);
  const disabled=buildRequest(fixtures.find(f=>f.id==='cache-disabled-reference'),null);
  const samples=[];
  for(let pair=-1;pair<3;pair++){
    let on,off;
    for(const reuse of pair%2===0?[true,false]:[false,true]){
      const request=reuse?enabled:disabled,start=performance.now();
      const result=runtime.analyzeSensitivity(request),duration_ms=performance.now()-start;
      assert.equal(result.status,'computed');
      const calls=result.receipt.provider_calls;
      const row={pair,reuse_exact_prefixes:reuse,duration_ms,provider_calls:calls.length,preprocess_fits:calls.filter(c=>c.operation==='preprocess_fit').length,cache_hits:result.receipt.exact_prefix_cache_hits,rss_after_bytes:process.memoryUsage().rss};
      if(pair>=0)samples.push(row);
      if(reuse)on=result;else off=result;
    }
    assert.deepEqual(on.representations,off.representations,'Fixed-panel evidence must remain exactly equal with/without prefix reuse');
    assert(on.receipt.provider_calls.length<off.receipt.provider_calls.length,'Actual owner call reduction required');
  }
  const receipt={protocol_version:'domains.preprocessing_benchmark.v1',provider:runtime.provider,fixture_sha256:sha(fixtureBytes),descriptor_bank_sha256:sha(bankBytes),plan:enabled.plan,population:{rows:enabled.reference_keys.length,bands:enabled.x.axis.length},initialization_ms,warmup_pairs:1,measured_pairs:3,samples,resource_usage:process.resourceUsage(),memory_after:process.memoryUsage(),memory_scope:'OS process resourceUsage and post-call Node RSS; no strict allocation containment or browser peak inference.',comparison_scope:'Same runtime, fixed complete synthetic panel, alternating order, end-to-end analyzeSensitivity including serialization; no real-data or general speed guarantee.',numerical_evidence_exactly_equal:true,new_real_scientific_fits:0};
  await mkdir(dirname(output),{recursive:true});
  await writeFile(output,JSON.stringify(receipt,null,2)+'\n');
  console.log('Preprocessing benchmark: 3 measured cache-on/off pairs, exact representation evidence preserved');
}
const [mode, output] = process.argv.slice(2);
if (!['wasm','benchmark'].includes(mode) || !output) throw new Error('Usage: node tests/preprocessing-protocol.mjs wasm|benchmark OUT');
await (mode==='benchmark'?benchmark(output):run(output));
