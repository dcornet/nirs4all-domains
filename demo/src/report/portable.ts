/** Portable presentation v2. Documentary serialization only; no provider calls. */
import type {DemoReport} from './model';
import {presentation,formatValue} from './presentation';
import {figureSvg} from './render';
import type {UiResult} from '../ui-types';
import fontUrl from './assets/NotoSans-Regular.ttf?url';
import fontLicense from './assets/OFL.txt?raw';

export const PORTABLE_PROTOCOL='domains.portable_report.v2';
export const CSV_COLUMNS=['section_id','result_id','representation_id','json_pointer','value_type','value_json','observation_key_json','axis_key_json','row_index','column_index','section_status','section_reason_json','unit_json'];
const encoder=new TextEncoder();
export const BOUNDS={csv:50_000_000,package:100_000_000,document:4_000_000,figurePoints:1000,deadline:120_000};
type Section={id:string;result_id:string;file:string;source_pointer:string;first_data_row:number;row_count:number;status:string;reason:string|null;scope:string;provider:string};
export interface PortableData {csv:string;json:string;sections:Section[];rows:number;}
const pointer=(s:string)=>s.replaceAll('~','~0').replaceAll('/','~1');
const cell=(v:unknown)=>'"'+String(v??'').replaceAll('"','""')+'"';
const idCell=(v:unknown)=>v===undefined?'':JSON.stringify(v);
type Context={representation?:string;keys?:unknown[];query?:unknown[];axis?:unknown[]};
/** Each permitted scalar has one typed, exact RFC6901 address; never samples. */
export function portableData(report:DemoReport):PortableData{
 if(report.raw_x_included!==false||report.numerical_evidence_recomputed_for_export!==false)throw Error('PERMISSION_FILTERED_REPORT_REQUIRED');
 const forbidden=new Set(['spectra','matrix','raw_X','raw_x','raw_y','raw_Y','state_bytes','n4me_bytes','raw_state','training_rows','Y','y']);
 const shape=(value:unknown)=>Array.isArray(value)&&value.length===2&&value.every(n=>Number.isSafeInteger(n)&&n>=0);
 const documentary=(path:string,key:string,value:any)=>{
  if(key==='y'&&/^\/pca\/points\/\d+$/.test(path))return typeof value==='number'&&Number.isFinite(value);
  if(key==='y'&&['/provenance/scoped_inventory/loaded','/scientific_report/inventory/loaded'].includes(path))return Array.isArray(value)&&value.every(column=>column&&typeof column==='object'&&Object.keys(column).sort().join(',')==='missing,name,rows,type,unit'&&typeof column.name==='string'&&typeof column.type==='string'&&(column.unit===null||typeof column.unit==='string')&&Number.isSafeInteger(column.rows)&&column.rows>=0&&Number.isSafeInteger(column.missing)&&column.missing>=0);
  if(key==='y'&&path.endsWith('/fields_read'))return Array.isArray(value)&&value.length===0;
  if(['matrix','state_bytes'].includes(key)&&path.endsWith('/shapes'))return shape(value);
  if(key==='matrix'&&(path.endsWith('/fields_read/x')||path.endsWith('/matrices')))return value&&typeof value==='object'&&Object.keys(value).sort().join(',')==='sha256,shape'&&/^[a-f0-9]{64}$/.test(value.sha256)&&shape(value.shape);
  return false;
 };
 const inspect=(value:unknown,path=''):void=>{if(typeof value==='number'&&!Number.isFinite(value))throw Error('NONFINITE_EXPORT_VALUE');if(value&&typeof value==='object')for(const [key,item] of Object.entries(value)){if(forbidden.has(key)&&!documentary(path,key,item))throw Error('FORBIDDEN_EXPORT_FIELD:'+path+'/'+key);inspect(item,path+'/'+pointer(key));}};
 inspect(report);
 const chunks=[CSV_COLUMNS.join(',')+'\r\n'];let bytes=chunks[0].length,rows=0;const sections:Section[]=[];
 for(const [index,e] of report.evidence.entries()){
  const result=e.value as Record<string,any>|null;
  const section:Section={id:e.id,result_id:String(result?.evidence_sha256??e.id),file:'results.csv',source_pointer:`/evidence/${index}/value`,first_data_row:rows+2,row_count:0,status:e.status,reason:e.reason,scope:e.scope??'not carried',provider:e.provider??'not carried'};
  function visit(value:unknown,path:string,ctx:Context){
   if(value!==null&&typeof value==='object'&&Object.keys(value).length){
    const o=value as Record<string,any>;
    const next={...ctx,...(!Array.isArray(o)&&o.family&&o.id?{representation:String(o.id)}:{}),
     ...(Array.isArray(o.axis)?{axis:o.axis}:{}),...(Array.isArray(o.receipt?.reference_keys)?{keys:o.receipt.reference_keys}:Array.isArray(o.receipt?.fit_keys)?{keys:o.receipt.fit_keys}:{}),
     ...(Array.isArray(o.receipt?.query_keys)?{query:o.receipt.query_keys}:{}),
     ...(Array.isArray(o.scope?.observation_ids)?{keys:o.scope.observation_ids}:{})};
    for(const [key,item] of Object.entries(o)){
     visit(item,path+'/'+pointer(key),next);
    }return;
   }
   if(typeof value==='number'&&!Number.isFinite(value))throw Error('NONFINITE_EXPORT_VALUE');
   const matrix=path.match(/\/(scores|train_scores|test_scores|loadings)\/(\d+)\/(\d+)$/),r=matrix?Number(matrix[2]):undefined,c=matrix?Number(matrix[3]):undefined;
   const keys=matrix?.[1]==='test_scores'?ctx.query:ctx.keys;
   const fields=[section.id,section.result_id,ctx.representation??'',path,value===null?'null':Array.isArray(value)?'array':typeof value,
    JSON.stringify(value),idCell(matrix?.[1]!=='loadings'&&r!==undefined?keys?.[r]:undefined),idCell(/\/axis\/\d+$/.test(path)?value:undefined),r??'',c??'',section.status,JSON.stringify(section.reason),JSON.stringify(/\/axis\/\d+$/.test(path)?report.dataset.axisUnit:null)];
   // Identifier strings are JSON-encoded too: CSV import cannot execute formulas.
   for(const i of [0,1,2])fields[i]=JSON.stringify(fields[i]);
   const line=fields.map(cell).join(',')+'\r\n';bytes+=encoder.encode(line).length;
   if(bytes>BOUNDS.csv)throw Error('CSV_ADMISSION_EXCEEDED');chunks.push(line);rows++;section.row_count++;
  }
  visit(e.value,section.source_pointer,{axis:report.dataset.axis,keys:e.id==='pca'?report.pca?.points.map(p=>p.id):undefined});sections.push(section);
 }
 const json=JSON.stringify(report,null,2)+'\n';if(encoder.encode(json).length>BOUNDS.package/2)throw Error('JSON_ADMISSION_EXCEEDED');
 return {csv:chunks.join(''),json,sections,rows};
}

