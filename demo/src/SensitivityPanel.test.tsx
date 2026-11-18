import {describe,it,expect,vi} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {SensitivityPanel} from './SensitivityPanel';
import {initialSensitivityPlan,type SensitivityHistory} from './engine/preprocessing';
describe('F4.3 explicit two-stage controls',()=>{
 it('renders balanced twelve-family parameters and disabled audit without a freeze; language/rendering never executes work',()=>{
  const onRun=vi.fn(),controls={factors:[],hasTest:true,frozen:null};
  for(const locale of ['en','fr'] as const){const html=renderToStaticMarkup(<SensitivityPanel results={[]} controls={controls} locale={locale} busy={false} onRun={onRun}/>);expect(html).toContain('sg_d2');expect(html).toContain('standard_scale');expect(html).toContain('Sensitivity plan JSON'.replace('Sensitivity plan JSON',locale==='fr'?'Plan de sensibilit\u00e9 JSON':'Sensitivity plan JSON'));expect(html).toContain('disabled');}
  expect(onRun).not.toHaveBeenCalled();
 });
 it('keeps refusal reasons visible and complete advanced evidence available in collapsed tables in both languages',()=>{
  const result={protocol_version:'domains.browser_preprocessing_sensitivity_result.v1',status:'computed',reason:null,stage:'reference_only',plan:initialSensitivityPlan(),receipt:{reference_keys:[],query_keys:[]},findings:[],limitations:[],representations:[{id:'raw',family:'raw',status:'unavailable',reason:'OWNER_LOCAL_FAILURE',steps:[],value:null}]} as unknown as SensitivityHistory;
  for(const locale of ['en','fr'] as const){
   const html=renderToStaticMarkup(<SensitivityPanel results={[result]} controls={{factors:[],hasTest:false,frozen:null}} locale={locale} busy={false} onRun={vi.fn()}/>);
   const advanced=html.indexOf('<details class="sensitivity-advanced">');
   expect(advanced).toBeGreaterThan(0);
   expect(html.slice(0,advanced)).toContain('OWNER_LOCAL_FAILURE');
   expect(html.slice(advanced)).toContain('reference_keys');
   expect(html.slice(advanced)).toContain('OWNER_LOCAL_FAILURE');
   expect(html).not.toContain('<details class="sensitivity-advanced" open');
  }
 });
});
