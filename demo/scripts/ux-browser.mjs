/** Actual F2 interactions and targeted accessibility checks; consumes F1 evidence. */
import assert from 'node:assert/strict';
import { mkdir,writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import axe from 'axe-core';

export async function auditAccessibility(page,output,name,check){
  await page.evaluate(source=>{if(!window.axe){const script=document.createElement('script');script.textContent=source;document.head.appendChild(script);}},axe.source);
  const result=await page.evaluate(async()=>{
    const {violations,incomplete,passes}=await window.axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}});
    return {violations:violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),incomplete:incomplete.map(v=>({id:v.id,node_count:v.nodes.length,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),passed_rules:passes.length};
  });
  const dir=resolve(output,'f2');await mkdir(dir,{recursive:true});await writeFile(resolve(dir,`${name}.a11y.json`),JSON.stringify({engine:'axe-core 4.14.1',scope:'Targeted automated A/AA checks; not WCAG certification or actual screen-reader use',...result},null,2));
  assert.deepEqual(result.violations,[],`Accessibility violations in ${name}: ${JSON.stringify(result.violations)}`);
  check(`F2 targeted accessibility: ${name}`,{passed_rules:result.passed_rules,incomplete:result.incomplete.length});
}
export async function uxLanding(page,output,screenshot,check){
  const guide=page.locator('#import-guide');await guide.locator('summary').first().focus();await page.keyboard.press('Enter');
  assert(await guide.locator('details').first().getAttribute('open')!==null);
  assert(await guide.getByText(/32 files|32 fichiers/).count());
  await screenshot(page,'f2-import-guide');
  await auditAccessibility(page,output,'landing-import-guide',check);
  await guide.locator('summary').first().press('Enter');
}
export async function uxLive(page,report,output,exported,screenshot,check){
  assert.equal(await page.locator('.journey-nav a').count(),4);
  const before=JSON.stringify(report.scientific_report.metrics);
  await page.locator('.journey-nav a').nth(1).focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator(':focus').getAttribute('id'),'journey-2');
  await page.locator('.context-help summary').filter({hasText:/^PCA$/}).first().focus();await page.keyboard.press('Enter');
  const help=page.locator('.help-card').filter({has:page.getByText('A projection of centered spectral variation onto mathematical axes.',{exact:true})}).first();
  assert.equal(await help.getAttribute('open')!==null,true);
  await page.locator('.journey-nav a').nth(3).focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator(':focus').getAttribute('id'),'journey-4');
  await page.locator('input[name=reading][value=summary]').check();
  const summary=JSON.parse(await exported(page,'json')),html=await exported(page,'html'),markdown=await exported(page,'markdown');
  assert.equal(summary.reading_mode,'summary');assert.deepEqual(summary.scientific_report.metrics,report.scientific_report.metrics);
  assert(html.includes('Partial synthesis:'));assert(markdown.includes('Partial synthesis'));
  assert(!('spectra' in summary.dataset));
  const dir=resolve(output,'f2');await mkdir(dir,{recursive:true});
  if(process.env.CI)for(const [ext,value]of[['html',html],['md',markdown],['json',JSON.stringify(summary,null,2)]])await writeFile(resolve(dir,`live-synthesis.en.${ext}`),value);
  await screenshot(page,'f2-summary');
  await page.locator('input[name=reading][value=complete]').check();
  const complete=JSON.parse(await exported(page,'json'));assert.equal(complete.reading_mode,'complete');assert.equal(JSON.stringify(complete.scientific_report.metrics),before);
  await page.locator('#report-summary a[href="#data"]').focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator(':focus').getAttribute('id'),'data');
  assert.equal((await page.locator('#axis-from').inputValue()),'0');
  await auditAccessibility(page,output,'live-four-steps',check);
  check('F2 keyboard journey, context help, partial/complete F1 exports and return to the unchanged dataset');
  return html;
}
export async function confirmReviewedImport(page,operation){
  const before=await page.evaluate(()=>window.__domainsWorkerAudit?.completed.length??0);
  await page.getByLabel('I confirm the displayed roles, join identifiers and partitions.').check();
  await page.getByRole('button',{name:'Import reviewed data',exact:true}).click();
  await page.getByRole('heading',{name:'Scoped analysis',exact:true}).waitFor();
  if(operation){await page.getByRole('button',{name:operation,exact:true}).click();await page.waitForFunction(n=>window.__domainsWorkerAudit.completed.length>=n+2,before);await page.locator('.workspace-summary').waitFor();}
  else await page.waitForFunction(n=>window.__domainsWorkerAudit.completed.length>=n+1,before);
}
export async function uxSummaryOffline(browser,html,report,output,screenshot,check){
  const context=await browser.newContext({offline:true,viewport:{width:1200,height:900}});
  try{
    const page=await context.newPage();let external=0;page.on('request',r=>{if(/^https?:/.test(r.url()))external++;});
    await page.setContent(html);assert.equal(await page.locator('script').count(),0);
    await screenshot(page,'f2-synthesis-offline');
    assert.equal(await page.locator('.report-full-reading').getAttribute('open'),null);
    const source=JSON.parse(await page.locator('.report-complete pre').textContent());assert.deepEqual(source.scientific_report,report.scientific_report);
    const link=page.locator('#summary-reading a[href^="#evidence-"]').first();
    await link.click();assert.equal(await page.locator('.report-full-reading').getAttribute('open')!==null,true,'Native evidence link must reveal full offline details');
    await page.emulateMedia({media:'print'});assert(await page.locator('.report-full-reading').evaluate(n=>n.getBoundingClientRect().height===0));
    assert(await page.locator('.report-partial').first().evaluate(n=>n.getBoundingClientRect().height>0));
    await screenshot(page,'f2-synthesis-print');
    if(process.env.CI)await page.pdf({path:resolve(output,'f2','synthesis-a4.pdf'),format:'A4',printBackground:true});
    assert.equal(external,0);check('F2 partial offline HTML is labeled, retains full originals, opens exact evidence without scripts and prints the selected scope');
  }finally{await context.close();}
}
export async function uxExtraInputs(page,home,importCsv,json,output,screenshot,check,confirmImport=confirmReviewedImport){
  // Explicit declared IDs justify keyed alignment; local row order is not a join contract.
  await home(page);
  const spec={schema_version:1,name:'Synthetic metadata import',sources:[
    {id:'X',role:'features',input:'X.csv',partition:'train',key:'join_id',columns:{features:['1000','1100'],id:['join_id']},params:{delimiter:',',has_header:true}},
    {id:'M',role:'metadata',input:'M.csv',partition:'train',key:'join_id',join:{right:'X'},columns:{metadata:['acquisition','batch','site'],id:['join_id']},params:{delimiter:',',has_header:true}},
  ]};
  await page.locator('input[type=file]').setInputFiles([
    {name:'example.nirs4all.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(spec))},
    {name:'X.csv',mimeType:'text/csv',buffer:Buffer.from('join_id,1000,1100\nx-a,1,2\nx-b,2,3\nx-c,3,4\n')},
    {name:'M.csv',mimeType:'text/csv',buffer:Buffer.from('join_id,acquisition,batch,site\nx-c,c,g1,s2\nx-a,a,g1,s1\nx-b,b,g1,s1\n')},
  ]);
  await confirmImport(page,'Train structure');
  await page.locator('.workspace-summary').waitFor();const withMetadata=await json(page);
  assert.deepEqual(withMetadata.dataset.metadata,['join_id','acquisition','batch','site']);assert.equal(withMetadata.dataset.observations,3);
  assert.equal(withMetadata.provenance.physical_independence,'unknown');
  await screenshot(page,'f2-metadata-import');check('F2 actual IO metadata import preserves declared rows/columns and unknown physical units');
  // Reuse the already frozen declared-group-exclusion geometry, not tuned data.
  await home(page);await importCsv(page,'1100,1090\n'+Array.from({length:8},(_,i)=>`${i},${(i%3)*0.25}`).join('\n')+'\n');await page.locator('.workspace-summary').waitFor();
  const noise=await json(page),noiseStructure=noise.scientific_report.unpartitioned_structure??noise.scientific_report;
  assert.equal(noiseStructure.metrics.density.status,'computed');assert.equal(noiseStructure.metrics.density.value.n_clusters,0);
  assert(noiseStructure.metrics.density.value.labels.every(label=>label===-1));
  await page.evaluate(()=>{const target=document.getElementById('evidence-density');for(let p=target?.parentElement;p;p=p.parentElement)if(p instanceof HTMLDetailsElement)p.open=true;});
  assert.equal(await page.locator('#evidence-density .report-status').count(),1);
  check('F2 frozen synthetic geometry returns computed all-noise density, not unavailability');
  await home(page);await importCsv(page,'1000,1100\n1,2\n1,2\n1,2\n');await page.locator('.workspace-summary').waitFor();
  const constant=await json(page),constantStructure=constant.scientific_report.unpartitioned_structure??constant.scientific_report;
  assert.equal(constantStructure.metrics.pca.status,'unavailable');assert.equal(constant.pca,null);
  await page.locator('.journey-nav a').nth(1).click();assert.equal(await page.locator('#geometry .unavailable').count(),1);
  await screenshot(page,'f2-pca-unavailable');check('F2 real constant-X PCA refusal has no invented coordinates');
  // Intentional F4 protocol change: retain the old blanket full-source guard
  // in contracts.test.ts; the browser now imports inventory and tests a
  // selected train-structure operation without inventing a train population.
  for(const partition of ['test','predict']){
    await home(page);const retained={schema_version:1,name:'Synthetic retained-partition refusal',sources:[{id:'X',role:'features',input:'X.csv',partition}]};
    await page.locator('input[type=file]').setInputFiles([{name:'retained.nirs4all.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(retained))},{name:'X.csv',mimeType:'text/csv',buffer:Buffer.from('1000\n1\n2\n3\n')}]);
    await confirmImport(page);
    const imported=await json(page);assert.equal(imported.scientific_report.scoped_operations.length,0);
    assert.equal(imported.scientific_report.inventory.loaded.partitions[0].name,partition);
    assert.equal(imported.pca,null,'Importing retained X must not fit or display PCA');
    const before=await page.evaluate(()=>window.__domainsWorkerAudit.completed.length);
    await page.getByRole('button',{name:'Train structure',exact:true}).click();await page.waitForFunction(n=>window.__domainsWorkerAudit.completed.length>=n+1,before);await page.locator('.workspace-summary').waitFor();
    const refused=await json(page),operation=refused.scientific_report.scoped_operations.at(-1);
    assert.notEqual(operation.status,'computed');assert.equal(operation.value,null);
    assert.equal(refused.pca,null,'A test-only/predict-only population cannot produce train structure coordinates');
    check(`F4 train-structure request on ${partition}-only data is refused with no PCA result`,{status:operation.status,reason:operation.reason});
  }
  await screenshot(page,'f4-retained-refusal');
  await auditAccessibility(page,output,'f4-retained-refusal',check);
  await home(page);
}

export async function uxBlockedWasm(browser,url,check){
  // Fault injection is isolated from the zero-error normal-path audit. Record only
  // demonstrated blocked-WASM console failures; unexpected failures still fail.
  const context=await browser.newContext();const errors=[],requests=[];
  try{
    const page=await context.newPage();page.setDefaultTimeout(120000);
    page.on('console',msg=>{if(msg.type()==='error')errors.push(msg.text());});
    page.on('pageerror',error=>assert.fail(`Uncaught error during WASM refusal: ${error.message}`));
    context.on('request',request=>{if(/^https?:/.test(request.url()))assert(new URL(request.url()).origin===new URL(url).origin&&['GET','HEAD'].includes(request.method()));});
    await page.route('**/*.wasm',route=>{requests.push(route.request().url());return route.abort('failed');});
    await page.goto(url);await page.getByRole('button',{name:/Two spectral populations/}).click();await page.getByRole('alert').waitFor();
    assert.equal(await page.locator('.workspace-summary').count(),0);assert(requests.length>0);
    assert((await page.getByRole('alert').innerText()).includes('WASM'));
    assert(errors.every(error=>/Failed to load resource: net::ERR_FAILED|WebAssembly|fetch|WASM/i.test(error)),JSON.stringify(errors));
    check('F2 actual blocked-WASM refusal: no substitute result or off-origin requests',{expected_blocked_assets:requests.length,expected_console_errors:errors});
  }finally{await context.close();}
}

export async function uxSavedSummary(page,report,output,exported,screenshot,check){
  await page.getByRole('button',{name:'FR',exact:true}).click();
  await page.locator('input[name=reading][value=summary]').check();
  const translated=JSON.parse(await exported(page,'json'));
  assert.equal(translated.source_mode,'saved_qualified_report');assert.deepEqual(translated.scientific_report,report.scientific_report);
  const html=await exported(page,'html'),markdown=await exported(page,'markdown');
  assert(html.includes('Synthèse partielle'));assert(markdown.includes('Synthèse partielle'));
  if(process.env.CI)for(const [ext,value]of[['html',html],['md',markdown],['json',JSON.stringify(translated,null,2)]])await writeFile(resolve(output,'f2',`tablet-synthesis.fr.${ext}`),value);
  await page.locator('#report-summary').scrollIntoViewIfNeeded();await screenshot(page,'f2-saved-synthesis');
  await page.locator('input[name=reading][value=complete]').check();await page.getByRole('button',{name:'EN',exact:true}).click();
  check('F2 French saved partial exports retain original companions and never imply a browser refit');
}
