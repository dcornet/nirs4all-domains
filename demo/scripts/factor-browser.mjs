/** Actual browser qualification for imported F4.1 factor/PCA association and coloring. */
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fixture, loadReviewed } from './scoped-browser.mjs';
import { auditAccessibility } from './ux-browser.mjs';

function factorFixture() {
  const base = fixture();
  const configFile = base.files.find(file => file.name === 'f4-scoped.nirs4all.json');
  assert(configFile, 'Scoped qualification fixture must include its reviewed import configuration');
  const config = JSON.parse(configFile.buffer.toString('utf8'));
  for (const [partition, count] of [['train', 8], ['test', 2], ['predict', 1]]) {
    const idPrefix = partition === 'train' ? 'tr' : partition === 'test' ? 'te' : 'pr';
    const sourceId = `M_${partition}`;
    const source = config.sources.find(item => item.id === sourceId);
    assert(source, `Fixture metadata source ${sourceId} must exist`);
    source.columns.metadata.push('dose');
    const file = base.files.find(item => item.name === `${sourceId}.csv`);
    assert(file, `Fixture metadata file ${sourceId}.csv must exist`);
    const rows = file.buffer.toString('utf8').trim().split(/\r?\n/).map(line => line.split(','));
    rows[0].push('dose');
    for (const row of rows.slice(1)) {
      const match = new RegExp(`^${idPrefix}-(\\d+)$`).exec(row[0]);
      assert(match, `Unexpected fixture row key ${row[0]}`);
      const rowNumber = Number(match[1]);
      const dose = partition === 'train' ? rowNumber : partition === 'test' ? 9_999 + rowNumber : 8_888 + rowNumber;
      row.push(String(dose));
    }
    file.buffer = Buffer.from(rows.map(row => row.join(',')).join('\n') + '\n');
    config.metadata_declarations[`${sourceId}__dose`] = { role: 'factor', derived_from_target: false, unit: '°C' };
    assert.equal(rows.length - 1, count);
  }
  configFile.buffer = Buffer.from(JSON.stringify(config));
  return base;
}

async function instrumentFactorWorkers(page) {
  await page.evaluate(() => {
    const Original = window.Worker;
    window.__f41FactorWorkers = { operations: [], completed: [] };
    window.Worker = class extends Original {
      constructor(...args) {
        super(...args);
        this.factorOperation = 'unknown';
        this.addEventListener('message', ({ data }) => {
          if (!data.stage) window.__f41FactorWorkers.completed.push({ operation: this.factorOperation, ok: data.ok });
        });
      }
      postMessage(message, transfer) {
        this.factorOperation = message.operation;
        window.__f41FactorWorkers.operations.push(message.operation);
        return super.postMessage(message, transfer);
      }
    };
  });
}

async function waitWorker(page, button) {
  const before = await page.evaluate(() => window.__f41FactorWorkers.completed.length);
  await page.getByRole('button', { name: button, exact: true }).click();
  await page.waitForFunction(count => window.__f41FactorWorkers.completed.length > count, before);
  await page.locator('.workspace-summary').waitFor();
}

async function capture(page, format, exported) {
  return exported(page, format);
}

function association(report, factorId, population = 'train') {
  const records = report.scientific_report.factor_associations ?? [];
  return [...records].reverse().find(record => record.status === 'computed'
    && record.value?.population === population
    && record.value?.factors?.some(factor => factor.factor_id === factorId));
}

function assertNoRowLevelColorExport(text, format) {
  for (const token of ['factor-level-0', 'factor-level-1', 'factor-bin-', 'factor-missing']) {
    assert(!text.includes(token), `${format} export disclosed a row-level factor-color token ${token} without authorization`);
  }
}

