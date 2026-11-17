/** Read-only public smoke, separately scoped from the candidate preview. */
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import {chromium} from 'playwright-core';
const url='https://dcornet.github.io/nirs4all-domains/';
const output=resolve(process.env.DOMAINS_PUBLIC_SMOKE_OUTPUT??'demo/test-results/public-smoke.json');
const receipt={url,reported_deployment_sha:process.env.DOMAINS_PUBLIC_DEPLOYMENT_SHA??null,scope:'Existing public deployment only; not a candidate deployment or byte-level SHA attestation',checks:[],assets:[],errors:[],network_violations:[],success:false};
const browser=await chromium.launch({headless:true,args:['--disable-gpu','--disable-extensions','--renderer-process-limit=1'],...(process.env.DOMAINS_BROWSER_EXE?{executablePath:process.env.DOMAINS_BROWSER_EXE}:{})});
const check=name=>receipt.checks.push(name);
function wire(context){
 context.on('request',r=>{if(/^https?:/.test(r.url())&&(new URL(r.url()).origin!==new URL(url).origin||!['GET','HEAD'].includes(r.method())))receipt.network_violations.push({method:r.method(),origin:new URL(r.url()).origin});});
 context.on('response',r=>{if(/\.(?:wasm|js|css|svg|woff2?)(?:\?|$)/.test(r.url()))receipt.assets.push({url:r.url(),status:r.status()});});
 context.on('page',p=>{p.on('pageerror',e=>receipt.errors.push(e.message));p.on('console',m=>{if(m.type()==='error')receipt.errors.push(m.text());});});
}
try{
 let context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});wire(context);
 await context.addInitScript(()=>{const create=URL.createObjectURL.bind(URL);window.__publicBlob=null;URL.createObjectURL=b=>{window.__publicBlob=b;return create(b);};const NativeWorker=window.Worker;window.__publicWorkerReplies=0;window.Worker=class extends NativeWorker{set onmessage(handler){super.onmessage=event=>{if(event.data&&typeof event.data.id==='number'&&('result'in event.data||'error'in event.data))window.__publicWorkerReplies++;handler?.call(this,event);};}get onmessage(){return super.onmessage;}};});
 let page=await context.newPage();page.setDefaultTimeout(120000);const response=await page.goto(url);assert.equal(response.status(),200);await page.getByRole('heading',{name:'Analyze my data'}).waitFor();check('Public HTTP 200 and landing');
 await page.reload();await page.getByRole('heading',{name:'Analyze my data'}).waitFor();check('Real deployment subpath refresh');
 await page.getByRole('button',{name:/Two spectral populations/}).click();await page.locator('.workspace-summary').waitFor();
 const exported=async format=>{const labels={json:/Structured JSON|JSON structuré/,html:/Offline HTML|HTML hors ligne/,markdown:/^↓ Markdown$/};const pending=page.waitForEvent('download');await page.getByRole('button',{name:labels[format]}).click();const download=await pending;const text=await page.evaluate(()=>window.__publicBlob.text());await download.cancel();return text;};
 const live=JSON.parse(await exported('json'));assert.equal(live.scientific_report.metrics.pca.status,'computed');assert.equal(live.dataset.observations,48);assert.equal(live.raw_x_included,false);check('Actual public Methods/Domains WASM synthetic example');
 await exported('html');await exported('markdown');check('All three existing public export formats');
 await page.getByRole('button',{name:'FR',exact:true}).click();await page.getByRole('button',{name:/thème|theme/i}).click();assert.equal(await page.locator('html').getAttribute('lang'),'fr');await page.getByRole('button',{name:'EN',exact:true}).click();check('Public language and theme');
 await page.getByRole('button',{name:/Domains · Home/}).click();await page.locator('input[type=file]').setInputFiles({name:'X.csv',mimeType:'text/csv',buffer:Buffer.from('1000\n1\n2\n3\n')});
 const importReview=page.locator('.dataset-import');
 const f4Import=await Promise.race([importReview.waitFor({state:'visible'}).then(()=>true),page.locator('.workspace-summary').waitFor().then(()=>false)]);
 if(f4Import){
  await page.getByRole('checkbox',{name:/I confirm the displayed roles, join identifiers and partitions/}).check();
  await page.getByRole('button',{name:'Import reviewed data'}).click();
  await page.locator('.scope-controls').waitFor();
  const workerReplies=await page.evaluate(()=>window.__publicWorkerReplies);
  await page.getByRole('button',{name:'Train structure'}).click();
  await page.waitForFunction(before=>window.__publicWorkerReplies>before,workerReplies);
  await page.locator('#geometry .geometry-grid').waitFor({state:'visible'});
 }
 await page.locator('.workspace-summary').waitFor();
 const imported=JSON.parse(await exported('json'));
 const importedStructure=imported.scientific_report.unpartitioned_structure??imported.scientific_report.scoped_operations?.findLast(op=>op.value?.structure)?.value.structure??imported.scientific_report;
 assert.equal(importedStructure.metrics.pca.value.eigenvalues[0],1);check('Public IO CSV and analytical variance one');
 await page.getByRole('button',{name:/Domains · Home/}).click();await page.getByRole('button',{name:/Tablets: a qualified saved report/}).click();await page.locator('.workspace-summary').waitFor();const saved=JSON.parse(await exported('json'));assert.equal(saved.provenance.browser_numerical_execution,false);check('Public saved tablet, no browser numerical refit');
 await context.close();context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});wire(context);page=await context.newPage();page.setDefaultTimeout(120000);await page.goto(url);await page.getByRole('button',{name:/A justified unavailable result/}).click();await page.locator('.workspace-summary').waitFor();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));check('Public mobile, real synthetic WASM and no document overflow');await context.close();
 if(!f4Import)assert(receipt.assets.some(a=>a.url.includes('nirs4all_formats_wasm')&&a.status===200));assert(receipt.assets.some(a=>a.url.includes('nirs4all_io_wasm')&&a.status===200));assert(receipt.assets.filter(a=>a.url.includes('.wasm')).length>=(f4Import?3:4));assert(receipt.assets.every(a=>[200,304].includes(a.status)));assert.deepEqual(receipt.errors,[]);assert.deepEqual(receipt.network_violations,[]);check('JS/CSS/icon/logo/WASM assets load; no upload/off-origin request or blocking errors');receipt.success=true;
}catch(error){receipt.failure={name:error.name,message:error.message};process.exitCode=1;process.stderr.write(error.stack+'\n');}
finally{await browser.close();await mkdir(dirname(output),{recursive:true});await writeFile(output,JSON.stringify(receipt,null,2)+'\n');}
process.stdout.write(JSON.stringify({success:receipt.success,checks:receipt.checks.length,errors:receipt.errors,network_violations:receipt.network_violations})+'\n');
