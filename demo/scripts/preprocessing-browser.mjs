/** Actual built-app F4.3 browser qualification. No numeric provider stubs or replacement values. */
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fixture,loadReviewed} from './scoped-browser.mjs';
import {auditAccessibility} from './ux-browser.mjs';
import catalog from '../../bindings/wasm/aom-bank.json' with {type:'json'};

const compactIds=['raw','snv','msc','detrend_1','sg_smooth_11_2','standard_scale'];
const history=report=>report.scientific_report?.preprocessing_sensitivity??[];
const latest=report=>history(report).at(-1);
const stable=value=>JSON.stringify(value);
const forbidden=['987654321.125','87654321.875'].flatMap(x=>[x,String(Math.fround(Number(x)))]);

/** Deterministic public synthetic data generation, not a numerical backend or numeric oracle. */
export function preprocessingFixture(name='Synthetic F4.3 keyed preprocessing fixture'){
 const base=fixture(),configFile=base.files.find(f=>f.name==='f4-scoped.nirs4all.json');
 const config=JSON.parse(configFile.buffer.toString('utf8')),axis=Array.from({length:25},(_,j)=>String(1000+j*100));
 const spectrum=i=>axis.map((_,j)=>20+.08*i+.2*j+2*Math.sin(j/4+i/10)+(i>=12?1.3:0)+.4*Math.cos(j/2-i/7));
 const train=Array.from({length:24},(_,i)=>({id:`tr-${i}`,x:spectrum(i),y:10+i,specimen:`spec-tr-${Math.floor(i/2)}`,group:i<12?'group-a':'group-b',reference:`ref-${Math.floor(i/2)}`,batch:i<12?'batch-a':'batch-b',instrument:i%2?'instrument-b':'instrument-a',repetition:String(i%2)}));
 const test=Array.from({length:4},(_,i)=>({id:`te-${i}`,x:i===0?[...train[2].x]:spectrum(24+i).map((x,j)=>x+.1*Math.sin(j)),y:987654321.125+i,specimen:`spec-test-${i}`,group:'group-test',reference:`ref-test-${i}`,batch:'batch-test',instrument:'instrument-test',repetition:'0'}));
 const predict=[{id:'pr-0',x:axis.map((_,j)=>87654321.875+j),y:987654321.125+10,specimen:'spec-predict',group:'group-predict',reference:'ref-predict',batch:'batch-predict',instrument:'instrument-predict',repetition:'0'}];
 const csv=rows=>rows.map(row=>row.join(',')).join('\n')+'\n';
 for(const [partition,rows] of [['train',train],['test',test],['predict',predict]]){
  const x=config.sources.find(s=>s.id===`X_${partition}`),m=config.sources.find(s=>s.id===`M_${partition}`);
  x.columns.features=axis;m.columns.metadata.push('instrument','repetition');
  base.files.find(f=>f.name===`X_${partition}.csv`).buffer=Buffer.from(csv([['id',...axis],...rows.map(row=>[row.id,...row.x])]));
  base.files.find(f=>f.name===`Y_${partition}.csv`).buffer=Buffer.from(csv([['id','yield'],...rows.map(row=>[row.id,row.y])]));
  base.files.find(f=>f.name===`M_${partition}.csv`).buffer=Buffer.from(csv([['id','specimen','group','reference','batch','instrument','repetition'],...[...rows].reverse().map(row=>[row.id,row.specimen,row.group,row.reference,row.batch,row.instrument,row.repetition])]));
  for(const role of ['instrument','repetition'])config.metadata_declarations[`M_${partition}__${role}`]={role,derived_from_target:false};
 }
 config.name=name;configFile.buffer=Buffer.from(JSON.stringify(config));
 return {files:base.files,train,test,predict,bands:axis.length};
}

