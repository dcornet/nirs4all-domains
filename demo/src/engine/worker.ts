/// <reference lib="webworker" />
import type {WorkerRequest,WorkerReply} from './types';

declare const __DOMAINS_BUILD__:{version:string;commit:string|null;dirty:boolean|null}|undefined;
const protocol='domains.worker_bootstrap.v1';
const build=typeof __DOMAINS_BUILD__!=='undefined'?__DOMAINS_BUILD__:{version:'unknown',commit:null,dirty:null};
let active:WorkerRequest|null=null,finished=false;
let phase='BOOTSTRAP_STARTED',component='worker';
function lifecycle(event:string,label:string){self.postMessage({id:0,ok:true,protocol_version:protocol,lifecycle_event:event,stage:label,stage_id:'prepare',component:'worker',build});}
function reply(message:Omit<WorkerReply,'id'>){
 if(finished||!active)return;
 if(message.lifecycle_event){phase=message.lifecycle_event;component=message.component??component;}
 if(!message.stage)finished=true;
 self.postMessage({id:active.id,...message});
}
function unexpected(code:string,originalMessageAvailable:boolean){
 if(finished)return;
 const error={code,message:code,details:{code,phase,component,original_message_available:originalMessageAvailable}};
 if(active)reply({ok:false,error});
 else{finished=true;self.postMessage({id:0,ok:false,protocol_version:protocol,lifecycle_event:code,error});}
}
self.addEventListener('error',event=>{unexpected('WORKER_UNCAUGHT_EXCEPTION',Boolean(event.message));event.preventDefault();});
self.addEventListener('unhandledrejection',event=>{unexpected('WORKER_UNHANDLED_REJECTION',event.reason!==undefined);event.preventDefault();});
lifecycle('WORKER_BOOTSTRAP_STARTED','Worker bootstrap started');
self.onmessage=async({data}:MessageEvent<WorkerRequest>)=>{
 if(active||finished)return; // Single-use worker: no duplicate scientific execution.
 if(!data||!Number.isSafeInteger(data.id)||data.id<1||!['import','prepare_import','assemble_import','analyze','scoped','factor_association','train_fitted_support','preprocessing_sensitivity','interpret'].includes(data.operation)){
  active={id:Number.isSafeInteger(data?.id)?data.id:0,operation:'analyze',payload:null};
  unexpected('WORKER_REQUEST_INVALID',false);return;
 }
 active=data;
 phase='OPERATION_MODULE_LOADING';
 reply({ok:true,stage:'Loading the selected operation module',stage_id:'prepare',lifecycle_event:phase,component:'worker'});
 try{
  const {runOperation}=await import('./worker-operations');
  phase='OPERATION_MODULE_READY';
  reply({ok:true,stage:'Operation module ready',stage_id:'prepare',lifecycle_event:phase,component:'worker'});
  await runOperation(data,reply);
 }catch(error){
  const e=error as {code?:string;message?:string;phase?:string;component?:string;asset?:unknown};
  const code=e.code??(phase==='OPERATION_MODULE_LOADING'?'WORKER_DEPENDENCY_IMPORT_FAILED':'WORKER_RUNTIME_EXCEPTION');
  reply({ok:false,error:{code,message:e.message??code,details:{code,phase:e.phase??phase,component:e.component??component,asset:e.asset,original_message_available:typeof e.message==='string'&&e.message.length>0}}});
 }
};
phase='BOOTSTRAP_READY';
lifecycle('WORKER_BOOTSTRAP_READY','Worker bootstrap ready');
