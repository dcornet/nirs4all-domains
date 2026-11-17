// Public synthetic execution only. Native replay uses exactly these recorded WASM PCA scores.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {dirname} from 'node:path';
import {createDomainsRuntime} from '../index.js';
import * as rust from '../native/nirs4all_domains.js';
import Ajv2020 from '../../../demo/node_modules/ajv/dist/2020.js';

const ajv=new Ajv2020({strict:true,allErrors:true});
const validateInput=ajv.compile(JSON.parse(await readFile(new URL('../factor-input.schema.json',import.meta.url))));
const validateResult=ajv.compile(JSON.parse(await readFile(new URL('../factor-result.schema.json',import.meta.url))));

const sha = value => createHash('sha256').update(value).digest('hex');
const close = (actual,expected,label) => {
  assert.equal(typeof actual,'number',label);
  assert.ok(Number.isFinite(actual) && Math.abs(actual-expected) <= 1e-10 + 1e-10*Math.abs(expected),`${label}: ${actual} != ${expected}`);
};
const fixtureBytes = await readFile(new URL('./factor-fixtures.json',import.meta.url));
const fixtures = JSON.parse(fixtureBytes);
assert.equal(fixtures.protocol_version,'domains.browser_factor_association_fixtures.v1');
const component = r => r.value.factors[0].components[0];
const compact = report => Object.fromEntries(['schema_version','protocol_version','status','scope','metrics','input_sha256','evidence_sha256','test_target_accessed','raw_spectra_included'].map(k=>[k,report[k]]));

