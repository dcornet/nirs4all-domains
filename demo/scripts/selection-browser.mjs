/** F3.5 consumes existing live/saved results. Selection/export never fits or creates groups. */
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {verifyEvidenceLinks} from './report-browser.mjs';

const option=(page,id)=>page.locator(`[data-export-section="${id}"]`);
const clear=page=>page.getByRole('button',{name:/Deselect supplements|Désélectionner les compléments/}).click();
const reset=page=>page.getByRole('button',{name:/Reset defaults|Réinitialiser les choix/}).click();
const manifest=[];
async function exportedCase(page,browser,output,exported,name,expected,check){
  const report=JSON.parse(await exported(page,'json')),html=await exported(page,'html'),markdown=await exported(page,'markdown');
  assert.equal(report.export_selection.protocol_version,'domains.report_export_selection.v1');
  assert.deepEqual(report.scientific_report,expected);assert.equal(report.raw_x_included,false);assert(!('spectra' in report.dataset));
  assert(!html.includes('<script'));assert(html.includes("default-src 'none'"));
  const directory=resolve(output,'f3_5');await mkdir(directory,{recursive:true});
  if(process.env.CI)for(const [extension,text]of[['html',html],['md',markdown],['json',JSON.stringify(report,null,2)]])await writeFile(resolve(directory,`${name}.${extension}`),text);
  const context=await browser.newContext({offline:true,viewport:{width:1200,height:900}});
  try{
    let requests=0;context.on('request',r=>{if(/^https?:/.test(r.url()))requests++;});
    const offline=await context.newPage();await offline.setContent(html);await verifyEvidenceLinks(offline);
    assert.equal(await offline.locator('script').count(),0);
    const original=JSON.parse(await offline.locator('.report-machine pre').textContent());assert.deepEqual(original.scientific_report,expected);
    const ids=await offline.locator('[id]').evaluateAll(nodes=>nodes.map(n=>n.id));assert.equal(new Set(ids).size,ids.length,'Duplicate evidence/section anchors');
    await offline.emulateMedia({media:'print'});
    const axisOverlaps=await offline.locator('.report-figure svg').evaluateAll(svgs=>svgs.flatMap(svg=>{
      const label=svg.querySelector('text[transform^="rotate"]');if(!label)return [];
      const a=label.getBoundingClientRect();return [...svg.querySelectorAll('text[text-anchor="end"]')].filter(t=>{const b=t.getBoundingClientRect();return Math.min(a.right,b.right)>Math.max(a.left,b.left)&&Math.min(a.bottom,b.bottom)>Math.max(a.top,b.top);}).map(t=>t.textContent);
    }));assert.deepEqual(axisOverlaps,[],'Printed axis labels must not overlap tick text');
    for(const section of report.export_selection.sections){
      if(section.id==='machine_evidence')continue;
      assert.equal(await offline.locator(`#supplement-${section.id}`).count(),report.export_selection.selected_sections.includes(section.id)?1:0);
      if(report.export_selection.selected_sections.includes(section.id))assert(await offline.locator(`#supplement-${section.id}`).evaluate(n=>n.getBoundingClientRect().height>0));
    }
    const machine=report.export_selection.selected_sections.includes('machine_evidence');
    assert.equal(await offline.locator('.report-machine pre').evaluate(n=>n.getBoundingClientRect().height>0),machine);
    if(process.env.CI)for(const format of ['A4','Letter']){
      const filename=`${name}-${format.toLowerCase()}.pdf`;
      await offline.pdf({path:resolve(directory,filename),format,printBackground:true});
      manifest.push({file:filename,format,name,machine,selected_sections:report.export_selection.selected_sections,
        required_text:name.startsWith('long-')?['LONG_SOURCE_END','documentary_field_649']:[],mode:report.source_mode});
    }
    assert.equal(requests,0);
  }finally{await context.close();}
  await writeFile(resolve(directory,'pdf-manifest.json'),JSON.stringify({protocol:'domains.export_selection_pdf_review.v1',cases:manifest,new_real_source_fits:0,page_limit:null},null,2));
  check(`F3.5 ${name}: selected reading, complete exact originals, offline links/CSP and A4/Letter print`);
  return report;
}
export async function qualifyLiveSelection(page,original,browser,output,exported,screenshot,check){
  const workers=await page.evaluate(()=>window.__domainsWorkerAudit.constructed);
  await clear(page);await page.locator('.export-options').scrollIntoViewIfNeeded();await screenshot(page,'f3-5-options-desktop');
  await exportedCase(page,browser,output,exported,'live-core',original.scientific_report,check);
  await option(page,'pca_scores').check();await option(page,'pca_scree').check();
  const figures=await exportedCase(page,browser,output,exported,'live-figures',original.scientific_report,check);
  await page.getByRole('button',{name:'FR',exact:true}).click();const french=JSON.parse(await exported(page,'json'));
  assert.deepEqual(french.export_selection,figures.export_selection);await page.getByRole('button',{name:'EN',exact:true}).click();
  await page.locator('input[name=intent][value=study]').check();await page.waitForFunction(()=>!document.querySelector('.run-banner'));
  const intent=JSON.parse(await exported(page,'json'));assert.deepEqual(intent.export_selection.selected_sections,figures.export_selection.selected_sections);
  assert.deepEqual(intent.scientific_report.metrics,original.scientific_report.metrics);assert.equal(intent.scientific_report.evidence_sha256,original.scientific_report.evidence_sha256);
  await page.locator('input[name=intent][value=unknown]').check();await page.waitForFunction(()=>!document.querySelector('.run-banner'));
  await page.getByRole('button',{name:'Select all available',exact:true}).click();
  await exportedCase(page,browser,output,exported,'live-all',JSON.parse(await exported(page,'json')).scientific_report,check);
  assert.equal(await page.evaluate(()=>window.__domainsWorkerAudit.constructed),workers+2,'Only the two existing intent interpretations may create workers; exports must not fit');
  await reset(page);check('F3.5 language/intent preserve section IDs and scientific metrics; reset restores legacy reading');
}
export async function qualifySavedSelection(page,original,browser,output,exported,screenshot,check){
  const workers=await page.evaluate(()=>window.__domainsWorkerAudit.constructed);
  await clear(page);assert(await option(page,'pca_scores').isDisabled());assert(await option(page,'pca_scree').isDisabled());assert(await option(page,'readiness').isEnabled());
  await exportedCase(page,browser,output,exported,'saved-core',original.scientific_report,check);
  for(const id of ['readiness','experimental_factors','extended_provenance'])await option(page,id).check();
  await page.locator('.export-options').scrollIntoViewIfNeeded();await screenshot(page,'f3-5-options-saved');
  await exportedCase(page,browser,output,exported,'saved-some',original.scientific_report,check);
  await page.getByRole('button',{name:'Select all available',exact:true}).click();
  await exportedCase(page,browser,output,exported,'saved-all',original.scientific_report,check);
  assert.equal(await page.evaluate(()=>window.__domainsWorkerAudit.constructed),workers);
  // Intentionally leave choices active: the original dataset transition must reset them.
}
export async function qualifySelectionReset(page,exported,check){
  const current=JSON.parse(await exported(page,'json'));assert.equal(current.export_selection,undefined);
  assert(await option(page,'pca_scores').isChecked());assert(await option(page,'readiness').isDisabled());
  check('F3.5 new dataset resets choices and rebuilds availability without stale saved references');
}
export async function qualifyLongSelection(browser,url,original,output,exported,screenshot,check,wire){
  const context=await browser.newContext({viewport:{width:1200,height:900}});wire(context,'f3-5-long-documentary-fixture');
  await context.addInitScript(()=>{const Original=window.Worker;window.__longWorkers=0;window.Worker=class extends Original{constructor(...args){super(...args);window.__longWorkers++;}};});
  try{
    const page=await context.newPage();page.setDefaultTimeout(120000);await page.goto(url);
    const fixture=structuredClone(original);fixture.title='Synthetic documentary stress fixture; not an authenticated study';
    fixture.cases[0].identity.value.dataset_id='synthetic-documentary-stress';
    fixture.limitations.push('Synthetic documentary source text. '.repeat(3200)+'LONG_SOURCE_END');
    const measurement=fixture.cases[0].companions.d1.value.warnings.find(w=>w.warning_id==='experimental_factor_structure').observation.value;
    measurement.documentary_fixture=Object.fromEntries(Array.from({length:650},(_,i)=>[`documentary_field_${i}`,`Synthetic text field ${i}; no new measurement`]));
    const numbers=(value,path='',out=[])=>{if(typeof value==='number')out.push([path,value]);else if(value&&typeof value==='object')for(const [key,child] of Object.entries(value))numbers(child,path+'/'+key,out);return out;};
    assert.deepEqual(numbers(fixture),numbers(original),'Documentary stress must preserve all original numerical leaves');
    await page.locator('input[type=file]:not([webkitdirectory])').setInputFiles({name:'synthetic-long-report.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(fixture))});
    await page.locator('.workspace-summary').waitFor();await clear(page);await option(page,'detailed_tables').check();
    await exportedCase(page,browser,output,exported,'long-documentary-reading',fixture,check);
    await option(page,'machine_evidence').check();
    const report=await exportedCase(page,browser,output,exported,'long-documentary-machine',fixture,check);
    assert.equal(report.provenance.browser_numerical_execution,false);assert(report.provenance.source_qualification.includes('not authenticated'));
    assert.equal(await page.evaluate(()=>window.__longWorkers),0);
    await page.setViewportSize({width:390,height:844});await page.getByRole('button',{name:'FR',exact:true}).click();
    await page.locator('.export-options').scrollIntoViewIfNeeded();await screenshot(page,'f3-5-options-mobile-panel',false,'.export-options');
    await page.locator('.export-options').evaluate(el=>scrollTo({top:el.getBoundingClientRect().top+scrollY-210,behavior:'instant'}));
    await screenshot(page,'f3-5-options-mobile-viewport');
    const layout=await page.evaluate(()=>({viewport:innerWidth,document_width:document.documentElement.scrollWidth,isolated_capture:'Sticky navigation hidden only during isolated component capture; viewport and layout assertions use unmodified UI.'}));
    await writeFile(resolve(output,'f3_5','mobile-layout.json'),JSON.stringify(layout,null,2));
    assert(layout.document_width<=layout.viewport+1);
    check('F3.5 long synthetic documentary copy: original public numerics unchanged, unauthenticated saved scope, mobile FR and no browser fit');
  }finally{await context.close();}
}