export async function qualifyFactorBrowser({ page, context, url, output, check, exported, json, screenshot }) {
  const browserName = page.context().browser()?.browserType().name() ?? 'browser';
  const captures = { protocol: 'domains.f4_1_factor_browser_qualification.v1', browser: browserName, success: false, checks: [], operations: [], exports: {}, screenshots: [] };
  const fixtureData = factorFixture();
  const outputDir = resolve(output, 'f4.1', browserName);
  await mkdir(outputDir, { recursive: true });
  await page.goto(url);
  page.setDefaultTimeout(120_000);
  const englishButton = page.getByRole('button', { name: 'EN', exact: true });
  if (await englishButton.getAttribute('aria-pressed') !== 'true') await englishButton.click();
  await instrumentFactorWorkers(page);
  await loadReviewed(page, fixtureData.files);
  const initial = await json(page);
  assert.equal(initial.scientific_report.factor_associations?.length ?? 0, 0, 'Import must not calculate factor associations');

  await waitWorker(page, 'Train structure');
  let current = await json(page);
  const trainOperation = [...current.scientific_report.scoped_operations].reverse().find(item => item.operation === 'train_structure' && item.status === 'computed');
  assert(trainOperation, 'A train-only PCA receipt is required before factor association');
  assert.equal(trainOperation.receipt.fit_keys.length, 8);
  assert.deepEqual(trainOperation.receipt.fit_keys, trainOperation.receipt.reference_keys);
  assert.equal(trainOperation.receipt.y_accessed, false);
  captures.operations.push({ operation: 'train_structure', status: trainOperation.status, receipt: trainOperation.receipt });

  const factorSelector = page.getByRole('combobox', { name: 'Factor', exact: true });
  await factorSelector.selectOption('batch');
  assert.equal(await page.getByRole('button', { name: 'Run factor association', exact: true }).isEnabled(), true);
  const beforeFactor = await page.evaluate(() => window.__f41FactorWorkers.completed.length);
  await page.getByRole('button', { name: 'Run factor association', exact: true }).click();
  await page.waitForFunction(count => window.__f41FactorWorkers.completed.length > count, beforeFactor);
  current = await json(page);
  const categorical = association(current, 'batch');
  assert(categorical, 'Owner factor result for selected batch factor must be present');
  assert.equal(categorical.receipt.pca_refits, 0);
  assert.equal(categorical.receipt.fields_read.x, false);
  assert.deepEqual(categorical.receipt.fields_read.y, []);
  assert.equal(categorical.receipt.y_accessed, false);
  assert.equal(categorical.receipt.test_m_accessed, false);
  assert.deepEqual(categorical.receipt.fit_keys, trainOperation.receipt.fit_keys);
  assert(categorical.receipt.fit_keys.every(key => JSON.parse(key)[1] === 'train'));
  assert.equal(categorical.value.factors[0].n_fit_observations, 8);
  assert.equal(categorical.value.factors[0].n_used, 8);
  assert.equal(categorical.value.factors[0].n_missing, 0);
  assert(categorical.value.factors[0].level_counts?.length >= 2);
  assert(categorical.receipt.provider_calls.length > 0);
  for (const call of categorical.receipt.provider_calls) {
    for (const [name, item] of Object.entries(call.inputs ?? {})) {
      assert.equal(item.count, 8, `Provider ${name} must contain only eight train rows`);
    }
  }
  const mReceipts = categorical.receipt.fields_read.m;
  assert(mReceipts.every(field => field.n_rows === 8 && !('values' in field) && !('row_keys' in field)));
  assert(!JSON.stringify(categorical.receipt).includes('batch-test'));
  for (const call of categorical.receipt.provider_calls) {
    for (const input of Object.values(call.inputs ?? {})) {
      assert.equal(typeof input, 'object');
      assert(!Array.isArray(input), 'Provider receipt stores input hashes/counts, not factor code or value arrays');
      assert.equal(typeof input.sha256, 'string');
      assert.equal(input.count, 8);
    }
  }
  captures.operations.push({ operation: 'factor_association', factor_id: 'batch', status: categorical.status, receipt: categorical.receipt });
  check('F4.1 categorical association is keyed to train PCA; receipt shows no X/Y/test-M provider inputs or refits');

  const categoricalMarkup = await page.locator('.factor-association-results').last().innerText();
  assert.match(categoricalMarkup, /Association with each resolved PCA component/);
  assert.match(categoricalMarkup, /Observed level counts/);
  await page.locator('.factor-association-controls').scrollIntoViewIfNeeded();
  await screenshot(page, `${browserName}-f4.1-factor-controls-en`, false, '.factor-association-controls');
  await screenshot(page, `${browserName}-f4.1-factor-results-en`, false, '.factor-association-results');
  captures.screenshots.push(`${browserName}-f4.1-factor-controls-en`, `${browserName}-f4.1-factor-results-en`);

  const baseScientific = JSON.stringify({
    scoped: current.scientific_report.scoped_operations,
    associations: current.scientific_report.factor_associations,
    scores: current.pca?.points?.map(({ id, x, y }) => [id, x, y]),
  });
  const workersBeforeCategoricalColor = await page.evaluate(() => window.__f41FactorWorkers.operations.length);
  await page.getByRole('button', { name: 'Color PCA by this factor (display only)', exact: true }).first().click();
  await page.locator('.factor-color-legend').waitFor();
  assert.equal(await page.evaluate(() => window.__f41FactorWorkers.operations.length), workersBeforeCategoricalColor,
    'Categorical color change must not run a worker operation');
  current = await json(page);
  assert.equal(JSON.stringify({
    scoped: current.scientific_report.scoped_operations,
    associations: current.scientific_report.factor_associations,
    scores: current.pca?.points?.map(({ id, x, y }) => [id, x, y]),
  }), baseScientific, 'Coloring must leave scientific operations and coordinates unchanged');

  const workerBeforeContinuous = await page.evaluate(() => window.__f41FactorWorkers.completed.length);
  await factorSelector.selectOption('dose');
  assert.equal(await page.getByRole('combobox', { name: 'Continuous association measure', exact: true }).inputValue(), 'pearson');
  await page.getByRole('button', { name: 'Run factor association', exact: true }).click();
  await page.waitForFunction(count => window.__f41FactorWorkers.completed.length > count, workerBeforeContinuous);
  current = await json(page);
  const continuous = association(current, 'dose');
  assert(continuous, 'Owner factor result for selected continuous dose factor must be present');
  assert.equal(continuous.value.factors[0].kind, 'continuous');
  assert.equal(continuous.value.factors[0].unit, '°C');
  assert.equal(continuous.value.factors[0].n_fit_observations, 8);
  assert.equal(continuous.value.factors[0].n_used, 8);
  assert.deepEqual(continuous.value.factors[0].range.value, { min: 0, max: 7 });
  captures.operations.push({ operation: 'factor_association', factor_id: 'dose', status: continuous.status, receipt: continuous.receipt });
  const workersBeforeContinuousColor = await page.evaluate(() => window.__f41FactorWorkers.operations.length);
  await page.getByRole('button', { name: 'Color PCA by this factor (display only)', exact: true }).last().click();
  await page.locator('.factor-color-legend').waitFor();
  const legendText = await page.locator('.factor-color-legend').innerText();
  assert.match(legendText, /0/); assert.match(legendText, /7/); assert.match(legendText, /°C/);
  assert.equal(await page.evaluate(() => window.__f41FactorWorkers.operations.length), workersBeforeContinuousColor,
    'Continuous color change must not run a worker operation');
  check('F4.1 continuous association preserves zero, owner unit/range and colors without a refit');

  await page.getByRole('button', { name: 'FR', exact: true }).click();
  await page.locator('html').waitFor({ state: 'attached' });
  assert.match(await page.locator('.factor-association-results').last().innerText(), /Association avec chaque composante/);
  await page.locator('.factor-association-controls').scrollIntoViewIfNeeded();
  await screenshot(page, `${browserName}-f4.1-factor-controls-fr`, false, '.factor-association-controls');
  await screenshot(page, `${browserName}-f4.1-factor-results-fr`, false, '.factor-association-results');
  captures.screenshots.push(`${browserName}-f4.1-factor-controls-fr`, `${browserName}-f4.1-factor-results-fr`);
  await auditAccessibility(page, output, `${browserName}-f4.1-factor-fr`, check);
  await page.getByRole('button', { name: /Tout sélectionner/ }).click();
  const frHtml = await capture(page, 'html', exported);
  const frMarkdown = await capture(page, 'markdown', exported);
  const frReport = await json(page);
  const frJson = JSON.stringify(frReport);
  for (const [name, text] of [['HTML-FR', frHtml], ['Markdown-FR', frMarkdown], ['JSON-FR', frJson]]) assertNoRowLevelColorExport(text, name);
  await writeFile(resolve(outputDir, 'factor-association-default-fr.html'), frHtml);
  await writeFile(resolve(outputDir, 'factor-association-default-fr.md'), frMarkdown);
  await writeFile(resolve(outputDir, 'factor-association-default-fr.json'), JSON.stringify(frReport, null, 2) + '\n');
  captures.exports.default_fr = { html_bytes: Buffer.byteLength(frHtml), markdown_bytes: Buffer.byteLength(frMarkdown), json_bytes: Buffer.byteLength(frJson), contains_row_level_color_tokens: false };
  await page.getByRole('button', { name: 'EN', exact: true }).click();

  const workersBeforeExport = await page.evaluate(() => window.__f41FactorWorkers.operations.length);
  let html = await capture(page, 'html', exported);
  let markdown = await capture(page, 'markdown', exported);
  let report = await json(page);
  let jsonText = JSON.stringify(report);
  assert.equal(report.export_selection?.provenance?.action, 'select_all');
  assert.equal(report.raw_x_included, false);
  assert.equal(report.numerical_evidence_recomputed_for_export, false);
  const exportedFactorResult = report.evidence.find(item => item.id === 'factor-association-1')?.value;
  assert.deepEqual(exportedFactorResult, categorical, 'Qualified aggregate owner result and its hash/count receipt must be preserved exactly');
  for (const [name, text] of [['HTML', html], ['Markdown', markdown], ['JSON', jsonText]]) assertNoRowLevelColorExport(text, name);
  assert.equal(await page.evaluate(() => window.__f41FactorWorkers.operations.length), workersBeforeExport);
  await writeFile(resolve(outputDir, 'factor-association-default.html'), html);
  await writeFile(resolve(outputDir, 'factor-association-default.md'), markdown);
  await writeFile(resolve(outputDir, 'factor-association-default.json'), JSON.stringify(report, null, 2) + '\n');
  captures.exports.default = {
    html_bytes: Buffer.byteLength(html), markdown_bytes: Buffer.byteLength(markdown), json_bytes: Buffer.byteLength(jsonText),
    contains_row_level_color_tokens: false, selection: report.export_selection,
  };
  check('F4.1 select-all report supplements do not grant or export observation-level factor colors');

  const grant = page.getByRole('checkbox', { name: /Authorize this factor.s observation-level colors in this report export/ });
  await grant.check();
  const authorizedReport = await json(page);
  assert.equal(authorizedReport.provenance.factor_color_export.factor_id, 'dose');
  assert.equal(authorizedReport.provenance.factor_color_export.source_permission_confirmed, true);
  html = await capture(page, 'html', exported);
  markdown = await capture(page, 'markdown', exported);
  report = await json(page);
  jsonText = JSON.stringify(report);
  assert(html.includes('factor-bin-') || html.includes('factor-level-'), 'Authorized HTML should retain the selected observation-to-color mapping');
  assert(jsonText.includes('factor-bin-') || jsonText.includes('factor-level-'), 'Authorized JSON should retain the selected observation-to-color mapping');
  await writeFile(resolve(outputDir, 'factor-association-authorized.html'), html);
  await writeFile(resolve(outputDir, 'factor-association-authorized.md'), markdown);
  await writeFile(resolve(outputDir, 'factor-association-authorized.json'), JSON.stringify(report, null, 2) + '\n');
  captures.exports.authorized = {
    html_bytes: Buffer.byteLength(html), markdown_bytes: Buffer.byteLength(markdown), json_bytes: Buffer.byteLength(jsonText),
    factor_id: report.provenance.factor_color_export.factor_id, source_permission_confirmed: report.provenance.factor_color_export.source_permission_confirmed,
  };
  assert.equal(await page.evaluate(() => window.__f41FactorWorkers.operations.length), workersBeforeExport);
  check('F4.1 separately authorized factor coloring is bound to the selected factor and current export');

  if (browserName === 'chromium') {
    const printPage = await context.newPage();
    try {
      await printPage.setContent(html, { waitUntil: 'load' });
      await printPage.pdf({ path: resolve(outputDir, 'factor-association-a4.pdf'), format: 'A4', printBackground: true });
      await printPage.pdf({ path: resolve(outputDir, 'factor-association-letter.pdf'), format: 'Letter', printBackground: true });
      captures.exports.print = ['factor-association-a4.pdf', 'factor-association-letter.pdf'];
    } finally { await printPage.close(); }
  } else captures.exports.print = 'not_applicable: PDF qualification runs on Chromium';

  captures.success = true;
  await writeFile(resolve(outputDir, 'factor-browser.json'), JSON.stringify(captures, null, 2) + '\n');
}
