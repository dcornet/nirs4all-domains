import {afterEach,describe,expect,it,vi} from 'vitest';
import {BrowserEngine} from './client';
import {makeWorkerDiagnostic} from './runtime-diagnostic';

const readyMessage = () => ({ id: 0, ok: true, stage: 'Worker bootstrap ready', stage_id: 'prepare',
  protocol_version: 'domains.worker_bootstrap.v1', lifecycle_event: 'WORKER_BOOTSTRAP_READY', component: 'worker' });

class BootstrapWorker {
  private handler:((event:{data:unknown})=>void)|null=null;
  autoReady=false;
  cloneError:Error|null=null;
  terminated=0;
  posts:{message:unknown;transfer:Transferable[]}[]=[];
  onerror:((event:{message:string})=>void)|null=null;
  onmessageerror:(()=>void)|null=null;
  set onmessage(value:((event:{data:unknown})=>void)|null){this.handler=value;if(value&&this.autoReady)this.ready();}
  get onmessage(){return this.handler;}
  postMessage(message:unknown,transfer:Transferable[]=[]){if(this.cloneError)throw this.cloneError;const clone=structuredClone(message,{transfer});this.posts.push({message:clone,transfer:[...transfer]});}
  terminate(){this.terminated++;}
  ready(build?:{commit:string|null}){this.handler?.({data:{...readyMessage(),...(build?{build}:{})}});}
  reply(value:object){this.handler?.({data:value});}
}
function fixture(){const workers:BootstrapWorker[]=[];const engine=new BrowserEngine(()=>{const w=new BootstrapWorker();workers.push(w);return w as unknown as Worker;});return {engine,workers};}
const errorCode=(error:unknown)=>error as {code?:string;message?:string;diagnostic?:unknown};
afterEach(()=>vi.useRealTimers());

