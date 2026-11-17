/** Actual published WASM loading/failure/recovery paths; no mocked scientific result. */
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';

export async function qualifyTechnicalLoading(browser,url,output,check){
  const context=await browser.newContext({viewport:{width:1200,height:900},acceptDownloads:true});
  const evidence={protocol:'domains.technical_loading.v1',assets:[],faults:[],console:[],success:false};let phase='normal';
  try{
    await context.addInitScript(()=>{
      const OriginalWorker=window.Worker;window.__transport={workers:[],blob:null};
      window.Worker=class extends OriginalWorker{
        constructor(...args){super(...args);this.audit={terminated:false,completed:false};window.__transport.workers.push(this.audit);this.addEventListener('message',({data})=>{if(!data.stage)this.audit.completed=true;});}
        postMessage(message,transfers){const files=['import','prepare_import'].includes(message.operation)?message.payload:[];this.audit.operation=message.operation;this.audit.input_bytes=Array.isArray(files)?files.reduce((n,f)=>n+(f.bytes?.byteLength??0),0):0;this.audit.transferred_bytes=(transfers??[]).reduce((n,b)=>n+(b.byteLength??0),0);super.postMessage(message,transfers??[]);this.audit.detached=Array.isArray(files)&&files.length>0&&files.every(f=>f.bytes.byteLength===0);}
        terminate(){this.audit.terminated=true;return super.terminate();}
      };
      const create=URL.createObjectURL.bind(URL);URL.createObjectURL=blob=>{window.__transport.blob=blob;return create(blob);};
    });
    const page=await context.newPage();page.setDefaultTimeout(120000);const pageErrors=[];
    page.on('pageerror',error=>pageErrors.push(error.message));
    page.on('console',message=>{if(message.type()==='error')evidence.console.push({phase,message:message.text()});});
    context.on('request',request=>{if(/^https?:/.test(request.url()))assert(new URL(request.url()).origin===new URL(url).origin&&['GET','HEAD'].includes(request.method()),'Unexpected upload/off-origin request');});
    context.on('response',response=>{if(/\.wasm(?:\?|$)/.test(response.url()))evidence.assets.push({phase,file:new URL(response.url()).pathname.split('/').pop(),status:response.status()});});
    await page.goto(url);assert.equal(evidence.assets.length,0,'Landing must not initialize numerical WASM');
    const home=async()=>{await page.getByRole('button',{name:/Domains · Home/}).click();await page.locator('input[type=file]').waitFor();};
    const upload=async(contents='1000\n1\n2\n3\n')=>page.locator('input[type=file]').setInputFiles({name:'X.csv',mimeType:'text/csv',buffer:Buffer.from(contents)});
    const reviewAndFit=async()=>{await page.getByRole('heading',{name:'Review X / Y / M roles'}).waitFor();const before=await page.evaluate(()=>window.__transport.workers.filter(w=>w.completed).length);await page.getByLabel('I confirm the displayed roles, join identifiers and partitions.').check();await page.getByRole('button',{name:'Import reviewed data',exact:true}).click();await page.getByRole('heading',{name:'Scoped analysis'}).waitFor();await page.getByRole('button',{name:'Train structure'}).click();await page.waitForFunction(n=>window.__transport.workers.filter(w=>w.completed).length>=n+2,before);};
    const json=async()=>{const pending=page.waitForEvent('download');await page.getByRole('button',{name:/Structured JSON/}).click();const download=await pending;const text=await page.evaluate(()=>window.__transport.blob.text());await download.cancel();return JSON.parse(text);};
    const successful=async()=>{await page.locator('.workspace-summary').waitFor();const report=await json();assert.equal(report.scientific_report.metrics.pca.value.eigenvalues[0],1);assert.equal(report.dataset.observations,3);return report;};
    await upload();await reviewAndFit();const first=await successful();
    assert(evidence.assets.some(a=>/io.*\.wasm|\.wasm.*io/i.test(a.file)&&a.status===200),'Reviewed table import must initialize published IO WASM');
    const imports=await page.evaluate(()=>window.__transport.workers.filter(w=>w.operation==='prepare_import'));
    assert(imports.length&&imports.every(w=>w.input_bytes>0&&w.transferred_bytes===w.input_bytes&&w.detached&&w.terminated));
    check('F3 real CSV: lazy modules, transferred/detached exact input bytes, original variance and worker termination');

    const wasm='**/nirs4all_io_wasm_bg-*.wasm';
    for(const fault of [
      {name:'HTTP_404',status:404,type:'text/plain',body:Buffer.from('not found'),reason:'WASM_ASSET_UNAVAILABLE'},
      {name:'HTML_RESPONSE',status:200,type:'text/html',body:Buffer.from('<html>wrong response</html>'),reason:'WASM_ASSET_INVALID_RESPONSE'},
      {name:'CORRUPT_BINARY',status:200,type:'application/wasm',body:Buffer.from([0,97,115,109]),reason:'WASM_ASSET_INVALID_BINARY'},
      {name:'INCOMPATIBLE_EXPORTS',status:200,type:'application/wasm',body:Buffer.from([0,97,115,109,1,0,0,0]),reason:'WASM_INITIALIZATION_FAILED'},
    ]){
      await home();phase=fault.name;await page.route(wasm,route=>route.fulfill({status:fault.status,contentType:fault.type,body:fault.body}));
      await upload();await page.getByRole('alert').waitFor();assert.equal(await page.locator('.workspace-summary').count(),0);
      const raw=await page.getByRole('alert').locator('pre').textContent();assert(raw.includes(fault.reason),`Missing exact ${fault.reason}: ${raw}`);evidence.faults.push({name:fault.name,reason:raw,no_result:true});
      await page.unroute(wasm);phase='recovery';await home();await upload();await reviewAndFit();const recovered=await successful();
      assert.equal(recovered.scientific_report.evidence_sha256,first.scientific_report.evidence_sha256);assert.deepEqual(recovered.scientific_report.metrics,first.scientific_report.metrics);
      check(`F3 actual WASM ${fault.name} refusal and fresh-worker recovery retain exact scientific evidence`);
    }
    await home();phase='replacement';await page.route(wasm,async route=>{await new Promise(done=>setTimeout(done,400));await route.continue().catch(()=>{});});
    await upload();await page.getByRole('button',{name:'Cancel analysis'}).waitFor();
    await page.locator('input[type=file]').evaluate(input=>{const files=new DataTransfer();files.items.add(new File(['1000\n0\n2\n4\n'],'X.csv',{type:'text/csv'}));input.files=files.files;input.dispatchEvent(new Event('change',{bubbles:true}));});
    await reviewAndFit();await page.locator('.workspace-summary').waitFor();const latest=await json();assert.equal(latest.scientific_report.metrics.pca.value.eigenvalues[0],4);
    assert.notEqual(latest.scientific_report.evidence_sha256,first.scientific_report.evidence_sha256);await page.unroute(wasm);
    check('F3 replacing an in-flight import terminates obsolete work and displays only the latest population');

    await home();phase='format-refusal';await page.locator('input[type=file]').setInputFiles({name:'invalid.spc',mimeType:'application/octet-stream',buffer:Buffer.from([0,1,2,3])});
    await page.getByRole('alert').waitFor();assert.equal(await page.locator('.workspace-summary').count(),0);
    assert(evidence.assets.some(a=>a.phase==='format-refusal'&&/formats.*wasm/i.test(a.file)&&a.status===200),'Non-table route must initialize the actual published Formats module');
    evidence.format_refusal=await page.getByRole('alert').locator('pre').textContent();
    phase='normal';await home();await upload();await reviewAndFit();await successful();check('F3 actual published Formats initializes for a non-table input, rejects corrupt source, and permits CSV recovery');
    assert.deepEqual(pageErrors,[]);assert(evidence.console.every(e=>e.phase!=='normal'&&e.phase!=='recovery'&&/Failed to load resource|ERR_ABORTED|ERR_FAILED|WebAssembly|WASM/i.test(e.message)),JSON.stringify(evidence.console));
    evidence.success=true;
  }finally{await context.close();await mkdir(resolve(output,'f3'),{recursive:true});await writeFile(resolve(output,'f3','loading.json'),JSON.stringify(evidence,null,2)+'\n');}
}
