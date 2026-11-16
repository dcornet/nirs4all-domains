/** Transport only. One in-flight initialization, retry after failure, no fallback. */
export function createWasmInitializer(url:string,imports:()=>WebAssembly.Imports,accept:(exports:WebAssembly.Exports)=>void){
  let pending:Promise<void>|undefined;
  return function init():Promise<void>{
    return pending??= (async()=>{
      const response=await fetch(url);
      if(!response.ok)throw new Error(`WASM_ASSET_UNAVAILABLE: ${response.status}`);
      if(/\btext\/html\b/i.test(response.headers.get('content-type')??''))throw new Error('WASM_ASSET_INVALID_RESPONSE: expected WASM, received HTML');
      const bytes=await response.arrayBuffer();
      let result:WebAssembly.WebAssemblyInstantiatedSource;
      try{result=await WebAssembly.instantiate(bytes,imports());}
      catch(error){throw new Error(`WASM_ASSET_INVALID_BINARY: ${error instanceof Error?error.message:String(error)}`,{cause:error});}
      try{accept(result.instance.exports);}
      catch(error){throw new Error(`WASM_INITIALIZATION_FAILED: ${error instanceof Error?error.message:String(error)}`,{cause:error});}
    })().catch(error=>{pending=undefined;throw error;});
  };
}
