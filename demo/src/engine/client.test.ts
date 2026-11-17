import {afterEach,describe,expect,it,vi} from 'vitest';
import {BrowserEngine} from './client';

class WorkerDouble {
  onmessage:((event:{data:unknown})=>void)|null=null;
  onerror:((event:{message:string})=>void)|null=null;
  onmessageerror:(()=>void)|null=null;
  terminated=0;message:{id:number;operation:string;payload:unknown}|null=null;
  cloneFailure=false;
  terminate(){this.terminated++;}
  postMessage(message:unknown,transfer:Transferable[]=[]){if(this.cloneFailure)throw new DOMException('Original clone failure','DataCloneError');this.message=structuredClone(message,{transfer}) as typeof this.message;}
  reply(value:object){this.onmessage?.({data:{id:this.message!.id,...value}});}
}
function fixture(){const workers:WorkerDouble[]=[];const engine=new BrowserEngine(()=>{const w=new WorkerDouble();workers.push(w);return w as unknown as Worker;});return {engine,workers};}
afterEach(()=>vi.useRealTimers());

describe('Worker ownership and bounded transport',()=>{
  it('keeps late errors and responses from a cancelled worker from failing its successor',async()=>{
    const {engine,workers}=fixture();const a=engine.request('analyze',{});const cancelled=expect(a).rejects.toMatchObject({code:'CANCELLED'});
    const b=engine.request('analyze',{});await cancelled;
    workers[0].onerror?.({message:'Late old-worker error'});workers[0].onmessageerror?.();workers[0].reply({ok:true,result:'obsolete'});
    workers[1].reply({ok:true,result:'current'});expect(await b).toBe('current');expect(workers[0].terminated).toBe(1);
  });
  it('settles a postMessage clone failure and immediately terminates/clears its timer',async()=>{
    vi.useFakeTimers();const worker=new WorkerDouble();worker.cloneFailure=true;
    const engine=new BrowserEngine(()=>worker as unknown as Worker);
    await expect(engine.request('analyze',{})).rejects.toMatchObject({name:'DataCloneError',message:'Original clone failure'});
    expect(worker.terminated).toBe(1);expect(vi.getTimerCount()).toBe(0);
  });
  it('refuses deserialization failure and malformed replies, then permits recovery',async()=>{
    const {engine,workers}=fixture();let pending=engine.request('analyze',{});let rejected=expect(pending).rejects.toThrow('WORKER_MESSAGE_DESERIALIZATION_FAILED');workers[0].onmessageerror?.();await rejected;
    pending=engine.request('analyze',{});rejected=expect(pending).rejects.toThrow('WORKER_INVALID_REPLY');workers[1].reply({ok:true});await rejected;
    const recovered=engine.request('interpret',{});workers[2].reply({ok:true,result:{unchanged:true}});expect(await recovered).toEqual({unchanged:true});
  });
  it('retains precise scientific refusal codes/messages and rejects invalid progress',async()=>{
    const {engine,workers}=fixture();let pending=engine.request('analyze',{});let rejected=expect(pending).rejects.toMatchObject({code:'BUDGET',message:'Exact provider scope'});workers[0].reply({ok:false,error:{code:'BUDGET',message:'Exact provider scope'}});await rejected;
    pending=engine.request('analyze',{});rejected=expect(pending).rejects.toThrow('WORKER_INVALID_REPLY');workers[1].reply({ok:true,stage:42});await rejected;
  });
  it('preserves the 120-second deadline and really terminates timed-out work',async()=>{
    vi.useFakeTimers();const {engine,workers}=fixture();const pending=engine.request('analyze',{}),rejected=expect(pending).rejects.toThrow('WORKER_TIME_BUDGET_EXCEEDED');
    await vi.advanceTimersByTimeAsync(119999);expect(workers[0].terminated).toBe(0);await vi.advanceTimersByTimeAsync(1);await rejected;expect(workers[0].terminated).toBe(1);expect(vi.getTimerCount()).toBe(0);
  });
  it('transfers each import buffer once, preserving exact names/order/byte views and freeing sender ownership',async()=>{
    const {engine,workers}=fixture();const buffer=new Uint8Array([0,4,5,6,7,0]);const files=[{name:'X.csv',bytes:buffer.subarray(1,3)},{name:'M.csv',bytes:buffer.subarray(3,5)}];
    const pending=engine.request('import',files);expect(buffer.byteLength).toBe(0);
    const received=workers[0].message!.payload as typeof files;expect(received.map(f=>({name:f.name,values:[...f.bytes]}))).toEqual([{name:'X.csv',values:[4,5]},{name:'M.csv',values:[6,7]}]);
    workers[0].reply({ok:true,result:'decoded'});expect(await pending).toBe('decoded');
  });
});