describe('worker bootstrap handshake',()=>{
  it('waits for one explicit READY before posting the unchanged request or detaching import bytes',async()=>{
    const {engine,workers}=fixture();
    const bytes=new Uint8Array([4,5,6]);
    const pending=engine.request('prepare_import',[{name:'X.csv',bytes}]);
    const w=workers[0]!;
    expect(w.posts).toHaveLength(0);expect(bytes.byteLength).toBe(3);
    w.ready();expect(w.posts).toHaveLength(1);expect(bytes.byteLength).toBe(0);
    const posted=w.posts[0]!.message as {id:number;operation:string;payload:{name:string;bytes:Uint8Array}[]};
    expect(posted.operation).toBe('prepare_import');expect(posted.payload[0]!.name).toBe('X.csv');
    w.ready();expect(w.posts).toHaveLength(1);
    w.reply({id:posted.id,ok:true,result:{prepared:true}});
    await expect(pending).resolves.toEqual({prepared:true});expect(w.terminated).toBe(1);
  });

  it('cancels before READY without transferring buffers; late readiness cannot post stale work',async()=>{
    const {engine,workers}=fixture();const bytes=new Uint8Array([7,8]);
    const old=engine.request('import',[{name:'X.csv',bytes}]);
    const cancelled=expect(old).rejects.toMatchObject({code:'CANCELLED'});
    engine.cancel();await cancelled;expect(workers[0]!.terminated).toBe(1);expect(bytes.byteLength).toBe(2);
    const current=engine.request('analyze',{current:true});
    workers[0]!.ready();expect(workers[0]!.posts).toHaveLength(0);
    workers[1]!.ready();expect(workers[1]!.posts).toHaveLength(1);
    const request=workers[1]!.posts[0]!.message as {id:number};
    workers[0]!.reply({id:request.id,ok:true,result:'stale'});
    workers[1]!.reply({id:request.id,ok:true,result:'current'});
    await expect(current).resolves.toBe('current');
  });

  it('uses the startup deadline before READY and the ordinary work deadline after READY',async()=>{
    vi.useFakeTimers();const {engine,workers}=fixture();
    const startup=engine.request('analyze',{}),startupRejected=expect(startup).rejects.toMatchObject({code:'WORKER_BOOTSTRAP_TIMEOUT'});
    await vi.advanceTimersByTimeAsync(120_000);await startupRejected;expect(workers[0]!.posts).toHaveLength(0);expect(workers[0]!.terminated).toBe(1);
    const work=engine.request('analyze',{}),workRejected=expect(work).rejects.toMatchObject({code:'WORKER_TIME_BUDGET_EXCEEDED'});
    workers[1]!.ready();expect(workers[1]!.posts).toHaveLength(1);
    await vi.advanceTimersByTimeAsync(120_000);await workRejected;expect(workers[1]!.terminated).toBe(1);expect(vi.getTimerCount()).toBe(0);
  });

  it('rejects terminal replies before READY, ignores duplicate controls, then accepts one valid handshake',async()=>{
    const {engine,workers}=fixture();const pending=engine.request('analyze',{});
    workers[0]!.reply({id:2,ok:true,result:'early'});
    await expect(pending).rejects.toMatchObject({code:'WORKER_PROTOCOL_NOT_READY'});
    expect(workers[0]!.posts).toHaveLength(0);expect(workers[0]!.terminated).toBe(1);

    const recovered=engine.request('analyze',{}),w=workers[1]!;
    w.ready();w.ready();expect(w.posts).toHaveLength(1);
    const request=w.posts[0]!.message as {id:number};w.reply({id:request.id,ok:true,result:'ok'});
    await expect(recovered).resolves.toBe('ok');
  });

  it('refuses a malformed bootstrap control without posting application data',async()=>{
    const {engine,workers}=fixture();const pending=engine.request('analyze',{}),w=workers[0]!;
    w.reply({...readyMessage(),id:1});
    await expect(pending).rejects.toMatchObject({code:'WORKER_BOOTSTRAP_INVALID_REPLY'});
    expect(w.posts).toHaveLength(0);expect(w.terminated).toBe(1);
  });

  it('rejects a known build commit mismatch before transferring import bytes',async()=>{
    const actual=makeWorkerDiagnostic({operation:'prepare_import',phase:'WORKER_CREATED',lastConfirmedPhase:'WORKER_CREATED',code:'WORKER_CREATED'}).demo.commit;
    expect(actual).toMatch(/^[a-f0-9]{40}$/);
    const {engine,workers}=fixture(),bytes=new Uint8Array([2,4,6]);
    const pending=engine.request('prepare_import',[{name:'X.csv',bytes}]);workers[0]!.ready({commit:'f'.repeat(40)});
    await expect(pending).rejects.toMatchObject({code:'DEPLOYMENT_ASSET_VERSION_MISMATCH'});
    expect(workers[0]!.posts).toHaveLength(0);expect(bytes.byteLength).toBe(3);expect(workers[0]!.terminated).toBe(1);
  });

  it('terminates without sending the request when the lifecycle progress callback throws',async()=>{
    const {engine,workers}=fixture();const pending=engine.request('analyze',{},stage=>{if(stage==='Worker bootstrap ready')throw new Error('progress callback failed');});
    const w=workers[0]!;w.ready();
    await expect(pending).rejects.toThrow('progress callback failed');
    expect(w.posts).toHaveLength(0);expect(w.terminated).toBe(1);
  });

  it('maps pre-READY and post-READY worker errors to distinct safe codes',async()=>{
    const {engine,workers}=fixture();let pending=engine.request('analyze',{});
    const startup=expect(pending).rejects.toMatchObject({code:'WORKER_STARTUP_EXCEPTION'});
    workers[0]!.onerror?.({message:'WASM sentinel startup'});await startup;
    pending=engine.request('analyze',{});workers[1]!.ready();
    const runtime=expect(pending).rejects.toMatchObject({code:'WORKER_RUNTIME_EXCEPTION'});
    workers[1]!.onerror?.({message:'runtime sentinel'});await runtime;
    pending=engine.request('analyze',{});
    const unknown=expect(pending).rejects.toMatchObject({code:'WORKER_STARTUP_CAUSE_UNAVAILABLE'});
    workers[2]!.onerror?.({message:''});await unknown;
    expect(workers.every(w=>w.terminated===1)).toBe(true);
  });

  it('keeps provider refusal detail for the caller but sanitizes the diagnostic',async()=>{
    const {engine,workers}=fixture(),pending=engine.request('analyze',{}),w=workers[0]!;
    w.ready();const request=w.posts[0]!.message as {id:number};
    w.reply({id:request.id,ok:false,error:{code:'EXACT_PROVIDER_REFUSAL',message:'private-sentinel-provider detail'}});
    const error=await pending.catch(reason=>reason),e=errorCode(error);
    expect(e.code).toBe('EXACT_PROVIDER_REFUSAL');expect(e.message).toBe('private-sentinel-provider detail');
    expect(JSON.stringify(e.diagnostic)).not.toContain('private-sentinel');expect(w.terminated).toBe(1);
  });

  it('reports construction failure and original structured-clone failure without leaking raw diagnostic text',async()=>{
    const construction=new BrowserEngine(()=>{throw new Error('asset path private-sentinel');});
    await expect(construction.request('analyze',{})).rejects.toMatchObject({code:'WORKER_CONSTRUCTION_FAILED'});
    const w=new BootstrapWorker();w.autoReady=true;w.cloneError=new DOMException('private-sentinel clone failure','DataCloneError');
    const cloneEngine=new BrowserEngine(()=>w as unknown as Worker);
    const bytes=new Uint8Array([1]);
    const pending=cloneEngine.request('import',[{name:'X.csv',bytes}]);
    const error=await pending.catch(reason=>reason),e=errorCode(error);
    expect(e.code).toBe('DATA_CLONE_FAILED');expect(e.message).not.toContain('private-sentinel');
    expect(JSON.stringify(e.diagnostic)).not.toContain('private-sentinel');expect((e.diagnostic as {original_message_available?:boolean}).original_message_available).toBe(true);
    expect(w.terminated).toBe(1);
  });
});
