import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';
import { browserWasm } from './scripts/browser-wasm';
import {execFileSync} from 'node:child_process';
import pkg from './package.json';

let commit:string|null=null,dirty:boolean|null=null;
try{
  commit=execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8',stdio:['ignore','pipe','ignore']}).trim();
  dirty=Boolean(execFileSync('git',['status','--porcelain'],{encoding:'utf8',stdio:['ignore','pipe','ignore']}).trim());
}catch{/* Unknown source identity is not replaced by an invented commit. */}
const buildIdentity={version:pkg.version,commit,dirty};

export default defineConfig({
  base: '/nirs4all-domains/', define:{__DOMAINS_BUILD__:JSON.stringify(buildIdentity)},
  plugins: [react(), browserWasm(),{name:'domains-public-build-identity',generateBundle(){this.emitFile({type:'asset',fileName:'build-info.json',source:JSON.stringify(buildIdentity)+'\n'});}}],
  worker: { format: 'es', plugins: () => [browserWasm()] },
  build: { target: 'es2022', sourcemap: false, chunkSizeWarningLimit: 700 },
  server: { host: '127.0.0.1' }, preview: { host: '127.0.0.1' },
  test: { css: { include: [/report\.css/] } },
});