/** Separate bounded lifecycle check: one raw representation, no export rendering or print attempt. */
export async function qualifyPreprocessingLifecycle({page,output,json,check}){
 page.setDefaultTimeout(30000);const directory=resolve(output,'f4.3','chromium');await mkdir(directory,{recursive:true});
 const data=preprocessingFixture();await page.getByRole('button',{name:/Home|Accueil/}).click();await page.locator('input[type=file]').waitFor({state:'visible'});await loadReviewed(page,data.files);await instrumentWorkers(page);
 if(await page.getByRole('button',{name:'EN',exact:true}).getAttribute('aria-pressed')!=='true')await page.getByRole('button',{name:'EN',exact:true}).click();
 await perform(page,'Train structure');await page.getByRole('combobox',{name:'Factor',exact:true}).selectOption('batch');await perform(page,'Run factor association');await perform(page,'Compute train reference and project test');
 const prior=await json(page),plan={bank_id:catalog.bank_id,kind:'prospective',parent_plan_sha256:null,representations:[structuredClone(catalog.entries.find(e=>e.spec.id==='raw').spec)],structure:true,compare_neighbors:true,compare_clusters:true,correlation_method:'pearson',support:{n_components:2,max_components:2,n_folds:5,alpha:.05,monitoring:true}};
 await editPlan(page,plan);await perform(page,'Compute panel on reference only');const reference=latest(await json(page));assert.equal(reference.status,'computed');assert.deepEqual(reference.representations.map(e=>[e.id,e.status]),[['raw','computed']]);assert.equal(reference.receipt.reference_keys.length,24);assert.deepEqual(reference.receipt.query_keys,[]);assert.equal(reference.receipt.test_x_accessed,false);
 await perform(page,'Freeze plan and audit test');const report=await json(page);assertAudit(latest(report),reference,data);for(const name of ['scoped_operations','factor_associations','train_fitted_support'])assert.deepEqual(report.scientific_report[name],prior.scientific_report[name]);
 await page.evaluate(()=>{window.__f43Audit.delayNext=true;});const terminated=await page.evaluate(()=>window.__f43Audit.terminated);await page.getByRole('button',{name:'Compute panel on reference only',exact:true}).click();await page.waitForFunction(()=>window.__f43Audit.delayed);await page.getByRole('button',{name:'Cancel analysis',exact:true}).click();await page.waitForFunction(n=>window.__f43Audit.terminated>n,terminated);await page.waitForFunction(()=>window.__f43Audit.delayReleased);assert.deepEqual((await json(page)).scientific_report,report.scientific_report);check('F4.3 bounded raw lifecycle: actual worker cancellation preserves all F4.0/F4.1/F4.2/F4.3 histories');
 await page.evaluate(()=>{window.__f43Audit.delayNext=true;window.__f43Audit.delayed=false;window.__f43Audit.delayReleased=false;});await page.getByRole('button',{name:'Compute panel on reference only',exact:true}).click();await page.waitForFunction(()=>window.__f43Audit.delayed);const beforeReset=await page.evaluate(()=>window.__f43Audit.terminated);await page.getByRole('button',{name:/Home|Accueil/}).click();await page.locator('input[type=file]').waitFor({state:'visible'});await page.waitForFunction(n=>window.__f43Audit.terminated>n,beforeReset);await page.waitForFunction(()=>window.__f43Audit.delayReleased);await loadReviewed(page,preprocessingFixture('F4.3 replacement identity').files);const replacement=await json(page);for(const name of ['preprocessing_sensitivity','scoped_operations','factor_associations','train_fitted_support'])assert.deepEqual(replacement.scientific_report[name],[]);
 const receipt={protocol:'domains.f4_3_preprocessing_lifecycle_qualification.v1',success:true,scope:'Synthetic raw-only actual reference/audit and lifecycle; six-family accessibility/export evidence is separate. Full browser/PDF qualification remains incomplete.',print:{status:'not_attempted',reason:'F43_PRINT_RESOURCE_QUALIFICATION_REQUIRED'},reference_evidence_sha256:reference.evidence_sha256,audit_evidence_sha256:latest(report).evidence_sha256,cancellation_preserves_all_histories:true,reset:{new_source_identity:true,histories_cleared:true,terminated_worker:true,stale_response_ignored:true}};
 await writeFile(resolve(directory,'preprocessing-lifecycle.json'),JSON.stringify(receipt,null,2)+'\n');check('F4.3 bounded raw lifecycle: pending-work reset terminates worker, replaces source and clears every history');
}

