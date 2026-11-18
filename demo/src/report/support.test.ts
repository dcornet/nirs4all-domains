import {describe,it,expect} from 'vitest';
import {supportFigures,supportTables,appendSupport} from './support';
import {figureSvg} from './render';
import {reportModel} from './model';
import {serializeReport} from './export';
import {createSelection} from './selection';
import type {SupportRun} from '../engine/support';
import type {SupportResult} from '@nirs4all/domains';
import type {UiResult} from '../ui-types';
// Presentation-only transport fixture. Numeric values are not a native/WASM qualification oracle.
const fixture={protocol_version:'domains.browser_train_fitted_support_result.v1',status:'computed',reason:null,
 projection:{status:'computed',reason:null,value:{train_scores:[[10,0,20]],test_scores:[[11,0,21]],components:3,display_components:[2],component_summaries:[{mean:10,stddev:0}],fit_state_sha256:'f'.repeat(64),reference_variance:{status:'unavailable',reason:'NOT_EXPOSED',value:null}}},
 monitoring:{status:'computed',reason:null,value:{reference_t2:[2],reference_q:[3],descriptive_fractions:{t2:{numerator:1,denominator:1,value:1}},monitored_t2:[7],monitored_q:[9],t2_limit:4,q_limit:5,centroid_distance:2}},
 limit_qualification:{status:'unknown',reasons:['UNKNOWN_PHYSICAL_IDENTITY'],source:null,fold_scheme:'row_index_modulo_n_folds',independent_units_certified:false},dependence:{},receipt:{fit_keys:['a'],query_keys:['b']},supported_claims:[],limitations:['No predictive validation.']} as unknown as SupportResult;
const base={mode:'live',protocol:'domains.browser_scoped_report.v1',dataset:{id:'transport',source:'X',contentHash:'a'.repeat(64),name:'Transport fixture',observations:2,variables:2,axisUnit:'nm',axis:[2,1],spectra:[],metadata:[],identity:'unknown',provenance:'transport-only',license:'synthetic'},summary:'Existing result',findings:[],evidence:[],pca:null,geometryReason:'none',limitations:[],provenance:{source_mode:'user_computed_live'}} as UiResult;
describe('F4.2 presentation-only transport tests',()=>{
 it('distinguishes local documentary refusal from the strict runtime result protocol without provider certification',()=>{
  const reason='LOCAL_REQUEST_REFUSED';
  const local:SupportRun={protocol_version:'domains.browser_train_fitted_support_local_refusal.v1',status:'unavailable',reason,local_refusal:true,evidence_sha256:null,
   projection:{status:'unavailable',reason,value:null},monitoring:{status:'unavailable',reason,value:null},
   limit_qualification:{status:'unknown',reasons:['NO_SUCCESSFUL_PROVIDER_RECEIPT'],source:null,fold_scheme:'row_index_modulo_n_folds',independent_units_certified:false,interpretation:'No provider receipt returned; limits unavailable.'},
   dependence:{},receipt:{execution_receipt:'not_returned; no successful execution inferred'},supported_claims:[],limitations:['Documentary refusal only.']};
  const view=appendSupport(base,[local]);expect(view.evidence[0].method).toBe(local.protocol_version);expect(view.evidence[0].provider).toContain('Local documentary refusal');
  expect(view.findings[0].status).toBe('unavailable');expect(view.findings[0].confidence).not.toContain('Provider-recorded');expect(view.findings[0].confidence).toContain('no owner certification');expect(supportFigures(local,'local','en')).toEqual([]);
  const report=reportModel(view,{train_fitted_support:[local]},'unknown','en');expect((report.scientific_report as any).train_fitted_support[0].evidence_sha256).toBeNull();
  expect(serializeReport(report,'json')).not.toContain('domains.browser_train_fitted_support_result.v1');
 });
 it('uses actual informative index, one-dimensional rail and distinct population shapes',()=>{
  const [f]=supportFigures(fixture,'support-1','en');expect(f.kind).toBe('scores1d');expect(f.xLabel).toBe('PC3');expect(f.points?.map(p=>p.x)).toEqual([20,21]);
  const svg=figureSvg(f,'en');expect(svg).toContain('<circle');expect(svg).toContain('<rect');expect(svg).not.toContain('PC2');
 });
 it('does not draw unavailable coordinates or infer qualified limits',()=>{
  expect(supportFigures({...fixture,projection:{status:'unavailable',value:null}},'support','fr').some(f=>f.id.endsWith('-projection'))).toBe(false);
  const monitor=supportTables(fixture,'en').find(t=>t.id==='support-monitoring')!;expect(monitor.note).toContain('limits unqualified');expect(monitor.rows.some(row=>row[0]==='monitored_q')).toBe(false);
  const tables=supportTables(fixture,'en'),test=tables.find(t=>t.id==='support-observations-monitored')!;expect(test.rows[0].slice(0,3)).toEqual(['b',7,9]);expect(test.rows[0][3]).toMatchObject({status:'unknown'});
  expect(tables.find(t=>t.id==='support-fractions')?.rows).toEqual([['t2',1,1,1]]);
  expect(supportFigures(fixture,'support','en').find(f=>f.id.endsWith('-t2'))?.points?.map(p=>p.id)).toEqual(['a','b']);
 });
 it('withholds figures for missing or mismatched receipt keys without inventing identities',()=>{
  for(const receipt of [{},{fit_keys:['a'],query_keys:[]},{fit_keys:['a'],query_keys:[null]}]){
   const result={...fixture,receipt};expect(supportFigures(result,'support','en')).toEqual([]);
   expect(supportTables(result,'en').find(t=>t.id==='support-observations-monitored')?.note).toContain('OBSERVATION_KEY_MAPPING_UNAVAILABLE');
  }
 });
 it('appends without mutating history and carries exact scientific evidence through FR/EN exports and selected annexes',()=>{
  const historical={...base,factorAssociations:[{protocol_version:'preserved-f41'}] as any,evidence:[{id:'f40',value:{status:'computed'}}] as any};const before=JSON.stringify(historical),view=appendSupport(historical,[fixture]);expect(JSON.stringify(historical)).toBe(before);expect(view.factorAssociations).toEqual(historical.factorAssociations);expect(view.evidence[0]).toEqual(historical.evidence[0]);
  for(const locale of ['en','fr'] as const){
   const model=reportModel(view,{protocol_version:base.protocol,train_fitted_support:[fixture]},'unknown',locale,undefined,'complete',createSelection(view,['pca_scores','detailed_tables']));
   expect(model.presentation?.figures[0].xLabel).toBe('PC3');
   for(const format of ['html','markdown','json'] as const){const output=serializeReport(model,format);expect(output).toContain('fit_state_sha256');expect(output).toContain('UNKNOWN_PHYSICAL_IDENTITY');expect(output).not.toContain('SECRET_PREDICT');}
  }
 });
});
