/** Real browser worker-bootstrap and shared-loader fault qualification. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdir,readFile,readdir,writeFile} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const xOnly={name:'X.csv',mimeType:'text/csv',buffer:Buffer.from('1000\n1\n2\n3\n')};
const csv=(header,rows)=>[header.join(','),...rows.map(row=>row.join(','))].join('\n')+'\n';
const train=Array.from({length:8},(_,i)=>[`tr-${i}`,String(i+1),String((i+1)*1.5)]);
const targets=train.map((r,i)=>[r[0],String(10+i)]);
const params={delimiter:',',has_header:true};
const xyConfig={schema_version:1,name:'Synthetic worker loading X/Y fixture',sources:[
 {id:'X_train',role:'features',input:'X_train.csv',partition:'train',key:'id',columns:{metadata:['id'],features:['1000','1100']},params},
 {id:'Y_train',role:'targets',input:'Y_train.csv',partition:'train',key:'id',join:{left:'Y_train',right:'X_train',left_on:'id',right_on:'id',cardinality:'1:1',coverage:'complete'},columns:{metadata:['id'],targets:['yield']},params},
],metadata_declarations:{},target_tasks:{yield:'regression'}};
const xAndY=[
 {name:'baseline.nirs4all.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(xyConfig))},
 {name:'X_train.csv',mimeType:'text/csv',buffer:Buffer.from(csv(['id','1000','1100'],train))},
 {name:'Y_train.csv',mimeType:'text/csv',buffer:Buffer.from(csv(['id','yield'],targets))},
];
const basenames=url=>new URL(url).pathname.split('/').at(-1)??'';

export async function qualifyWorkerLoadingBrowser({page,context,url,output,check,exported,json,screenshot}){
 const browser=page.context().browser(),browserType=browser?.browserType().name()??'unknown';
 const evidence={protocol:'domains.worker_loading_browser.v1',browser:{name:browserType,version:browser?.version()??'unknown'},build_info:null,production_asset_digests:[],cases:[],success:false,scope:{data:'synthetic only',raw_values_recorded:false,y_used_for_train_structure:false,provider_output_fabricated:false}};
 const out=resolve(output,'worker-loading');await mkdir(out,{recursive:true});
 const infoResponse=await page.request.get(new URL('build-info.json',url).href);
 evidence.build_info={status:infoResponse.status(),content_type:infoResponse.headers()['content-type']?.split(';')[0]??null};
 assert.equal(infoResponse.status(),200,'The generated build identity asset must be served by the production preview');
 assert.equal(evidence.build_info.content_type,'application/json');
 const info=await infoResponse.json();evidence.build_info={...evidence.build_info,version:typeof info.version==='string'?info.version:null,commit:typeof info.commit==='string'?info.commit:null,dirty:typeof info.dirty==='boolean'?info.dirty:null};
 assert(evidence.build_info.version&&(/^[a-f0-9]{40}$/.test(evidence.build_info.commit??'')||evidence.build_info.commit===null));
 const assetsDir=resolve(dirname(fileURLToPath(import.meta.url)),'../dist/assets'),assets=await readdir(assetsDir);
 for(const name of assets.filter(n=>/\.(?:js|wasm)$/.test(n)).sort()){
  const bytes=await readFile(resolve(assetsDir,name));evidence.production_asset_digests.push({name,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
 }
 const appOrigin=new URL(url).origin;let activeAudit=null;
 const safeAssetPath=raw=>{try{const u=new URL(raw);return u.origin===appOrigin&&u.pathname.startsWith('/nirs4all-domains/assets/')?u.pathname:undefined;}catch{return undefined;}};
 const errorClass=text=>text.includes('controlled synthetic worker top-level throw')?'injected_top_level_throw':/\b404\b/i.test(text)?'http_404':/wasm|webassembly/i.test(text)?'wasm_error':/module|chunk|script/i.test(text)?'module_error':/Failed to load resource|ERR_FAILED|ERR_ABORTED/i.test(text)?'resource_load_error':'unexpected_error';
 const auditSnapshot=a=>({requests:a.requests.length,off_origin_requests:a.offOrigin,non_get_requests:a.nonGet,console_errors:a.consoleErrors,page_errors:a.pageErrors,asset_responses:a.assets});
 const startAudit=id=>{activeAudit={id,requests:[],offOrigin:0,nonGet:0,consoleErrors:[],pageErrors:[],assets:[],injectedPaths:[]};return activeAudit;};
 const finishAudit=(a,fault=false)=>{
  assert.equal(a.offOrigin,0,`${a.id} made no off-origin requests`);assert.equal(a.nonGet,0,`${a.id} made no non-GET requests`);
  if(!fault){assert.deepEqual(a.consoleErrors,[],`${a.id} has no blocking console errors`);assert.deepEqual(a.pageErrors,[],`${a.id} has no page errors`);assert(a.assets.every(r=>r.status>=200&&r.status<400),`${a.id} all requested JS/CSS/WASM assets are healthy`);}
  else{
   const injectedPaths=[...new Set(a.injectedPaths)],injectedNames=injectedPaths.map(path=>path.split('/').at(-1));
   assert(injectedPaths.length,`${a.id} fault evidence must identify the same-origin injected asset`);
   for(const error of [...a.consoleErrors,...a.pageErrors]){
    assert.notEqual(error.category,'unexpected_error',`${a.id} has an unrelated browser error`);
    if(error.category==='injected_top_level_throw')assert.equal(a.id,'worker-script-top-level-throw');
    if(error.asset_path&&injectedPaths.includes(error.asset_path)){error.association='reported_asset_url';error.associated_asset_path=error.asset_path;continue;}
    if(!error.asset_path&&(a.workerErrorAssets??[]).some(name=>injectedNames.includes(name))){error.association='worker_error_filename';error.associated_asset_path=injectedPaths[injectedNames.indexOf(a.workerErrorAssets.find(name=>injectedNames.includes(name)))];continue;}
    assert.equal(injectedPaths.length,1,`${a.id} can attribute pathless browser errors only to one isolated injected asset`);
    assert(a.assets.every(response=>response.status>=400? injectedPaths.includes(response.path):true),`${a.id} has no other failed JS/CSS/WASM responses`);
    error.association='single_isolated_asset_route';error.associated_asset_path=injectedPaths[0];
   }
  }
  const snapshot=auditSnapshot(a);if(activeAudit===a)activeAudit=null;return snapshot;
 };
 context.on('request',request=>{if(!activeAudit||!/^https?:/.test(request.url()))return;const u=new URL(request.url());activeAudit.requests.push({method:request.method(),same_origin:u.origin===appOrigin});if(u.origin!==appOrigin)activeAudit.offOrigin++;if(!['GET','HEAD'].includes(request.method()))activeAudit.nonGet++;});
 context.on('response',response=>{if(!activeAudit)return;const path=safeAssetPath(response.url());if(!path||!(/\.(?:js|css|wasm)$/.test(path)))return;activeAudit.assets.push({path,status:response.status(),content_type:response.headers()['content-type']?.split(';')[0]??null});});
 context.on('console',message=>{if(!activeAudit||message.type()!=='error')return;const path=safeAssetPath(message.location().url??'');activeAudit.consoleErrors.push({category:errorClass(message.text()),asset_path:path??null});});
 page.on('pageerror',error=>{if(!activeAudit)return;const message=String(error.message??'');const path=safeAssetPath(error.url??'');activeAudit.pageErrors.push({name:error.name||'Error',category:errorClass(message),message_available:message.length>0,asset_path:path??null});});
 await context.addInitScript(()=>{
  const Native=window.Worker;window.__workerLoadingAudit=[];
  window.__workerLoadingClipboard='';try{Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.__workerLoadingClipboard=String(text);},readText:async()=>window.__workerLoadingClipboard}});}catch{}
  window.Worker=class extends Native{
   constructor(...args){super(...args);const row={asset:String(args[0]??'').split('/').at(-1),errors:[],operations:[],lifecycle:[],completed:0,terminated:false};window.__workerLoadingAudit.push(row);this.__workerLoadingRow=row;
    this.addEventListener('error',event=>row.errors.push({message_available:typeof event.message==='string'&&event.message.trim().length>0,filename: String(event.filename||'').split('/').at(-1)}));
    this.addEventListener('message',event=>{const d=event.data;if(d?.lifecycle_event)row.lifecycle.push({event:d.lifecycle_event,phase:d.phase??null,component:d.component??null});if(d&&!d.stage&&!d.lifecycle_event)row.completed++;});}
   postMessage(message,transfer){this.__workerLoadingRow?.operations.push(String(message?.operation??'unknown'));return super.postMessage(message,transfer??[]);}
   terminate(){if(this.__workerLoadingRow)this.__workerLoadingRow.terminated=true;return super.terminate();}
  };
 });
 const home=async()=>{await page.goto(url,{waitUntil:'domcontentloaded'});await page.locator('input[type=file]:not([webkitdirectory])').waitFor({state:'attached',timeout:60000});};
 const prepareFiles=async(files)=>{
  const before=await page.evaluate(()=>window.__workerLoadingAudit.reduce((n,w)=>n+w.completed,0));
  const operationBefore=await page.evaluate(()=>window.__workerLoadingAudit.flatMap(w=>w.operations).length);
  await page.locator('input[type=file]:not([webkitdirectory])').setInputFiles(files);
  const summary=page.locator('.workspace-summary'),alert=page.getByRole('alert');
  const outcome=await Promise.race([
   summary.waitFor({state:'visible',timeout:120000}).then(()=> 'loaded'),
   alert.waitFor({state:'visible',timeout:120000}).then(()=> 'error'),
  ]);
  if(outcome==='error')return {error:await diagnostic(page)};
  await page.getByRole('heading',{name:'Scoped analysis',exact:true}).waitFor({timeout:120000});
  await page.locator('.dataset-loaded-summary').waitFor({state:'visible',timeout:120000});
  assert.equal(await page.getByRole('checkbox',{name:/I confirm the displayed roles, join identifiers and partitions/}).count(),0,
   'A normal import must not require a role confirmation checkbox');
  assert.equal(await page.getByRole('button',{name:'Import reviewed data',exact:true}).count(),0,
   'A normal import must not require a second import action');
  await page.waitForFunction(n=>window.__workerLoadingAudit.reduce((sum,w)=>sum+w.completed,0)>=n+2,before,{timeout:120000});
  assert.deepEqual(await page.evaluate(index=>window.__workerLoadingAudit.flatMap(w=>w.operations).slice(index),operationBefore),
   ['prepare_import','assemble_import'],'One-shot import completes its two expected worker operations');
  return {error:null,completedBefore:before,operationBefore};
 };
 const diagnostic=async()=>{
  const section=page.locator('.technical-diagnostic[role=alert]');
  await section.waitFor({timeout:60000});
  const dts=await section.locator('dt').allTextContents(),dds=await section.locator('dd').allTextContents();
  const fields=Object.fromEntries(dts.map((dt,i)=>[dt.trim(),dds[i]?.trim()??'']));
  const blocks=await section.locator('details pre').allTextContents();let jsonDiag=null;
  for(const block of blocks.slice().reverse()){try{const value=JSON.parse(block);if(value.protocol_version==='domains.worker_diagnostic.v1'){jsonDiag=value;break;}}catch{}}
  assert(jsonDiag,'Expected the actual local technical diagnostic JSON in the error details');
  return {protocol_version:jsonDiag.protocol_version,code:jsonDiag.code,phase:jsonDiag.phase,last_confirmed_phase:jsonDiag.last_confirmed_phase,operation:jsonDiag.operation,component:jsonDiag.component,asset:jsonDiag.asset?{relative_path:jsonDiag.asset.relative_path,http_status:jsonDiag.asset.http_status,content_type:jsonDiag.asset.content_type}:null,original_message_available:jsonDiag.original_message_available,fields,privacy_text_present:(await section.innerText()).includes('Nothing is uploaded.')};
 };
 const summarizeReport=report=>{
  const sr=report.scientific_report??{},op=sr.scoped_operations?.findLast?.(x=>x.operation==='train_structure')??sr.scoped_operations?.at(-1);
  const structure=op?.value?.structure??sr.unpartitioned_structure??sr;
  return {source_mode:report.source_mode??null,observations:report.dataset?.observations??null,variables:report.dataset?.variables??null,
   y_inventory:(sr.inventory?.loaded?.y??[]).map(y=>({name:y.name,rows:y.rows,missing:y.missing,type:y.type})),
   operation_status:op?.status??null,y_accessed:op?.receipt?.y_accessed??null,
   provider_calls:(op?.receipt?.provider_calls??[]).map(c=>c.operation),pca_status:structure?.metrics?.pca?.status??null,
   contains_raw_x:report.raw_x_included===true||sr.raw_X_Y_exported===true};
 };
 const fitAndReport=async()=>{
  await page.getByRole('button',{name:'Train structure',exact:true}).click();
  await page.locator('.workspace-summary').waitFor({timeout:120000});
  return summarizeReport(await json(page));
 };
 const workerSnapshot=async()=>page.evaluate(()=>window.__workerLoadingAudit.map(w=>({asset:w.asset,operations:w.operations,lifecycle:w.lifecycle,errors:w.errors,completed:w.completed,terminated:w.terminated})));
 const loadHealthy=async(id,files)=>{
  const audit=startAudit(id);
  await home();const loaded=await prepareFiles(files);assert.equal(loaded.error,null,`${id} import must complete using published IO`);
  const report=await fitAndReport();
  const operations=await page.evaluate(index=>window.__workerLoadingAudit.flatMap(w=>w.operations).slice(index),loaded.operationBefore);
  const completed=await page.evaluate(()=>window.__workerLoadingAudit.reduce((n,w)=>n+w.completed,0));
  assert.deepEqual(operations,['prepare_import','assemble_import','scoped'],'A normal import and one analysis complete exactly three worker operations');
  assert.equal(completed,loaded.completedBefore+3,'The two import replies and one analysis reply all complete');
  assert.equal(report.source_mode,'user_computed_live',`${id} actual source mode ${JSON.stringify(report)}`);assert.equal(report.operation_status,'computed',`${id} actual analysis status ${JSON.stringify(report)}`);assert.equal(report.y_accessed,false);assert.equal(report.pca_status,'computed');assert.equal(report.contains_raw_x,false);
  evidence.cases.push({id,status:'computed',report,workers:await workerSnapshot(),network:auditSnapshot(audit)});finishAudit(audit);
  check(`Worker loading: ${id} import and actual train-only Methods analysis`);return report;
 };
 const faultCase=async({id,files=xOnly,stage='import',matcher,response,mutate,expectedCode,expectedPhase,expectedComponent})=>{
  const audit=startAudit(id);await home();const matched=[];
  const handler=async route=>{
   const request=route.request(),requestUrl=new URL(request.url()),file=basenames(request.url());
   if(requestUrl.origin===new URL(url).origin&&requestUrl.pathname.startsWith('/nirs4all-domains/assets/')&&matcher(file)){
    let status=response.status,contentType=response.contentType,body=response.body;
    if(mutate){const original=await route.fetch();status=original.status();contentType=original.headers()['content-type']??contentType;body=await mutate(Buffer.from(await original.body()));}
    matched.push({path:requestUrl.pathname,status,content_type:contentType,...(mutate?{mutation:'appended valid WASM custom section; imports/exports checked'}:{})});
    audit.injectedPaths.push(requestUrl.pathname);
    await route.fulfill({status,contentType,body});
   }else await route.continue();
  };
  await context.route('**/*',handler);
  try{
   const load=await prepareFiles(files);
   if(load.error){evidence.cases.push({id,status:'refused',diagnostic:load.error,intercepted:matched,workers:await workerSnapshot()});}
   else if(stage==='analysis'){
    await page.getByRole('button',{name:'Train structure',exact:true}).click();
    const alert=page.getByRole('alert');await alert.waitFor({timeout:120000});
    const d=await diagnostic(page);evidence.cases.push({id,status:'refused',diagnostic:d,intercepted:matched,workers:await workerSnapshot()});
   }else assert.fail(`${id} unexpectedly completed import`);
   const item=evidence.cases.at(-1);assert(matched.length,`${id} route injection was not requested by the actual browser worker`);
   assert.equal(item.status,'refused');assert.equal(item.diagnostic.code,expectedCode,`${id} actual diagnostic code`);
   if(expectedPhase)assert.equal(item.diagnostic.phase,expectedPhase,`${id} lifecycle phase`);
   if(expectedComponent)assert.equal(item.diagnostic.component,expectedComponent,`${id} loader component`);
   if(stage!=='analysis')assert.equal(await page.locator('.workspace-summary').count(),0,`${id} must not create an analysis result`);
   if(id==='worker-script-404'){
    assert.equal(item.diagnostic.asset?.http_status,404);assert(await page.getByRole('button',{name:/Reload application/}).count(),'Confirmed asset mismatch exposes an explicit reload action');
    const title=page.locator('.technical-diagnostic h3'),english=await title.textContent();
    await page.getByRole('button',{name:'FR',exact:true}).click();const french=await title.textContent();assert(english&&french&&english!==french,'Technical diagnostic should localize to French');
    assert.equal((await diagnostic(page)).code,expectedCode);await page.getByRole('button',{name:'EN',exact:true}).click();
    assert((await page.locator('.technical-diagnostic').innerText()).includes('Nothing is uploaded.'));
    await page.getByRole('button',{name:'Copy technical diagnostic',exact:true}).click();await page.getByText('Diagnostic copied locally.',{exact:true}).waitFor();
    const copied=await page.evaluate(()=>JSON.parse(window.__workerLoadingClipboard));assert.equal(copied.protocol_version,'domains.worker_diagnostic.v1');assert.equal(copied.code,expectedCode);
    assert(!JSON.stringify(copied).includes('tr-0'));item.diagnostic_copy_verified=true;
    await screenshot?.(page,`worker-loading-error-${browserType}`,false,'.technical-diagnostic');
   }
   audit.workerErrorAssets=item.workers.flatMap(worker=>worker.errors.map(error=>error.filename));
   item.network=auditSnapshot(audit);item.network=finishAudit(audit,true);
   check(`Worker loading refusal: ${id} (${item.diagnostic.code})`,{asset:matched[0].path});
  }finally{await context.unroute('**/*',handler);}
 };
 const routeBytes=array=>Buffer.from(array);
 const validDigestMismatch=async bytes=>{
  const original=await WebAssembly.compile(bytes),mutated=Buffer.concat([bytes,Buffer.from([0,2,0,66])]),changed=await WebAssembly.compile(mutated);
  assert.deepEqual(WebAssembly.Module.exports(changed),WebAssembly.Module.exports(original));
  assert.deepEqual(WebAssembly.Module.imports(changed),WebAssembly.Module.imports(original));return mutated;
 };
 const syntheticUnhandledWorker=`const send=(event,stage)=>self.postMessage({id:0,ok:true,protocol_version:'domains.worker_bootstrap.v1',lifecycle_event:event,stage,stage_id:'prepare',component:'worker',build:{version:'0.1.0-alpha.17',commit:null,dirty:null}});send('WORKER_BOOTSTRAP_STARTED','Worker bootstrap started');send('WORKER_BOOTSTRAP_READY','Worker bootstrap ready');let activeId=0;self.addEventListener('message',event=>{activeId=event.data.id;Promise.reject(new Error('controlled synthetic unhandled rejection'));});self.addEventListener('unhandledrejection',event=>{self.postMessage({id:activeId,ok:false,error:{code:'WORKER_UNHANDLED_REJECTION',message:'controlled synthetic unhandled rejection',details:{code:'WORKER_UNHANDLED_REJECTION',phase:'OPERATION_MODULE_READY',component:'worker',original_message_available:true}}});event.preventDefault();});`;
 try{
  const x=await loadHealthy('x-only',xOnly);assert.equal(x.observations,3);assert.equal(x.variables,1);
  const xy=await loadHealthy('x-y-train-only',xAndY);assert.equal(xy.observations,8);assert.equal(xy.variables,2);assert.deepEqual(xy.y_inventory,[{name:'yield',rows:8,missing:0,type:'numeric'}]);
  await faultCase({id:'worker-script-404',matcher:f=>/^worker-[A-Za-z0-9_-]+\.js$/.test(f)&&!f.startsWith('worker-operations-'),response:{status:404,contentType:'application/javascript',body:'/* controlled worker entry 404 */'},expectedCode:'WORKER_ASSET_UNAVAILABLE'});
  await page.getByRole('button',{name:/Reload application/}).click();await page.locator('input[type=file]:not([webkitdirectory])').waitFor({state:'attached',timeout:60000});
  await loadHealthy('fresh-worker-after-explicit-reload',xAndY);
  await faultCase({id:'worker-script-html',matcher:f=>/^worker-[A-Za-z0-9_-]+\.js$/.test(f)&&!f.startsWith('worker-operations-'),response:{status:200,contentType:'text/html',body:'<!doctype html><title>not JavaScript</title>'},expectedCode:'JAVASCRIPT_ASSET_INVALID_RESPONSE'});
  await faultCase({id:'worker-script-top-level-throw',matcher:f=>/^worker-[A-Za-z0-9_-]+\.js$/.test(f)&&!f.startsWith('worker-operations-'),response:{status:200,contentType:'application/javascript',body:"throw new Error('controlled synthetic worker top-level throw');"},expectedCode:'WORKER_STARTUP_EXCEPTION',expectedPhase:'WORKER_CREATED',expectedComponent:'worker'});
  await faultCase({id:'ready-then-unhandled-rejection',matcher:f=>/^worker-[A-Za-z0-9_-]+\.js$/.test(f)&&!f.startsWith('worker-operations-'),response:{status:200,contentType:'application/javascript',body:syntheticUnhandledWorker},expectedCode:'WORKER_UNHANDLED_REJECTION',expectedPhase:'OPERATION_MODULE_READY',expectedComponent:'worker'});
  await faultCase({id:'worker-operation-chunk-404',stage:'analysis',files:xOnly,matcher:f=>/^worker-operations-[A-Za-z0-9_-]+\.js$/.test(f),response:{status:404,contentType:'application/javascript',body:'/* controlled operation chunk 404 */'},expectedCode:'WORKER_DEPENDENCY_IMPORT_FAILED',expectedPhase:'OPERATION_MODULE_LOADING',expectedComponent:'worker'});
  await faultCase({id:'worker-operation-chunk-html',stage:'analysis',files:xOnly,matcher:f=>/^worker-operations-[A-Za-z0-9_-]+\.js$/.test(f),response:{status:200,contentType:'text/html',body:'<!doctype html><title>not JavaScript</title>'},expectedCode:'WORKER_DEPENDENCY_IMPORT_FAILED',expectedPhase:'OPERATION_MODULE_LOADING',expectedComponent:'worker'});
  const io='nirs4all_io_wasm_bg-';
  for(const fault of [
   {id:'io-wasm-404',response:{status:404,contentType:'application/wasm',body:new Uint8Array()},expectedCode:'WASM_ASSET_UNAVAILABLE'},
   {id:'io-wasm-corrupt',response:{status:200,contentType:'application/wasm',body:routeBytes([0,97,115,109])},expectedCode:'WASM_COMPILE_FAILED'},
   {id:'io-wasm-wrong-mime',response:{status:200,contentType:'text/html',body:'<!doctype html><title>not WASM</title>'},expectedCode:'WASM_ASSET_INVALID_RESPONSE'},
   {id:'io-wasm-incompatible-exports',response:{status:200,contentType:'application/wasm',body:routeBytes([0,97,115,109,1,0,0,0])},expectedCode:'WASM_EXPORT_MISSING'},
   {id:'io-wasm-nonhtml-wrong-mime',response:{status:200,contentType:'application/json',body:'{}'},expectedCode:'WASM_CONTENT_TYPE_INVALID'},
  ])await faultCase({id:fault.id,matcher:f=>f.startsWith(io)&&f.endsWith('.wasm'),response:fault.response,expectedCode:fault.expectedCode,expectedPhase:'IO_RUNTIME_LOADING',expectedComponent:'io'});
  await faultCase({id:'io-wasm-digest-mismatch',matcher:f=>f.startsWith(io)&&f.endsWith('.wasm'),response:{status:200,contentType:'application/wasm',body:null},mutate:validDigestMismatch,expectedCode:'ASSET_INTEGRITY_MISMATCH',expectedPhase:'IO_RUNTIME_LOADING',expectedComponent:'io'});
  await faultCase({id:'formats-wasm-404',files:{name:'invalid.spc',mimeType:'application/octet-stream',buffer:Buffer.from([0,1,2,3])},matcher:f=>f.startsWith('nirs4all_formats_wasm_bg-')&&f.endsWith('.wasm'),response:{status:404,contentType:'application/wasm',body:new Uint8Array()},expectedCode:'WASM_ASSET_UNAVAILABLE',expectedPhase:'FORMATS_RUNTIME_LOADING',expectedComponent:'formats'});
  await faultCase({id:'domains-wasm-404',stage:'analysis',files:xOnly,matcher:f=>f.startsWith('nirs4all_domains_bg-')&&f.endsWith('.wasm'),response:{status:404,contentType:'application/wasm',body:new Uint8Array()},expectedCode:'DOMAINS_INITIALIZATION_FAILED',expectedPhase:'DOMAINS_RUNTIME_LOADING',expectedComponent:'domains'});
  await faultCase({id:'methods-wasm-incompatible-abi',stage:'analysis',files:xOnly,matcher:f=>f.startsWith('n4m-')&&f.endsWith('.wasm'),response:{status:200,contentType:'application/wasm',body:routeBytes([0,97,115,109,1,0,0,0])},expectedCode:'METHODS_INITIALIZATION_FAILED',expectedPhase:'METHODS_RUNTIME_LOADING',expectedComponent:'methods'});
  const dataSensitive=JSON.stringify(evidence);
  for(const secret of ['tr-0','yield,10','1000,1','1.5'])assert(!dataSensitive.includes(secret),`Diagnostic evidence must not include source values (${secret})`);
  evidence.success=true;
 }finally{
  await writeFile(resolve(out,`loading-${browserType}.json`),JSON.stringify(evidence,null,2)+'\n');
 }
}
