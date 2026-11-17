/** Actual browser qualification of operation-scoped X/Y/M import and receipts. */
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';

const ySentinel='987654321.125';
const xSentinel='87654321.875';
function fixture(){
  const train=Array.from({length:8},(_,i)=>({id:`tr-${i}`,x:i===2?[3,4]:[i+1,(i+1)*1.5],y:10+i,specimen:`spec-tr-${i}`,group:i<4?'group-a':'group-b',reference:i<4?'ref-a':'ref-b',batch:i<4?'batch-a':'batch-b'}));
  const test=[{id:'te-0',x:[3,4],y:Number(ySentinel),specimen:'spec-test-duplicate',group:'group-a',reference:'ref-a',batch:'batch-test'},
    {id:'te-1',x:[Number(xSentinel),Number(xSentinel)+1],y:Number(ySentinel)+1,specimen:'spec-test-1',group:'group-c',reference:'ref-c',batch:'batch-test'}];
  const predict=[{id:'pr-0',x:[21,34],y:Number(ySentinel)+2,specimen:'spec-predict',group:'group-p',reference:'ref-p',batch:'batch-predict'}];
  const sources=[],files=[];
  const csv=(headers,rows)=>[headers.join(','),...rows.map(row=>row.join(','))].join('\n')+'\n';
  const params={delimiter:',',has_header:true};
  const declarations={};
  for(const [part,rows] of [['train',train],['test',test],['predict',predict]]){
    const X=`X_${part}`,Y=`Y_${part}`,M=`M_${part}`;
    const xs=rows.map(row=>[row.id,...row.x]);
    const ys=rows.map(row=>[row.id,String(row.y)]);
    // Reverse the M order to prove the explicit key join, never row position, binds fields.
    const ms=[...rows].reverse().map(row=>[row.id,row.specimen,row.group,row.reference,row.batch]);
    sources.push(
      {id:X,role:'features',input:`${X}.csv`,partition:part,key:'id',columns:{metadata:['id'],features:['1000','1100']},params},
      {id:Y,role:'targets',input:`${Y}.csv`,partition:part,key:'id',join:{left:Y,right:X,left_on:'id',right_on:'id',cardinality:'1:1',coverage:'complete'},columns:{metadata:['id'],targets:['yield']},params},
      {id:M,role:'metadata',input:`${M}.csv`,partition:part,key:'id',join:{left:M,right:X,left_on:'id',right_on:'id',cardinality:'1:1',coverage:'complete'},columns:{metadata:['id','specimen','group','reference','batch']},params},
    );
    files.push(
      {name:`${X}.csv`,mimeType:'text/csv',buffer:Buffer.from(csv(['id','1000','1100'],xs))},
      {name:`${Y}.csv`,mimeType:'text/csv',buffer:Buffer.from(csv(['id','yield'],ys))},
      {name:`${M}.csv`,mimeType:'text/csv',buffer:Buffer.from(csv(['id','specimen','group','reference','batch'],ms))},
    );
    for(const field of ['specimen','group','reference','batch']) declarations[`${M}__${field}`]={role:field==='group'?'group':field==='specimen'?'specimen':field==='reference'?'reference':'factor',derived_from_target:false};
  }
  const config={schema_version:1,name:'Synthetic F4 scoped fixture',sources,metadata_declarations:declarations,
    target_tasks:{yield:'regression'}};
  files.unshift({name:'f4-scoped.nirs4all.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(config))});
  return {files,train,test,predict};
}

const downloadText=async(page,format,exported)=>exported(page,format);
const reportJson=async(page,json)=>json(page);
const operation=(report,name,diagnostic)=>report.scientific_report.scoped_operations.find(item=>item.operation===name && (!diagnostic||item.diagnostic===diagnostic) && item.status==='computed') ?? report.scientific_report.scoped_operations.at(-1);

async function loadReviewed(page,files){
  await page.locator('input[type=file]').setInputFiles(files);
  await page.getByRole('heading',{name:'Review X / Y / M roles'}).waitFor();
  const reviewText=await page.locator('.dataset-import').innerText();
  assert.match(reviewText,/Declared partitions/);
  for(const partition of ['train','test','predict'])assert(reviewText.includes(`X_${partition}.csv: ${partition}`),`Partition role missing from review: ${partition}`);
  // The shared builder starts at Source; column controls belong to step three
  // and the currently selected source, not every file at once.
  await page.getByRole('button',{name:'3. Columns',exact:true}).click();
  for(const partition of ['train','test','predict']){
    for(const [source,roles] of [[`X_${partition}`,[['1000','x'],['1100','x'],['id','id']]],[`Y_${partition}`,[['yield','y'],['id','id']]]]){
      await page.locator('.dsb-source-card__switch').selectOption(source);
      for(const [name,role] of roles)
        assert.equal(await page.getByLabel(`${name} role`,{exact:true}).inputValue(),role,`Reviewed role missing: ${source} / ${name} / ${role}`);
    }
  }
  await page.locator('summary').filter({hasText:/^Metadata origin and roles$/}).click();
  for(const [name,role] of [['specimen','specimen'],['group','group'],['reference','reference'],['batch','factor']]){
    const selectors=page.getByLabel(`${name} metadata role`);
    assert.equal(await selectors.count(),3,`Expected one reviewed ${name} declaration per partition`);
    for(let i=0;i<3;i++)await selectors.nth(i).selectOption(role);
    const derived=page.getByLabel(`${name} derived from Y`);
    for(let i=0;i<3;i++)await derived.nth(i).selectOption('false');
  }
  await page.getByLabel('I confirm the displayed roles, join identifiers and partitions.').check();
  await page.getByRole('button',{name:'Import reviewed data',exact:true}).click();
  await page.getByRole('heading',{name:'Scoped analysis',exact:true}).waitFor();
  await page.locator('.workspace-summary').waitFor();
}
async function instrumentWorkers(page){
  await page.evaluate(()=>{
    const Base=window.Worker;window.__f4WorkerOperations=[];window.__f4WorkerCompleted=[];
    window.Worker=class extends Base{
      constructor(...args){super(...args);this.f4Operation='unknown';this.addEventListener('message',({data})=>{if(!data.stage)window.__f4WorkerCompleted.push({operation:this.f4Operation,ok:data.ok});});}
      postMessage(message,transfers){this.f4Operation=message.operation;window.__f4WorkerOperations.push(message.operation);return super.postMessage(message,transfers);}
    };
  });
}
async function performOperation(page,name){
  const before=await page.evaluate(()=>window.__f4WorkerCompleted.length);
  await page.getByRole('button',{name,exact:true}).click();
  await page.waitForFunction(count=>window.__f4WorkerCompleted.length>count,before);
}

export async function qualifyScopedBrowser({page,browser,url,output,screenshot,check,wire,exported,json}){
  const fixtureData=fixture(),captures={protocol:'domains.f4_scoped_browser_qualification.v1',operations:[],exports:{},screenshots:[],success:false};
  await instrumentWorkers(page);
  await loadReviewed(page,fixtureData.files);
  const loaded=await reportJson(page,json);
  assert.equal(loaded.scientific_report.scoped_operations.length,0,'Reviewed assembly must not trigger a numerical operation');
  assert.equal(loaded.pca,null,'Loaded all-X inventory must not create an all-population PCA');
  assert.deepEqual(loaded.scientific_report.inventory.loaded.partitions.map(p=>[p.name,p.rows]),[['train',8],['test',2],['predict',1]]);
  assert.equal(loaded.scientific_report.inventory.loaded.x.rows,11);
  assert.equal(loaded.scientific_report.inventory.loaded.y[0].rows,11);
  assert.equal(loaded.scientific_report.inventory.loaded.y[0].missing,0);
  assert.equal(loaded.scientific_report.inventory.loaded.y[0].name,'yield');
  assert.equal(loaded.scientific_report.inventory.loaded.y[0].type,'numeric');
  assert.equal(loaded.scientific_report.inventory.loaded.metadata.find(m=>m.role==='specimen')?.rows,11);
  assert(loaded.scientific_report.inventory.loaded.metadata.some(m=>m.role==='group'));
  assert(loaded.scientific_report.inventory.loaded.metadata.some(m=>m.role==='reference'));
  assert(loaded.scientific_report.inventory.loaded.metadata.some(m=>m.name==='batch'));
  assert.equal(await page.getByLabel('Timing context').inputValue(),'unspecified');
  assert.equal(JSON.stringify(loaded).includes(ySentinel),false);
  await page.locator('.scope-controls').scrollIntoViewIfNeeded();
  await screenshot(page,'f4-scope-controls-desktop',false,'.scope-controls');

  const intentWorkerOpsBefore=await page.evaluate(()=>window.__f4WorkerOperations.length);
  await performOperation(page,'Train structure');await page.locator('.workspace-summary').waitFor();
  let current=await reportJson(page,json),trainResult=operation(current,'train_structure');
  assert.equal(trainResult.status,'computed');assert.deepEqual(trainResult.receipt.fit_keys,trainResult.receipt.reference_keys);
  assert.equal(trainResult.receipt.fit_keys.length,8);assert.equal(trainResult.receipt.query_keys.length,0);
  assert.equal(trainResult.receipt.selection_context,'unspecified');
  assert.equal(trainResult.receipt.y_accessed,false);
  const trainStructure=trainResult.value.structure;
  assert.equal(trainStructure.scope.n_observations,8);
  assert.equal(trainStructure.metrics.pca.value.scores.length,8);
  const pcaCall=trainResult.receipt.provider_calls.find(call=>call.operation==='pca');
  assert(pcaCall,'Train structure receipt must preserve the actual public Methods PCA call');
  assert.equal(pcaCall.matrices.matrix.shape[0],8);
  captures.operations.push({operation:trainResult.operation,status:trainResult.status,receipt:trainResult.receipt});
  check('F4 reviewed import stays inventory-only; train structure fits only eight train rows with actual provider receipt');

  await performOperation(page,'Exact spectra train/test audit');await page.locator('.workspace-summary').waitFor();
  current=await reportJson(page,json);let exact=operation(current,'integrity_audit','exact_spectra');
  assert.equal(exact.diagnostic,'exact_spectra');assert.equal(exact.receipt.fit_keys.length,0);
  assert.equal(exact.receipt.y_accessed,false);assert.equal(exact.receipt.test_x_accessed,true);
  const duplicate=exact.value.metrics.find(metric=>metric.metric_id==='integrity.cross_partition_exact_duplicate_pairs');
  assert(duplicate,'Original Preflight cross-partition exact duplicate metric ID must be retained');
  assert.equal(duplicate.value,1,'The train/test exact duplicate has different declared specimen identities');
  captures.operations.push({operation:exact.operation,diagnostic:exact.diagnostic,status:exact.status,receipt:exact.receipt});
  check('F4 exact audit retains original Preflight metric ID and one cross-partition exact duplicate pair');

  await performOperation(page,'Identity audit (no X)');await page.locator('.workspace-summary').waitFor();
  current=await reportJson(page,json);let identity=operation(current,'integrity_audit','declared_identities');
  assert.equal(identity.diagnostic,'declared_identities');assert.equal(identity.receipt.fields_read.x,null);
  assert.equal(identity.receipt.test_x_accessed,false);assert.equal(identity.receipt.provider_calls.length,0);
  assert(identity.value.columns.some(column=>column.role==='group'&&column.literal_shared_nonmissing_value_count>0));
  assert(identity.value.columns.some(column=>column.role==='reference'&&column.literal_shared_nonmissing_value_count>0));
  captures.operations.push({operation:identity.operation,diagnostic:identity.diagnostic,status:identity.status,receipt:identity.receipt});
  check('F4 declared-identity audit reports no X access and calls no numerical provider');

  await performOperation(page,'Train M factors');await page.locator('.workspace-summary').waitFor();
  current=await reportJson(page,json);let factors=operation(current,'metadata_factor_audit');
  assert.equal(factors.receipt.fields_read.x,null);assert.deepEqual(factors.receipt.fields_read.y,[]);
  assert.equal(factors.receipt.provider_calls.length,0);
  assert.equal(factors.value.assembly,'documentary counts and literal set intersection; no association test');
  assert(factors.value.columns.length>0&&factors.value.columns.every(column=>column.reference.n_rows===8));
  assert(factors.value.columns.every(column=>column.association.status==='unavailable'));
  captures.operations.push({operation:factors.operation,status:factors.status,receipt:factors.receipt});
  check('F4 train M-factor operation is documentary and sends neither X nor Y to a provider');

  await performOperation(page,'Cross-partition M audit');await page.locator('.workspace-summary').waitFor();
  current=await reportJson(page,json);let cross=operation(current,'cross_partition_metadata_audit');
  assert.equal(cross.receipt.fields_read.x,null);assert.deepEqual(cross.receipt.fields_read.y,[]);
  assert.equal(cross.receipt.provider_calls.length,0);
  assert(cross.value.columns.length>0&&cross.value.columns.every(column=>column.reference.n_rows===8&&column.query.n_rows===2));
  captures.operations.push({operation:cross.operation,status:cross.status,receipt:cross.receipt});
  check('F4 cross-partition M operation retains documentary scope without X/Y provider access');

  await performOperation(page,'Raw support: train reference → test query');await page.locator('.workspace-summary').waitFor();
  current=await reportJson(page,json);let support=operation(current,'train_reference_test_query');
  assert.equal(support.receipt.reference_keys.length,8);assert.equal(support.receipt.query_keys.length,2);
  assert.equal(support.receipt.fit_keys.length,0);assert.equal(support.receipt.y_accessed,false);
  captures.operations.push({operation:support.operation,status:support.status,receipt:support.receipt});
  check('F4 raw support keeps train reference and test query distinct and records test-X access');

  await page.getByLabel('I explicitly authorize a descriptive fit on train + test; prediction rows remain excluded.').check();
  await performOperation(page,'Global descriptive analysis');await page.locator('.workspace-summary').waitFor();
  current=await reportJson(page,json);let global=operation(current,'global_descriptive_transductive');
  assert.equal(global.receipt.explicit_transductive,true);assert.equal(global.receipt.fit,'transductive');
  assert.equal(global.receipt.fit_keys.length,10);assert.equal(global.receipt.fit_keys.some(key=>global.receipt.query_keys.includes(key)),true);
  assert.equal(global.receipt.y_accessed,false);
  captures.operations.push({operation:global.operation,status:global.status,receipt:global.receipt});
  check('F4 explicit consent creates a distinct transductive train+test receipt and excludes prediction rows');

  const workersBeforeColor=await page.evaluate(()=>window.__f4WorkerOperations.length);
  await page.getByLabel('Color PCA display by M field').selectOption({label:'batch'});
  assert.equal(await page.evaluate(()=>window.__f4WorkerOperations.length),workersBeforeColor,'Display color must not start a worker');
  const beforeIntent=await reportJson(page,json),numericBefore=JSON.stringify(beforeIntent.scientific_report.scoped_operations),
    hashesBefore=JSON.stringify(beforeIntent.scientific_report.scoped_operations.map(item=>item.receipt.request_sha256));
  const completedBeforeIntent=await page.evaluate(()=>window.__f4WorkerCompleted.length);
  await page.getByRole('radio',{name:'A new study or acquisition context'}).check();
  await page.waitForFunction(before=>window.__f4WorkerCompleted.length>before,completedBeforeIntent);
  await page.waitForFunction(()=>!document.querySelector('[role=alert]'));
  const afterIntent=await reportJson(page,json);
  assert.equal(JSON.stringify(afterIntent.scientific_report.scoped_operations),numericBefore);
  assert.equal(JSON.stringify(afterIntent.scientific_report.scoped_operations.map(item=>item.receipt.request_sha256)),hashesBefore);
  const intentOps=await page.evaluate(()=>window.__f4WorkerOperations.slice());
  assert(intentOps.slice(workersBeforeColor).every(op=>op==='interpret'),'Intent update may interpret existing evidence but must not refit or rerun scoped operations');
  const colorOps=await page.evaluate(()=>window.__f4WorkerOperations.slice(0,workersBeforeColor));
  assert.equal(colorOps.length,workersBeforeColor);
  check('F4 intent rereads existing evidence only; provider receipts, scoped hashes and numerical outputs stay unchanged');

  const html=await downloadText(page,'html',exported),markdown=await downloadText(page,'markdown',exported),final=await reportJson(page,json);
  assert.equal(final.export_selection.protocol_version,'domains.report_export_selection.v1');
  assert(final.export_selection.selected_sections.includes('machine_evidence'),'F3.5 machine evidence selection remains available for scoped reports');
  for(const [name,text] of [['html',html],['markdown',markdown],['json',JSON.stringify(final)]]){
    assert(!text.includes(ySentinel),`${name} export exposed Y sentinel`);assert(!text.includes(xSentinel),`${name} export exposed X sentinel`);
    assert(!text.includes('"matrix":['),`${name} export exposed a raw data matrix`);
    captures.exports[name]={bytes:Buffer.byteLength(text),contains_target_sentinel:false,contains_x_sentinel:false};
  }
  assert.equal(final.raw_x_included,false);assert.equal(final.scientific_report.raw_X_Y_exported,false);
  assert.equal(final.scientific_report.scoped_operations.length,7);
  const outDir=resolve(output,'f4');await mkdir(outDir,{recursive:true});
  if(process.env.CI)for(const [ext,text]of[['html',html],['md',markdown],['json',JSON.stringify(final,null,2)]])await writeFile(resolve(outDir,`scoped-live.${ext}`),text);
  captures.final_operation_count=final.scientific_report.scoped_operations.length;
  check('F4 JSON/HTML/Markdown preserve scoped receipts and contain neither raw matrices nor X/Y sentinel values');

  const mobile=await browser.newContext({viewport:{width:390,height:844},isMobile:true,deviceScaleFactor:1,hasTouch:true,locale:'en-US'});
  wire(mobile,'chromium-mobile-f4');
  try{
    const mobilePage=await mobile.newPage();mobilePage.setDefaultTimeout(120_000);await mobilePage.goto(url);
    await instrumentWorkers(mobilePage);
    const mfixture=fixture();await loadReviewed(mobilePage,mfixture.files);
    await performOperation(mobilePage,'Train structure');await mobilePage.locator('.workspace-summary').waitFor();
    assert(await mobilePage.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'F4 mobile controls must not overflow horizontally');
    await mobilePage.locator('.scope-controls').scrollIntoViewIfNeeded();await screenshot(mobilePage,'f4-scope-controls-mobile',false,'.scope-controls');
    captures.screenshots.push('f4-scope-controls-desktop','f4-scope-controls-mobile');
    check('F4 scoped controls render on mobile without horizontal overflow');
  }finally{await mobile.close();}
  captures.success=true;
  await mkdir(resolve(output,'f4'),{recursive:true});
  await writeFile(resolve(output,'f4','scoped-browser.json'),JSON.stringify(captures,null,2)+'\n');
}