async function sha(bytes:Uint8Array){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new Uint8Array(bytes)))).map(n=>n.toString(16).padStart(2,'0')).join('');}
export async function manifest(report:DemoReport,data:PortableData,files:Record<string,Uint8Array>){
 return {protocol_version:PORTABLE_PROTOCOL,generated_at_utc:report.generated_at_utc,dataset:report.dataset,source_protocol:report.protocol_version,
  selection:report.export_selection??null,scope:'Complete existing permission-filtered evidence; PDF annex selection grants no new export permission.',
  csv:{file:'results.csv',encoding:'UTF-8',line_ending:'CRLF',format:'RFC4180',columns:CSV_COLUMNS,row_count:data.rows,
   ordering:'Evidence order, then original object/array order. Row/column indices are zero-based. Source pointers address report.json.',
   values:'value_json, reason/unit and *_key_json are JSON literals; identifier cells also encode JSON strings for spreadsheet safety. Section status/reason accompany every independent CSV row. unit_json carries the original physical axis unit for axis cells; null means not carried for this scalar. Null/empty containers are explicit. No newly computed metrics.',
   absence:'Only carried values are exported; absent loadings or other diagnostics are not reconstructed.'},sections:data.sections,
  files:await Promise.all(Object.entries(files).map(async([path,bytes])=>({path,bytes:bytes.length,sha256:await sha(bytes)}))),
  qualifications:report.limitations,raw_x_included:false,numerical_evidence_recomputed_for_export:false};
}

