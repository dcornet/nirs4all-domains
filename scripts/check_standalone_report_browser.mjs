// Offline browser checks only. No NIRS runtime, HTTP service or fitting API.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { createHash } from "node:crypto";
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.D4_PLAYWRIGHT_MODULE ?? "playwright-core");
const [prefixArg, outputArg] = process.argv.slice(2);
if (!prefixArg || !outputArg) throw new Error("Usage: report-prefix output-directory");
const prefix = resolve(prefixArg), output = resolve(outputArg);
mkdirSync(output, { recursive: true });
const view = JSON.parse(readFileSync(prefix + ".json", "utf8"));
const hash = text => createHash("sha256").update(text).digest("hex");
const chrome = process.env.CHROME ?? ["C:/Program Files/Google/Chrome/Application/chrome.exe", "/usr/bin/google-chrome", "/usr/bin/chromium"].find(existsSync);
if (!chrome) throw new Error("EXISTING_CHROME_UNAVAILABLE");
const browser = await chromium.launch({ executablePath: chrome, headless: true, args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"] });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
const errors = [], requests = [];
page.on("pageerror", e => errors.push(e.message));
page.on("request", request => requests.push(request.url()));
try {
  await page.goto(pathToFileURL(prefix + ".html").href);
  assert.equal(await page.locator("body > section").count(), view.cases.length);
  assert.equal(await page.locator("script, iframe, img, form").count(), 0);
  for (let i = 0; i < view.cases.length; i++) {
    assert.equal(await page.locator(`#case-${i} > h2`).textContent(), view.cases[i].label);
    await page.locator(`nav a[href="#case-${i}"]`).click();
    assert(page.url().endsWith(`#case-${i}`));
  }
  const embedded = JSON.parse(await page.locator("#domains-view-data").textContent());
  assert.deepEqual(embedded, view);
  assert.equal(await page.evaluate(() => window.D4_INJECTION), undefined);
  assert.equal(await page.locator("meta[http-equiv='Content-Security-Policy']").count(), 1);
  await page.locator('nav a[href="#case-0"]').click();
  await page.screenshot({ path: resolve(output, "standalone-report.png"), fullPage: false });
  await page.setViewportSize({ width: 390, height: 844 });
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), "Mobile overflow");
  await page.screenshot({ path: resolve(output, "standalone-mobile.png"), fullPage: false });
  assert.deepEqual(errors, []);
  assert(requests.every(url => url.startsWith("file:")), "Unexpected network resource");
  const receipt = { browser: browser.version(), cases: view.cases.length, canonical_dataset_ids: view.coverage.canonical_dataset_ids, original_database_count: view.coverage.original_database_count, source_view_matches: true, embedded_json_exact: true, network_resources: 0, executable_scripts: 0, fitting_calls: 0, html_sha256: hash(readFileSync(prefix + ".html")), markdown_sha256: hash(readFileSync(prefix + ".md")), json_sha256: hash(readFileSync(prefix + ".json")) };
  writeFileSync(resolve(output, "browser-receipt.json"), JSON.stringify(receipt, null, 2) + "\n");
  console.log(JSON.stringify({ cases: view.cases.length, source_view_matches: true, embedded_json_exact: true, network_resources: 0, fitting_calls: 0 }));
} finally { await browser.close(); }
