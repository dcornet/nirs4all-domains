/** Production-browser import qualification: real IO workers, synthetic local files. */
import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {oneShotFixtureCases} from './one-shot-fixtures.mjs';
import {auditAccessibility} from './ux-browser.mjs';

const file = (name,text) => ({name,mimeType:name.endsWith('.json')?'application/json':name.endsWith('.jdx')?'chemical/x-jcamp-dx':'text/csv',buffer:Buffer.from(text)});
const files = scenario => scenario.files.map(item=>file(item.name,item.text));
const combined = {
 id:'combined-xy-m',expected:'loaded',files:[{name:'combined.csv',text:'id,2000,1000,yield,batch\na,1,2,10,A\nb,3,4,,B\nc,5,6,30,'},
 {name:'combined.nirs4all.json',text:JSON.stringify({schema_version:1,name:'Combined local dataset',sources:[{id:'combined',input:'combined.csv',role:'mixed',key:'id',columns:{features:['2000','1000'],targets:['yield'],metadata:['id','batch']},params:{delimiter:',',has_header:true}}],metadata_declarations:{combined__batch:{role:'factor',derived_from_target:true}}})}],
};
const inferredSingleFiles = [
 {id:'inferred-single-csv-x-y',expected:'loaded',files:[{name:'measurements.csv',text:'id,2000,1000,yield\na,1,2,10\nb,3,4,20\nc,5,6,30'}]},
 {id:'inferred-single-csv-x-y-m',expected:'loaded',files:[{name:'measurements.csv',text:'id,2000,1000,yield,batch\na,1,2,10,A\nb,3,4,20,B\nc,5,6,30,A'}]},
];
const multipleMetadata = {id:'explicit-multiple-m-sources',expected:'loaded',files:[
 {name:'train_x.csv',text:'id,2000,1000\na,1,2\nb,3,4\nc,5,6'},
 {name:'batch.csv',text:'id,batch\nc,C\na,A\nb,B'},
 {name:'instrument.csv',text:'id,instrument\nb,I2\nc,I3\na,I1'},
 {name:'multiple-m.nirs4all.json',text:JSON.stringify({schema_version:1,sources:[
  {id:'X',input:'train_x.csv',role:'features',key:'id',partition:'train',columns:{features:['2000','1000'],metadata:['id']},params:{delimiter:',',has_header:true}},
  ...[['M_batch','batch.csv','batch'],['M_instrument','instrument.csv','instrument']].map(([id,input,column])=>({id,input,role:'metadata',key:'id',partition:'train',columns:{metadata:['id',column]},params:{delimiter:',',has_header:true},join:{left:id,right:'X',left_on:'id',right_on:'id',cardinality:'1:1',coverage:'complete'}})),
 ]})},
]};
const additionalBoundaryCases = [
 {id:'all-empty-x-band-preserved',expected:'loaded',files:[{name:'train_x.csv',text:'id,2000,1000\na,1,\nb,3,\nc,5,'}]},
 {id:'partial-m-manifest-allow-missing',expected:'loaded',files:[
  {name:'train_x.csv',text:'id,2000,1000\na,1,2\nb,3,4\nc,5,6'},
  {name:'train_m.csv',text:'id,batch\na,A\nc,C'},
  {name:'partial-m.nirs4all.json',text:JSON.stringify({schema_version:1,sources:[
   {id:'X',input:'train_x.csv',role:'features',partition:'train',key:'id',columns:{features:['2000','1000'],metadata:['id']},params:{delimiter:',',has_header:true}},
   {id:'M',input:'train_m.csv',role:'metadata',partition:'train',key:'id',columns:{metadata:['id','batch']},params:{delimiter:',',has_header:true},join:{left:'M',right:'X',left_on:'id',right_on:'id',cardinality:'1:1',coverage:'warn'}},
  ]})},
 ]},
 {id:'formats-jcamp-dx-real-decode',expected:'loaded',files:[{name:'synthetic.jdx',text:[
  '##TITLE=Synthetic one-shot JCAMP fixture','##JCAMP-DX=5.00','##DATA TYPE=INFRARED SPECTRUM',
  '##XUNITS=1/CM','##YUNITS=ABSORBANCE','##FIRSTX=2000','##LASTX=1000','##NPOINTS=2',
  '##XFACTOR=1','##YFACTOR=1','##XYDATA=(X++(Y..Y))','2000 1 2','##END=','',
 ].join('\n')}]},
];

