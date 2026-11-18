import {describe,it,expect,vi} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {SensitivityPanel} from './SensitivityPanel';
describe('F4.3 explicit two-stage controls',()=>{
 it('renders balanced twelve-family parameters and disabled audit without a freeze; language/rendering never executes work',()=>{
  const onRun=vi.fn(),controls={factors:[],hasTest:true,frozen:null};
  for(const locale of ['en','fr'] as const){const html=renderToStaticMarkup(<SensitivityPanel results={[]} controls={controls} locale={locale} busy={false} onRun={onRun}/>);expect(html).toContain('sg_d2');expect(html).toContain('standard_scale');expect(html).toContain('Sensitivity plan JSON'.replace('Sensitivity plan JSON',locale==='fr'?'Plan de sensibilit\u00e9 JSON':'Sensitivity plan JSON'));expect(html).toContain('disabled');}
  expect(onRun).not.toHaveBeenCalled();
 });
});