async function wasm(output) {
  const runtime = await createDomainsRuntime({wasmModule:await readFile(new URL('../native/nirs4all_domains_bg.wasm',import.meta.url))});
  assert.equal(runtime.provider.version,'1.3.13+abi.2.20.0');
  const cases=[];
  function request(id,x,values,kind='categorical',method='pearson',exact=false,options={}) {
    const keys=x.map((_,i)=>`${id}-${i}`);
    const dataset={dataset_id:id,source_id:'synthetic-x',content_version:'f41-public-synthetic-v1',content_sha256:sha(JSON.stringify(x))};
    const population=options.population??'train',global=population==='global_transductive';
    const manifest=[...keys.map((key,i)=>({key,partition:population==='unpartitioned'?'unpartitioned':global&&i>=4?'test':'train'})),...(options.extraManifest??[])];
    const matrix=x.map(v=>options.twoFeatures?[v,2*v]:[v]),axis=options.twoFeatures?[1000,1100]:[1000];
    let source,report,fitReceipt;
    if(population==='unpartitioned') {
      report=compact(runtime.analyze({schema_version:1,dataset_id:dataset.dataset_id,source_id:dataset.source_id,content_sha256:dataset.content_sha256,observation_ids:keys,axis,axis_unit:'nm',spectra:matrix}));
      fitReceipt=null;
    } else {
      source=runtime.analyzeScoped({schema_version:1,protocol_version:'domains.browser_scoped_analysis.v1',operation:global?'global_descriptive_transductive':'train_structure',diagnostic:null,
        dataset,manifest,reference_keys:global?keys.slice(0,4):keys,query_keys:global?keys.slice(4):[],access:{x:true,m_fields:[],y_fields:[]},fit:global?'transductive':'train',representation:'raw',selection_context:'unspecified',
        explicit_transductive:global,parameters:{preset:'f4_fixed_raw_v1'},exclusion_field:null,x:{row_keys:keys,matrix,axis,axis_unit:'nm'},metadata:[]});
      assert.equal(source.status,'computed',id);
      report=compact(source.value.structure);fitReceipt=source.receipt;
    }
    if(report.metrics.pca.status!=='computed')return {source,unavailable:true};
    const column=(name,role,vals,type)=>({name,role,kind:type,unit:type==='continuous'?'synthetic-unit':null,origin:'public-synthetic-by-construction',derived_from_target:false,evidence:'verified',row_keys:keys,values:vals});
    const factors=[column('factor','factor',values,kind)];
    const dependencies=exact?[column('unit','specimen',keys.map(k=>`unit-${k}`),'categorical')]:[];
    const plan=exact?{protocol_version:'domains.factor_exchangeability.v1',population,dataset_content_sha256:dataset.content_sha256,pca_evidence_sha256:report.evidence_sha256,
      external_evidence:{uri:'urn:domains:public-synthetic-design',content_sha256:sha('independent-by-construction synthetic units'),qualification:'externally_qualified',basis:'Synthetic fixture units are independent by construction; this grants no real-data qualification.'},
      unit_field:'unit',unit_kind:'specimen',dependency_fields:['unit'],no_other_dependencies:true,selection:'prospective',factor_ids:['factor'],components:'all_resolved',missingness:'complete_units',null_model:'unrestricted_exchangeability_given_fitted_x'}:null;
    return {schema_version:1,protocol_version:'domains.browser_factor_association.v1',dataset,manifest,population,pca:{report,row_keys:keys,fit_receipt:fitReceipt},factors,dependencies,
      access:{x:false,m_fields:[...factors,...dependencies].map(c=>c.name),y_fields:[]},representation:'raw',explicit_transductive:global,components:'all_resolved',correlation_method:method,
      inference:{mode:exact?'exact_if_qualified':'descriptive',plan},parameters:{preset:'f41_factor_pc_v1'}};
  }
  function record(id,input) {
    assert.ok(!input.unavailable,id);
    assert.ok(validateInput(input),`${id} input schema: ${JSON.stringify(validateInput.errors)}`);
    const result=runtime.analyzeFactor(input);
    assert.ok(validateResult(result),`${id} result schema: ${JSON.stringify(validateResult.errors)}`);
    assert.equal(result.status,'computed');
    assert.equal(result.receipt.pca_refits,0);
    assert.equal(result.receipt.fields_read.x,false);
    assert.deepEqual(result.receipt.fields_read.y,[]);
    assert.equal(result.receipt.test_m_accessed,input.population==='global_transductive');
    assert.equal(result.receipt.y_accessed,false);
    for(const call of result.receipt.provider_calls)assert.ok(!['pca','hdbscan','nearest_neighbors'].includes(call.operation));
    // The receipt names codes/values, but carries only count/hash descriptors.
    // Assert the admissible shape rather than forbidding those documentary names.
    for(const call of result.receipt.provider_calls)for(const input of Object.values(call.inputs)){
      assert.deepEqual(Object.keys(input).sort(),['count','sha256']);
      assert.ok(Number.isInteger(input.count));assert.match(input.sha256,/^[0-9a-f]{64}$/);
    }
    const noRawVectors=value=>{
      if(value&&typeof value==='object')for(const [key,item] of Object.entries(value)){
        if(key==='codes'||key==='values')assert.equal(Array.isArray(item),false,`Raw ${key} vector in result`);
        noRawVectors(item);
      }
    };
    noRawVectors(result);
    cases.push({id,request:input,result});
    return result;
  }
  function run(id,x,m,kind='categorical',method='pearson',exact=false,options={}) {
    return record(id,request(id,x,m,kind,method,exact,options));
  }
  const strong=run('categorical-strong',[1,2,3,7,8,9],[0,0,0,1,1,1]);
  close(component(strong).descriptive.value.estimate,27/29,'strong eta2');
  close(component(strong).descriptive.value.owner_output.f_statistic,54,'strong F');
  assert.equal(component(strong).descriptive.value.owner_output.p_value,null);
  assert.equal(component(strong).descriptive.value.owner_output.n_permutations_executed,0);
  close(component(run('categorical-zero',[-3,-2,-1,1,2,3],[0,1,0,0,1,0])).descriptive.value.estimate,0,'zero group means');
  for(const method of ['pearson','spearman']) {
    const r=run(`owner-${method}`,[2,4,5,4,5],[1,2,3,4,5],'continuous',method);
    close(Math.abs(component(r).descriptive.value.estimate),method==='pearson'?6/Math.sqrt(60):7/Math.sqrt(90),method);
    assert.equal(component(r).descriptive.value.owner_output.n_permutations_executed,0);
  }
  const missing=run('partial-missing',[1,2,3,7,8,9],['A',null,'A','B','B',null]);
  assert.equal(missing.value.factors[0].n_used,4);assert.equal(missing.value.factors[0].n_missing,2);
  close(component(missing).descriptive.value.estimate,121/131,'missing eta2');
  close(component(missing).descriptive.value.owner_output.f_statistic,24.2,'missing F');
  const saturated=run('singleton-saturated',[1,2,3,7,8,9],['a','b','c','d','e','f']);
  close(component(saturated).descriptive.value.estimate,1,'saturated eta2');
  assert.equal(component(saturated).descriptive.value.owner_output.f_statistic,null);
  for(const [id,m,kind] of [['one-level',[1,1,1,1,1,1],'categorical'],['constant-factor',[1,1,1,1,1,1],'continuous']]) {
    assert.equal(component(run(id,[1,2,3,7,8,9],m,kind)).descriptive.status,'unavailable');
  }
  const constant=request('constant-score',[1,1,1,1],[0,0,1,1]);
  assert.ok(constant.unavailable || constant.pca.report.metrics.pca.value.n_components_resolved===0,'constant scores have no resolved component');
  const factorExact=run('independent-exact',[1,2,3,4],[0,0,1,1],'categorical','pearson',true);
  const correlationExact=run('continuous-exact',[1,2,3,4],[1,2,3,4],'continuous','pearson',true);
  for(const [r,n,p] of [[factorExact,6,1/3],[correlationExact,24,1/12]]) {
    const i=component(r).inference;
    assert.equal(i.status,'computed');assert.equal(i.value.owner_exact.n_arrangements,n);
    close(i.value.owner_exact.p_value,p,'exact p');close(i.value.holm_adjusted_p,p,'Holm single family');
    assert.equal(r.value.inference.level,'conditionally_admissible');
  }
  const baseInput=()=>structuredClone(cases.find(c=>c.id==='categorical-strong').request);
  const exactInput=()=>structuredClone(cases.find(c=>c.id==='independent-exact').request);
  const grants=input=>{input.access.m_fields=[...input.factors,...input.dependencies].map(c=>c.name);};
  const reordered=baseInput();
  // The builder deliberately shares immutable population keys; reorder M alone.
  reordered.factors[0].row_keys=[...reordered.factors[0].row_keys].reverse();
  reordered.factors[0].values=[...reordered.factors[0].values].reverse();
  const reorderedResult=record('reordered-M',reordered);
  close(component(reorderedResult).descriptive.value.estimate,27/29,'reordered eta2');
  assert.equal(reorderedResult.receipt.scores_sha256,strong.receipt.scores_sha256);
  for(const kind of ['repeated-specimen','shared-reference','unknown-units']) {
    const input=exactInput();
    if(kind==='repeated-specimen')input.dependencies[0].values=['u0','u0','u1','u1'];
    if(kind==='shared-reference') {
      input.dependencies.push({...structuredClone(input.dependencies[0]),name:'reference',role:'reference',values:['r0','r0','r1','r1']});
      input.inference.plan.dependency_fields.push('reference');grants(input);
    }
    if(kind==='unknown-units')input.dependencies[0].evidence='unknown';
    const r=record(kind,input);
    assert.equal(component(r).descriptive.status,'computed');
    assert.equal(r.value.inference.level,'unqualified');assert.equal(component(r).inference.value,null);
    assert.equal(r.receipt.provider_calls.some(c=>c.operation.endsWith('_exact')||c.operation==='holm_adjust'),false);
  }
  for(const crossed of [false,true]) {
    const input=baseInput();input.factors[0].name='instrument';input.factors[0].role='instrument';
    input.factors.push({...structuredClone(input.factors[0]),name:crossed?'operator':'lot',role:'factor',values:crossed?['o0','o1','o2','o0','o1','o2']:['l0','l0','l0','l1','l1','l1']});
    grants(input);const r=record(crossed?'crossed-factors':'confounded-instrument-lot',input);
    const table=r.value.dependency_audit.pairwise_context_tables[0];
    assert.equal(table.literal_total_confounding,!crossed);
    assert.equal(table.observed_combinations.length,crossed?6:2);
    assert.equal(table.absent_combination_count,crossed?0:2);
  }
  const family=exactInput();
  family.factors.push({...structuredClone(family.factors[0]),name:'linear',kind:'continuous',unit:'synthetic-unit',values:[1,2,3,4]});
  family.inference.plan.factor_ids=['factor','linear'];grants(family);
  const familyResult=record('two-factor-prespecified-family',family);
  for(const [i,p,adjusted] of [[0,1/3,1/3],[1,1/12,1/6]]) {
    const v=familyResult.value.factors[i].components[0].inference.value;
    close(v.owner_exact.p_value,p,'family raw p');close(v.holm_adjusted_p,adjusted,'family Holm p');assert.equal(v.family_size,2);
  }
  const unpartitioned=run('unpartitioned-default',[1,2,3,7,8,9],[0,0,0,1,1,1],'categorical','pearson',false,{population:'unpartitioned'});
  close(component(unpartitioned).descriptive.value.estimate,27/29,'unpartitioned eta2');
  assert.equal(unpartitioned.receipt.source_pca_fit_receipt_sha256,null);
  const globalResult=run('global-consented',[1,2,3,7,8,9],[0,0,0,1,1,1],'categorical','pearson',false,{population:'global_transductive'});
  assert.equal(globalResult.receipt.source_pca_uses_test_x,true);assert.equal(globalResult.receipt.test_scores_accessed,true);
  const mixed=run('train-only-excludes-test',[1,2,3,4],['A','A','B','B'],'categorical','pearson',false,
    {extraManifest:[{key:'test-only-sentinel',partition:'test'},{key:'predict-only-sentinel',partition:'predict'}]});
  assert.equal(mixed.value.factors[0].n_fit_observations,4);assert.equal(mixed.value.factors[0].n_levels,2);
  assert.equal(mixed.receipt.test_m_accessed,false);assert.equal(mixed.receipt.test_scores_accessed,false);
  assert.deepEqual(mixed.receipt.fit_keys,cases.find(c=>c.id==='train-only-excludes-test').request.manifest.filter(r=>r.partition==='train').map(r=>r.key));
  assert.ok(mixed.receipt.provider_calls.every(c=>c.inputs.scores?.count===4));
  assert.equal(mixed.receipt.fit_keys.includes('test-only-sentinel'),false);
  const rankOne=run('rank-one-two-feature',[1,2,3,7,8,9],[0,0,0,1,1,1],'categorical','pearson',false,{twoFeatures:true});
  const rankSource=cases.find(c=>c.id==='rank-one-two-feature').request.pca.report.metrics.pca.value;
  assert.equal(rankSource.n_components_requested,2);assert.equal(rankSource.n_components_resolved,1);
  assert.equal(rankOne.value.factors[0].components[1].descriptive.reason,'PCA_COMPONENT_NOT_RESOLVED');
  // A real WASM boundary spy proves malformed source/access requests never reach any provider.
  const adversaries=[];
  for(const mutate of [r=>{r.access.y_fields=['target'];},r=>{r.factors[0].derived_from_target=true;},r=>{r.factors[0].origin='Y';},r=>{r.factors[0].values[0]=9007199254740992;},r=>{r.pca.report.evidence_sha256='0'.repeat(64);},r=>{r.pca.fit_receipt.fit_keys.reverse();},r=>{r.factors[0].row_keys[0]='test-row';}]) {
    const r=structuredClone(cases[0].request);mutate(r);let calls=0;
    assert.throws(()=>rust.analyze_factor_json(JSON.stringify(r),()=>{calls++;return '{}';},runtime.provider.version));
    assert.equal(calls,0);adversaries.push({provider_calls:calls,status:'refused_before_provider'});
  }
  for(const mutate of [r=>{r.explicit_transductive=false;},r=>{r.population='train';r.explicit_transductive=false;}]) {
    const r=structuredClone(cases.find(c=>c.id==='global-consented').request);mutate(r);let calls=0;
    assert.throws(()=>rust.analyze_factor_json(JSON.stringify(r),()=>{calls++;return '{}';},runtime.provider.version));
    assert.equal(calls,0);adversaries.push({provider_calls:calls,status:'global_scope_refused_before_provider'});
  }
  await mkdir(dirname(output),{recursive:true});
  await writeFile(output,JSON.stringify({protocol_version:'domains.factor_same_scores_wasm.v1',fixture_sha256:sha(fixtureBytes),provider:runtime.provider,
    tolerance:{absolute:1e-10,relative:1e-10},cases,adversaries,constant_score_source:constant.source??constant.pca.report,new_real_scientific_fits:0})+'\n');
  console.log(`Factor WASM: ${cases.length} executed cases, ${adversaries.length} pre-provider refusals`);
}

