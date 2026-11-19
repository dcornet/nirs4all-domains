/** Actual browser qualification for the F4.2 train-fitted support workflow. */
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fixture,loadOneShot} from './scoped-browser.mjs';
import {auditAccessibility} from './ux-browser.mjs';

const resultList=report=>report.scientific_report?.train_fitted_support??[];
const latest=report=>resultList(report).at(-1);
const operation=(report,name)=>report.scientific_report?.scoped_operations?.findLast(item=>item.operation===name);
const stable=value=>JSON.stringify(value);

async function instrumentSupportWorkers(page){
  await page.evaluate(()=>{
    const Original=window.Worker;
    window.__f42SupportAudit={operations:[],completed:[],terminated:0,delayNext:false,delayed:false,delayReleased:false};
    window.Worker=class extends Original{
      constructor(...args){super(...args);this.supportOperation='unknown';this.addEventListener('message',({data})=>{if(!data.stage)window.__f42SupportAudit.completed.push({operation:this.supportOperation,ok:data.ok});});}
      postMessage(message,transfer){
        this.supportOperation=message.operation;window.__f42SupportAudit.operations.push(message.operation);
        if(message.operation==='train_fitted_support'&&window.__f42SupportAudit.delayNext){
          window.__f42SupportAudit.delayNext=false;window.__f42SupportAudit.delayed=true;
          setTimeout(()=>{window.__f42SupportAudit.delayReleased=true;try{super.postMessage(message,transfer);}catch{}},1000);
          return;
        }
        return super.postMessage(message,transfer);
      }
      terminate(){window.__f42SupportAudit.terminated++;return super.terminate();}
    };
  });
}
async function completedSupport(page){
  const before=await page.evaluate(()=>window.__f42SupportAudit.completed.filter(item=>item.operation==='train_fitted_support').length);
  await page.getByRole('button',{name:/Compute train reference and project test/}).click();
  await page.waitForFunction(n=>window.__f42SupportAudit.completed.filter(item=>item.operation==='train_fitted_support').length>n,before);
  await page.locator('.workspace-summary').waitFor();
}
function assertSafeResult(report,result,fixtureData){
  assert(result,'Support result must be present in the actual exported scientific report');
  assert.equal(result.protocol_version,'domains.browser_train_fitted_support_result.v1');
  assert.deepEqual(result.receipt.fit_keys,report.scientific_report.train_fitted_support.at(-1).receipt.fit_keys);
  assert.equal(result.receipt.fit_population,'train');
  assert.equal(result.receipt.query_population,'test');
  assert.equal(result.receipt.fit_keys.length,fixtureData.train.length);
  assert.equal(result.receipt.query_keys.length,fixtureData.test.length);
  assert(result.receipt.fit_keys.every(key=>JSON.parse(key)[1]==='train'));
  assert(result.receipt.query_keys.every(key=>JSON.parse(key)[1]==='test'));
  assert.equal(result.receipt.x_test_accessed,true);
  assert.equal(result.receipt.x_predict_accessed,false);
  assert.equal(result.receipt.y_train_accessed,false);
  assert.equal(result.receipt.y_test_accessed,false);
  assert.equal(result.receipt.f41_pca_reused,false);
  assert.equal(result.receipt.monitoring_and_projection_same_fitted_object,false);
  assert.equal(result.projection.status,'computed');
  assert.equal(result.projection.value.train_scores.length,fixtureData.train.length);
  assert.equal(result.projection.value.test_scores.length,fixtureData.test.length);
  assert(result.projection.value.train_scores.flat().every(Number.isFinite));
  assert(result.projection.value.test_scores.flat().every(Number.isFinite));
  assert.equal(result.projection.value.fitted_state_unchanged,true);
  assert.equal(result.projection.value.reference_variance.value,null);
  assert.equal(result.projection.value.numerical_rank.value,null);
  assert.equal(result.limit_qualification.independent_units_certified,false);
  assert.notEqual(result.limit_qualification.status,'conditional_external');
  assert.equal(result.receipt.provider,'1.3.13+abi.2.20.0');
  assert(result.receipt.provider_calls.some(call=>call.operation==='pca_fit'));
  assert(result.receipt.provider_calls.some(call=>call.operation==='pca_transform'));
  assert(result.receipt.provider_calls.some(call=>call.operation==='pca_destroy'));
}

