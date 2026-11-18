import {describe,it,expect,vi} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {SupportPanel} from './SupportPanel';
describe('F4.2 explicit execution controls',()=>{
 it('changing language or rendering pending controls cannot start a scientific operation',()=>{
  const run=vi.fn();
  const en=renderToStaticMarkup(<SupportPanel results={[]} locale="en" busy={false} onRun={run}/>);
  const fr=renderToStaticMarkup(<SupportPanel results={[]} locale="fr" busy={true} onRun={run}/>);
  expect(run).not.toHaveBeenCalled();expect(en).toContain('Parameters fixed before execution');expect(fr).toContain('disabled');
  expect(en).toContain('no test optimization');expect(en).not.toContain('independence checkbox');
 });
});
