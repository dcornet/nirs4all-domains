import { createHash } from 'node:crypto';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const demo = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const root = resolve(demo, '..');
const publicRoot = join(demo, 'public', 'licenses');
const maxFileBytes = 512 * 1024;
const maxOutputBytes = 2 * 1024 * 1024;
const generated = [];
let outputBytes = 0;

const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const normalized = path => path.split(sep).join('/');

async function copyAllowed(source, destination, origin) {
  const bytes = await readFile(source);
  if (bytes.byteLength > maxFileBytes) throw new Error(`License file exceeds size cap: ${source}`);
  outputBytes += bytes.byteLength;
  if (outputBytes > maxOutputBytes) throw new Error('Prepared license bundle exceeds 2 MiB cap');
  await mkdir(dirname(destination), { recursive: true });
  await writeFile(destination, bytes);
  generated.push({ path: normalized(relative(publicRoot, destination)), sha256: sha256(bytes), bytes: bytes.byteLength, origin });
}

async function copyNoticeTree(packageRoot, outputRoot, origin) {
  async function visit(path) {
    for (const item of await readdir(path, { withFileTypes: true })) {
      const source = join(path, item.name);
      const rel = relative(packageRoot, source);
      if (item.isDirectory()) {
        if (rel === 'LICENSES' || rel.startsWith(`LICENSES${sep}`)) await visit(source);
        continue;
      }
      if (/^(LICENSE|LICENSING\.md|THIRD_PARTY_NOTICES\.md|COPY_PROVENANCE\.md|nirs4all-.*\.cdx\.json)$/i.test(item.name) ||
          rel.startsWith(`LICENSES${sep}`)) {
        await copyAllowed(source, join(outputRoot, rel), `${origin}/${normalized(rel)}`);
      }
    }
  }
  await visit(packageRoot);
}

async function readJson(path) { return JSON.parse(await readFile(path, 'utf8')); }

function collectLockPackages(lock, lockName, sourceRoot) {
  return Object.entries(lock.packages ?? {}).flatMap(([path, entry]) => {
    if (!path || entry.link === true || entry.dev === true || entry.devOptional === true) return [];
    const pkgPath = path.startsWith('node_modules/') ? path.slice('node_modules/'.length) : path;
    const scopeEnd = pkgPath.startsWith('@') ? pkgPath.indexOf('/', pkgPath.indexOf('/') + 1) : -1;
    const name = entry.name ?? (scopeEnd > 0 ? pkgPath.slice(0, scopeEnd) : pkgPath);
    return [{ name, version: entry.version ?? null, license: entry.license ?? 'UNDECLARED', resolved: entry.resolved ?? null,
      integrity: entry.integrity ?? null, lockfile: lockName, localPath: entry.resolved?.startsWith('file:') ? entry.resolved : null,
      installPath: entry.resolved?.startsWith('file:') ? resolve(sourceRoot, entry.resolved.slice(5)) : null }];
  });
}

const demoLock = await readJson(join(demo, 'package-lock.json'));
const bindingDir = join(root, 'bindings', 'wasm');
const bindingLock = await readJson(join(bindingDir, 'package-lock.json'));
const packages = [
  ...collectLockPackages(demoLock, 'demo/package-lock.json', demo),
  ...collectLockPackages(bindingLock, 'bindings/wasm/package-lock.json', bindingDir),
];
const uniquePackages = [...new Map(packages.map(pkg => [`${pkg.name}@${pkg.version ?? 'local'}|${pkg.lockfile}`, pkg])).values()]
  .sort((a, b) => a.name.localeCompare(b.name) || String(a.version).localeCompare(String(b.version)) || a.lockfile.localeCompare(b.lockfile));

// Core license choices for this application and its dual-licensed NIRS packages.
for (const file of ['CeCILL-2.1.txt', 'AGPL-3.0-or-later.txt']) {
  await copyAllowed(join(root, 'LICENSES', file), join(publicRoot, 'families', file), `repository LICENSES/${file}`);
}

const packageCopies = [
  ['nirs4all-ui', join(demo, 'node_modules', 'nirs4all-ui')],
  ['@nirs4all/io-wasm', join(demo, 'node_modules', '@nirs4all', 'io-wasm')],
  ['@nirs4all/formats-wasm', join(demo, 'node_modules', '@nirs4all', 'formats-wasm')],
  ['react', join(demo, 'node_modules', 'react')],
  ['react-dom', join(demo, 'node_modules', 'react-dom')],
  ['scheduler', join(demo, 'node_modules', 'scheduler')],
];
const installedMetadata = [];
for (const [name, packageRoot] of packageCopies) {
  const metadata = await readJson(join(packageRoot, 'package.json'));
  const locked = uniquePackages.find(pkg => pkg.name === name && pkg.version === metadata.version);
  if (!locked) throw new Error(`No matching lockfile entry for ${name}@${metadata.version}`);
  await copyNoticeTree(packageRoot, join(publicRoot, 'packages', name), locked.resolved ?? `installed package ${name}`);
  installedMetadata.push({ name, version: metadata.version, license: metadata.license ?? 'UNDECLARED', resolved: locked.resolved, integrity: locked.integrity });
}

const methodsVersion = '1.3.13';
const methodsLock = uniquePackages.find(pkg => pkg.name === '@nirs4all/methods' && pkg.version === methodsVersion);
if (!methodsLock || methodsLock.license !== 'CECILL-2.1') {
  throw new Error(`Expected locked @nirs4all/methods@${methodsVersion} with the exact CECILL-2.1 npm license declaration`);
}
const methodsCommit = 'fa8ff57603ec23bce95f73d52170285e8f3e2861';
installedMetadata.push({ name: '@nirs4all/methods', version: methodsVersion, license: methodsLock.license,
  resolved: methodsLock.resolved, integrity: methodsLock.integrity });
