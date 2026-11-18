import {describe,it,expect} from 'vitest';
import {makeWorkerDiagnostic,diagnosticError,technicalDiagnosticJSON,sharedDiagnosticText,sanitizedWorkerDiagnostic} from './runtime-diagnostic';
const options={operation:'prepare_import',phase:'IO_RUNTIME_LOADING',lastConfirmedPhase:'BOOTSTRAP_READY',code:'WASM_ASSET_UNAVAILABLE',component:'nirs4all-io'};
describe('Worker diagnostic public contract and privacy',()=>{
 it('uses the actual pure UI runtime helpers with a strict rt_error envelope inside a separate Domains extension',()=>{
  const d=makeWorkerDiagnostic(options);expect(d.protocol_version).toBe('domains.worker_diagnostic.v1');expect(d.rt_error_contract).toBe('rt_error.v1');expect(Object.keys(d.rt_error).sort()).toEqual(['cause','message','mitigation','verb']);
  expect(sharedDiagnosticText(d)).toContain('Run refused');expect(sharedDiagnosticText(d)).toContain(d.rt_error.message);expect(d.demo.version).toBe('0.1.0-alpha.17');expect(d.demo.commit===null||/^[a-f0-9]{40}$/.test(d.demo.commit)).toBe(true);
 });
 it('preserves only safe public asset fields and excludes query strings, credentials, cross-origin/private paths and injected fields',()=>{
  const d=makeWorkerDiagnostic({...options,asset:{relative_path:'/nirs4all-domains/assets/worker-Ab12Cd34.js',http_status:404,content_type:'text/html; charset=utf-8',sha256:'a'.repeat(64),expected_sha256:'b'.repeat(64),stack:'SECRET_STACK',matrix:[[987654321.125]]}});
  expect(d.asset).toEqual({relative_path:'/nirs4all-domains/assets/worker-Ab12Cd34.js',http_status:404,content_type:'text/html',sha256:'a'.repeat(64),expected_sha256:'b'.repeat(64)});
  for(const path of ['C:\\private\\samples.csv','/home/person/data.csv','/nirs4all-domains/assets/worker-Ab12Cd34.js?secret=Y','https://private.invalid/nirs4all-domains/assets/worker-Ab12Cd34.js','/nirs4all-domains/assets/worker-PHYSICAL_SECRET.js','/nirs4all-domains/assets/sample.csv','/nirs4all-domains/assets/../secret.js','/nirs4all-domains/assets/worker-%20.js'])expect(makeWorkerDiagnostic({...options,asset:{relative_path:path}}).asset).toBeUndefined();
 });
 it('never serializes raw exception messages, file/data sentinels, identifiers, paths, stacks, or arbitrary diagnostic properties',()=>{
  const secret='987654321.125 PHYSICAL_SECRET C:\\private\\input.csv';
  const d=makeWorkerDiagnostic({...options,originalMessage:new Error(secret)});expect(d.original_message_available).toBe(true);
  const poisoned={...d,rt_error:{verb:'run',cause:'runtime_error',message:secret,severity:'error'},demo:{version:secret,commit:secret,dirty:secret},x:[[987654321.125]],y:secret,metadata:secret,stack:secret};
  const json=technicalDiagnosticJSON(poisoned as any);for(const token of ['987654321','PHYSICAL_SECRET','private','severity','metadata','stack'])expect(json).not.toContain(token);
  expect(JSON.parse(json).rt_error.message).toBe(d.rt_error.message);expect(diagnosticError(poisoned as any).message).toBe(d.rt_error.message);
 });
 it('retains known public loading codes, virtual glue/method assets and version mismatch reload without leaking error text',()=>{
  for(const code of ['WORKER_STARTUP_EXCEPTION','WORKER_RUNTIME_EXCEPTION','WORKER_PROTOCOL_NOT_READY','WORKER_BOOTSTRAP_INVALID_REPLY','DATA_CLONE_FAILED','DEPLOYMENT_ASSET_VERSION_MISMATCH','WORKER_DEPENDENCY_IMPORT_FAILED','JAVASCRIPT_ASSET_INVALID_RESPONSE','JAVASCRIPT_ASSET_INVALID_CONTENT_TYPE','WORKER_ASSET_UNAVAILABLE','WASM_ASSET_INVALID_RESPONSE','WASM_ASSET_INVALID_BINARY','WASM_INITIALIZATION_FAILED','WORKER_BOOTSTRAP_STARTED','WORKER_BOOTSTRAP_READY'])expect(makeWorkerDiagnostic({...options,code}).code).toBe(code);
  for(const file of ['_virtual_nirs4all-io-Ab12Cd34.js','_virtual_nirs4all-formats-Ab12Cd34.js','n4m-Ab12Cd34.wasm','wasm-Ab12Cd34.js','wasm-asset-Ab12Cd34.js'])expect(makeWorkerDiagnostic({...options,asset:{relative_path:'/nirs4all-domains/assets/'+file}}).asset?.relative_path).toContain(file);
  expect(makeWorkerDiagnostic({...options,code:'DEPLOYMENT_ASSET_VERSION_MISMATCH'}).remediation).toBe('reload');expect(makeWorkerDiagnostic({...options,originalMessage:''}).original_message_available).toBe(false);
  const d=makeWorkerDiagnostic(options);expect(JSON.parse(technicalDiagnosticJSON({...d,demo:{version:'1.2.3',commit:'c'.repeat(40),dirty:false}})).demo).toEqual({version:'1.2.3',commit:'c'.repeat(40),dirty:false});
 });
 it('normalizes all untrusted enum/code/component fields and does not invent a known startup cause',()=>{
  const d=makeWorkerDiagnostic({...options,operation:'USER_ID',phase:'C:\\private',lastConfirmedPhase:'raw-Y',code:'DATA_SENTINEL',component:'PRIVATE_ID'});expect(d.code).toBe('UNKNOWN_RUNTIME_FAILURE');expect(d.operation).toBe('unknown');expect(d.phase).toBe('UNKNOWN');expect(d.component).toBe('unknown');
  const unknown=makeWorkerDiagnostic({...options,code:'WORKER_STARTUP_CAUSE_UNAVAILABLE',originalMessage:undefined});expect(unknown.rt_error.message).toContain('did not reveal');expect(unknown.original_message_available).toBe(false);expect(unknown.remediation).toBe('inspect');
  expect(sanitizedWorkerDiagnostic({...unknown,original_message_available:'SECRET'}).original_message_available).toBe(false);
 });
});
