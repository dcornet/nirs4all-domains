/** F1 checks consume existing page/export results; they perform no extra fit. */
import assert from 'node:assert/strict';
import { mkdir,writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

export async function verifyEvidenceLinks(page) {
  const broken=await page.locator('a[href^="#evidence-"]').evaluateAll(links=>links.map(a=>a.getAttribute('href').slice(1)).filter(id=>!document.getElementById(id)));
  assert.deepEqual(broken,[],'Every evidence link must resolve to its exact displayed object');
}
export async function reportArtifacts(page, report, exported, output, name, check) {
  const html=await exported(page,'html'),markdown=await exported(page,'markdown');
  assert.equal(report.presentation.protocol_version,'domains.report_presentation.v1');
  assert.equal(report.raw_x_included,false);assert(!('spectra' in report.dataset));
  assert(!html.includes('<script'));assert(html.includes("default-src 'none'"));
  for(const block of report.presentation.blocks) {
    assert(html.includes(`id="evidence-${encodeURIComponent(block.id)}"`));
    assert(markdown.includes(block.id.replaceAll('_','\\_')));
  }
  await verifyEvidenceLinks(page);
  // Large examples/PDFs stay in ordinary CI artifacts, not the source tree.
  if(process.env.CI) {
    const destination=resolve(output,'f1','examples');await mkdir(destination,{recursive:true});
    for(const [ext,value] of [['html',html],['md',markdown],['json',JSON.stringify(report,null,2)+'\n']])await writeFile(resolve(destination,`${name}.${report.language}.${ext}`),value);
  }
  check(`F1 ${name}: original values, semantic tables, evidence anchors and three export formats`);
  return html;
}
export async function verifyOfflineReport(page, html, output, screenshot, check) {
  let foreign=0;page.on('request',r=>{if(/^https?:/.test(r.url()))foreign++;});
  await page.setContent(html);await verifyEvidenceLinks(page);
  assert.equal(await page.locator('script').count(),0);
  assert.equal(await page.locator('table caption').count()>0,true);
  assert.equal(await page.locator('.report-figure svg').count(),2);
  assert(await page.locator('.report-figure svg text').count()>8,'Figure axes must have ticks');
  await page.locator('#proof').scrollIntoViewIfNeeded();await screenshot(page,'report-detail');
  await page.emulateMedia({media:'print'});
  const hiddenOriginal=page.locator('.report-complete pre');
  assert(await hiddenOriginal.evaluate(node=>node.getBoundingClientRect().height>0),'Print must expose originally closed technical detail');
  await screenshot(page,'report-print-detail');
  if(process.env.CI) {
    const destination=resolve(output,'f1');await mkdir(destination,{recursive:true});
    await page.pdf({path:resolve(destination,'report-a4.pdf'),format:'A4',printBackground:true});
    await page.pdf({path:resolve(destination,'report-letter.pdf'),format:'Letter',printBackground:true});
  }
  assert.equal(foreign,0,'Standalone HTML must make no external request, even while offline');
  check('F1 offline HTML, graduated SVG, readable tables and printed closed details; A4/Letter PDFs in CI');
}
export async function verifySavedOffline(browser,html,report,screenshot,check) {
  const context=await browser.newContext({offline:true,viewport:{width:1200,height:900}});
  try {
    const page=await context.newPage();let requests=0;
    page.on('request',r=>{if(/^https?:/.test(r.url()))requests++;});
    await page.setContent(html);await verifyEvidenceLinks(page);
    assert.equal(await page.locator('.report-figure svg').count(),0);
    assert.equal(await page.locator('script').count(),0);
    const original=JSON.parse(await page.locator('.report-complete pre').textContent());
    assert.deepEqual(original.scientific_report,report.scientific_report);
    assert(await page.getByText('density_parameter',{exact:true}).count());
    assert(await page.getByText('not_executed',{exact:true}).count());
    assert.equal(requests,0);
    await page.locator('#evidence-decision_summary').evaluate(node=>node.scrollIntoView({block:'start',behavior:'instant'}));
    await screenshot(page,'saved-report-offline');
    check('F1 saved offline HTML retains exact original companions, density kind, unexecuted checks and no invented figures');
  } finally {await context.close();}
}