/** ZIP store format: binary transport, no compression/analysis kernel. */
export function zipStore(files:Record<string,Uint8Array>):Uint8Array{
 if(Object.values(files).reduce((sum,value)=>sum+value.length,22)>BOUNDS.package)throw Error('PACKAGE_ADMISSION_EXCEEDED');
 const parts:Uint8Array[]=[],central:Uint8Array[]=[];let offset=0,centralBytes=0;
 const u16=(v:DataView,p:number,n:number)=>v.setUint16(p,n,true),u32=(v:DataView,p:number,n:number)=>v.setUint32(p,n,true);
 for(const [path,bytes] of Object.entries(files)){
  if(!/^[a-zA-Z0-9_./-]+$/.test(path)||path.startsWith('/')||path.split('/').includes('..'))throw Error('UNSAFE_ARCHIVE_PATH');
  const name=encoder.encode(path);let crc=0xffffffff;for(const b of bytes){crc^=b;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}crc=(crc^0xffffffff)>>>0;
  const local=new Uint8Array(30+name.length),l=new DataView(local.buffer);u32(l,0,0x04034b50);u16(l,4,20);u16(l,6,0x800);u16(l,12,33);u32(l,14,crc);u32(l,18,bytes.length);u32(l,22,bytes.length);u16(l,26,name.length);local.set(name,30);
  const directory=new Uint8Array(46+name.length),d=new DataView(directory.buffer);u32(d,0,0x02014b50);u16(d,4,20);u16(d,6,20);u16(d,8,0x800);u16(d,14,33);u32(d,16,crc);u32(d,20,bytes.length);u32(d,24,bytes.length);u16(d,28,name.length);u32(d,42,offset);directory.set(name,46);
  parts.push(local,bytes);central.push(directory);offset+=local.length+bytes.length;centralBytes+=directory.length;
  if(offset+centralBytes+22>BOUNDS.package)throw Error('PACKAGE_ADMISSION_EXCEEDED');
 }
 const end=new Uint8Array(22),v=new DataView(end.buffer);u32(v,0,0x06054b50);u16(v,8,central.length);u16(v,10,central.length);u32(v,12,centralBytes);u32(v,16,offset);
 const result=new Uint8Array(offset+centralBytes+22);let at=0;for(const p of [...parts,...central,end]){result.set(p,at);at+=p.length;}return result;
}

async function raster(svg:string):Promise<Uint8Array>{
 const image=new Image(),url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'}));
 try{image.src=url;await image.decode();const canvas=document.createElement('canvas');canvas.width=1110;canvas.height=525;const context=canvas.getContext('2d')!;context.fillStyle='white';context.fillRect(0,0,canvas.width,canvas.height);context.drawImage(image,0,0,canvas.width,canvas.height);return new Uint8Array(await(await fetch(canvas.toDataURL('image/png'))).arrayBuffer());}finally{URL.revokeObjectURL(url);}
}

