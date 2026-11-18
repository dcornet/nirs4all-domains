import {describe,it,expect} from 'vitest';
import {appendSensitivity,sensitivityTables,sensitivityFigures} from './preprocessing';
import {initialSensitivityPlan,type SensitivityHistory} from '../engine/preprocessing';
import {reportModel} from './model';
import {serializeReport} from './export';
import {createSelection} from './selection';
import type {UiResult} from '../ui-types';
// Presentation-only transport fixture; values are not a numerical execution oracle.
const fixture={schema_version:1,protocol_version:'domains.browser_preprocessing_sensitivity_result.v1',status:'computed',reason:null,stage:'reference_only',population:'train',plan:initialSensitivityPlan(),plan_sha256:'p',receipt:{reference_keys:['a','b'],query_keys:[],y_accessed:false},limitations:['No causal attribution.'],representations:Array.from({length:12},(_,i)=>({id:i?'representation-'+i:'raw',family:'transport-fixture',status:i===11?'unavailable':'computed',reason:i===11?'OWNER_LOCAL_FAILURE':null,steps:[],value:i===11?null:{source:{source_id:'derived-'+i},axis:[2,1],axis_unit:'nm',transformations:[{operator:'transport-only',state_sha256:'state-'+i}],structure:{status:'computed',reason:null,value:{report:{metrics:{pca:{status:'computed',reason:null,value:{scores:[[1,2],[3,4]],eigenvalues:[2,1]}}}},scoped:null}},factors:[],support:{status:'unavailable',reason:'REFERENCE_ONLY',value:null},comparisons:{neighbors:{status:'computed',value:{retained:1,original:2,fraction:0.5}},partition:{status:'unavailable',reason:'ALL_NOISE',value:null}}}}))} as unknown as SensitivityHistory;
const base={mode:'live',protocol:'domains.browser_scoped_report.v1',dataset:{id:'fixture',source:'X',contentHash:'a'.repeat(64),name:'Transport fixture',observations:2,variables:2,axisUnit:'nm',axis:[2,1],spectra:[],metadata:[],identity:'unknown',provenance:'transport-only',license:'synthetic'},summary:'Existing history',findings:[],evidence:[{id:'f40',value:{original:true}}],factorAssociations:[{original:'f41'}],supportResults:[{original:'f42'}],pca:null,geometryReason:'none',limitations:[],provenance:{source_mode:'user_computed_live'}} as unknown as UiResult;
describe('F4.3 uncapped presentation-only transport',()=>{
 it('draws each available representation using its own source and keys; retains every unavailable reason and comparison',()=>{
  const figures=sensitivityFigures(fixture,'preprocessing-sensitivity-1','en');expect(figures).toHaveLength(22);expect(figures[0].points?.map(p=>p.id)).toEqual(['a','b']);expect(figures[2].representation).toContain('derived-1');
  const tables=sensitivityTables(fixture,'en');expect(tables.find(t=>t.id==='sensitivity-panel')?.rows).toHaveLength(12);expect(JSON.stringify(tables)).toContain('OWNER_LOCAL_FAILURE');expect(JSON.stringify(tables)).toContain('ALL_NOISE');expect(JSON.stringify(tables)).toContain('retained');
 });
 it('never invents point identity and preserves earlier operations and original scientific objects in all exports',()=>{
  expect(sensitivityFigures({...fixture,receipt:{reference_keys:[]}},'sensitivity','fr')).toEqual([]);const snapshot=JSON.stringify(base),view=appendSensitivity(base,[fixture]);expect(JSON.stringify(base)).toBe(snapshot);expect(view.supportResults).toEqual(base.supportResults);expect(view.factorAssociations).toEqual(base.factorAssociations);expect(view.evidence[0]).toEqual(base.evidence[0]);
  for(const locale of ['en','fr'] as const){const model=reportModel(view,{protocol_version:base.protocol,preprocessing_sensitivity:[fixture]},'unknown',locale,undefined,'complete',createSelection(view,['representation_sensitivity','pca_scores','pca_scree','detailed_tables']));expect(model.presentation?.figures).toHaveLength(22);for(const format of ['html','markdown','json'] as const){const output=serializeReport(model,format);expect(output).toContain('representation-11');expect(output).toContain('OWNER_LOCAL_FAILURE');expect(output).toContain('state-10');expect(output).not.toContain('SECRET_TARGET');}}
 });
});