/** The caller supplies the actual built-app page/context and browser harness helpers. */
export async function qualifySupportBrowser({page,context,url,output,check,exported,json,screenshot}){
  const browserName=page.context().browser()?.browserType().name()??'browser';
  const outputDir=resolve(output,'f4.2',browserName);
  await mkdir(outputDir,{recursive:true});
  const captures={protocol:'domains.f4_2_support_browser_qualification.v1',browser:browserName,success:false,operations:[],exports:{},screenshots:[]};
  const fixtureData=fixture();
  // Start from a fresh reviewed import even when the caller ran F4.0/F4.1 helpers first.
  const home=page.getByRole('button',{name:/Home|Accueil/});
  if(await home.count()){
    await home.click();
    await page.locator('input[type=file]:not([webkitdirectory])').waitFor({state:'attached'});
  }
  await loadOneShot(page,fixtureData.files);
  await instrumentSupportWorkers(page);
  const initial=await json(page);
  assert.deepEqual(resultList(initial),[],'Reviewed import must not run support automatically');
  assert.equal(initial.scientific_report.scoped_operations.length,0);
  const ySentinel='987654321.125',xSentinel='87654321.875';
  assert(!JSON.stringify(initial).includes(ySentinel),'Imported Y sentinel must not enter the initial report');
  const english=page.getByRole('button',{name:'EN',exact:true});
  if(await english.count()&&await english.getAttribute('aria-pressed')!=='true')await english.click();

  // Qualify the independent raw-neighbor path and F4.1 owner score evidence first.
  let before=await page.evaluate(()=>window.__f42SupportAudit.completed.length);
  await page.getByRole('button',{name:'Train structure',exact:true}).click();
  await page.waitForFunction(n=>window.__f42SupportAudit.completed.length>n,before);
  let current=await json(page);
  const train=current.scientific_report.scoped_operations.findLast(item=>item.operation==='train_structure'&&item.status==='computed');
  assert(train,'Actual Rust/WASM train PCA receipt required');
  assert.deepEqual(train.receipt.fit_keys,train.receipt.reference_keys);
  assert.equal(train.receipt.fit_keys.length,8);

  const factor=page.getByRole('combobox',{name:'Factor',exact:true});
  await factor.selectOption('batch');
  before=await page.evaluate(()=>window.__f42SupportAudit.completed.length);
  await page.getByRole('button',{name:'Run factor association',exact:true}).click();
  await page.waitForFunction(n=>window.__f42SupportAudit.completed.length>n,before);
  current=await json(page);
  const association=current.scientific_report.factor_associations?.findLast(item=>item.status==='computed'&&item.value?.factors?.some(f=>f.factor_id==='batch'));
  assert(association,'F4.1 Methods association must be present before support');
  assert.equal(association.receipt.pca_refits,0);
  assert.equal(association.receipt.y_accessed,false);
  const rawBefore=current.scientific_report.scoped_operations.findLast(item=>item.operation==='train_reference_test_query');
  if(!rawBefore){
    before=await page.evaluate(()=>window.__f42SupportAudit.completed.length);
    await page.getByRole('button',{name:/Raw support: train reference/}).click();
    await page.waitForFunction(n=>window.__f42SupportAudit.completed.length>n,before);
    current=await json(page);
  }
  const raw=operation(current,'train_reference_test_query');
  assert(raw,'F4.0 raw-neighbor result must remain independently available');
  const f41Before=stable(current.scientific_report.factor_associations);
  const rawBeforeSupport=stable(current.scientific_report.scoped_operations.filter(item=>item.operation==='train_reference_test_query'));
  captures.operations.push({operation:'train_structure',status:train.status,receipt:train.receipt},
    {operation:'factor_association',status:association.status,receipt:association.receipt},
    {operation:'train_reference_test_query',status:raw.status,receipt:raw.receipt});

  await page.locator('#train-fitted-support').scrollIntoViewIfNeeded();
  const supportInputs=page.locator('#train-fitted-support input[type=number]');
  assert.equal(await supportInputs.count(),4,'Projection and monitor parameter controls are expected');
  await completedSupport(page);
  current=await json(page);
  let result=latest(current);
  assertSafeResult(current,result,fixtureData);
  assert.equal(result.projection.value.train_scores[0].length,2);
  assert.equal(result.projection.value.test_scores[0].length,2);
  assert.equal(result.monitoring.status,'computed');
  const monitoring=result.monitoring.value;
  for(const [key,count] of [['reference_t2',8],['reference_q',8],['monitored_t2',2],['monitored_q',2]]){
    assert.equal(monitoring[key].length,count,`Methods owner monitoring output ${key} must retain its population`);
    assert(monitoring[key].every(value=>value===null||Number.isFinite(value)));
  }
  assert.equal(result.monitoring.value.reference_protocol,'Methods statsPcaMonitor; out-of-fold row-index-modulo reference, separate full-reference PCA for query');
  assert.equal(stable(current.scientific_report.factor_associations),f41Before,'F4.2 must preserve F4.1 score association evidence exactly');
  assert.equal(stable(current.scientific_report.scoped_operations.filter(item=>item.operation==='train_reference_test_query')),rawBeforeSupport,
    'Raw F4.0 neighbors remain independent and unchanged');
  assert(!JSON.stringify(result).includes(ySentinel));
  assert(!JSON.stringify(result).includes(xSentinel));
  captures.operations.push({operation:'train_fitted_support',status:result.status,parameters:result.receipt.parameters,
    projection:result.projection,monitoring:result.monitoring,limit_qualification:result.limit_qualification,
    dependence:result.dependence,receipt:result.receipt});
  check('F4.2 executes actual Methods train-only projection and separate monitor; preserves F4.0/F4.1 evidence',
    {fit_rows:result.receipt.fit_keys.length,test_rows:result.receipt.query_keys.length,projection_components:result.projection.value.components,
      monitor_status:result.monitoring.status,fit_state_sha256:result.projection.value.fit_state_sha256});
  // Keep evidence focused: the complete tables/receipts are preserved in exports.
  // Capturing the whole growing history duplicates those long tables as PNGs.
  await screenshot(page,`${browserName}-f4.2-support-controls-en`,false,'#train-fitted-support form');
  await screenshot(page,`${browserName}-f4.2-support-results-en`,false,'#train-fitted-support [id="train-fitted-support-1-projection"]');
  captures.screenshots.push(`${browserName}-f4.2-support-controls-en`,`${browserName}-f4.2-support-results-en`);
  await auditAccessibility(page,output,`${browserName}-f4.2-support-en`,check);

  // One returned component is presented as one-dimensional; no synthetic PC2.
  await supportInputs.nth(0).fill('1');
  await completedSupport(page);
  current=await json(page);result=latest(current);
  assert.equal(result.projection.status,'computed');
  assert.equal(result.projection.value.train_scores[0].length,1);
  assert.equal(result.projection.value.test_scores[0].length,1);
  assert.deepEqual(result.projection.value.display_components,[0]);
  assert.equal(result.projection.value.numerical_rank.value,null);
  assert.equal(resultList(current).length,2,'Each parameterized run appends a distinct support result');
  const scoreFigure=current.presentation?.figures?.find(figure=>figure.id==='train-fitted-support-2-projection');
  assert.equal(scoreFigure?.kind,'scores1d','One component must not fabricate a measured PC2');
  captures.operations.push({operation:'train_fitted_support_one_component',status:result.status,receipt:result.receipt,
    components:result.projection.value.components,display_components:result.projection.value.display_components});
  check('F4.2 one-component owner output remains one-dimensional and appends a separate result');

  // Browser form constraint is a local refusal: no worker operation and no history loss.
  const operationCount=await page.evaluate(()=>window.__f42SupportAudit.operations.length),historyBeforeInvalid=stable(resultList(current));
  await supportInputs.nth(2).fill('1');
  await page.getByRole('button',{name:/Compute train reference and project test/}).click();
  assert.equal(await supportInputs.nth(2).evaluate(input=>input.validity.valid),false);
  assert.equal(await page.evaluate(()=>window.__f42SupportAudit.operations.length),operationCount);
  const afterInvalid=await json(page);
  assert.equal(stable(resultList(afterInvalid)),historyBeforeInvalid,'Invalid fold count must preserve support history');
  assert.equal(latest(afterInvalid).projection.status,'computed','Local parameter refusal must preserve the prior valid projection');
  assert.equal(afterInvalid.scientific_report.inventory.loaded.partitions.find(p=>p.name==='train').rows,8);
  await supportInputs.nth(2).fill('5');
  check('Invalid fold count is refused by the local form without worker execution or loss of imported data/history');

  // Language/export selection are presentation choices and cannot mutate evidence or permissions.
  const scientificBeforeLanguage=stable({support:resultList(afterInvalid),factors:afterInvalid.scientific_report.factor_associations,
    scoped:afterInvalid.scientific_report.scoped_operations});
  const workersBeforeLanguage=await page.evaluate(()=>window.__f42SupportAudit.operations.length);
  await page.getByRole('button',{name:'FR',exact:true}).click();
  assert.equal(await page.locator('html').getAttribute('lang'),'fr');
  await page.locator('#train-fitted-support').scrollIntoViewIfNeeded();
  assert.match(await page.locator('#train-fitted-support').innerText(),/Comment les observations/);
  await screenshot(page,`${browserName}-f4.2-support-results-fr`,false,'#train-fitted-support [id="train-fitted-support-1-projection"]');
  captures.screenshots.push(`${browserName}-f4.2-support-results-fr`);
  await auditAccessibility(page,output,`${browserName}-f4.2-support-fr`,check);
  await page.getByRole('button',{name:'EN',exact:true}).click();
  const afterLanguage=await json(page);
  assert.equal(stable({support:resultList(afterLanguage),factors:afterLanguage.scientific_report.factor_associations,
    scoped:afterLanguage.scientific_report.scoped_operations}),scientificBeforeLanguage);
  assert.equal(await page.evaluate(()=>window.__f42SupportAudit.operations.length),workersBeforeLanguage,
    'Language changes and report reads must not execute scientific operations');
  assert.deepEqual(afterLanguage.provenance.factor_color_export,{status:'unavailable',reason:'OBSERVATION_LEVEL_FACTOR_COLORS_NOT_AUTHORIZED'},'F4.2 does not grant the separate factor-color export permission');
  const colorGrant=page.getByRole('checkbox',{name:/Authorize this factor.s observation-level colors in this report export/});
  if(await colorGrant.count())assert.equal(await colorGrant.isChecked(),false,'Existing separate M-color authorization remains unchecked');

  const workersBeforeExport=await page.evaluate(()=>window.__f42SupportAudit.operations.length);
  await page.getByRole('button',{name:'Select all available',exact:true}).click();
  const html=await exported(page,'html'),markdown=await exported(page,'markdown'),report=await json(page),jsonText=JSON.stringify(report);
  assert.equal(report.export_selection?.provenance?.action,'select_all');
  assert.equal(report.raw_x_included,false);
  assert.deepEqual(resultList(report),resultList(afterLanguage),'Selecting report sections must preserve exact support outputs');
  const ownerDigest=resultList(report)[0].evidence_sha256;
  assert.equal(typeof ownerDigest,'string');
  assert(html.includes(ownerDigest)&&markdown.includes(ownerDigest)&&jsonText.includes(ownerDigest),
    'All formats must retain the same owner evidence digest');
  assert.deepEqual(report.provenance.factor_color_export,{status:'unavailable',reason:'OBSERVATION_LEVEL_FACTOR_COLORS_NOT_AUTHORIZED'},'Select-all does not authorize M observation coloring');
  if(await colorGrant.count())assert.equal(await colorGrant.isChecked(),false);
  assert.equal(await page.evaluate(()=>window.__f42SupportAudit.operations.length),workersBeforeExport,
    'Report selection/export must not trigger a scientific operation');
  assert(![html,markdown,jsonText].some(text=>text.includes('factor-level-')||text.includes('factor-bin-')),
    'No observation-level M color mapping is exported without its separate permission');
  assert(![html,markdown,jsonText].some(text=>text.includes(ySentinel)||text.includes(xSentinel)),'Report exports must not contain raw X/Y sentinels');
  for(const [name,text]of [['html',html],['markdown',markdown],['json',jsonText]]){
    await writeFile(resolve(outputDir,`train-fitted-support.${name==='markdown'?'md':name}`),name==='json'?JSON.stringify(report,null,2)+'\n':text);
    captures.exports[name]={bytes:Buffer.byteLength(text),support_results:resultList(report).length,
      contains_raw_x_y_sentinel:false,contains_unauthorized_factor_color:false};
  }
  const supportEvidence=report.evidence.find(item=>item.id==='train-fitted-support-1');
  assert.deepEqual(supportEvidence?.value,resultList(report)[0],'Export retains exact original owner support evidence');
  assert.deepEqual(supportEvidence.value.receipt,resultList(report)[0].receipt);
  check('F4.2 HTML/Markdown/JSON preserve exact owner receipts, omit raw sentinels, and leave M-color export permission separate');

  if(browserName==='chromium'){
    const printPage=await context.newPage();
    try{
      await printPage.setContent(html,{waitUntil:'load'});
      await printPage.pdf({path:resolve(outputDir,'train-fitted-support-a4.pdf'),format:'A4',printBackground:true});
      await printPage.pdf({path:resolve(outputDir,'train-fitted-support-letter.pdf'),format:'Letter',printBackground:true});
      captures.exports.print=['train-fitted-support-a4.pdf','train-fitted-support-letter.pdf'];
    }finally{await printPage.close();}
  }else captures.exports.print='not_applicable: PDF generation/review is Chromium-only';

  // Cancellation and reset terminate an actual worker; delayed post is only scheduling instrumentation.
  await page.evaluate(()=>{window.__f42SupportAudit.delayNext=true;});
  const terminatedBeforeCancel=await page.evaluate(()=>window.__f42SupportAudit.terminated);
  await page.getByRole('button',{name:/Compute train reference and project test/}).click();
  await page.waitForFunction(()=>window.__f42SupportAudit.delayed===true);
  await page.getByRole('button',{name:'Cancel analysis',exact:true}).click();
  await page.waitForFunction(n=>window.__f42SupportAudit.terminated>n,terminatedBeforeCancel);
  await page.waitForFunction(()=>window.__f42SupportAudit.delayReleased===true);
  current=await json(page);
  assert.equal(resultList(current).length,2,'A cancelled support operation cannot append stale evidence');
  assert.equal(current.scientific_report.inventory.loaded.partitions.find(p=>p.name==='train').rows,8);
  assert.equal(stable(current.scientific_report.factor_associations),f41Before);
  assert.equal(stable(current.scientific_report.scoped_operations.filter(item=>item.operation==='train_reference_test_query')),rawBeforeSupport);
  check('Cancelling a pending real support worker leaves prior support history intact');

  // Reset to a changed reviewed import while an actual worker request is pending.
  await page.evaluate(()=>{window.__f42SupportAudit.delayReleased=false;window.__f42SupportAudit.delayed=false;window.__f42SupportAudit.delayNext=true;});
  const terminatedBeforeReset=await page.evaluate(()=>window.__f42SupportAudit.terminated);
  await page.getByRole('button',{name:/Compute train reference and project test/}).click();
  await page.waitForFunction(()=>window.__f42SupportAudit.delayed===true);
  const resetButton=page.getByRole('button',{name:/Home|Accueil/});
  await resetButton.click();
  await page.waitForFunction(n=>window.__f42SupportAudit.terminated>n,terminatedBeforeReset);
  await page.locator('input[type=file]:not([webkitdirectory])').waitFor({state:'attached'});
  await page.waitForFunction(()=>window.__f42SupportAudit.delayReleased===true);
  const secondFixture=fixture(),configFile=secondFixture.files.find(file=>file.name==='f4-scoped.nirs4all.json');
  const config=JSON.parse(configFile.buffer.toString('utf8'));config.name='F4.2 support reset identity';configFile.buffer=Buffer.from(JSON.stringify(config));
  await loadOneShot(page,secondFixture.files);
  current=await json(page);
  assert.deepEqual(resultList(current),[],'New dataset identity must not inherit stale support results');
  assert.deepEqual(current.scientific_report.factor_associations??[],[],'New dataset identity must clear F4.1 results');
  assert.deepEqual(current.scientific_report.scoped_operations,[],'New dataset identity must clear F4.0 receipts');
  assert.equal(current.pca,null);
  captures.reset={new_content_identity:true,support_history_cleared:true,f41_history_cleared:true,f40_history_cleared:true,stale_worker_ignored:true};
  check('Reset during a pending support worker clears dataset-bound histories and ignores the stale reply');
  captures.success=true;
  await writeFile(resolve(outputDir,'support-browser.json'),JSON.stringify(captures,null,2)+'\n');
}
