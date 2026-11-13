/** End-to-end qualification of the built, subpath-hosted app; no mocked scientific output. */
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile, stat } from 'node:fs/promises';
import { resolve, dirname, extname, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium, firefox } from 'playwright-core';

const demo = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const dist = resolve(demo, 'dist');
const output = resolve(process.env.DOMAINS_BROWSER_RESULTS || resolve(demo, 'test-results/browser'));
const base = '/nirs4all-domains/';
const receipt = { started_at: new Date().toISOString(), base_path: base, checks: [], assets: [], screenshots: [], browsers: [], console_errors: [], page_errors: [], bounds: { screenshot_bytes: 10_000_000, operation_timeout_ms: 120_000 }, success: false };
await stat(resolve(dist, 'index.html'));
await mkdir(output, { recursive: true });
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.wasm': 'application/wasm', '.css': 'text/css', '.svg': 'image/svg+xml', '.json': 'application/json' };
const server = createServer(async (req, res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    if (pathname.endsWith('favicon.ico')) { res.writeHead(204).end(); return; }
    if (!pathname.startsWith(base)) { res.writeHead(404).end(); return; }
    const path = resolve(dist, pathname.slice(base.length) || 'index.html');
    if (relative(dist, path).startsWith(`..${sep}`) || relative(dist, path) === '..') { res.writeHead(403).end(); return; }
    const data = await readFile(path);
    res.writeHead(200, { 'Content-Type': mime[extname(path)] || 'application/octet-stream', 'Cache-Control': 'no-store' }).end(data);
  } catch { res.writeHead(404).end(); }
});
await new Promise(resolveListening => server.listen(0, '127.0.0.1', resolveListening));
const url = `http://127.0.0.1:${server.address().port}${base}`;
receipt.url = url;
let screenshotBytes = 0;
const browsers = [];
function check(name, detail = {}) { receipt.checks.push({ name, ...detail }); process.stdout.write(`PASS ${name}\n`); }
async function visible(locator) { await locator.waitFor({ state: 'visible', timeout: 120_000 }); }
async function screenshot(page, name, fullPage = false) {
  const path = resolve(output, `${name}.png`);
  const bytes = await page.screenshot({ path, fullPage, animations: 'disabled' });
  screenshotBytes += bytes.length;
  assert(screenshotBytes <= receipt.bounds.screenshot_bytes, 'Screenshot budget exceeded');
  receipt.screenshots.push({ file: `${name}.png`, bytes: bytes.length });
}
async function exported(page, format) {
  const labels = { json: /Structured JSON|JSON structuré/, html: /Offline HTML|HTML hors ligne/, markdown: /^↓ Markdown$/ };
  const waiting = page.waitForEvent('download');
  await page.getByRole('button', { name: labels[format] }).click();
  const download = await waiting;
  const path = await download.path();
  assert(path, 'Download failed');
  return readFile(path, 'utf8');
}
async function json(page) { return JSON.parse(await exported(page, 'json')); }
async function home(page) { await page.getByRole('button', { name: /Domains · Home|Domains · Accueil/ }).click(); await visible(page.locator('input[type=file]')); }
async function example(page, name) { await page.getByRole('button', { name: new RegExp(name) }).click(); await visible(page.locator('.workspace-summary')); }
async function importCsv(page, contents, name = 'X.csv') {
  await page.locator('input[type=file]').setInputFiles({ name, mimeType: 'text/csv', buffer: Buffer.from(contents) });
}
function wire(context, label) {
  context.on('console', msg => { if (msg.type() === 'error') receipt.console_errors.push({ browser: label, message: msg.text().slice(0, 1000) }); });
  context.on('page', page => page.on('pageerror', error => receipt.page_errors.push({ browser: label, message: error.message.slice(0, 1000) })));
  context.on('response', response => {
    if (/\.(wasm|js|css|svg)(?:\?|$)/.test(response.url())) receipt.assets.push({ browser: label, url: response.url().replace(url, base), status: response.status(), declared_bytes: Number(response.headers()['content-length'] || 0) });
  });
}
try {
  const browser = await chromium.launch({ headless: true, args: ['--disable-gpu', '--disable-extensions', '--renderer-process-limit=1'], ...(process.env.DOMAINS_BROWSER_EXE ? { executablePath: process.env.DOMAINS_BROWSER_EXE } : {}) });
  browsers.push(browser); receipt.browsers.push({ name: 'chromium', version: browser.version() });
  let context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true, locale: 'en-US', colorScheme: 'light' });
  wire(context, 'chromium-desktop');
  await context.addInitScript(() => {
    const OriginalWorker = window.Worker;
    window.__domainsWorkerAudit = { constructed: 0, terminated: 0 };
    window.Worker = class extends OriginalWorker {
      constructor(...args) { super(...args); window.__domainsWorkerAudit.constructed++; }
      terminate() { window.__domainsWorkerAudit.terminated++; return super.terminate(); }
    };
  });
  let page = await context.newPage(); page.setDefaultTimeout(120_000);
  await page.goto(url); await visible(page.getByRole('heading', { name: 'Analyze my data' }));
  await screenshot(page, 'landing-desktop');
  await page.keyboard.press('Tab'); assert.equal(await page.locator(':focus').textContent(), 'Skip to content');
  await page.keyboard.press('Enter'); assert.equal(await page.locator(':focus').getAttribute('id'), 'main');
  check('Subpath landing and keyboard skip link');

  await example(page, 'Two spectral populations');
  const initial = await json(page);
  assert.equal(initial.source_mode, 'synthetic_computed_live');
  assert.equal(initial.scientific_report.metrics.pca.status, 'computed');
  assert(initial.scientific_report.metrics.pca.value.eigenvalues[0] > 0);
  assert(receipt.assets.some(asset => /\.wasm/.test(asset.url) && asset.status === 200), 'No actual WASM response');
  check('Real synthetic example computes Methods PCA in WASM', { first_eigenvalue: initial.scientific_report.metrics.pca.value.eigenvalues[0] });
  await page.locator('#spectra').scrollIntoViewIfNeeded(); await screenshot(page, 'spectra');
  await page.locator('#geometry').scrollIntoViewIfNeeded(); await screenshot(page, 'pca');
  await page.getByLabel('Select an observation').selectOption({ index: 1 });
  await visible(page.locator('.selection')); check('Spectrum selection');
  await page.getByLabel('First displayed variable index').fill('2');
  assert.equal(await page.locator('#axis-from').inputValue(), '2');
  await page.getByRole('button', { name: 'Reset view' }).click();
  assert.equal(await page.locator('#axis-from').inputValue(), '0'); check('Display-only axis zoom and reset');
  await page.locator('#warnings').scrollIntoViewIfNeeded();
  await page.locator('.finding details').first().getByText('Understand this finding', { exact: true }).click();
  await screenshot(page, 'findings');
  await page.getByLabel('Target population', { exact: true }).fill('future specimens <unverified>');
  await page.getByLabel('Prediction unit', { exact: true }).fill('physical specimen');
  await page.getByLabel('New acquisition or study context', { exact: true }).fill('a separate study');
  const interpretationWorkers = await page.evaluate(() => window.__domainsWorkerAudit.terminated);
  await page.getByRole('radio', { name: 'A new study or acquisition context' }).check();
  await page.waitForFunction(before => window.__domainsWorkerAudit.terminated > before, interpretationWorkers);
  await page.waitForFunction(() => document.querySelector('.workspace-summary') && !document.querySelector('[role=alert]'));
  const changed = await json(page);
  assert.equal(changed.intended_use, 'new_context');
  assert.equal(changed.provenance.evidence_sha256, initial.provenance.evidence_sha256);
  assert.deepEqual(changed.scientific_report.metrics, initial.scientific_report.metrics);
  assert.equal(changed.user_declarations.prediction_unit, 'physical specimen');
  assert.equal(changed.provenance.verification_execution, 'not_executed');
  check('Intent changes contextual reading without numerical refit; declarations remain unverified');
  await page.locator('#intent').scrollIntoViewIfNeeded(); await screenshot(page, 'decision');

  await page.getByRole('button', { name: 'Switch theme' }).click();
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
  await page.getByRole('button', { name: 'FR', exact: true }).click();
  assert.equal(await page.locator('html').getAttribute('lang'), 'fr');
  const translated = await json(page), markdown = await exported(page, 'markdown'), html = await exported(page, 'html');
  assert.equal(translated.language, 'fr');
  assert.deepEqual(translated.evidence, changed.evidence);
  assert(html.includes('lang="fr"') && markdown.includes('Comprendre la structure de vos spectres'));
  assert(html.includes(translated.dataset.contentHash) && markdown.includes(translated.dataset.contentHash));
  assert.equal(translated.raw_x_included, false); assert(!('spectra' in translated.dataset));
  check('Theme, French UI and consistent HTML / Markdown / JSON exports');
  const preferences = await context.storageState();
  await context.close(); // Qualify the complete offline report serially, without retaining a WASM renderer.
  const reportContext = await browser.newContext({ offline: true, viewport: { width: 1200, height: 900 } });
  const reportPage = await reportContext.newPage();
  await reportPage.setContent(html); assert.equal(await reportPage.locator('script').count(), 0);
  assert.equal(await reportPage.locator('[http-equiv="Content-Security-Policy"]').count(), 1);
  await visible(reportPage.getByRole('heading', { name: 'Comprendre la structure de vos spectres' }));
  await screenshot(reportPage, 'report-offline');
  await reportPage.emulateMedia({ media: 'print' }); await screenshot(reportPage, 'report-print');
  await reportContext.close(); check('Standalone report renders offline with CSP and no scripts; print layout');
  context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true, locale: 'en-US', colorScheme: 'light', storageState: preferences });
  wire(context, 'chromium-desktop-import');
  await context.addInitScript(() => {
    const OriginalWorker = window.Worker;
    window.__domainsWorkerAudit = { constructed: 0, terminated: 0 };
    window.Worker = class extends OriginalWorker {
      constructor(...args) { super(...args); window.__domainsWorkerAudit.constructed++; }
      terminate() { window.__domainsWorkerAudit.terminated++; return super.terminate(); }
    };
  });
  page = await context.newPage(); page.setDefaultTimeout(120_000); await page.goto(url);
  await page.getByRole('button', { name: 'EN', exact: true }).click();
  await page.getByRole('button', { name: 'Switch theme' }).click();

  await home(page); await importCsv(page, '1000\n1\n2\n3\n');
  await visible(page.locator('.workspace-summary'));
  const imported = await json(page);
  assert.equal(imported.source_mode, 'user_computed_live');
  assert.equal(imported.dataset.observations, 3); assert.equal(imported.dataset.variables, 1);
  assert(Math.abs(imported.scientific_report.metrics.pca.value.eigenvalues[0] - 1) < 1e-10, '3×1 sample covariance must be one');
  assert.equal(imported.provenance.physical_independence, 'unknown');
  assert(receipt.assets.some(asset => /io.*\.wasm|\.wasm.*io/i.test(asset.url)), 'IO WASM was not loaded');
  assert(await page.getByText('Not provided in this import.', { exact: false }).count());
  await screenshot(page, 'import'); check('User CSV 3×1 decoded by IO WASM; PCA eigenvalue one and unknown physical independence');

  await home(page); await example(page, 'A justified unavailable result');
  const small = await json(page);
  assert.equal(small.scientific_report.metrics.density.status, 'unavailable');
  assert(small.scientific_report.metrics.density.reason);
  await page.locator('#evidence').scrollIntoViewIfNeeded(); await screenshot(page, 'unavailable');
  check('Small population preserves density unavailability and reason');

  await home(page);
  const beforeSavedWorkers = await page.evaluate(() => window.__domainsWorkerAudit.constructed);
  await example(page, 'Tablets: a qualified saved report');
  const saved = await json(page);
  assert.equal(saved.provenance.browser_numerical_execution, false);
  assert.equal(await page.evaluate(() => window.__domainsWorkerAudit.constructed), beforeSavedWorkers);
  assert.equal(saved.dataset.variables, null);
  const variantResponse = page.waitForResponse(response => /tablet\.new_specimens\.saved\.json$/.test(response.url()) && response.status() === 200);
  await page.getByRole('radio', { name: 'New physical specimens' }).check();
  await variantResponse;
  await page.waitForFunction(() => !document.querySelector('[role=alert]'));
  const savedVariant = await json(page);
  assert.equal(savedVariant.intended_use, 'new_specimens');
  assert.equal(await page.evaluate(() => window.__domainsWorkerAudit.constructed), beforeSavedWorkers);
  check('Qualified tablet saved report and intent variant without any worker numerical fit');

  await home(page);
  await page.route('**/*.wasm', route => new Promise(resolveRoute => setTimeout(() => resolveRoute(route.continue().catch(() => {})), 800)));
  const auditBefore = await page.evaluate(() => ({ ...window.__domainsWorkerAudit }));
  await page.getByRole('button', { name: /Two spectral populations/ }).click();
  await page.waitForFunction(before => window.__domainsWorkerAudit.constructed > before, auditBefore.constructed);
  await visible(page.getByRole('button', { name: 'Cancel analysis' }));
  await page.getByRole('button', { name: 'Cancel analysis' }).click();
  await page.waitForTimeout(1100);
  assert.equal(await page.locator('.workspace-summary').count(), 0);
  assert(await page.getByText('Analysis cancelled.', { exact: false }).count());
  const auditAfter = await page.evaluate(() => ({ ...window.__domainsWorkerAudit }));
  assert(auditAfter.constructed > auditBefore.constructed && auditAfter.terminated > auditBefore.terminated);
  await page.unroute('**/*.wasm'); check('Cancellation terminates the actual Worker and rejects stale result');

  for (const [name, buffer, expected] of [
    ['malformed.json', Buffer.from('{broken'), /JSON|Unexpected|property|position/i],
    ['X.csv', Buffer.from('1000,1100\n1,\n2,3\n4,5\n'), /NONFINITE|missing|finite|NaN/i],
    ['too-large.csv', null, /BUDGET_EXCEEDED/i],
  ]) {
    await home(page);
    if (buffer === null) {
      // A real oversize browser File, without an unnecessary base64/CDP copy in the test harness.
      await page.locator('input[type=file]').evaluate(input => {
        const transfer = new DataTransfer();
        transfer.items.add(new File([new Uint8Array(8 * 1024 * 1024 + 1)], 'too-large.csv', { type: 'text/csv' }));
        input.files = transfer.files; input.dispatchEvent(new Event('change', { bubbles: true }));
      });
    } else await page.locator('input[type=file]').setInputFiles({ name, mimeType: 'text/plain', buffer });
    await visible(page.getByRole('alert'));
    assert(expected.test(await page.getByRole('alert').innerText()), `Unexpected refusal category: ${name}`);
    assert.equal(await page.locator('.workspace-summary').count(), 0);
    check(`Explicit refusal: ${name}`);
  }
  await home(page);
  const malicious = '<img src=x onerror=alert(1)>.csv';
  await importCsv(page, '1000\n1\n2\n3\n', malicious); await visible(page.locator('.workspace-summary'));
  const safeHtml = await exported(page, 'html');
  assert(!safeHtml.includes('<img src=x onerror=alert(1)>'));
  assert(!safeHtml.includes('<script>'));
  check('Malicious import filename remains escaped in report export');
  await home(page); await example(page, 'Two spectral populations');
  assert.equal((await json(page)).source_mode, 'synthetic_computed_live'); check('Example reload after cancellations and refusals');
  await context.close();

  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, deviceScaleFactor: 1, hasTouch: true, locale: 'en-US' });
  wire(mobile, 'chromium-mobile');
  const mobilePage = await mobile.newPage(); mobilePage.setDefaultTimeout(120_000);
  await mobilePage.goto(url); await screenshot(mobilePage, 'landing-mobile', true);
  await example(mobilePage, 'A justified unavailable result');
  assert(await mobilePage.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Mobile document overflows');
  await mobilePage.getByRole('button', { name: 'FR', exact: true }).click();
  assert.equal(await mobilePage.locator('html').getAttribute('lang'), 'fr');
  check('Chromium mobile example, language and no horizontal document overflow');
  await mobile.close();
  await browser.close(); // Browser engines are qualified serially, preserving the same resource envelope.
  if (process.env.DOMAINS_FIREFOX_EXE || process.env.DOMAINS_TEST_FIREFOX === '1') {
    const second = await firefox.launch({ headless: true, ...(process.env.DOMAINS_FIREFOX_EXE ? { executablePath: process.env.DOMAINS_FIREFOX_EXE } : {}) }); browsers.push(second);
    receipt.browsers.push({ name: 'firefox', version: second.version() });
    const secondContext = await second.newContext(); wire(secondContext, 'firefox'); const secondPage = await secondContext.newPage();
    await secondPage.goto(url); await example(secondPage, 'A justified unavailable result');
    assert((await json(secondPage)).scientific_report.metrics.pca.value.eigenvalues[0] > 0); check('Firefox actual WASM example');
    await secondContext.close();
  } else receipt.second_engine = 'not_executed: DOMAINS_FIREFOX_EXE not supplied';
  assert.equal(receipt.page_errors.length, 0, 'Uncaught browser errors');
  assert.equal(receipt.console_errors.length, 0, 'Browser console errors');
  receipt.success = true;
} catch (error) {
  receipt.failure = { name: error.name, message: error.message, stack: error.stack?.split('\n').slice(0, 6).join('\n') };
  process.exitCode = 1;
  process.stderr.write(`${error.stack}\n`);
} finally {
  for (const browser of browsers) await browser.close().catch(() => {});
  await new Promise(resolveClose => server.close(resolveClose));
  receipt.finished_at = new Date().toISOString(); receipt.screenshot_bytes = screenshotBytes;
  receipt.asset_declared_bytes = receipt.assets.reduce((sum, asset) => sum + asset.declared_bytes, 0);
  receipt.memory_measurement = 'Node process only; browser process resource bounds are measured by the external OS guard, not inferred here.';
  receipt.node_memory_bytes = process.memoryUsage();
  await writeFile(resolve(output, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n');
}
