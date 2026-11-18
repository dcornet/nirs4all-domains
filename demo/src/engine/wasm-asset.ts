/** Transport only. Owner bytes remain unchanged; failures reset initialization. */
interface AssetOptions {component?:'io'|'formats'|'domains';expectedSha256?:string;requiredExports?:string[]}
function phaseOf(component:string){return component==='formats'?'FORMATS_RUNTIME_LOADING':component==='domains'?'DOMAINS_RUNTIME_LOADING':'IO_RUNTIME_LOADING';}
function transportError(code:string,message:string,component:string,asset:unknown,cause?:unknown){
 return Object.assign(new Error(message,{cause}),{code,component,phase:phaseOf(component),asset});
}
export function createWasmInitializer(url:string,imports:()=>WebAssembly.Imports,accept:(exports:WebAssembly.Exports)=>void,options:AssetOptions={}){
 let pending:Promise<void>|undefined;
 return function init():Promise<void>{
  return pending??=(async()=>{
   const component=options.component??'io';
   let response:Response;
   try{response=await fetch(url);}catch(error){throw transportError('WASM_ASSET_UNAVAILABLE','WASM_ASSET_UNAVAILABLE: network response unavailable',component,{url},error);}
   const asset={url,http_status:response.status,content_type:response.headers.get('content-type')??'',expected_sha256:options.expectedSha256,sha256:undefined as string|undefined};
   if(!response.ok)throw transportError('WASM_ASSET_UNAVAILABLE','WASM_ASSET_UNAVAILABLE: '+response.status,component,asset);
   if(/\btext\/html\b/i.test(asset.content_type))throw transportError('WASM_ASSET_INVALID_RESPONSE','WASM_ASSET_INVALID_RESPONSE: expected WASM, received HTML',component,asset);
   if(asset.content_type&&!/^(application\/wasm|application\/octet-stream)(;|$)/i.test(asset.content_type))throw transportError('WASM_CONTENT_TYPE_INVALID','WASM_CONTENT_TYPE_INVALID: unexpected response MIME type',component,asset);
   const bytes=await response.arrayBuffer();
   let compiled:WebAssembly.Module;
   try{compiled=await WebAssembly.compile(bytes);}
   catch(error){throw transportError('WASM_COMPILE_FAILED','WASM_ASSET_INVALID_BINARY: '+(error instanceof Error?error.message:'compilation failed'),component,asset,error);}
   const names=new Set(WebAssembly.Module.exports(compiled).map(e=>e.name));
   if(options.requiredExports?.some(name=>!names.has(name)))throw transportError('WASM_EXPORT_MISSING','WASM_INITIALIZATION_FAILED: required owner export missing',component,asset);
   if(options.expectedSha256){
    if(!globalThis.crypto?.subtle)throw transportError('WASM_DIGEST_UNAVAILABLE','WASM_DIGEST_UNAVAILABLE',component,asset);
    asset.sha256=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');
    if(asset.sha256!==options.expectedSha256)throw transportError('ASSET_INTEGRITY_MISMATCH','ASSET_INTEGRITY_MISMATCH: published WASM digest differs',component,asset);
   }
   let instance:WebAssembly.Instance;
   try{instance=await WebAssembly.instantiate(compiled,imports());}
   catch(error){throw transportError('WASM_INSTANTIATION_FAILED','WASM_INSTANTIATION_FAILED: '+(error instanceof Error?error.message:'instantiation failed'),component,asset,error);}
   try{accept(instance.exports);}
   catch(error){throw transportError('WASM_INITIALIZATION_FAILED','WASM_INITIALIZATION_FAILED: '+(error instanceof Error?error.message:'owner initialization failed'),component,asset,error);}
  })().catch(error=>{pending=undefined;throw error;});
 };
}
