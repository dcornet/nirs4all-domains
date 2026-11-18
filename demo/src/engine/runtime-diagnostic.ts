/** Data-free Domains extension around the unchanged shared rt_error.v1 contract. */
import {normalizeRuntimeDiagnostics,formatRuntimeRefusalText} from 'nirs4all-ui/runtime';
import pkg from '../../package.json';
declare const __DOMAINS_BUILD__:unknown;
export type DiagnosticRemediation='reload'|'retry'|'inspect'|'none';
export interface WorkerDiagnostic {
 protocol_version:'domains.worker_diagnostic.v1';operation:string;phase:string;last_confirmed_phase:string;category:string;code:string;component:string;
 demo:{version:string;commit:string|null;dirty:boolean|null};rt_error_contract:'rt_error.v1';
 rt_error:{verb:'run'|'inspect'|'validate';cause:'unsupported_shape'|'unsupported_capability'|'unavailable_backend'|'invalid_request'|'runtime_error';message:string;mitigation?:string};
 asset?:{relative_path:string;http_status?:number;content_type?:string;sha256?:string;expected_sha256?:string};
 original_message_available:boolean;recoverable:boolean;remediation:DiagnosticRemediation;
}
export interface WorkerFailureDetails {code:string;component?:string;phase?:string;asset?:unknown;original_message_available?:boolean}
type Entry={category:string;message:string;mitigation:string;cause:WorkerDiagnostic['rt_error']['cause'];remediation:DiagnosticRemediation};
const entries:Record<string,Entry>={};
const add=(codes:string,category:string,message:string,mitigation:string,cause:Entry['cause']='runtime_error',remediation:DiagnosticRemediation='inspect')=>{for(const code of codes.split(' '))entries[code]={category,message,mitigation,cause,remediation};};
add('WORKER_STARTUP_CAUSE_UNAVAILABLE WORKER_LOADING_FAILED','startup','The browser did not reveal the worker startup cause.','Inspect the last confirmed phase and local technical diagnostic.','unavailable_backend');
add('WORKER_STARTUP_EXCEPTION WORKER_DEPENDENCY_IMPORT_FAILED WORKER_STARTUP_FAILED WORKER_CONSTRUCTION_FAILED WORKER_MODULE_IMPORT_FAILED OPERATION_MODULE_IMPORT_FAILED DYNAMIC_IMPORT_FAILED STATIC_IMPORT_FAILED','startup','A worker JavaScript module could not be initialized.','Inspect the module-loading phase and asset status.','unavailable_backend');
add('WORKER_ASSET_UNAVAILABLE DEPLOYMENT_ASSET_VERSION_MISMATCH JS_ASSET_UNAVAILABLE WASM_ASSET_UNAVAILABLE ASSET_HTTP_ERROR ASSET_NOT_FOUND ASSET_DEPLOYMENT_INCOHERENT ASSET_VERSION_MISMATCH ASSET_INTEGRITY_MISMATCH WASM_INTEGRITY_MISMATCH WASM_DIGEST_MISMATCH','asset','A required application resource is missing or inconsistent with this build.','Reload explicitly, then retry the original action if appropriate.','unavailable_backend','reload');
add('JAVASCRIPT_ASSET_INVALID_RESPONSE JAVASCRIPT_ASSET_INVALID_CONTENT_TYPE ASSET_CONTENT_TYPE_INVALID ASSET_CONTENT_TYPE_MISMATCH WASM_CONTENT_TYPE_INVALID MODULE_CONTENT_TYPE_INVALID JS_CONTENT_TYPE_INVALID ASSET_HTML_RESPONSE WASM_ASSET_INVALID_RESPONSE','asset','A resource response has an unexpected content type.','Inspect the resource path, HTTP status and deployment.','unavailable_backend','reload');
add('WASM_ASSET_INVALID_BINARY WASM_INVALID_BINARY WASM_COMPILE_FAILED WASM_COMPILE_ERROR WASM_INSTANTIATION_FAILED WASM_INSTANTIATE_FAILED WASM_EXPORT_MISSING WASM_ABI_MISMATCH METHODS_ABI_MISMATCH ABI_MISMATCH WASM_DIGEST_UNAVAILABLE','wasm','A WebAssembly resource could not be compiled, instantiated or matched to its required interface.','Inspect the component and build identity.','unavailable_backend');
add('IO_RUNTIME_INITIALIZATION_FAILED IO_INITIALIZATION_FAILED FORMATS_RUNTIME_INITIALIZATION_FAILED FORMATS_INITIALIZATION_FAILED DOMAINS_RUNTIME_INITIALIZATION_FAILED DOMAINS_INITIALIZATION_FAILED METHODS_RUNTIME_INITIALIZATION_FAILED METHODS_INITIALIZATION_FAILED WASM_INITIALIZATION_FAILED RUNTIME_INITIALIZATION_FAILED','initialization','A required runtime did not finish initialization.','Inspect the last confirmed runtime phase before retrying explicitly.','unavailable_backend','retry');
add('DATA_CLONE_FAILED WORKER_PROTOCOL_NOT_READY WORKER_BOOTSTRAP_INVALID_REPLY WORKER_MESSAGE_DESERIALIZATION_FAILED WORKER_MESSAGE_CLONE_FAILED WORKER_STRUCTURED_CLONE_FAILED WORKER_INVALID_REPLY WORKER_POST_MESSAGE_FAILED','transport','A worker message could not be transferred or validated.','Retry explicitly; transferred byte buffers must be read again.','invalid_request','retry');
add('WORKER_BOOTSTRAP_TIMEOUT WORKER_BOOTSTRAP_TIME_BUDGET_EXCEEDED WORKER_TIME_BUDGET_EXCEEDED','timeout','The worker did not confirm completion within its time budget.','Inspect the last confirmed phase; no automatic scientific retry is performed.','unavailable_backend','retry');
add('CANCELLED','cancelled','The local worker operation was cancelled.','Start another operation explicitly when ready.','runtime_error','none');
add('WORKER_REQUEST_INVALID INVALID_WORKER_REQUEST LOCAL_ANALYSIS_REFUSED DOMAINS_WORKER_REFUSAL IMPLICIT_PARTITION_GENERATION_NOT_ADMITTED','request','The requested local operation was refused.','Inspect its operation scope and original scientific prerequisites.','invalid_request');
add('WORKER_RUNTIME_EXCEPTION WORKER_UNHANDLED_REJECTION WORKER_UNCAUGHT_EXCEPTION WORKER_RUNTIME_ERROR UNKNOWN_RUNTIME_FAILURE','runtime','The local operation did not complete; its precise cause is unavailable in this diagnostic.','Inspect the last confirmed phase. Original exception details are intentionally excluded.');
const phases='UNKNOWN WORKER_CREATED BOOTSTRAP_STARTED BOOTSTRAP_READY OPERATION_MODULE_LOADING OPERATION_MODULE_READY IO_RUNTIME_LOADING IO_RUNTIME_READY FORMATS_RUNTIME_LOADING FORMATS_RUNTIME_READY DOMAINS_RUNTIME_LOADING DOMAINS_RUNTIME_READY METHODS_RUNTIME_LOADING METHODS_RUNTIME_READY IMPORT_RUNNING IMPORT_COMPLETE OPERATION_RUNNING OPERATION_COMPLETE'.split(' ');
for(const phase of phases.filter(p=>p!=='UNKNOWN'))entries[phase]={category:'lifecycle',message:'Worker lifecycle phase: '+phase+'.',mitigation:'No estimated completion percentage is inferred.',cause:'runtime_error',remediation:'none'};
entries.WORKER_BOOTSTRAP_STARTED=entries.BOOTSTRAP_STARTED;entries.WORKER_BOOTSTRAP_READY=entries.BOOTSTRAP_READY;
const operations='import prepare_import assemble_import analyze scoped factor_association train_fitted_support interpret bootstrap unknown'.split(' ');
const components='worker browser transport io formats domains methods nirs4all-io nirs4all-formats nirs4all-domains nirs4all-methods nirs4all-ui unknown'.split(' ');
const record=(v:unknown):Record<string,unknown>=>v!==null&&typeof v==='object'&&!Array.isArray(v)?v as Record<string,unknown>:{};
const safePhase=(v:unknown)=>{const p=typeof v==='string'?v.replace(/^WORKER_BOOTSTRAP_/,'BOOTSTRAP_'):'UNKNOWN';return phases.includes(p)?p:'UNKNOWN';};
const hash=(v:unknown)=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v)?v:undefined;
function safeAsset(input:unknown):WorkerDiagnostic['asset']|undefined{
 const a=record(input),candidate=typeof input==='string'?input:a.relative_path??a.url;
 if(typeof candidate!=='string'||/[?#%\\]/.test(candidate))return;
 let path=candidate;
 if(!path.startsWith('/')){if(!/^https?:\/\//.test(path))return;try{const u=new URL(path);if(typeof location==='undefined'||u.origin!==location.origin||u.username||u.password)return;path=u.pathname;}catch{return;}}
 if(!/^\/nirs4all-domains\/assets\/(?:_virtual_nirs4all-(?:io|formats)|n4m|wasm|wasm-asset|worker|worker-operations|index|browser-wasm|dataset-io|import-draft|factor-provider|support-provider|methods|io|formats|nirs4all[-_](?:io|formats|domains|methods)(?:_wasm)?(?:_bg)?)(?:-[A-Za-z0-9_-]{8})?\.(?:js|wasm)$/.test(path))return;
 const result:NonNullable<WorkerDiagnostic['asset']>={relative_path:path};
 if(typeof a.http_status==='number'&&Number.isInteger(a.http_status)&&a.http_status>=100&&a.http_status<=599)result.http_status=a.http_status;
 const mime=typeof a.content_type==='string'?a.content_type.toLowerCase().split(';')[0].trim():'';
 if(['application/wasm','application/javascript','text/javascript','text/html','application/octet-stream'].includes(mime))result.content_type=mime;
 if(hash(a.sha256))result.sha256=hash(a.sha256);if(hash(a.expected_sha256))result.expected_sha256=hash(a.expected_sha256);return result;
}
function buildMetadata():WorkerDiagnostic['demo']{
 const b=typeof __DOMAINS_BUILD__==='undefined'?{}:record(__DOMAINS_BUILD__);
 return {version:typeof b.version==='string'&&/^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$/.test(b.version)?b.version:pkg.version,commit:typeof b.commit==='string'&&/^[a-f0-9]{40}$/.test(b.commit)?b.commit:null,dirty:typeof b.dirty==='boolean'?b.dirty:null};
}
export function makeWorkerDiagnostic(options:{operation:string;phase:string;lastConfirmedPhase:string;code:string;component?:string;asset?:unknown;originalMessage?:unknown;recoverable?:boolean;remediation?:DiagnosticRemediation}):WorkerDiagnostic{
 const code=Object.hasOwn(entries,options.code)?options.code:'UNKNOWN_RUNTIME_FAILURE',e=entries[code],asset=safeAsset(options.asset);
 const remediation=options.remediation&&['reload','retry','inspect','none'].includes(options.remediation)?options.remediation:e.remediation;
 return {protocol_version:'domains.worker_diagnostic.v1',operation:operations.includes(options.operation)?options.operation:'unknown',phase:safePhase(options.phase),last_confirmed_phase:safePhase(options.lastConfirmedPhase),category:e.category,code,component:components.includes(options.component??'worker')?options.component??'worker':'unknown',demo:buildMetadata(),rt_error_contract:'rt_error.v1',rt_error:{verb:'run',cause:e.cause,message:e.message,mitigation:e.mitigation},...(asset?{asset}:{}),original_message_available:typeof options.originalMessage==='string'?options.originalMessage.length>0:options.originalMessage!==undefined&&options.originalMessage!==null,recoverable:typeof options.recoverable==='boolean'?options.recoverable:['reload','retry'].includes(remediation),remediation};
}
export function sanitizedWorkerDiagnostic(input:unknown):WorkerDiagnostic{
 const v=record(input),d=makeWorkerDiagnostic({operation:typeof v.operation==='string'?v.operation:'unknown',phase:typeof v.phase==='string'?v.phase:'UNKNOWN',lastConfirmedPhase:typeof v.last_confirmed_phase==='string'?v.last_confirmed_phase:'UNKNOWN',code:typeof v.code==='string'?v.code:'UNKNOWN_RUNTIME_FAILURE',component:typeof v.component==='string'?v.component:'unknown',asset:v.asset,recoverable:typeof v.recoverable==='boolean'?v.recoverable:false,remediation:['reload','retry','inspect','none'].includes(String(v.remediation))?v.remediation as DiagnosticRemediation:'inspect'});
 const b=record(v.demo);
 if(typeof b.version==='string'&&/^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$/.test(b.version))d.demo.version=b.version;
 if(b.commit===null||typeof b.commit==='string'&&/^[a-f0-9]{40}$/.test(b.commit))d.demo.commit=b.commit;
 if(b.dirty===null||typeof b.dirty==='boolean')d.demo.dirty=b.dirty;
 d.original_message_available=v.original_message_available===true;return d;
}
export function diagnosticError(d:WorkerDiagnostic):Error&{code:string;diagnostic:WorkerDiagnostic}{const safe=sanitizedWorkerDiagnostic(d);return Object.assign(new Error(safe.rt_error.message),{code:safe.code,diagnostic:safe});}
export function technicalDiagnosticJSON(d:WorkerDiagnostic):string{return JSON.stringify(sanitizedWorkerDiagnostic(d),null,2);}
export function sharedDiagnosticText(d:WorkerDiagnostic):string{const safe=sanitizedWorkerDiagnostic(d),items=normalizeRuntimeDiagnostics({rt_error:safe.rt_error});return items.length?formatRuntimeRefusalText(items[0]):safe.rt_error.message;}