export async function portablePdf(report:DemoReport,data:PortableData,paper:'a4'|'letter'):Promise<Uint8Array>{
 const start=Date.now(),{PDFDocument,PDFString,rgb}=await import('pdf-lib'),fontkit=(await import('@pdf-lib/fontkit')).default;
 const pdf=await PDFDocument.create();pdf.registerFontkit(fontkit);const response=await fetch(fontUrl);if(!response.ok)throw Error('PDF_FONT_UNAVAILABLE');
 const font=await pdf.embedFont(await response.arrayBuffer(),{subset:true}),supported=new Set(font.getCharacterSet());
 const size: [number,number]=paper==='a4'?[595.28,841.89]:[612,792];const margin=42,width=size[0]-2*margin;let page=pdf.addPage(size),y=size[1]-margin,documentBytes=0;
 const advances=new Map<string,number>();
 const advance=(char:string,size:number)=>{const key=size+':'+char;let value=advances.get(key);if(value===undefined){value=font.widthOfTextAtSize(char,size);advances.set(key,value);}return value;};
 const check=()=>{if(Date.now()-start>BOUNDS.deadline)throw Error('PDF_GENERATION_DEADLINE');};
 const room=(height:number)=>{check();if(y-height<margin){page=pdf.addPage(size);y=size[1]-margin;}};
 const text=(value:unknown,size=10,color=rgb(.12,.2,.23))=>{
  const literal=String(value??'Not carried').replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g,c=>'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'));
  documentBytes+=encoder.encode(literal).length;if(documentBytes>BOUNDS.document)throw Error('PDF_DOCUMENT_ADMISSION_EXCEEDED');
  // A visible Unicode escape retains unsupported identifier characters; exact UTF-8 is in companions.
  const str=Array.from(literal).map(c=>supported.has(c.codePointAt(0)!)||c==='\n'?c:'[U+'+c.codePointAt(0)!.toString(16).toUpperCase()+']').join('');
  for(const paragraph of str.split('\n')){
   let line='',lineWidth=0;const flush=()=>{room(size+5);page.drawText(line||' ',{x:margin,y,font,size,color});y-=size+5;line='';lineWidth=0;};
   for(const word of paragraph.split(/\s+/).filter(Boolean)){
    const wordWidth=Array.from(word).reduce((n,c)=>n+advance(c,size),0),gap=line?advance(' ',size):0;
    if(line&&lineWidth+gap+wordWidth>width-4)flush();
    if(wordWidth<=width-4){if(line){line+=' ';lineWidth+=advance(' ',size);}line+=word;lineWidth+=wordWidth;}
    else for(const char of word){const w=advance(char,size);if(lineWidth+w>width-4&&line)flush();line+=char;lineWidth+=w;}
   }flush();
  }
 };
 const link=(path:string,label:string)=>{room(18);const ly=y;text(label,9,rgb(0,.35,.4));const annotation=pdf.context.obj({Type:'Annot',Subtype:'Link',Rect:[margin,ly-3,size[0]-margin,ly+12],Border:[0,0,0],A:{Type:'Action',S:'URI',URI:PDFString.of(path)}});page.node.addAnnot(pdf.context.register(annotation));};
 const heading=(s:string)=>{room(48);y-=10;text(s,15);};
 const view={mode:report.source_mode.includes('saved')?'saved':'live',dataset:{...report.dataset,spectra:[]},protocol:report.protocol_version,summary:report.summary,findings:report.findings,evidence:report.evidence,pca:report.pca,geometryReason:null,limitations:report.limitations,provenance:report.provenance} as UiResult;
 const p=presentation(view,report.language,report.intended_use,{compact:true});
 const selected=report.export_selection?new Set<string>(report.export_selection.selected_sections):null;
 const show=(id:string)=>!selected||selected.has(id);
 pdf.setTitle('Domains - '+report.dataset.name);pdf.setLanguage(report.language);pdf.setSubject(PORTABLE_PROTOCOL);pdf.setCreationDate(new Date(report.generated_at_utc));
 heading(report.language==='fr'?'Domains - Synthese scientifique':'Domains - Scientific synthesis');text(report.dataset.name,13);text(report.generated_at_utc+' / '+paper.toUpperCase());text(report.summary);
 text('Population: '+String(report.dataset.population)+'; observations: '+String(report.dataset.observations)+'; variables: '+String(report.dataset.variables));text('Source: '+report.dataset.source+' / '+report.dataset.contentHash);text('Protocol: '+report.protocol_version+' / '+PORTABLE_PROTOCOL);text('Representation-conditional observations; no preprocessing ranking or predictive-risk score.');
 text('Compact reading with complete permitted companions. PDF summaries do not replace machine evidence. Numeric portability remains unqualified until the mandatory provider gate passes.');
 text('Extract domains-results.zip to keep the PDF and its relative CSV, JSON and manifest paths together.');
 link('results.csv',`Detailed CSV: results.csv (${data.rows} typed value rows; ${CSV_COLUMNS.length} columns)`);link('report.json','Structured evidence: report.json');link('manifest.json','Sections, row counts and provenance: manifest.json');
 for(const f of report.findings){heading(f.title);for(const s of [f.status,f.observation,f.hypothesis,f.relevance,f.verification,f.limitation])text(s);}
 for(const block of p.blocks){
  heading(block.title);text('Evidence: '+block.id+' / '+block.status+' / '+(block.reason??'computed'));text('Scope: '+block.scope+' / '+block.representation);text('Provider: '+block.provider);text(block.definition);text(block.observed);
  text('Method/protocol: '+String(report.evidence.find(e=>e.id===block.id)?.method??'not carried'),9);
  const section=data.sections.find(s=>s.id===block.id)!;link('results.csv',`${section.row_count} complete typed value rows: results.csv; section ${JSON.stringify(block.id)}; first data row ${section.first_data_row}`);
  const original=block.original as Record<string,any>|null;
  if(original?.stage)text(`Stage: ${original.stage}; population: ${original.population}; reference rows: ${original.receipt?.reference_keys?.length??'not carried'}; query rows: ${original.receipt?.query_keys?.length??'not carried'}`);
  if(Array.isArray(original?.representations))for(const r of original.representations){
   text(`${r.id} / ${r.family} / ${r.status} / ${r.reason??'available'}; parameters: ${JSON.stringify(r.steps)}`);
   const metrics=r.value?.structure?.value?.report?.metrics;
   if(metrics?.pca?.status==='computed')text(`Recorded PCA: ${metrics.pca.value.n_components_resolved} resolved components; scores ${metrics.pca.value.scores?.length??'not carried'} rows x ${metrics.pca.value.scores?.[0]?.length??'not carried'} columns; eigenvalues: ${formatValue(metrics.pca.value.eigenvalues,report.language)}`,9);
   if(metrics?.density)text(`Recorded density: ${metrics.density.status}; clusters: ${metrics.density.value?.n_clusters??'unavailable'}; reason: ${metrics.density.reason??'not carried'}`,9);
   if(show('experimental_factors')||show('representation_sensitivity'))for(const factor of r.value?.factors??[]){text(`Factor association: ${factor.status}; ${factor.reason??'available'}`,9);for(const f of factor.value?.factors??[]){text(String(f.factor_id),10);for(const pc of f.components.slice(0,12))text(`PC${pc.component}: ${pc.descriptive.status}; ${pc.descriptive.value?.measure??'unavailable'} = ${formatValue(pc.descriptive.value?.estimate,report.language)}; ${pc.descriptive.reason??''}`,9);if(f.components.length>12)text(`All ${f.components.length} component records, counts, owner outputs and statuses are in results.csv.`,9);}}
   if(r.value?.support)text(`Frozen support: ${r.value.support.status}; ${r.value.support.reason??'read recorded diagnostics in companions'}`,9);
  }
  if(show('detailed_tables')||show('methods_parameters'))for(const table of block.tables){text(table.title,11);const rows=table.rows.slice(0,12);for(const row of rows){const values=row.slice(0,8).map(v=>{const s=formatValue(v,report.language);return s.length>180?`Detailed ${typeof v} value in CSV (${s.length} characters)`:s;});text(values.join(' | '),9);}if(table.rows.length>12||table.columns.length>8)text(`Compact layout: ${table.rows.length} rows x ${table.columns.length} columns; all values in results.csv.`,9);}
  for(const limit of block.limitations)text(limit,9);
 }
 for(const figure of p.figures){if(!show(figure.kind==='scree'?'pca_scree':'pca_scores'))continue;heading(figure.title);text(figure.population+' / '+figure.representation);text(figure.definition,9);if((figure.points?.length??0)>BOUNDS.figurePoints){text(`Figure deferred without subsampling: ${figure.points!.length} points; complete CSV/JSON companions.`);continue;}
  const svg=figureSvg(figure,report.language);documentBytes+=encoder.encode(svg).length;if(documentBytes>BOUNDS.document)throw Error('PDF_DOCUMENT_ADMISSION_EXCEEDED');const png=await pdf.embedPng(await raster(svg));room(265);page.drawImage(png,{x:margin,y:y-240,width,height:width*350/740});y-=250;for(const l of figure.limitations)text(l,9);
 }
 heading('Limitations and provenance');for(const l of report.limitations)text(l,9);if(show('extended_provenance'))text(JSON.stringify(report.provenance),9);text('Unicode glyphs unavailable in the embedded font are shown as [U+CODE]; exact UTF-8 source names remain in JSON/CSV.');
 const pages=pdf.getPages();pages.forEach((p,i)=>p.drawText(`${i+1} / ${pages.length}`,{x:margin,y:22,font,size:8}));check();return pdf.save();
}

