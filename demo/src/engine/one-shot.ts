/** Technical import orchestration only. IO owns inference, parsing, validation and joins. */
import {buildExportConfig,type DatasetExportConfig,type DatasetSource} from 'nirs4all-ui/datasetBuilder';
import {assembleDatasetDraft,prepareDataset,type DatasetDraft,type FormatsRuntime,type IoRuntime,type ReviewedDatasetConfig} from './import-draft';
import type {InputFile,LocalDataset} from './types';

export interface ImportIssue {
 code:string;kind:'source_role'|'join_key'|'partition'|'target'|'delimiter'|'advanced';
 source_id?:string;column?:string;message:string;blocking:boolean;
}
export interface ImportSession {
 draft:DatasetDraft;config:DatasetExportConfig;sources:DatasetSource[];issues:ImportIssue[];
}
export interface ImportSummary {
 observations:number;variables:number;targets:{name:string;type:string;missing:number;rows:number}[];
 metadata:{name:string;missing:number;rows:number}[];partitions:{name:string;rows:number}[];
 missing_x:number;alignment:'validated'|'restricted';unresolved_sources:number;content_sha256:string;
}
export type ImportOutcome={status:'loaded';dataset:LocalDataset;session:ImportSession}|{status:'needs_input';dataset?:LocalDataset;session:ImportSession};

const errorText=(error:unknown)=>error instanceof Error?error.message:String(error);
const hasX=(s:DatasetSource)=>s.columns.some(c=>c.assignedRole==='x');
const ignored=(s:DatasetSource):DatasetSource=>({...s,columns:s.columns.map(c=>({...c,assignedRole:'ignored'}))});
const explicit=(draft:DatasetDraft)=>draft.files.some(f=>f.name.endsWith('.nirs4all.json'));

