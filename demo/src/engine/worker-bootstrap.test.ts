import {readFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';
import ts from 'typescript';
import {describe,expect,it} from 'vitest';

const source=readFileSync(resolve(dirname(fileURLToPath(import.meta.url)),'worker.ts'),'utf8');
const moduleCode=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText;
const build={version:'1.2.3',commit:'a'.repeat(40),dirty:false};
function workerContext(){
 const messages:unknown[]=[],events=new Map<string,((event:any)=>void)[]>(),self:any={onmessage:null,
  postMessage:(message:unknown)=>messages.push(JSON.parse(JSON.stringify(message))),
  addEventListener:(type:string,listener:(event:any)=>void)=>events.set(type,[...(events.get(type)??[]),listener]),
 };
 vm.runInNewContext(moduleCode,{self,__DOMAINS_BUILD__:build,exports:{}},{filename:'worker.ts'});
 return {self,messages,events};
}
const plain=(v:unknown)=>JSON.parse(JSON.stringify(v)) as any;

describe('actual worker entry bootstrap protocol',()=>{
 it('emits STARTED then READY controls with build identity before any request',()=>{
  const {messages}=workerContext(),controls=plain(messages);
  expect(controls).toHaveLength(2);
  expect(controls.map((m:any)=>m.lifecycle_event)).toEqual(['WORKER_BOOTSTRAP_STARTED','WORKER_BOOTSTRAP_READY']);
  for(const control of controls){
   expect(control).toMatchObject({id:0,ok:true,protocol_version:'domains.worker_bootstrap.v1',stage_id:'prepare',component:'worker',build});
   expect(typeof control.stage).toBe('string');
  }
 });

 it.each([
  ['error','WORKER_UNCAUGHT_EXCEPTION',{message:'private error sentinel'}],
  ['unhandledrejection','WORKER_UNHANDLED_REJECTION',{reason:'private rejection sentinel'}],
 ])('converts a pre-request global %s into one safe structured bootstrap refusal',(_eventType,eventCode,fields)=>{
  const {messages,events}=workerContext();let prevented=false;
  const event={...fields,preventDefault:()=>{prevented=true;}};
  for(const listener of events.get(_eventType)??[])listener(event);
  const controls=plain(messages).filter((m:any)=>m.ok===false);
  expect(controls).toHaveLength(1);
  expect(controls[0]).toMatchObject({id:0,ok:false,protocol_version:'domains.worker_bootstrap.v1',lifecycle_event:eventCode,error:{code:eventCode,message:eventCode}});
  expect(JSON.stringify(controls[0])).not.toContain('private');expect(prevented).toBe(true);
 });

 it.each([
  ['unsupported operation',{id:2,operation:'not-an-operation',payload:{sentinel:'private'}}],
  ['invalid request id',{id:0,operation:'analyze',payload:{sentinel:'private'}}],
 ])('refuses %s exactly once after READY without loading an operation module',async(_label,data)=>{
  const {self,messages}=workerContext(),initial=messages.length;
  await self.onmessage({data});
  const first=plain(messages.slice(initial));
  expect(first).toHaveLength(1);expect(first[0].ok).toBe(false);expect(first[0].error.code).toBe('WORKER_REQUEST_INVALID');
  expect(first[0].error.details).toMatchObject({code:'WORKER_REQUEST_INVALID',component:'worker',original_message_available:false});
  expect(JSON.stringify(first)).not.toContain('sentinel');
  await self.onmessage({data:{id:3,operation:'analyze',payload:{}}});
  expect(messages).toHaveLength(initial+1);
 });
});