export type PortableFormat='pdf_a4'|'pdf_letter'|'csv'|'archive';
export async function portableFiles(report:DemoReport,format:PortableFormat):Promise<{name:string;bytes:Uint8Array;type:string}>{
 const data=portableData(report);
 if(format==='csv')return {name:'results.csv',bytes:encoder.encode(data.csv),type:'text/csv;charset=utf-8'};
 if(format==='pdf_a4'||format==='pdf_letter')return {name:`report-${format.slice(4)}.pdf`,bytes:await portablePdf(report,data,format==='pdf_a4'?'a4':'letter'),type:'application/pdf'};
 const files:Record<string,Uint8Array>={'report.json':encoder.encode(data.json),'results.csv':encoder.encode(data.csv),'licenses/NotoSans-OFL.txt':encoder.encode(fontLicense)};
 files['report-a4.pdf']=await portablePdf(report,data,'a4');files['report-letter.pdf']=await portablePdf(report,data,'letter');
 files['manifest.json']=encoder.encode(JSON.stringify(await manifest(report,data,files),null,2)+'\n');return {name:'domains-results.zip',bytes:zipStore(files),type:'application/zip'};
}

export async function downloadPortable(report:DemoReport,format:PortableFormat,current=()=>true){const file=await portableFiles(report,format);if(!current())return;const url=URL.createObjectURL(new Blob([new Uint8Array(file.bytes)],{type:file.type}));const a=document.createElement('a');a.href=url;a.download=file.name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
