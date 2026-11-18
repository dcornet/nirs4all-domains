/** Same-input, end-to-end engineering measurements; not a scientific benchmark. */
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,readdir,mkdir,writeFile} from 'node:fs/promises';
import {resolve,dirname,relative,extname,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {chromium} from 'playwright-core';

const demo=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const dist=resolve(process.env.DOMAINS_BENCH_DIST??resolve(demo,'dist'));
const output=resolve(process.env.DOMAINS_BENCH_OUTPUT??resolve(demo,'test-results/technical-benchmark.json'));
const repetitions=Number(process.env.DOMAINS_BENCH_REPETITIONS??3);
assert(Number.isInteger(repetitions)&&repetitions>=1&&repetitions<=3);
const base='/nirs4all-domains/',samples=[],assets=[];
const rankOneFixture={name:'X.csv',contents:'1000\n1\n2\n3\n'};
const scientificOf=report=>{
  const wrapper=report.scientific_report;
  if(wrapper?.protocol_version==='domains.browser_scoped_report.v1'){
    const scoped=wrapper.scoped_operations?.filter(operation=>operation.operation==='train_structure'&&operation.value?.structure).at(-1)?.value.structure;
    const scientific=scoped??wrapper.unpartitioned_structure;
    assert(scientific,'No executed structure in scoped report');
    return scientific;
  }
  return wrapper;
};
async function inventory(path){for(const f of await readdir(path,{withFileTypes:true})){const p=resolve(path,f.name);if(f.isDirectory())await inventory(p);else{const b=await readFile(p);assets.push({file:relative(dist,p).split(sep).join('/'),bytes:b.length,sha256:createHash('sha256').update(b).digest('hex')});}}}
await inventory(dist);
const mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.wasm':'application/wasm','.svg':'image/svg+xml','.json':'application/json'};
const server=createServer(async(req,res)=>{try{const path=new URL(req.url,'http://localhost').pathname;if(path.endsWith('/favicon.ico')){res.writeHead(204).end();return;}if(!path.startsWith(base)){res.writeHead(404).end();return;}const p=resolve(dist,decodeURIComponent(path.slice(base.length))||'index.html');if(relative(dist,p).startsWith('..')){res.writeHead(403).end();return;}const b=await readFile(p);res.writeHead(200,{'Content-Type':mime[extname(p)]??'application/octet-stream','Content-Length':b.length,'Cache-Control':'no-store'}).end(b);}catch{res.writeHead(404).end();}});
await new Promise(done=>server.listen(0,'127.0.0.1',done));
const url=`http://127.0.0.1:${server.address().port}${base}`;
let browser;
const result={protocol:'domains.technical_benchmark.v2',label:process.env.DOMAINS_BENCH_LABEL??'unspecified',browser:null,node:process.version,repetitions,fixture:'Unchanged X.csv rank-one CSV 3x1 and two-populations synthetic example 48x24; no real-source fit',assets,samples,success:false,measurement_limits:['Local HTTP timings are not Internet latency.','F4 import timing includes automatic IO prepare/assembly and one explicit structure action; it is workflow latency, not a matched import-throughput comparison with F2.','The unchanged synthetic example retains its matched before/after execution and exact report/hash comparison.','Worker request spans include loading, initialization, transport and owner execution; owner-internal phases are not separately observable.','CDP script/layout deltas include browser automation and are not pure React render time.','JS heap is the main-thread sample, not a process-tree peak; the external supervisor measures that peak.','Each repetition uses a fresh browser process/context; OS caches may persist.','Small fixtures do not establish a whole-bank memory or speed guarantee.']};
const metricMap=async c=>Object.fromEntries((await c.send('Performance.getMetrics')).metrics.map(m=>[m.name,m.value]));
try{
  for(let repetition=0;repetition<repetitions;repetition++){
    browser=await chromium.launch({headless:true,args:['--disable-gpu','--disable-extensions','--renderer-process-limit=1'],...(process.env.DOMAINS_BROWSER_EXE?{executablePath:process.env.DOMAINS_BROWSER_EXE}:{})});
    result.browser??=browser.version();
    const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true,locale:'en-US',colorScheme:'light'});
    try{
      await context.addInitScript(fixture=>{
        const WorkerBase=window.Worker;
        window.__technical={workers:[],lastBlob:null,captureRankOne:false,rankOne:{}};
        const requireFixture=files=>{
          if(!Array.isArray(files)||files.length!==1||files[0].name!==fixture.name||new TextDecoder().decode(files[0].bytes)!==fixture.contents)
            throw new Error('BENCHMARK_CAPTURE_REQUIRES_EXACT_PUBLIC_RANK_ONE_FIXTURE');
        };
        const requireMatrix=matrix=>{
          if(JSON.stringify(matrix)!=='[[1],[2],[3]]')throw new Error('BENCHMARK_CAPTURE_REQUIRES_UNCHANGED_RANK_ONE_VALUES');
        };
        const binding=input=>({schema_version:input.schema_version,dataset_id:input.dataset_id,source_id:input.source_id,
          content_sha256:input.content_sha256,observation_ids:input.observation_ids,axis:input.axis,axis_unit:input.axis_unit,
          group_ids:input.group_ids??null});
        window.Worker=class extends WorkerBase{
          constructor(...args){super(...args);this.audit={created:performance.now(),messages:[]};window.__technical.workers.push(this.audit);this.addEventListener('message',({data})=>{
            this.audit.messages.push({at:performance.now(),id:data.id,stage:data.stage??null,stage_id:data.stage_id??null,final:!data.stage,ok:data.ok});
            if(!this.capture||!data.ok||data.stage)return;
            if(['import','assemble_import'].includes(this.audit.operation)){
              let imported=data.result;
              if(this.audit.operation==='assemble_import'&&this.audit.importMode==='one_shot'){
                if(!this.audit.knownRankOneFixture)throw new Error('BENCHMARK_ONE_SHOT_CAPTURE_REQUIRES_KNOWN_FIXTURE');
                if(imported?.status!=='loaded'||!imported.dataset)throw new Error('BENCHMARK_ONE_SHOT_IMPORT_NOT_LOADED');
                imported=imported.dataset;
              }
              requireMatrix(imported.rawX??imported.input.spectra);
              if((imported.targets??[]).length)throw new Error('UNEXPECTED_BENCHMARK_TARGET');
              // This capture is armed only for the exact public X.csv fixture.
              // No generic imported values or private user configuration is saved.
              window.__technical.rankOne.imported={input:binding(imported.input),provenance:imported.importProvenance??null,
                reviewed_spec:imported.importProvenance?imported.importSpec:null};
            }
            if(this.audit.operation==='analyze')window.__technical.rankOne.actual_result=data.result;
            if(this.audit.operation==='scoped')window.__technical.rankOne.actual_result=data.result.value?.structure??null;
          });}
          postMessage(message,transfers){
            const start=performance.now();this.capture=window.__technical.captureRankOne;
            const files=['import','prepare_import'].includes(message.operation)?message.payload:[];
            if(this.capture&&files.length)requireFixture(files);
            if(this.capture&&message.operation==='assemble_import')requireFixture(message.payload.draft.files);
            if(this.capture&&message.operation==='analyze'){
              requireMatrix(message.payload.spectra);
              window.__technical.rankOne.analysis_request={...binding(message.payload),operation:'analyze',partitions:null};
            }
            if(this.capture&&message.operation==='scoped'){
              const r=message.payload;requireMatrix(r.x?.matrix);
              if(r.operation!=='train_structure'||r.fit!=='train'||r.query_keys.length||r.metadata.length||r.exclusion_field!==null||r.access.y_fields.length)
                throw new Error('UNEXPECTED_RANK_ONE_SCIENTIFIC_SCOPE');
              window.__technical.rankOne.analysis_request={...binding({schema_version:1,...r.dataset,observation_ids:r.x.row_keys,
                axis:r.x.axis,axis_unit:r.x.axis_unit}),operation:r.operation,partitions:r.manifest};
            }
            const bytes=Array.isArray(files)?files.reduce((sum,f)=>sum+(f.bytes?.byteLength??0),0):0;
            const transferred_bytes=(Array.isArray(transfers)?transfers:[]).reduce((sum,b)=>sum+(b.byteLength??0),0);
            this.audit.operation=message.operation;
            this.audit.importMode=message.operation==='assemble_import'?message.payload?.mode??null:null;
            if(this.capture&&message.operation==='assemble_import')this.audit.knownRankOneFixture=true;
            super.postMessage(message,transfers??[]);this.audit.post_message_ms=performance.now()-start;
            this.audit.input_bytes=bytes;this.audit.transferred_bytes=transferred_bytes;this.audit.sender_detached=Array.isArray(files)&&files.length>0&&files.every(f=>f.bytes.byteLength===0);
          }
          terminate(){this.audit.terminated=performance.now();return super.terminate();}
        };
        const create=URL.createObjectURL.bind(URL);URL.createObjectURL=blob=>{window.__technical.lastBlob=blob;return create(blob);};
      },rankOneFixture);
      const page=await context.newPage();page.setDefaultTimeout(120000);
      const network=[],networkPending=[];
      context.on('requestfinished',request=>{if(/\.wasm(?:\?|$)/.test(request.url()))networkPending.push((async()=>{const response=await request.response();const t=request.timing();network.push({asset:new URL(request.url()).pathname.split('/').pop(),duration_ms:t.responseEnd,body_bytes:Number(response?.headers()['content-length']??0),timing:t});})());});
      const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
      context.on('request',r=>{if(/^https?:/.test(r.url()))assert(new URL(r.url()).origin===new URL(url).origin&&['GET','HEAD'].includes(r.method()),'Unexpected upload/off-origin request');});
      const cdp=await context.newCDPSession(page);await cdp.send('Performance.enable');
      const started=performance.now();await page.goto(url);await page.locator('input[type=file]:not([webkitdirectory])').waitFor({state:'attached'});
      const landing_ms=performance.now()-started;
      await page.evaluate(()=>{window.__technical.captureRankOne=true;});
      const importedAt=performance.now();await page.locator('input[type=file]:not([webkitdirectory])').setInputFiles({name:rankOneFixture.name,mimeType:'text/csv',buffer:Buffer.from(rankOneFixture.contents)});
      const route=result.label==='F2-f4289f5'?'automatic':'one_shot';
      if(route==='automatic'){
        // The exact archived F2 frontend imports and analyzes automatically.
        // It predates F4 scope controls and the new loaded-dataset summary.
        await page.waitForFunction(()=>window.__technical.workers.some(w=>w.operation==='analyze'&&w.messages.some(m=>m.final)));
        assert.deepEqual(await page.evaluate(()=>window.__technical.workers.map(w=>w.operation)),['import','analyze'],
          'The frozen F2 source must retain its original import and analysis operations');
      }else{
        await page.locator('.workspace-summary').waitFor({state:'visible'});
        await page.getByRole('heading',{name:'Scoped analysis',exact:true}).waitFor();
        await page.locator('.dataset-loaded-summary').waitFor({state:'visible'});
        assert.equal(await page.getByRole('checkbox',{name:/I confirm the displayed roles, join identifiers and partitions/}).count(),0,'One-shot import has no mandatory confirmation checkbox');
        assert.equal(await page.getByRole('button',{name:'Import reviewed data'}).count(),0,'One-shot import has no second import action');
        await page.getByRole('button',{name:'Train structure'}).click();
        await page.waitForFunction(()=>window.__technical.workers.some(w=>w.operation==='scoped'&&w.messages.some(m=>m.final)));
        assert.deepEqual(await page.evaluate(()=>window.__technical.workers.map(w=>w.operation)),['prepare_import','assemble_import','scoped'],
          'A normal import and one analysis complete exactly three worker operations');
      }
      await page.locator('.workspace-summary').waitFor();await page.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));
      const import_to_visible_ms=performance.now()-importedAt;
      const exportReading=async format=>{
        const names={json:/Structured JSON/,html:/Offline HTML/,markdown:/^↓ Markdown$/};const start=performance.now();
        const pending=page.waitForEvent('download');await page.getByRole('button',{name:names[format]}).click();const download=await pending;
        const text=await page.evaluate(()=>window.__technical.lastBlob.text());await download.cancel();
        return {ms:performance.now()-start,bytes:Buffer.byteLength(text),text};
      };
      const json=await exportReading('json'),report=JSON.parse(json.text),scientific=scientificOf(report);
      assert.equal(scientific.metrics.pca.value.eigenvalues[0],1);assert.equal(report.dataset.observations,3);assert.equal(report.raw_x_included,false);
      const captured=await page.evaluate(()=>window.__technical.rankOne);
      assert.deepEqual(captured.actual_result,scientific,'Export must preserve the actual worker scientific result');
      assert(captured.imported&&captured.analysis_request,'Actual import and scientific request bindings required');
      const {operation,partitions,...requestBinding}=captured.analysis_request;
      assert.deepEqual(requestBinding,captured.imported.input,'Scientific execution must retain the actual imported source binding');
      assert.equal(scientific.scope.content_sha256,requestBinding.content_sha256);
      const rank_one={wrapper_protocol:report.scientific_report.protocol_version,protocol_version:scientific.protocol_version,
        input_sha256:scientific.input_sha256,evidence_sha256:scientific.evidence_sha256,scope:scientific.scope,metrics:scientific.metrics,
        source_binding:{kind:captured.imported.provenance?'file_bindings_reviewed_spec.v1':'file_bindings.v1',fixture:rankOneFixture,
          input:requestBinding,import_provenance:captured.imported.provenance,reviewed_spec:captured.imported.reviewed_spec},
        operation,population_manifest:partitions};
      await Promise.all(networkPending);const importNetwork=network.map(entry=>({...entry}));
      const workers=await page.evaluate(()=>window.__technical.workers);
      await page.evaluate(()=>{window.__technical.captureRankOne=false;});
      await page.getByRole('button',{name:/Domains · Home/}).click();await page.getByRole('button',{name:/Two spectral populations/}).click();await page.locator('.workspace-summary').waitFor();
      const live=JSON.parse((await exportReading('json')).text);const before=await metricMap(cdp);const renderAt=performance.now();
      for(let i=0;i<8;i++)await page.getByLabel('Target population',{exact:true}).fill(`Declared population ${i}`);
      await page.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));const after=await metricMap(cdp);
      const declaration_edit_ms=performance.now()-renderAt;
      const html=await exportReading('html'),markdown=await exportReading('markdown');
      const offline=await context.newPage();const offlineStart=performance.now();await offline.setContent(html.text);await offline.locator('.report-cover').waitFor();await offline.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));const offline_render_ms=performance.now()-offlineStart;
      assert.equal(await offline.locator('script').count(),0);await offline.close();assert.deepEqual(errors,[]);
      samples.push({repetition,landing_ms,import_to_visible_ms,import_route:route,network:importNetwork,workers,rank_one,
        live:{input_sha256:live.scientific_report.input_sha256,evidence_sha256:live.scientific_report.evidence_sha256,metrics:live.scientific_report.metrics,
          scientific_report:live.scientific_report},declaration_edit_ms,main_thread_script_delta_ms:(after.ScriptDuration-before.ScriptDuration)*1000,layout_delta_ms:(after.LayoutDuration-before.LayoutDuration)*1000,main_thread_heap_sample_bytes:after.JSHeapUsedSize,json_export:{ms:json.ms,bytes:json.bytes},html_export:{ms:html.ms,bytes:html.bytes},markdown_export:{ms:markdown.ms,bytes:markdown.bytes},offline_render_ms});
    }finally{await context.close();await browser.close();browser=null;}
  }
  result.success=true;
}catch(error){result.failure={name:error.name,message:error.message};process.exitCode=1;process.stderr.write(error.stack+'\n');}
finally{await browser?.close();await new Promise(done=>server.close(done));await mkdir(dirname(output),{recursive:true});await writeFile(output,JSON.stringify(result,null,2)+'\n');}
process.stdout.write(JSON.stringify({success:result.success,label:result.label,repetitions:samples.length,asset_bytes:assets.reduce((s,a)=>s+a.bytes,0),wasm:assets.filter(a=>a.file.endsWith('.wasm')).map(a=>({file:a.file,bytes:a.bytes})),timings:samples.map(s=>({import_ms:s.import_to_visible_ms,edit_ms:s.declaration_edit_ms,wasm_requests:s.network.length}))})+'\n');