export function defaultImportConfig(draft:DatasetDraft):ReviewedDatasetConfig{
 const config:ReviewedDatasetConfig={...buildExportConfig(draft.spec.name??'Imported dataset',draft.sources),metadata_declarations:draft.spec.metadata_declarations as ReviewedDatasetConfig['metadata_declarations']};
 const tasks=draft.spec.target_tasks as Record<string,string>|undefined;
 config.targets=config.targets.map(t=>({...t,...(tasks?.[t.column]?{task:tasks[t.column] as typeof t.task}:{})}));
 // Inferred attachments use native left coverage: no X row is removed for absent Y/M.
 // An explicit manifest's requested coverage is authoritative and stays strict.
 config.joins=config.joins.map(join=>{
  const source=draft.sources.find(s=>s.name===join.right),original=draft.spec.sources.find(s=>s.id===source?.id);
  const coverage=(original?.join as {coverage?:unknown}|undefined)?.coverage;
  return {...join,strategy:(!explicit(draft)||coverage==='warn')?'allow_missing':'strict'};
 });
 return config;
}
function issue(error:unknown,source?:DatasetSource,blocking=true):ImportIssue{
 const message=errorText(error);
 const kind:ImportIssue['kind']=/join|duplicate.*key|identifier|key|required.*anchor/i.test(message)?'join_key'
  :/delimiter|csv|column.*not found|unknown column|column.*missing/i.test(message)?'delimiter'
  :/partition/i.test(message)?'partition':/spectral|MULTISOURCE|FEATURE|NO_X/i.test(message)?'source_role':'advanced';
 const stable=message.match(/^([A-Z][A-Z0-9_]+)(?::|$)/)?.[1];
 return {code:stable??'IO_ASSEMBLY_REQUIRES_INPUT',kind,...(source?{source_id:source.id}:{}),message,blocking:blocking||/duplicate keys|ambiguous/i.test(message)};
}
export function summarizeImport(data:LocalDataset,session:ImportSession):ImportSummary{
 const rows=data.rowManifest??[];
 const partitions=new Map<string,number>();for(const row of rows)partitions.set(row.partition,(partitions.get(row.partition)??0)+1);
 const missing=(v:readonly unknown[])=>v.reduce<number>((n,x)=>n+(x===null?1:0),0);
 return {observations:rows.length,variables:data.input.axis.length,
  targets:(data.targets??[]).map(t=>({name:t.name,type:t.type,missing:missing(t.values),rows:t.values.length})),
  metadata:data.metadata.map(m=>({name:m.name,missing:missing(m.values),rows:m.values.length})),
  partitions:[...partitions].map(([name,rows])=>({name,rows})),missing_x:(data.missingX??[]).reduce((n,row)=>n+row.filter(Boolean).length,0),
  alignment:session.issues.length?'restricted':'validated',unresolved_sources:new Set(session.issues.map(i=>i.source_id).filter(Boolean)).size,content_sha256:data.input.content_sha256};
}
export async function autoImportDataset(files:InputFile[],io:IoRuntime,formats:FormatsRuntime):Promise<ImportOutcome>{
 const draft=prepareDataset(files,io,formats,{allowUnassigned:true});
 return resolveDatasetDraft(draft,defaultImportConfig(draft),draft.sources,io,'automatic');
}
/** No parser or join lives here: every candidate is validated/materialized by IO. */
export async function resolveDatasetDraft(draft:DatasetDraft,config:DatasetExportConfig,sources:DatasetSource[],io:IoRuntime,mode:'automatic'|'user_configured'='automatic'):Promise<ImportOutcome>{
 if(mode==='user_configured'){
  // A parser edit changes the owner's header vocabulary. Re-materialize that
  // source with IO before translating roles; never split/parse CSV in JS.
  for(const source of sources){
   const previous=draft.sources.find(s=>s.id===source.id);
   if(!previous||JSON.stringify(previous.parsing)===JSON.stringify(source.parsing))continue;
   const original=draft.spec.sources.find(s=>s.id===source.id);if(!original)continue;
   const probe:DatasetDraft['spec']['sources'][number]={...original,params:{...original.params,delimiter:source.parsing.separator,has_header:source.parsing.headerMode!=='none',decimal_separator:source.parsing.decimal??'.'}};
   delete probe.columns;
   try{
    const decoded:FormatsRuntime={openWithSidecars:(name)=>{const record=draft.records.find(r=>r.source===name);if(!record)throw new Error('EXISTING_FORMATS_RECORD_REQUIRED');return record.records;}};
    const refreshed=prepareDataset(draft.files,io,decoded,{allowUnassigned:true,specOverride:{...draft.spec,sources:[probe]},refreshColumns:true});
    if(refreshed.assemblyError)throw new Error(refreshed.assemblyError);
    const fresh=refreshed.sources[0];
    if(!fresh?.columns.length)throw new Error('IO_PARSED_COLUMNS_REQUIRED');
    const old=new Map(source.columns.map(c=>[c.name,c]));
    const updated={...fresh,...source,columns:fresh.columns.map(c=>({...c,...(old.has(c.name)?{assignedRole:old.get(c.name)!.assignedRole,manual:old.get(c.name)!.manual}:{})}))};
    sources=sources.map(s=>s.id===source.id?updated:s);
    draft={...draft,spec:{...draft.spec,sources:draft.spec.sources.map(s=>s.id===source.id?probe:s)},sources:draft.sources.map(s=>s.id===source.id?updated:s)};
   }catch(error){return {status:'needs_input',session:{draft,config,sources,issues:[{...issue(error,source),kind:'delimiter'}]}};}
  }
 }
 const session:ImportSession={draft,config,sources,issues:[]};
 if(draft.unassignedInputs?.length){session.issues=draft.unassignedInputs.map(name=>({code:'IO_UNASSIGNED_INPUT_REQUIRES_EXPLICIT_CONFIGURATION',kind:'source_role',message:`IO did not associate source ${name}. Open advanced settings to declare its role.`,blocking:true}));return {status:'needs_input',session};}
 const spectral=sources.filter(hasX);
 if(!spectral.length){session.issues=[{code:'SPECTRAL_SOURCE_REQUIRED',kind:'source_role',message:'Which source contains the spectral X columns?',blocking:true}];return {status:'needs_input',session};}
 const partition=(s:DatasetSource)=>s.columns.some(c=>c.assignedRole==='partition')?'column':s.usage.useAs==='x_test'?'test':s.usage.useAs==='x_train'?'train':draft.spec.sources.find(o=>o.id===s.id)?.partition??'unpartitioned';
 if(spectral.some((s,i)=>spectral.slice(i+1).some(t=>partition(t)===partition(s)))){
  session.issues=spectral.map(s=>({code:'MULTISOURCE_SELECTION_REQUIRED_NO_IMPLICIT_FUSION',kind:'source_role',source_id:s.id,message:'Choose the spectral source to explore. Independent X blocks are not fused automatically; other files remain in this session.',blocking:true}));return {status:'needs_input',session};
 }
 const assemble=(candidate:DatasetSource[])=>assembleDatasetDraft(draft,config,candidate,io,mode==='user_configured');
 const finish=(dataset:LocalDataset):ImportOutcome=>{
  if(session.issues.length)dataset.warnings.push(...session.issues.map(i=>`${i.code}: source ${i.source_id??'unknown'} is retained separately, not joined to X. Its dependent operations remain unavailable.`));
  return session.issues.some(i=>i.blocking)?{status:'needs_input',dataset,session}:{status:'loaded',dataset,session};
 };
 try{return finish(await assemble(sources));}catch(error){
  const auxiliaries=sources.filter(s=>!hasX(s)&&s.columns.some(c=>c.assignedRole!=='ignored'));
  if(!auxiliaries.length){session.issues=[issue(error)];return {status:'needs_input',session};}
  const baseSources=sources.map(s=>hasX(s)?s:ignored(s));
  let base:LocalDataset;
  try{base=await assemble(baseSources);}catch(baseError){session.issues=[issue(baseError)];return {status:'needs_input',session};}
  const valid=new Set<string>(),failures:ImportIssue[]=[];
  for(const source of auxiliaries){
   try{await assemble(sources.map(s=>hasX(s)||s.id===source.id?s:ignored(s)));valid.add(source.id);}
   catch(sourceError){failures.push(issue(sourceError,source,explicit(draft)));}
  }
  if(valid.size){
   try{const data=await assemble(sources.map(s=>hasX(s)||valid.has(s.id)?s:ignored(s)));session.issues=failures;return finish(data);}
   catch(combinationError){session.issues=auxiliaries.map(s=>issue(combinationError,s,false));return finish(base);}
  }
  session.issues=failures.length?failures:auxiliaries.map(s=>issue(error,s,false));return finish(base);
 }
}