export async function qualifyOneShotBrowser({page,context,url,output,check,exported,json,screenshot}) {
 const out=resolve(output,'one-shot');await mkdir(out,{recursive:true});
 const receipt={protocol:'domains.one_shot_browser.v1',browser:context.browser()?.browserType().name(),version:context.browser()?.version(),cases:[],success:false,scope:'Synthetic dataset import through production IO/Formats workers; no automatic numerical diagnostic, durable dataset persistence or external data transmission.'};
 const network=[];const origin=new URL(url).origin;
 const auditRequest=request=>{if(/^https?:/.test(request.url())&&(new URL(request.url()).origin!==origin||!['GET','HEAD'].includes(request.method())))network.push({method:request.method(),same_origin:new URL(request.url()).origin===origin});};
 context.on('request',auditRequest);
 await context.addInitScript(()=>{
  const Native=window.Worker;window.__oneShotBrowser={workers:[],operations:[],completed:[],lifecycle:[],gestures:{file_selection:0,folder_selection:0,correction_submit:0,settings_apply:0}};
  document.addEventListener('change',event=>{const input=event.target;if(input instanceof HTMLInputElement&&input.type==='file'&&input.files?.length){window.__oneShotBrowser.gestures.file_selection++;if(input.hasAttribute('webkitdirectory'))window.__oneShotBrowser.gestures.folder_selection++;}},true);
  document.addEventListener('click',event=>{const button=event.target instanceof Element?event.target.closest('button'):null;if(!button)return;if(/^(Apply corrections|Appliquer les corrections)$/.test(button.textContent?.trim()??''))window.__oneShotBrowser.gestures.correction_submit++;if(/^(Apply changes|Appliquer les modifications)$/.test(button.textContent?.trim()??''))window.__oneShotBrowser.gestures.settings_apply++;},true);
  window.Worker=class extends Native {
   constructor(...args){super(...args);this.audit={terminated:false};window.__oneShotBrowser.workers.push(this.audit);this.addEventListener('message',event=>{if(event.data?.lifecycle_event)window.__oneShotBrowser.lifecycle.push({event:event.data.lifecycle_event,component:event.data.component});if(event.data&&!event.data.stage&&!event.data.lifecycle_event)window.__oneShotBrowser.completed.push(event.data.ok===false?'error':'reply');});}
   postMessage(message,transfer){window.__oneShotBrowser.operations.push(String(message?.operation??'unknown'));return super.postMessage(message,transfer??[]);}
   terminate(){this.audit.terminated=true;return super.terminate();}
  };
 });
 const home=async(locale='en')=>{await page.goto(url,{waitUntil:'domcontentloaded'});await page.getByRole('button',{name:locale.toUpperCase(),exact:true}).click();await page.getByRole('heading',{name:locale==='fr'?'Charger mon dataset':'Load my dataset',exact:true}).waitFor();};
 const ops=()=>page.evaluate(()=>window.__oneShotBrowser.operations);
 const settled=async()=>{await page.waitForFunction(()=>!document.querySelector('.run-banner')&&Boolean(document.querySelector('.dataset-loaded-summary,.import-resolution,.technical-diagnostic[role="alert"],.alert')),{},{timeout:120000});const error=page.locator('.technical-diagnostic[role="alert"],.alert');assert.equal(await error.count(),0,await error.count()?await error.first().textContent():'Import has no runtime failure');};
 const summary=()=>page.locator('.dataset-loaded-summary');
 const facts=()=>summary().locator('dl').evaluate(node=>Object.fromEntries(Array.from(node.children).map(row=>[row.querySelector('dt')?.textContent,row.querySelector('dd')?.textContent])));
 const snapshot=async id=>{const gestures=await page.evaluate(()=>window.__oneShotBrowser.gestures);return {id,operations:await ops(),worker_count:await page.evaluate(()=>window.__oneShotBrowser.workers.length),facts:await summary().count()?await facts():null,pending_questions:await page.locator('.import-resolution .import-issue').count(),gestures,one_load_gesture:gestures.file_selection===1&&gestures.correction_submit===0&&gestures.settings_apply===0};};
 const submit=async(scenario,{locale='en',assertions=true}={})=>{
  await home(locale);
  await page.locator('.import-card input[type=file]').first().setInputFiles(files(scenario));
  await settled();
  assert.deepEqual(await ops(),['prepare_import','assemble_import'],`${scenario.id}: import runs no scientific operation`);
  assert.equal(await page.getByRole('checkbox',{name:/I confirm the displayed roles|Je confirme les rôles/}).count(),0);
  if(scenario.expected==='loaded') {await summary().waitFor();assert.equal(await page.locator('.import-resolution').count(),0,`${scenario.id}: no required question`);}
  else await page.locator('.import-resolution').waitFor();
  const record={...await snapshot(scenario.id),outcome:scenario.expected};
  assert.equal(record.worker_count,2,`${scenario.id}: both import workers are single-use`);
  assert.deepEqual(record.gestures,{file_selection:1,folder_selection:0,correction_submit:0,settings_apply:0},`${scenario.id}: exactly one actual file-selection event, with no correction or settings submission`);
  if(assertions){receipt.cases.push(record);check(`One-shot browser: ${scenario.id}`,{operations:record.operations,one_load_gesture:true});}
  return record;
 };
 try {
  await home();await auditAccessibility(page,output,'one-shot-landing-en',check);await screenshot(page,'one-shot-landing-en',false);
  const multiYMetadata={id:'keyed-multiple-y-and-m',expected:'loaded',files:[...oneShotFixtureCases.find(item=>item.id==='mixed-y-numeric-categorical').files,oneShotFixtureCases.find(item=>item.id==='x-m').files[1]]};
  for(const scenario of [...oneShotFixtureCases,...inferredSingleFiles,combined,multiYMetadata,multipleMetadata,...additionalBoundaryCases]) {
   const record=await submit(scenario);
   if(scenario.id==='x-only'){assert.equal(record.facts.Observations,'3');assert.equal(record.facts['Spectral variables'],'2');await auditAccessibility(page,output,'one-shot-loaded-en',check);await screenshot(page,'one-shot-loaded-en',false);}
   if(scenario.id==='keyed-train-test'){assert.equal(record.facts.Observations,'5');assert.equal(record.facts.train,'3');assert.equal(record.facts.test,'2');}
   if(scenario.id==='mixed-y-numeric-categorical'){assert.equal(record.facts['Y targets'],'2');await summary().locator('summary').click();const text=await summary().textContent();assert.match(text,/yield · numeric/);assert.match(text,/class · categorical/);}
   if(scenario.id==='all-missing-y'){assert.equal(record.facts.Observations,'2');assert.equal(record.facts['Y targets'],'1');await summary().locator('summary').click();assert.match(await summary().textContent(),/yield.*missing: 2 \/ 2/);}
   if(scenario.id==='all-missing-m'){assert.equal(record.facts.Observations,'3');await summary().locator('summary').click();assert.match(await summary().textContent(),/batch.*missing: 3 \/ 3/);}
   if(['partial-m-inferred-allow-missing','partial-m-manifest-allow-missing'].includes(scenario.id)){assert.equal(record.facts.Observations,'3');await summary().locator('summary').click();assert.match(await summary().textContent(),/batch.*missing: 1 \/ 3/);}
   if(scenario.id==='all-empty-x-band-preserved'){assert.equal(record.facts.Observations,'3');assert.equal(record.facts['Spectral variables'],'2');assert.match(await summary().textContent(),/Missing X values: 3/);}
   if(scenario.id==='formats-jcamp-dx-real-decode'){assert.equal(record.facts.Observations,'1');assert.equal(record.facts['Spectral variables'],'2');const lifecycle=await page.evaluate(()=>window.__oneShotBrowser.lifecycle);assert(lifecycle.some(item=>item.event==='FORMATS_RUNTIME_READY'&&item.component==='formats'),'JCAMP import must load the actual Formats WASM runtime');record.formats_lifecycle=lifecycle.filter(item=>item.component==='formats');}
   if(scenario.id==='na-empty'){assert.equal(record.facts.Observations,'3');assert.match(await summary().textContent(),/Missing X values: 1/);}
   if(scenario.id==='unassociated-y-no-key'){assert.equal(record.facts['Y targets'],'0');assert.match(await summary().textContent(),/restrictions identified.*Unresolved sources: 1/);}
   if(scenario.id.startsWith('two-x-')) assert.match(await page.locator('.import-resolution').textContent(),/MULTISOURCE_SELECTION_REQUIRED_NO_IMPLICIT_FUSION/);
   if(scenario.id==='two-x-same-axis'){
    await page.locator('.import-resolution .import-correction select').nth(1).selectOption('ignored');await page.getByRole('button',{name:'Apply corrections',exact:true}).click();await summary().waitFor();assert.equal((await facts()).Observations,'3');assert.equal((await facts())['Spectral variables'],'2');assert.deepEqual(await ops(),['prepare_import','assemble_import','assemble_import']);receipt.cases.push({...await snapshot('two-x-explicit-selection'),one_load_gesture:false,correction_gestures:2});
   }
   if(scenario.id==='keyed-multiple-y-and-m'){assert.equal(record.facts['Y targets'],'2');assert.equal(record.facts.Observations,'3');}
   if(scenario.id.startsWith('inferred-single-csv-')){assert.equal(record.facts['Y targets'],'1','Single CSV IO inference must identify the target without a manifest');assert.equal(record.facts['Spectral variables'],'2');if(scenario.id.endsWith('-m')){await summary().locator('summary').click();assert.match(await summary().textContent(),/M · batch · missing: 0 \/ 3/);}}
   if(scenario.id==='explicit-multiple-m-sources'){await summary().locator('summary').click();const text=await summary().textContent();assert.match(text,/M · (?:M_batch__)?batch · missing: 0 \/ 3/);assert.match(text,/M · (?:M_instrument__)?instrument · missing: 0 \/ 3/);}
   if(scenario.id==='combined-xy-m'){await page.locator('.data-settings>summary').click();await page.getByText('Metadata origin and roles',{exact:true}).click();assert.equal(await page.getByRole('combobox',{name:'batch derived from Y',exact:true}).inputValue(),'true');}
   if(scenario.id==='explicit-delimiter-correction') {
    const labels=await page.locator('.import-resolution .import-correction label').allTextContents();
    assert(labels.some(text=>text.includes('Delimiter')),'Delimiter failure offers a targeted delimiter control');
    await page.locator('.import-resolution .import-correction select').first().selectOption(';');
    await page.getByRole('button',{name:'Apply corrections',exact:true}).click();
    await summary().waitFor();assert.equal((await facts()).Observations,'3');
    assert.deepEqual(await ops(),['prepare_import','assemble_import','assemble_import'],'Recovery uses session files, not a new file prompt');
    receipt.cases.push({...await snapshot('delimiter-session-recovery'),one_load_gesture:false,correction_gestures:2});
   }
  }
  // Native random-split declarations are refused before any assembly request.
  await home();await page.locator('.import-card input[type=file]:not([webkitdirectory])').setInputFiles([
   file('train_x.csv','id,2000,1000\na,1,2\nb,3,4\nc,5,6'),
   file('random.nirs4all.json',JSON.stringify({schema_version:1,partitions:{by:'random',test_size:0.25},sources:[{id:'X',input:'train_x.csv',role:'features',key:'id',params:{delimiter:',',has_header:true}}]})),
  ]);
  const splitRefusal=page.locator('.technical-diagnostic[role="alert"],.alert').first();await splitRefusal.waitFor();assert.match(await splitRefusal.textContent(),/\bIMPLICIT_PARTITION_GENERATION_NOT_ADMITTED\b/);assert.equal(await summary().count(),0);assert.deepEqual(await ops(),['prepare_import']);receipt.cases.push({...await snapshot('native-random-partition-refused-before-assembly'),refusal_code:'IMPLICIT_PARTITION_GENERATION_NOT_ADMITTED'});
  await submit(oneShotFixtureCases[0],{locale:'fr',assertions:false});await auditAccessibility(page,output,'one-shot-loaded-fr',check);await screenshot(page,'one-shot-loaded-fr',false);receipt.cases.push(await snapshot('french-one-shot'));
  // A real browser directory input retains relative paths, including all train/test files.
  const directoryCase=oneShotFixtureCases.find(item=>item.id==='keyed-train-test');
  const directoryNames={'train_x.csv':'Xcal.csv','train_y.csv':'Ycal.csv','test_x.csv':'Xtest.csv','test_y.csv':'Ytest.csv'};
  for(const directoryName of ['dataset-submission-cal','folder-keyword-submission']) {
   await home();const directory=resolve(out,directoryName);await mkdir(directory,{recursive:true});
   for(const item of directoryCase.files)await writeFile(resolve(directory,directoryNames[item.name]),item.text);
   await page.locator('input[webkitdirectory]').setInputFiles(directory);await settled();await summary().waitFor();assert.equal((await facts()).Observations,'5');assert.equal((await facts()).train,'3');assert.equal((await facts()).test,'2');receipt.cases.push(await snapshot(`directory-Xcal-Ycal-Xtest-Ytest-${directoryName}`));
  }
  const inventory=await json(page);assert.equal(inventory.scientific_report.scoped_operations.length,0);assert.equal(inventory.pca,null);
  // Explicit identity audit supplies dependent evidence to invalidate, without fitting a model.
  await page.getByRole('button',{name:'Identity audit (no X)',exact:true}).click();await settled();
  const audited=await json(page);assert.equal(audited.scientific_report.scoped_operations.length,1);
  // A successful technical edit creates fresh content provenance and clears operations.
  await page.locator('.data-settings>summary').click();const oldHash=await page.locator('.hash').first().textContent();
  const editor=page.locator('.dataset-import');
  const datasetName=editor.getByRole('textbox',{name:'Dataset name',exact:true});
  await datasetName.fill('Renamed local dataset');
  await editor.getByRole('button',{name:'Apply changes',exact:true}).click();
  await page.locator('#workspace-title').filter({hasText:'Renamed local dataset'}).waitFor();
  assert.notEqual(await page.locator('.hash').first().textContent(),oldHash,'Assembly setting changes receive new content provenance');
  assert.deepEqual(await ops(),['prepare_import','assemble_import','scoped','assemble_import']);assert.equal((await json(page)).scientific_report.scoped_operations.length,0,'Old diagnostic evidence is invalidated after assembly edits');receipt.cases.push(await snapshot('post-load-settings-revalidated'));
  // Failed replacement keeps the validated dataset/settings instead of committing a candidate.
  await page.locator('.replacement-import>summary').click();const validTitle=await page.locator('#workspace-title').textContent();
  await page.locator('.replacement-import input[type=file]').first().setInputFiles(files(oneShotFixtureCases.find(item=>item.id==='two-x-same-axis')));
  await page.locator('.import-resolution').waitFor();assert.equal(await page.locator('#workspace-title').textContent(),validTitle);receipt.cases.push({...await snapshot('failed-replacement-preserves-valid-dataset'),one_load_gesture:true});
  await page.getByRole('button',{name:'Dismiss corrections',exact:true}).click();assert.equal(await page.locator('.import-resolution').count(),0);assert.equal(await page.locator('#workspace-title').textContent(),validTitle);
  // Hold only the real worker module's HTTP response to make cancellation deterministic.
  const heldWorker=async()=>{
   let release,seen;const gate=new Promise(done=>{release=done;}),observed=new Promise(done=>{seen=done;});let first=true;
   const pattern=/\/assets\/worker-[^/]+\.js$/;
   const route=async request=>{if(first){first=false;seen();await gate;}try{await request.continue();}catch{/* cancellation can abort the held asset */}};
   await context.route(pattern,route);return {observed,release,close:()=>context.unroute(pattern,route)};
  };
  await home();let held=await heldWorker();await page.locator('.import-card input[type=file]:not([webkitdirectory])').setInputFiles(files(oneShotFixtureCases[0]));await held.observed;
  await page.locator('.run-banner').getByRole('button',{name:'Cancel analysis',exact:true}).click();held.release();await held.close();
  assert.equal(await summary().count(),0);assert(await page.evaluate(()=>window.__oneShotBrowser.workers.some(worker=>worker.terminated)));receipt.cases.push({id:'cancel-in-flight-import',terminated:true,loaded:false});
  await home();held=await heldWorker();await page.locator('.import-card input[type=file]:not([webkitdirectory])').setInputFiles(files(oneShotFixtureCases[0]));await held.observed;
  await page.locator('.import-card input[type=file]:not([webkitdirectory])').setInputFiles([file('newer_x.csv','2000,1000\n1,2\n3,4\n5,6\n7,8')]);held.release();await held.close();await settled();
  assert.equal((await facts()).Observations,'4','Latest user submission wins over a cancelled older import');assert(await page.evaluate(()=>window.__oneShotBrowser.workers.some(worker=>worker.terminated)));receipt.cases.push({...await snapshot('new-dataset-supersedes-in-flight-import'),one_load_gesture:false,load_gestures:2});
  // The full shared editor is shown before assembly only when explicitly requested.
  await home();await page.locator('.import-settings-before>summary').click();const optionalSettings=page.getByRole('checkbox',{name:'Open advanced settings after IO identifies the sources',exact:true});
  assert.equal(await optionalSettings.isChecked(),false);await optionalSettings.check();
  await page.locator('.import-card input[type=file]:not([webkitdirectory])').setInputFiles(files(oneShotFixtureCases[0]));
  await page.getByRole('heading',{name:'Data import settings',exact:true}).waitFor();
  assert.deepEqual(await ops(),['prepare_import'],'Explicit pre-import settings pause after IO identifies sources, before assembly');assert.equal(await summary().count(),0);assert.equal(await page.locator('.import-resolution .import-issue').count(),0);
  await page.locator('.import-resolution').getByRole('button',{name:'Apply changes',exact:true}).click();await settled();await summary().waitFor();assert.equal((await facts()).Observations,'3');assert.deepEqual(await ops(),['prepare_import','assemble_import']);
  receipt.cases.push({...await snapshot('explicit-optional-pre-import-settings'),one_load_gesture:false});
  const operationBeforeHome=(await ops()).length;await page.locator('.brand').click();await page.getByRole('heading',{name:'Load my dataset',exact:true}).waitFor();await page.locator('.import-settings-before>summary').click();assert.equal(await optionalSettings.isChecked(),false,'Home resets optional pre-import review intent');
  await page.locator('.import-card input[type=file]:not([webkitdirectory])').setInputFiles(files(oneShotFixtureCases[0]));await settled();await summary().waitFor();assert.equal(await page.locator('.import-resolution').count(),0);assert.deepEqual((await ops()).slice(operationBeforeHome),['prepare_import','assemble_import']);receipt.cases.push({...await snapshot('home-restores-default-one-shot'),operations_since_home_reset:(await ops()).slice(operationBeforeHome)});
  // A saved report remains a report, with no import workers and no dataset summary.
  await home();const saved=await readFile(new URL('../public/examples/tablet.unknown.saved.json',import.meta.url));
  await page.locator('.import-card input[type=file]').first().setInputFiles({name:'saved-report.json',mimeType:'application/json',buffer:saved});
  await page.locator('.workspace-summary').waitFor();assert.equal(await summary().count(),0);assert.deepEqual(await ops(),[]);receipt.cases.push({id:'saved-report-distinct',operations:[],dataset_summary:false});
  assert.deepEqual(network,[],'No external or non-GET request carries local data');receipt.network_violations=network;
  receipt.success=true;check('One-shot production-browser qualification complete',{cases:receipt.cases.length});
 } finally {context.off('request',auditRequest);await writeFile(resolve(out,'receipt.json'),JSON.stringify(receipt,null,2));}
 return receipt;
}
