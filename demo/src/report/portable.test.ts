import {describe,it,expect} from 'vitest';
import {portableData,zipStore,manifest,CSV_COLUMNS,BOUNDS} from './portable';
import type {DemoReport} from './model';

const report=(value:unknown):DemoReport=>({protocol_version:'domains.browser_demo_report.v1',generated_at_utc:'2026-11-19T16:00:00Z',language:'en',source_mode:'live',intended_use:'unknown',user_declarations:{population:null,prediction_unit:null,new_context:null},dataset:{name:'synthetic',id:'synthetic',source:'public',contentHash:'a'.repeat(64),observations:3,variables:2,axis:[1000,1100],axisUnit:'nm',metadata:[],identity:'declared',provenance:'synthetic',license:'synthetic'},summary:'Synthetic only',findings:[],evidence:[{id:'result-1',method:'test',status:'computed',reason:null,value,scope:'train',provider:'pinned'}],pca:null,limitations:['No predictive qualification'],provenance:{},scientific_report:null,raw_x_included:false,numerical_evidence_recomputed_for_export:false});
describe('Portable evidence serialization',()=>{
 it('retains null, refusal, quoted/newline/formula strings and every scalar without fitting',()=>{
  const value={status:'unavailable',reason:'refusal, "quoted"\nline',scores:[[1,2],[3,4]],absent:null,empty:[],text:'=HYPERLINK("bad")'};
  const r=report(value),original=JSON.stringify(r),data=portableData(r);
  expect(data.rows).toBe(9);expect(data.sections[0].row_count).toBe(9);expect(data.csv.startsWith(CSV_COLUMNS.join(','))).toBe(true);
  expect(data.csv).toContain('/evidence/0/value/scores/1/1');expect(data.csv).toContain('value_type');expect(data.json).toContain('unavailable');expect(JSON.stringify(r)).toBe(original);
 });
 it('exports a large logical matrix completely without generating a presentation DOM',()=>{
  const data=portableData(report({scores:Array.from({length:10000},(_,i)=>[i,-i])}));
  expect(data.rows).toBe(20000);expect(data.csv).toContain('/scores/9999/1');expect(data.json).not.toContain('presentation');
 });
 it('refuses an oversized table before returning a partial CSV',()=>{
  const previous=BOUNDS.csv,r=report({scores:Array.from({length:100},(_,i)=>[i,-i])}),original=JSON.stringify(r);
  try{BOUNDS.csv=512;expect(()=>portableData(r)).toThrow('CSV_ADMISSION_EXCEEDED');expect(JSON.stringify(r)).toBe(original);}finally{BOUNDS.csv=previous;}
 });
 it('rejects raw/private fields and nonfinite numbers rather than extending permissions',()=>{
  for(const value of [{spectra:[[1,2]]},{Y:[1]},{state_bytes:[2]},{bad:Infinity}])expect(()=>portableData(report(value))).toThrow();
  expect(()=>portableData({...report({safe:1}),scientific_report:{Y:[1]}})).toThrow();
  expect(()=>portableData({...report({safe:1}),provenance:{bad:Infinity}})).toThrow();
 });
 it('uses stable source pointers and carries observation/axis keys only when supplied',()=>{
  const data=portableData(report({receipt:{reference_keys:['a','b'],query_keys:['t']},scores:[[1],[2]],test_scores:[[3]],axis:[1000],loadings:[[.2]]}));
  expect(data.csv).toContain('""a""');expect(data.csv).toContain('""t""');expect(data.csv).toContain('1000');
  expect(portableData(report({receipt:{fit_keys:['fit'],query_keys:['query']},train_scores:[[1]],test_scores:[[2]]})).csv).toContain('""fit""');
 });
 it('preserves only existing hash/shape and empty-access receipts, never raw payloads under similar names',()=>{
  const descriptor={sha256:'a'.repeat(64),shape:[3,2]};
  expect(()=>portableData(report({receipt:{fields_read:{x:{matrix:descriptor},y:[]},provider_calls:[{shapes:{matrix:[3,2],state_bytes:[1,32]},matrices:{matrix:descriptor}}]}}))).not.toThrow();
  for(const value of [{receipt:{fields_read:{y:[1]}}},{receipt:{fields_read:{x:{matrix:{...descriptor,raw:[1,2]}}}}},{receipt:{shapes:{state_bytes:[1,2,3]}}}])expect(()=>portableData(report(value))).toThrow();
  const meta={name:'yield',unit:null,type:'numeric',rows:3,missing:0};
  expect(()=>portableData({...report({safe:1}),scientific_report:{inventory:{loaded:{y:[meta]}}}})).not.toThrow();
  expect(()=>portableData({...report({safe:1}),scientific_report:{inventory:{loaded:{y:[{...meta,values:[1,2,3]}]}}}})).toThrow();
  expect(()=>portableData({...report({safe:1}),pca:{points:[{id:'a',x:1,y:2}],eigenvalues:[1,1],totalVariance:2,xLabel:'PC1',yLabel:'PC2',resolvedComponents:2}})).not.toThrow();
 });
 it('maps complete sections to actual companion bytes, with safe extractable ZIP paths',async()=>{
  const r=report({value:1}),d=portableData(r),files={'results.csv':new TextEncoder().encode(d.csv),'report.json':new TextEncoder().encode(d.json)};
  const m=await manifest(r,d,files);expect(m.csv.row_count).toBe(1);expect(m.files.every(f=>/^[a-f0-9]{64}$/.test(f.sha256))).toBe(true);
  const zip=zipStore(files);expect(new DataView(zip.buffer).getUint32(0,true)).toBe(0x04034b50);expect(()=>zipStore({'../escape':new Uint8Array()})).toThrow();
 });
});
