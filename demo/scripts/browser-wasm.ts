// Transport adaptation of the dual-licensed Preflight demo's browser-wasm loader.
// Retain the published generated IO/Formats parsers and binaries verbatim.
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Plugin } from 'vite';
import admitted from './wasm-loaders.lock.json';

export function verifyPublishedLoader(pkg:string,version:string,source:string,binary:Uint8Array){
  const expected=admitted.packages[pkg as keyof typeof admitted.packages];
  const sha=(value:string|Uint8Array)=>createHash('sha256').update(value).digest('hex');
  if(!expected||version!==expected.version||sha(source)!==expected.glue_sha256||sha(binary)!==expected.wasm_sha256)
    throw new Error(`UNQUALIFIED_PUBLISHED_WASM_PACKAGE: ${pkg}@${version}`);
  const marker=source.indexOf('const wasmPath =');
  if(marker<0||source.indexOf('const wasmPath =',marker+1)>=0)throw new Error(`Unsupported published loader: ${pkg}`);
  return marker;
}

export function browserWasm(): Plugin {
  const require = createRequire(import.meta.url);
  const packages: Record<string, string> = {
    'virtual:nirs4all-io': '@nirs4all/io-wasm',
    'virtual:nirs4all-formats': '@nirs4all/formats-wasm',
  };
  return {
    name: 'domains-published-io-browser-loader',
    resolveId(id) { if(id==='virtual:domains-wasm-asset-loader')return fileURLToPath(new URL('../src/engine/wasm-asset.ts',import.meta.url));if (packages[id]) return `\0${id}`; },
    load(id) {
      const pkg = packages[id.slice(1)];
      if (!pkg) return;
      const entry = require.resolve(pkg);
      const source = readFileSync(entry, 'utf8');
      const names = [...source.matchAll(/^exports\.(\w+) = /gm)].map(m => m[1]);
      const binary = join(dirname(entry), pkg.endsWith('io-wasm') ? 'nirs4all_io_wasm_bg.wasm' : 'nirs4all_formats_wasm_bg.wasm');
      const metadata=JSON.parse(readFileSync(join(dirname(entry),'package.json'),'utf8'));
      const marker=verifyPublishedLoader(pkg,metadata.version,source,readFileSync(binary));
      return `import wasmUrl from ${JSON.stringify(`${binary}?url`)};
import { createWasmInitializer } from 'virtual:domains-wasm-asset-loader';
const exports = {};
${source.slice(0, marker)}
let wasm;
export const init = createWasmInitializer(wasmUrl, __wbg_get_imports, value => {
  const previous = wasm;
  wasm = value;
  try { wasm.__wbindgen_start(); } catch(error) { wasm = previous; throw error; }
});
export { ${names.join(', ')} };`;
    },
  };
}
