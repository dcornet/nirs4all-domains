import type {Operation,WorkerReply} from './types';
import type {ProcessingStage} from '../ui-types';
import {makeWorkerDiagnostic,diagnosticError,type WorkerDiagnostic} from './runtime-diagnostic';
import workerURL from './worker.ts?worker&url';

const entryURL=new URL(workerURL,import.meta.url);
const BOOTSTRAP='domains.worker_bootstrap.v1';
type Progress=(stage:string,step?:ProcessingStage,diagnostic?:WorkerDiagnostic)=>void;
type Detail={code:string;component?:string;phase?:string;asset?:unknown;original_message_available?:boolean};
interface Pending {id:number;resolve(value:unknown):void;reject(reason:Error):void;progress:Progress;timer:ReturnType<typeof setTimeout>;
 operation:Operation;phase:string;confirmed:string;ready:boolean;posted:boolean;send():void}

/** Transfer once after explicit readiness. Termination is actual cancellation. */
export class BrowserEngine {
 private worker:Worker|null=null;
 private sequence=0;
 private pending:Pending|null=null;
 private readonly factory:()=>Worker;
 private readonly probeURL:URL|null;
 constructor(factory?:()=>Worker){this.factory=factory??(()=>new Worker(entryURL,{type:'module'}));this.probeURL=factory?null:entryURL;}
 async request<T>(operation:Operation,payload:unknown,progress:Progress=()=>{}):Promise<T>{
  this.cancel();const id=++this.sequence;
  return new Promise<T>((resolve,reject)=>{
   const pending:Pending={id,resolve:v=>resolve(v as T),reject,progress,operation,phase:'WORKER_CREATED',confirmed:'WORKER_CREATED',ready:false,posted:false,
    timer:setTimeout(()=>{if(this.pending===pending)this.failCode(pending.ready?'WORKER_TIME_BUDGET_EXCEEDED':'WORKER_BOOTSTRAP_TIMEOUT');},120_000),
    send:()=>{
     if(this.pending!==pending||!pending.ready||pending.posted||!this.worker)return;
     pending.posted=true;
     try{
      const buffers=(operation==='import'||operation==='prepare_import')&&Array.isArray(payload)
       ?[...new Set(payload.flatMap(f=>f?.bytes instanceof Uint8Array&&f.bytes.buffer instanceof ArrayBuffer?[f.bytes.buffer]:[]))]:[];
      this.worker.postMessage({id,operation,payload},buffers);
     }catch(error){this.failCode(error instanceof DOMException&&error.name==='DataCloneError'?'DATA_CLONE_FAILED':'WORKER_POST_MESSAGE_FAILED',{originalMessage:error});}
    }};
   this.pending=pending;
   try{
    const worker=this.factory();this.worker=worker;
    const current=()=>this.worker===worker&&this.pending===pending;
    this.progress(pending,'WORKER_CREATED','Worker created','prepare');
    worker.onerror=event=>{if(current())void this.onWorkerError(pending,event);};
    worker.onmessageerror=()=>{if(current())this.failCode('WORKER_MESSAGE_DESERIALIZATION_FAILED');};
    worker.onmessage=({data}:MessageEvent<WorkerReply&{protocol_version?:string;lifecycle_event?:string;component?:string;build?:{commit?:string}}>)=>{
     if(!current())return;
     if(data?.protocol_version===BOOTSTRAP){
      if(data.id===0&&data.ok===false&&['WORKER_UNCAUGHT_EXCEPTION','WORKER_UNHANDLED_REJECTION'].includes(data.lifecycle_event??'')){
       this.failCode(data.lifecycle_event!,{originalMessage:data.error?.details?.original_message_available?'message available':undefined});return;
      }
      if(data.id!==0||data.ok!==true||typeof data.stage!=='string'||!['WORKER_BOOTSTRAP_STARTED','WORKER_BOOTSTRAP_READY'].includes(data.lifecycle_event??'')){
       this.failCode('WORKER_BOOTSTRAP_INVALID_REPLY');return;
      }
      if(pending.ready)return;
      if(data.lifecycle_event==='WORKER_BOOTSTRAP_READY'){
       const diagnostic=makeWorkerDiagnostic({operation,phase:'BOOTSTRAP_READY',lastConfirmedPhase:'BOOTSTRAP_READY',code:'BOOTSTRAP_READY',component:'worker'});
       if(diagnostic.demo.commit&&data.build?.commit&&diagnostic.demo.commit!==data.build.commit){this.failCode('DEPLOYMENT_ASSET_VERSION_MISMATCH',{remediation:'reload'});return;}
       pending.ready=true;this.progress(pending,'BOOTSTRAP_READY',data.stage,'prepare');pending.send();
      }else this.progress(pending,'BOOTSTRAP_STARTED',data.stage,'prepare');
      return;
     }
     if(!data||typeof data.id!=='number'||typeof data.ok!=='boolean'){this.failCode('WORKER_INVALID_REPLY');return;}
     if(!pending.ready){this.failCode('WORKER_PROTOCOL_NOT_READY');return;}
     if(data.id!==id)return;
     if('stage' in data){
      if(typeof data.stage!=='string'||!data.stage||!data.ok){this.failCode('WORKER_INVALID_REPLY');return;}
      this.progress(pending,data.lifecycle_event??pending.phase,data.stage,data.stage_id,data.component);return;
     }
     if(data.ok&&!('result'in data)){this.failCode('WORKER_INVALID_REPLY');return;}
     if(data.ok){this.close();pending.resolve(data.result);}
     else{
      const error=data.error as (NonNullable<WorkerReply['error']>&{details?:Detail})|undefined;
      const details=error?.details;
      const diagnostic=this.diagnostic(pending,details?.code??error?.code??'DOMAINS_WORKER_REFUSAL',{
       phase:details?.phase,component:details?.component,asset:details?.asset,
       originalMessage:details?.original_message_available?'message available':error?.message});
      // Keep the existing local provider error; copied diagnostics omit its text.
      const failure=Object.assign(new Error(error?.message??diagnostic.rt_error.message),{code:error?.code??diagnostic.code,diagnostic});
      this.close();pending.reject(failure);
     }
    };
   }catch(error){if(this.pending===pending)this.failCode('WORKER_CONSTRUCTION_FAILED',{originalMessage:error});}
  });
 }
 private progress(p:Pending,phase:string,stage:string,step?:ProcessingStage,component='worker'){
  p.phase=phase;
  if(/_READY$|_COMPLETE$/.test(phase)||phase==='WORKER_CREATED'||phase==='BOOTSTRAP_STARTED')p.confirmed=phase;
  try{p.progress(stage,step,makeWorkerDiagnostic({operation:p.operation,phase,lastConfirmedPhase:p.confirmed,code:phase,component}));}
  catch(error){if(this.pending===p)this.fail(error instanceof Error?error:new Error('PROGRESS_CALLBACK_FAILED'));}
 }
 private diagnostic(p:Pending,code:string,options:{phase?:string;component?:string;asset?:unknown;originalMessage?:unknown;remediation?:'reload'|'retry'|'inspect'|'none'}={}){
  return makeWorkerDiagnostic({operation:p.operation,phase:options.phase??p.phase,lastConfirmedPhase:p.confirmed,code,component:options.component??'worker',asset:options.asset,
   originalMessage:options.originalMessage,recoverable:code!=='CANCELLED',remediation:options.remediation});
 }
 private failCode(code:string,options:Parameters<BrowserEngine['diagnostic']>[2]={}){
  if(this.pending)this.fail(diagnosticError(this.diagnostic(this.pending,code,options)));
 }
 private async onWorkerError(p:Pending,event:ErrorEvent){
  const beforeReady=!p.ready;const available=typeof event.message==='string'&&event.message.trim().length>0;
  let code=available?(beforeReady?'WORKER_STARTUP_EXCEPTION':'WORKER_RUNTIME_EXCEPTION'):'WORKER_STARTUP_CAUSE_UNAVAILABLE';
  let asset:unknown;let remediation:'reload'|'inspect'='inspect';
  if(this.probeURL){
   const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),2_000);
   try{
    const url=new URL(event.filename||this.probeURL.href,location.href);
    if(url.origin===location.origin&&url.pathname.startsWith('/nirs4all-domains/assets/')){
     const response=await fetch(url,{signal:controller.signal});const contentType=response.headers.get('content-type')??'';
     asset={relative_path:url.pathname,http_status:response.status,content_type:contentType};
     if(!response.ok){code='WORKER_ASSET_UNAVAILABLE';remediation='reload';}
     else if(/text\/html/i.test(contentType)){code='JAVASCRIPT_ASSET_INVALID_RESPONSE';remediation='reload';}
     else if(!/(?:application|text)\/(?:javascript|ecmascript)/i.test(contentType)){code='JAVASCRIPT_ASSET_INVALID_CONTENT_TYPE';remediation='reload';}
    }
   }catch{/* A failed probe does not establish a particular network cause. */}
   finally{clearTimeout(timer);}
  }
  if(this.pending===p)this.failCode(code,{asset,originalMessage:available?event.message:undefined,remediation});
 }
 private close(){if(this.pending)clearTimeout(this.pending.timer);this.pending=null;this.worker?.terminate();this.worker=null;}
 private fail(error:Error){const task=this.pending;this.close();task?.reject(error);}
 cancel(){this.sequence++;if(this.pending)this.failCode('CANCELLED',{remediation:'none'});else this.close();}
}