const localDomains = await readJson(join(bindingDir, 'package.json'));
const localDomainsPackage = { name: localDomains.name, version: localDomains.version, license: localDomains.license,
  resolved: 'file:../bindings/wasm', integrity: null, source: 'local workspace binding; generated WASM is built from the locked Rust workspace' };
const methodsSourceRoot = join(publicRoot, 'methods', methodsCommit);
const methodsSourceFiles = [
  'NOTICE.md', 'THIRD_PARTY_NOTICES.md', 'THIRD_PARTY_LICENSES.md',
  'LICENSES/CeCILL-2.1.txt', 'LICENSES/BSD-3-Clause.txt',
  'cpp/src/core/clustering/_vendored/LICENSE.scikit_learn.txt',
  'cpp/src/core/common/_vendored/fitpack/LICENSE.scipy.txt',
  'cpp/src/core/filters/_vendored/LICENSE.scikit_learn.txt',
  'cpp/src/core/optimization/_vendored/LICENSE.scipy.txt',
];
const methodsSources = [];
for (const path of methodsSourceFiles) {
  const file = join(methodsSourceRoot, path);
  const bytes = await readFile(file);
  if (bytes.byteLength > maxFileBytes) throw new Error(`Vendored Methods notice exceeds size cap: ${path}`);
  methodsSources.push({ path: `methods/${methodsCommit}/${normalized(path)}`, sha256: sha256(bytes), bytes: bytes.byteLength,
    source: `https://github.com/GBeurier/nirs4all-methods/blob/${methodsCommit}/${path}` });
}

const manifest = {
  schema_version: 1,
  source_lockfiles: ['demo/package-lock.json', 'bindings/wasm/package-lock.json'],
  packages: [...uniquePackages, localDomainsPackage].sort((a, b) => a.name.localeCompare(b.name) || String(a.version).localeCompare(String(b.version))),
  installed_notice_packages: installedMetadata,
  methods_notice_source: {
    name: '@nirs4all/methods', version: methodsVersion, license_declared_by_npm: methodsLock.license,
    registry_tarball: methodsLock.resolved, integrity: methodsLock.integrity, git_head: methodsCommit,
    upstream_notice_license_statement_conflicts_with_npm_metadata: true, files: methodsSources,
  },
  prepared_files: generated.sort((a, b) => a.path.localeCompare(b.path)),
  generated_file_bytes: outputBytes,
};
await writeFile(join(publicRoot, 'dependency-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);

const lines = [
  '# Browser demo dependency and license notices', '',
  'This document is generated by `node demo/scripts/prepare-licenses.mjs` from the two checked-in npm lockfiles and the installed packages. `dependency-manifest.json` records each locked package source URL, npm integrity, license metadata, and hashes for the copied notices. It is not a substitute for the original license terms.', '',
  '## Direct browser runtime packages', '',
  '| Package | Version | License declared by package | Source archive | Integrity |',
  '|---|---:|---|---|---|',
];
for (const pkg of installedMetadata) lines.push(`| \`${pkg.name}\` | ${pkg.version} | ${pkg.license} | ${pkg.resolved ?? 'local package'} | \`${pkg.integrity ?? 'local'}\` |`);
lines.push('', 'The build also includes local `@nirs4all/domains`, built from the locked Rust workspace; full production dependency closure and lock sources are in the manifest.', '',
  '## License and notice files', '',
  '- Repository CeCILL-2.1 and AGPL-3.0-or-later texts: [`public/licenses/families/`](public/licenses/families/).',
  '- UI, IO-WASM, Formats-WASM, React, React DOM, and Scheduler notices copied from the installed versions pinned by the demo lock: [`public/licenses/packages/`](public/licenses/packages/).',
  `- Methods license and bundled-code notices from upstream Git commit \`${methodsCommit}\`, corresponding to the exact npm ${methodsVersion} ` +
    `gitHead: [source files](public/licenses/methods/${methodsCommit}/) and hashes in the manifest.`, '',
  '## Methods license scope and known gap', '',
  '`@nirs4all/methods@1.3.13` declares `CECILL-2.1` in npm metadata and in its package lock. This demo does not describe that exact npm package as dual-licensed. The package tarball contains no LICENSE or notice files, so the corresponding CeCILL text and vendored-code notices are supplied from its exact registry `gitHead` commit.', '',
  'That commit contains inconsistent general statements: `THIRD_PARTY_NOTICES.md` describes the repository as `CeCILL-2.1 OR AGPL-3.0-or-later`, while `NOTICE.md` says the compiled library is under CeCILL-2.1 and lists bundled BSD-3-Clause-derived components. The npm package metadata is the exact distribution declaration used here; the upstream wording conflict is preserved and flagged in the manifest for maintainer review. Do not infer an AGPL option for this pinned npm package from the repository-level notice.', '',
  'The pinned IO-WASM package includes its CycloneDX SBOM and license families. The Formats-WASM package includes `THIRD_PARTY_NOTICES.md` but its published package is missing the `LICENSES/` family directory referenced by that notice; repository license texts are included here for the dual-licensed application packages, while the compiled Rust dependency closure remains a source-notice/manifest limitation. Review package notices and release SBOMs before redistribution.', '',
  'No source dataset is relicensed by these notices. Public example data and reports retain their recorded rights and source restrictions. Brand assets are not copied or modified by this preparation step.', '');
await writeFile(join(demo, 'DEPENDENCIES.md'), lines.join('\n'));
console.log(`Prepared ${generated.length} package/repository notice files (${outputBytes} bytes); manifest covers ${uniquePackages.length} locked production package records.`);
