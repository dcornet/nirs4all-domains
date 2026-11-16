import {afterEach,describe,expect,it,vi} from 'vitest';
import {createWasmInitializer} from './wasm-asset';
import {verifyPublishedLoader} from '../../scripts/browser-wasm';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {dirname,join} from 'node:path';

const emptyModule=new Uint8Array([0,97,115,109,1,0,0,0]);
afterEach(()=>vi.unstubAllGlobals());
describe('WASM asset transport with actual WebAssembly instantiation',()=>{
  it('coalesces concurrent initialization and retains successful initialization',async()=>{
    const fetch=vi.fn(async()=>new Response(emptyModule,{headers:{'content-type':'application/wasm'}}));vi.stubGlobal('fetch',fetch);
    const accept=vi.fn(),init=createWasmInitializer('/app/fixture.wasm',()=>({}),accept);
    const a=init(),b=init();expect(a).toBe(b);await Promise.all([a,b]);await init();expect(fetch).toHaveBeenCalledOnce();expect(accept).toHaveBeenCalledOnce();
  });
  it('preserves HTTP refusal and retries after failure without a substitute module',async()=>{
    const fetch=vi.fn().mockResolvedValueOnce(new Response('missing',{status:404})).mockResolvedValueOnce(new Response(emptyModule));vi.stubGlobal('fetch',fetch);
    const accept=vi.fn(),init=createWasmInitializer('/app/retry.wasm',()=>({}),accept);
    await expect(init()).rejects.toThrow('WASM_ASSET_UNAVAILABLE: 404');expect(accept).not.toHaveBeenCalled();await init();expect(accept).toHaveBeenCalledOnce();expect(fetch).toHaveBeenCalledTimes(2);
  });
  it('rejects HTML and corrupt binaries, with no accepted result',async()=>{
    const accept=vi.fn();vi.stubGlobal('fetch',vi.fn(async()=>new Response('<html>',{headers:{'content-type':'text/html'}})));
    await expect(createWasmInitializer('/app/html.wasm',()=>({}),accept)()).rejects.toThrow('WASM_ASSET_INVALID_RESPONSE');
    vi.stubGlobal('fetch',vi.fn(async()=>new Response(new Uint8Array([0,97,115,109]))));
    await expect(createWasmInitializer('/app/corrupt.wasm',()=>({}),accept)()).rejects.toThrow('WASM_ASSET_INVALID_BINARY');expect(accept).not.toHaveBeenCalled();
  });
  it('rejects incompatible initialized exports and allows a clean later attempt',async()=>{
    vi.stubGlobal('fetch',vi.fn(async()=>new Response(emptyModule)));let fail=true;const accept=()=>{if(fail)throw new Error('required owner export missing');};const init=createWasmInitializer('/app/wrong.wasm',()=>({}),accept);
    await expect(init()).rejects.toThrow('WASM_INITIALIZATION_FAILED: required owner export missing');fail=false;await init();
  });
  it.each(['@nirs4all/io-wasm','@nirs4all/formats-wasm'])('admits only the exact published package and binary: %s',pkg=>{
    const require=createRequire(import.meta.url),entry=require.resolve(pkg),base=dirname(entry),metadata=JSON.parse(readFileSync(join(base,'package.json'),'utf8'));
    const source=readFileSync(entry,'utf8'),binary=readFileSync(entry.replace(/\.js$/,'_bg.wasm'));
    expect(verifyPublishedLoader(pkg,metadata.version,source,binary)).toBeGreaterThan(0);
    expect(()=>verifyPublishedLoader(pkg,'999.0.0',source,binary)).toThrow('UNQUALIFIED');expect(()=>verifyPublishedLoader(pkg,metadata.version,source+'\n',binary)).toThrow('UNQUALIFIED');
    expect(()=>verifyPublishedLoader(pkg,metadata.version,source,emptyModule)).toThrow('UNQUALIFIED');
  });
});