async function instrumentWorkers(page){
 await page.evaluate(()=>{
  const Original=window.Worker;
  window.__f43Audit={operations:[],requests:[],completed:[],terminated:0,delayNext:false,delayed:false,delayReleased:false};
  window.Worker=class extends Original{
   constructor(...args){super(...args);this.operation='unknown';this.addEventListener('message',({data})=>{if(!data.stage)window.__f43Audit.completed.push({operation:this.operation,ok:data.ok});});}
   postMessage(message,transfer){
    this.operation=message.operation;window.__f43Audit.operations.push(message.operation);
    if(message.operation==='preprocessing_sensitivity'){
     const p=message.payload;
     window.__f43Audit.requests.push({stage:p.stage,reference_keys:p.reference_keys,query_keys:p.query_keys,x_keys:p.x.row_keys,x_shape:[p.x.matrix.length,p.x.axis.length],access:p.access,factors:p.factors.map(f=>({name:f.name,row_keys:f.row_keys})),dependencies:p.dependencies.map(f=>({name:f.name,row_keys:f.row_keys})),frozen_evidence_sha256:p.frozen_reference?.evidence_sha256??null});
     if(window.__f43Audit.delayNext){window.__f43Audit.delayNext=false;window.__f43Audit.delayed=true;setTimeout(()=>{window.__f43Audit.delayReleased=true;try{super.postMessage(message,transfer);}catch{}},1000);return;}
    }
    return super.postMessage(message,transfer);
   }
   terminate(){window.__f43Audit.terminated++;return super.terminate();}
  };
 });
}
async function perform(page,name){
 const before=await page.evaluate(()=>window.__f43Audit.completed.length);
 await page.getByRole('button',{name,exact:true}).click();
 await page.waitForFunction(n=>window.__f43Audit.completed.length>n,before);
}
async function editPlan(page,plan){
 const summary=page.getByText('Advanced plan and parameters (JSON)',{exact:true});
 if(await summary.evaluate(el=>!el.closest('details').open))await summary.click();
 await page.getByRole('textbox',{name:'Sensitivity plan JSON',exact:true}).fill(JSON.stringify(plan,null,2));
}
function assertHash(value,label){assert.match(value,/^[a-f0-9]{64}$/,label);}
function assertReference(result,data){
 assert.equal(result.protocol_version,'domains.browser_preprocessing_sensitivity_result.v1');assert.equal(result.status,'computed');assert.equal(result.stage,'reference_only');
 assert.equal(result.receipt.reference_keys.length,data.train.length);assert.deepEqual(result.receipt.query_keys,[]);assert.equal(result.receipt.test_x_accessed,false);assert.equal(result.receipt.y_accessed,false);assert.equal(result.receipt.x_predict_accessed,false);
 assert(result.receipt.reference_keys.every(k=>JSON.parse(k)[1]==='train'));
 for(const key of ['input_sha256','reference_input_sha256','plan_sha256','evidence_sha256'])assertHash(result[key],key);
 assert.deepEqual(result.representations.map(r=>r.id),compactIds);
 for(const entry of result.representations){
  assert.equal(entry.status,'computed',`${entry.id}: ${entry.reason}`);assert(entry.value,entry.id);assert.equal(entry.value.axis.length,data.bands);
  for(const stage of entry.value.transformations){assert.equal(stage.fit_keys_role,'reference_only');assert.equal(stage.state_unchanged_after_transform,true);assertHash(stage.state_sha256,'actual serialized owner state');}
  const structure=entry.value.structure;assert.equal(structure.status,'computed',entry.id+' structure');assert.equal(structure.value.report.metrics.pca.status,'computed',entry.id+' owner PCA');
 }
 const fits=result.receipt.provider_calls.filter(c=>c.operation==='preprocess_fit');assert(fits.length>=5,'Five distinct nonraw family fits expected');
 for(const call of result.receipt.provider_calls){assertHash(call.request_sha256??call.payload_sha256,'actual provider request hash');if(['preprocess_fit','pca','pca_fit'].includes(call.operation))assert.deepEqual(call.row_keys,result.receipt.reference_keys,'All preprocessing/PCA fits must see reference only');assert(!call.row_keys.some(k=>JSON.parse(k)[1]==='predict'));}
}
function assertAudit(result,reference,data){
 assert.equal(result.protocol_version,'domains.browser_preprocessing_sensitivity_result.v1');assert.equal(result.stage,'test_audit');assert.equal(result.receipt.reference_keys.length,data.train.length);assert.equal(result.receipt.query_keys.length,data.test.length);assert.equal(result.receipt.test_x_accessed,true);assert.equal(result.receipt.y_accessed,false);assert.equal(result.receipt.x_predict_accessed,false);
 assert.equal(result.plan_sha256,reference.plan_sha256);assert.equal(result.reference_input_sha256,reference.reference_input_sha256);assert.notEqual(result.input_sha256,reference.input_sha256);
 assert(result.receipt.query_keys.every(k=>JSON.parse(k)[1]==='test'));
 for(const entry of result.representations){
  assert.equal(entry.status,'computed',`${entry.id}: ${entry.reason}`);const old=reference.representations.find(r=>r.id===entry.id);assert.equal(entry.value.reference_matrix_sha256,old.value.reference_matrix_sha256);assert.deepEqual(entry.value.transformations,old.value.transformations);
  const support=entry.value.support;assert.equal(support.status,'computed',`${entry.id} support: ${support.reason}`);assert.equal(support.value.receipt.fit_keys.length,data.train.length);assert.equal(support.value.receipt.query_keys.length,data.test.length);assert.equal(support.value.receipt.y_test_accessed,false);
 }
 for(const call of result.receipt.provider_calls.filter(c=>['preprocess_fit','pca','pca_fit'].includes(c.operation)))assert.deepEqual(call.row_keys,result.receipt.reference_keys,'Test-audit reference fits never see query rows');
}

