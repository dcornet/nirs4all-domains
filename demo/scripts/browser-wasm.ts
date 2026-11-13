// Transport adaptation of the dual-licensed Preflight demo's browser-wasm loader.
// Retain the published generated IO/Formats parsers and binaries verbatim.
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import type { Plugin } from 'vite';

export function browserWasm(): Plugin {
  const require = createRequire(import.meta.url);
  const packages: Record<string, string> = {
    'virtual:nirs4all-io': '@nirs4all/io-wasm',
    'virtual:nirs4all-formats': '@nirs4all/formats-wasm',
  };
  return {
    name: 'domains-published-io-browser-loader',
    resolveId(id) { if (packages[id]) return `\0${id}`; },
    load(id) {
      const pkg = packages[id.slice(1)];
      if (!pkg) return;
      const entry = require.resolve(pkg);
      const source = readFileSync(entry, 'utf8');
      const marker = source.indexOf('const wasmPath =');
      if (marker < 0) throw new Error(`Unsupported published loader: ${pkg}`);
      const names = [...source.matchAll(/^exports\.(\w+) = /gm)].map(m => m[1]);
      const binary = join(dirname(entry), pkg.endsWith('io-wasm') ? 'nirs4all_io_wasm_bg.wasm' : 'nirs4all_formats_wasm_bg.wasm');
      return `import wasmUrl from ${JSON.stringify(`${binary}?url`)};
const exports = {};
${source.slice(0, marker)}
let wasm;
let pending;
export function init() {
  return pending ??= fetch(wasmUrl).then(response => {
    if (!response.ok) throw new Error('WASM_ASSET_UNAVAILABLE: ' + response.status);
    return response.arrayBuffer();
  }).then(bytes => WebAssembly.instantiate(bytes, __wbg_get_imports())).then(result => {
    wasm = result.instance.exports;
    wasm.__wbindgen_start();
  }).catch(error => { pending = undefined; throw error; });
}
export { ${names.join(', ')} };`;
    },
  };
}