async function compare(wasmPath,nativePath,output) {
  const bytes=await readFile(wasmPath),w=JSON.parse(bytes),n=JSON.parse(await readFile(nativePath));
  assert.equal(n.wasm_artifact_sha256,sha(bytes));assert.equal(n.provider_version,w.provider.version);
  assert.equal(n.pca_refits,0);assert.deepEqual(Object.keys(n.reports).sort(),w.cases.map(c=>c.id).sort());
  let numeric=0;
  function same(a,b,path) {
    if(typeof a==='number') {
      if(/\/(n_[^/]+|[^/]*count|component|family_size|df1|df2)$/.test(path))assert.equal(b,a,path);
      else close(b,a,path);
      numeric++;return;
    }
    if(Array.isArray(a)) { assert.ok(Array.isArray(b),path);assert.equal(b.length,a.length,path);a.forEach((x,i)=>same(x,b[i],`${path}/${i}`));return; }
    if(a&&typeof a==='object') { assert.deepEqual(Object.keys(b).sort(),Object.keys(a).sort(),path);for(const key of Object.keys(a))same(a[key],b[key],`${path}/${key}`);return; }
    assert.deepEqual(b,a,path);
  }
  // Provider response hashes intentionally differ when owner floating arithmetic differs.
  // Compare all scientific values/statuses/counts, and exact source-score identity separately.
  for(const c of w.cases) {
    const native=n.reports[c.id];
    assert.ok(validateInput(c.request),`${c.id} replay input schema: ${JSON.stringify(validateInput.errors)}`);
    assert.ok(validateResult(c.result),`${c.id} WASM result schema: ${JSON.stringify(validateResult.errors)}`);
    assert.ok(validateResult(native),`${c.id} native result schema: ${JSON.stringify(validateResult.errors)}`);
    same(c.result.value,native.value,c.id);
    assert.equal(native.receipt.scores_sha256,c.result.receipt.scores_sha256);
    assert.equal(native.receipt.source_pca_evidence_sha256,c.result.receipt.source_pca_evidence_sha256);
    assert.deepEqual(native.receipt.fit_keys,c.result.receipt.fit_keys);
    assert.deepEqual(native.receipt.provider_calls.map(x=>[x.operation,x.status,x.reason]),c.result.receipt.provider_calls.map(x=>[x.operation,x.status,x.reason]));
  }
  await writeFile(output,JSON.stringify({protocol_version:'domains.factor_same_scores_parity_receipt.v1',status:'passed',cases:w.cases.length,numeric_comparisons:numeric,
    tolerance:{absolute:1e-10,relative:1e-10},same_recorded_scores:true,provider:w.provider,pca_refits:0,new_real_scientific_fits:0})+'\n');
  console.log(`Factor same-score native/WASM parity: ${w.cases.length} cases, ${numeric} numeric comparisons`);
}
const [mode,...args]=process.argv.slice(2);
if(mode==='wasm'&&args.length===1)await wasm(args[0]);
else if(mode==='compare'&&args.length===3)await compare(...args);
else throw new Error('Usage: factor-protocol.mjs wasm OUT | compare WASM NATIVE RECEIPT');