/** Root harness runs this helper against actual built Methods/WASM in each selected browser engine. */
export async function qualifyPreprocessingBrowser({page,context,url,output,check,exported,json,screenshot}){
 const engine=page.context().browser()?.browserType().name()??'browser',directory=resolve(output,'f4.3',engine);await mkdir(directory,{recursive:true});
 const captures={protocol:'domains.f4_3_preprocessing_browser_qualification.v1',browser:engine,success:false,operations:[],exports:{},screenshots:[],limitations:['Synthetic fixture only; targeted automated accessibility, not WCAG certification.']};
 const data=preprocessingFixture();await page.getByRole('button',{name:/Home|Accueil/}).click();await page.locator('input[type=file]').waitFor({state:'visible'});await loadReviewed(page,data.files);await instrumentWorkers(page);
 if(await page.getByRole('button',{name:'EN',exact:true}).getAttribute('aria-pressed')!=='true')await page.getByRole('button',{name:'EN',exact:true}).click();
 let current=await json(page);assert.deepEqual(history(current),[]);assert.equal(current.scientific_report.scoped_operations.length,0);assert.equal(current.scientific_report.inventory.loaded.x.rows,29);
 const initialText=stable(current);assert(forbidden.every(s=>!initialText.includes(s)));
 // Establish historical operations on this exact source before the additive panel.
 await perform(page,'Train structure');await page.getByRole('combobox',{name:'Factor',exact:true}).selectOption('batch');await perform(page,'Run factor association');
 await perform(page,/^Raw support: train reference/);await perform(page,'Exact spectra train/test audit');await perform(page,'Compute train reference and project test');
 current=await json(page);
 const preserved={scoped:current.scientific_report.scoped_operations,factors:current.scientific_report.factor_associations,support:current.scientific_report.train_fitted_support};
 assert(preserved.scoped.some(r=>r.operation==='train_structure'&&r.status==='computed'));assert(preserved.factors.some(r=>r.status==='computed'));assert(preserved.support.some(r=>r.projection.status==='computed'));
 const panel=page.locator('#preprocessing-sensitivity'),factorGroup=panel.getByRole('group',{name:'Reference factors (at most two)',exact:true});await factorGroup.getByRole('checkbox',{name:'batch',exact:true}).check();
 const plan={bank_id:catalog.bank_id,kind:'prospective',parent_plan_sha256:null,representations:compactIds.map(id=>structuredClone(catalog.entries.find(e=>e.spec.id===id).spec)),structure:true,compare_neighbors:true,compare_clusters:true,correlation_method:'pearson',support:{n_components:2,max_components:2,n_folds:5,alpha:.05,monitoring:true}};
 await editPlan(page,plan);const auditButton=panel.getByRole('button',{name:'Freeze plan and audit test',exact:true});assert.equal(await auditButton.isEnabled(),false);
 await perform(page,'Compute panel on reference only');current=await json(page);const reference=latest(current);assertReference(reference,data);
 const firstRequest=await page.evaluate(()=>window.__f43Audit.requests[0]);assert.deepEqual(firstRequest.query_keys,[]);assert.deepEqual(firstRequest.x_keys,reference.receipt.reference_keys);assert.deepEqual(firstRequest.x_shape,[24,25]);assert.deepEqual(firstRequest.access.y_fields,[]);assert(firstRequest.factors.every(f=>stable(f.row_keys)===stable(reference.receipt.reference_keys)));
 assert.equal(await auditButton.isEnabled(),true);captures.operations.push({stage:'reference_only',evidence_sha256:reference.evidence_sha256,receipt:reference.receipt,representations:reference.representations.map(e=>({id:e.id,status:e.status,reason:e.reason,transformations:e.value?.transformations}))});
 check('F4.3 actual compact six-family reference panel fits only 24 train rows, retains 25 bands and excludes test/predict/Y',{families:compactIds,reference_input_sha256:reference.reference_input_sha256});
 // A modified plan cannot audit using the earlier frozen reference. Restoring the exact controls is allowed.
 const requestsBeforeEdit=await page.evaluate(()=>window.__f43Audit.operations.length);await editPlan(page,{...plan,compare_neighbors:false});assert.equal(await auditButton.isEnabled(),false);assert.equal(await page.evaluate(()=>window.__f43Audit.operations.length),requestsBeforeEdit);await editPlan(page,plan);assert.equal(await auditButton.isEnabled(),true);
 await perform(page,'Freeze plan and audit test');current=await json(page);const audit=latest(current);assertAudit(audit,reference,data);
 const auditRequest=await page.evaluate(()=>window.__f43Audit.requests.at(-1));assert.deepEqual(auditRequest.x_shape,[28,25]);assert.equal(auditRequest.frozen_evidence_sha256,reference.evidence_sha256);assert(auditRequest.factors.every(f=>stable(f.row_keys)===stable(reference.receipt.reference_keys)));assert(auditRequest.dependencies.every(d=>d.row_keys.length===28));
 captures.operations.push({stage:'test_audit',evidence_sha256:audit.evidence_sha256,receipt:audit.receipt});check('F4.3 explicit frozen audit reuses identical reference fingerprints and grants only four test queries; factor values remain reference-only');
 assert.equal(stable({scoped:current.scientific_report.scoped_operations,factors:current.scientific_report.factor_associations,support:current.scientific_report.train_fitted_support}),stable(preserved),'F4.0/F4.1/F4.2 history must remain byte-identical');
 const advancedTables=panel.locator('details.sensitivity-advanced');assert.equal(await advancedTables.count(),2);for(const detail of await advancedTables.all())assert.equal(await detail.getAttribute('open'),null,'Complete live tables start collapsed; availability and figures remain visible');
 captures.live_layout=await page.evaluate(()=>({nodes:document.getElementsByTagName('*').length,scroll_height:document.documentElement.scrollHeight}));
 assert.equal(await page.locator('#structure-evidence details.science-disclosure #evidence-preprocessing-sensitivity-1').count(),1,'Original generic evidence block and anchor remain in the existing scientific disclosure');
 await screenshot(page,`${engine}-f4.3-controls-en`,false,'#preprocessing-sensitivity > fieldset');await screenshot(page,`${engine}-f4.3-projection-en`,false,'#preprocessing-sensitivity-1-raw-scores');captures.screenshots.push(`${engine}-f4.3-controls-en`,`${engine}-f4.3-projection-en`);await auditAccessibility(page,output,`${engine}-f4.3-preprocessing-en`,check);
 // One invalid SG parameter is a representation-local refusal, not a reason to hide valid siblings.
 const broken=structuredClone(plan);broken.representations=[broken.representations[0],{...structuredClone(broken.representations.find(r=>r.id==='sg_smooth_11_2')),id:'sg_invalid_polyorder'},structuredClone(broken.representations.find(r=>r.id==='snv'))];broken.representations[1].steps[0].parameters.polyorder=11;
 await editPlan(page,broken);await perform(page,'Compute panel on reference only');current=await json(page);const partial=latest(current);assert.equal(partial.protocol_version,'domains.browser_preprocessing_sensitivity_result.v1');assert.equal(partial.plan.kind,'exploratory_revision');assert.equal(partial.representations.length,3);assert.equal(partial.representations[0].status,'computed');assert.equal(partial.representations[1].status,'unavailable');assert.equal(typeof partial.representations[1].reason,'string');assert.equal(partial.representations[2].status,'computed');assert.deepEqual(history(current).slice(0,2),[reference,audit]);captures.operations.push({stage:'local_representation_refusal',evidence_sha256:partial.evidence_sha256,representations:partial.representations.map(r=>({id:r.id,status:r.status,reason:r.reason}))});check('F4.3 invalid SG polynomial order remains visible while raw and subsequent SNV succeed, preserving prior histories');
 const evidenceBefore=stable(current.scientific_report),workersBefore=await page.evaluate(()=>window.__f43Audit.operations.length);await page.getByRole('button',{name:'FR',exact:true}).click();assert.equal(await page.locator('html').getAttribute('lang'),'fr');await screenshot(page,`${engine}-f4.3-projection-fr`,false,'#preprocessing-sensitivity-1-raw-scores');captures.screenshots.push(`${engine}-f4.3-projection-fr`);await auditAccessibility(page,output,`${engine}-f4.3-preprocessing-fr`,check);await page.getByRole('button',{name:'EN',exact:true}).click();
 assert.equal(stable((await json(page)).scientific_report),evidenceBefore);assert.equal(await page.evaluate(()=>window.__f43Audit.operations.length),workersBefore,'Language/display/report reads must not run scientific work');
 await page.getByRole('button',{name:'Select all available',exact:true}).click();const html=await exported(page,'html'),markdown=await exported(page,'markdown'),report=await json(page),jsonText=JSON.stringify(report);
 assert.equal(report.export_selection.provenance.action,'select_all');assert.equal(report.raw_x_included,false);assert.deepEqual(history(report),history(current));assert.equal(await page.evaluate(()=>window.__f43Audit.operations.length),workersBefore);
 for(const text of [html,markdown,jsonText]){assert(forbidden.every(s=>!text.includes(s)),'Raw X/Y sentinels must not enter any export');assert(!text.includes('factor-level-')&&!text.includes('factor-bin-'),'Annex selection must not grant observation-level M colors');for(const result of history(report))assert(text.includes(result.evidence_sha256),'Every exact scientific evidence digest must remain in every export');assert(text.includes('sg_invalid_polyorder'));}
 for(const result of history(report)){const matching=report.evidence.find(e=>e.id===`preprocessing-sensitivity-${history(report).indexOf(result)+1}`);assert.deepEqual(matching.value,result);}
 const colorGrant=page.getByRole('checkbox',{name:/Authorize this factor.s observation-level colors in this report export/});if(await colorGrant.count())assert.equal(await colorGrant.isChecked(),false);
 for(const [extension,text] of [['html',html],['md',markdown],['json',JSON.stringify(report,null,2)+'\n']]){await writeFile(resolve(directory,`preprocessing-sensitivity.${extension}`),text);captures.exports[extension]={bytes:Buffer.byteLength(text),results:history(report).length,raw_sentinels:false,unauthorized_m_colors:false};}
 captures.exports.evidence_sha256=history(report).map(r=>r.evidence_sha256);check('F4.3 uncapped HTML/Markdown/JSON retain all six-family comparisons, unavailable entries, exact receipts and separate M-color permissions');
 // Delay only request scheduling; actual kernels are never stubbed. Termination must preserve all prior histories.
 await page.evaluate(()=>{window.__f43Audit.delayNext=true;});const terminated=await page.evaluate(()=>window.__f43Audit.terminated);await page.getByRole('button',{name:'Compute panel on reference only',exact:true}).click();await page.waitForFunction(()=>window.__f43Audit.delayed);await page.getByRole('button',{name:'Cancel analysis',exact:true}).click();await page.waitForFunction(n=>window.__f43Audit.terminated>n,terminated);await page.waitForFunction(()=>window.__f43Audit.delayReleased);assert.deepEqual(history(await json(page)),history(report));check('F4.3 worker cancellation preserves earlier F4.3 and F4.0/F4.1/F4.2 results');
 await page.evaluate(()=>{window.__f43Audit.delayNext=true;window.__f43Audit.delayed=false;window.__f43Audit.delayReleased=false;});await page.getByRole('button',{name:'Compute panel on reference only',exact:true}).click();await page.waitForFunction(()=>window.__f43Audit.delayed);await page.getByRole('button',{name:/Home|Accueil/}).click();await page.locator('input[type=file]').waitFor({state:'visible'});await page.waitForFunction(()=>window.__f43Audit.delayReleased);await loadReviewed(page,preprocessingFixture('F4.3 replacement identity').files);current=await json(page);assert.deepEqual(history(current),[]);assert.deepEqual(current.scientific_report.factor_associations,[]);assert.deepEqual(current.scientific_report.train_fitted_support,[]);assert.deepEqual(current.scientific_report.scoped_operations,[]);
 captures.reset={new_source_identity:true,histories_cleared:true,terminated_worker:true,stale_response_ignored:true};check('F4.3 reset while work is pending clears all dataset-bound histories and rejects the obsolete worker');
 // Engineering admission only: the observed 42 MB export exceeded 10 GB renderer RAM.
 // Preserve exact exports and fail qualification; never trim scientific content for printing.
 const printAdmissionBytes=8_000_000;
 if(engine==='chromium'&&Buffer.byteLength(html)>printAdmissionBytes){captures.exports.print={status:'unavailable',reason:'F43_PRINT_RESOURCE_QUALIFICATION_REQUIRED',html_bytes:Buffer.byteLength(html),admission_limit_bytes:printAdmissionBytes};await writeFile(resolve(directory,'preprocessing-browser.json'),JSON.stringify(captures,null,2)+'\n');assert.fail('F43_PRINT_RESOURCE_QUALIFICATION_REQUIRED: exact uncapped HTML exceeds the engineering admission bound; HTML/Markdown/JSON and lifecycle evidence are preserved.');}
 if(engine==='chromium'){
  const printPage=await context.newPage();try{await printPage.setContent(html,{waitUntil:'load'});for(const [paper,format] of [['a4','A4'],['letter','Letter']])await printPage.pdf({path:resolve(directory,`preprocessing-sensitivity-${paper}.pdf`),format,printBackground:true});captures.exports.print=['preprocessing-sensitivity-a4.pdf','preprocessing-sensitivity-letter.pdf'];}finally{await printPage.close();}
 }else captures.exports.print='not_applicable: Chromium-only PDF generation/review';
 captures.success=true;await writeFile(resolve(directory,'preprocessing-browser.json'),JSON.stringify(captures,null,2)+'\n');
}
