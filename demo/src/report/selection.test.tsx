import {describe,expect,it,vi} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {Parser,HtmlRenderer} from 'commonmark';
import {savedView,reportModel} from './model';
import {serializeReport} from './export';
import {createSelection,sectionAvailability,defaultSections,optionalSections,mandatorySections,selectionOwner} from './selection';
import {ExportOptions} from './ExportOptions';
import source from '../../public/examples/tablet.unknown.saved.json';
import type {UiResult} from '../ui-types';

function live(components=2):UiResult{
  const view=savedView(source);view.mode='live';view.protocol='synthetic-display';view.provenance={source_mode:'synthetic_computed_live',verification_execution:'not_executed'};
  view.dataset={...view.dataset,id:'synthetic-display',name:'Synthetic selection fixture',contentHash:'display-hash',observations:3,variables:2,axis:[1000,1010],spectra:[{id:'raw-sentinel',values:[987654321.234,123456789.987]}]};
  view.evidence=[{id:'pca',status:'computed',reason:null,value:{eigenvalues:components===1?[4]:[4,2],full_moments:[10,20],n_components_resolved:components},scope:'three acquisitions',provider:'synthetic display fixture',method:'PCA',pointer:'/metrics/pca'},
    {id:'density',status:'computed',reason:null,value:{labels:[-1,-1,-1],membership:[0,0,0],persistence:[],n_clusters:0,noise_count:3},scope:'three acquisitions',provider:'synthetic display fixture',method:'HDBSCAN',pointer:'/metrics/density'},
    {id:'raw_neighbors',status:'unavailable',reason:'NO_ADMISSIBLE_REFERENCE',value:null,scope:'three acquisitions',provider:'synthetic display fixture',method:'neighbors',pointer:'/metrics/raw_neighbors'}];
  view.pca={points:[{id:'a',x:-1,y:components===1?0:1},{id:'b',x:0,y:0},{id:'c',x:1,y:components===1?0:-1}],eigenvalues:components===1?[4]:[4,2],totalVariance:10,xLabel:'PC1',yLabel:'PC2',resolvedComponents:components};
  view.findings=[{id:'contrary',title:'Contrary result',status:'contradicted',observation:'No measured predictive degradation',hypothesis:'Unconfirmed mechanism',relevance:'Only in the stated scope',verification:'Not executed',limitation:'No transfer demonstrated',confidence:'Source scoped',evidenceIds:['density'],prerequisites:['Original groups missing']}];
  return view;
}
function custom(view:UiResult,ids:readonly typeof optionalSections[number][]){
  const scientific=view.mode==='saved'?source:{protocol_version:view.protocol,unchanged_evidence:'original'};
  return reportModel(view,scientific,'unknown','en',undefined,'complete',createSelection(view,ids));
}
function originalFence(markdown:string){const walker=new Parser().parse(markdown).walker(),objects=[];for(let e=walker.next();e;e=walker.next())if(e.entering&&e.node.type==='code_block'&&e.node.info==='json')objects.push(JSON.parse(e.node.literal!));return objects;}

describe('F3.5 scientific core and additive export selection',()=>{
  it('keeps every finding/status/reason/value, missing prerequisite and trace with no supplements',()=>{
    const view=live(),r=custom(view,[]),html=serializeReport(r,'html'),markdown=serializeReport(r,'markdown');
    expect(r.export_selection!.mandatory_sections).toEqual(mandatorySections);expect(r.export_selection!.selected_sections).toEqual([]);
    for(const value of ['No measured predictive degradation','Original groups missing','NO_ADMISSIBLE_REFERENCE','contradicted','noise_count','evidence-density'])expect(html).toContain(value);
    expect(html).not.toContain('<figure');expect(html).toContain('All carried labels are noise');
    expect(markdown).toContain('NO\\_ADMISSIBLE\\_REFERENCE');expect(originalFence(markdown)).toEqual([r]);
    expect(JSON.parse(serializeReport(r,'json'))).toEqual(r);
  });
  it.each([['none',[]],['figures',['pca_scores','pca_scree']],['tables and methods',['detailed_tables','methods_parameters']],['provenance',['extended_provenance']],['all',optionalSections]] as const)('preserves complete original evidence and excludes display X: %s',(_,ids)=>{
    const view=live(),r=custom(view,ids),before=JSON.stringify(r.scientific_report);
    for(const format of ['html','markdown','json'] as const){const text=serializeReport(r,format);expect(text).not.toContain('987654321.234');expect(text).not.toContain('raw-sentinel');}
    expect(JSON.stringify(r.scientific_report)).toBe(before);expect(r.raw_x_included).toBe(false);expect(r.numerical_evidence_recomputed_for_export).toBe(false);
    expect(serializeReport(r,'html').includes('data-machine-appendix="true"')).toBe(ids.includes('machine_evidence' as never));
  });
  it.each([1,2])('uses the carried %sD PCA with exact axes/values and no invented component',components=>{
    const r=custom(live(components),['pca_scores','pca_scree','detailed_tables']),html=serializeReport(r,'html');
    expect(html.match(/<figure /g)).toHaveLength(2);expect(html).toContain('40 %');
    if(components===1)expect(html).toContain('PC2 is unavailable');
  });
  it('explains requested unavailable saved PCA and retains original readiness and scientific companions',()=>{
    const view=savedView(source),r=custom(view,['pca_scores','readiness','experimental_factors','representation_sensitivity']),html=serializeReport(r,'html');
    expect(r.export_selection!.selected_sections).not.toContain('pca_scores');expect(html).toContain('Requested supplement unavailable');expect(html).not.toContain('<figure');
    expect(html).toContain('supplement-readiness');expect(html).toContain('not_executed');expect(r.scientific_report).toBe(source);
    expect(r.export_selection!.sections.find(s=>s.id==='experimental_factors')!.available).toBe(true);
  });
  it('does not offer readiness or geometry from unavailable or absent source slots',()=>{
    const view=live();view.pca=null;
    expect(sectionAvailability(view).find(s=>s.id==='pca_scores')!.available).toBe(false);
    expect(sectionAvailability(view).find(s=>s.id==='readiness')!.available).toBe(false);
    expect(defaultSections(view)).not.toContain('machine_evidence');
  });
  it('retains language-neutral IDs and scopes choices to the exact dataset/source/report',()=>{
    const view=savedView(source),selection=createSelection(view,['readiness','glossary']);
    const en=reportModel(view,source,'study','en',undefined,'complete',selection),fr=reportModel(view,source,'new_context','fr',undefined,'complete',selection);
    expect(en.export_selection).toEqual(fr.export_selection);expect(serializeReport(fr,'html')).toContain('Sélection des sections du rapport');
    const other=structuredClone(view);other.dataset.id='another-dataset';expect(selectionOwner(other)).not.toBe(selectionOwner(view));
    expect(()=>reportModel(other,source,'unknown','en',undefined,'complete',selection)).toThrow('SCOPE_OR_AVAILABILITY');
  });
  it('refuses altered mandatory/available lists, unknown IDs and unknown versions',()=>{
    const view=savedView(source),r=custom(view,[]);
    expect(()=>createSelection(view,['invented' as never])).toThrow('UNKNOWN_SECTION');
    r.export_selection!.mandatory_sections=[];expect(()=>serializeReport(r,'json')).toThrow('SCOPE_OR_AVAILABILITY');
    r.export_selection=createSelection(view,[]);r.export_selection.protocol_version='unrecognized' as never;expect(()=>serializeReport(r,'html')).toThrow('VERSION_UNSUPPORTED');
  });
  it('keeps historical serialization/readings when no selection is supplied',()=>{
    const view=savedView(source),complete=reportModel(view,source,'unknown','en'),summary=reportModel(view,source,'unknown','en',undefined,'summary');
    expect(complete.export_selection).toBeUndefined();expect(JSON.parse(serializeReport(complete,'json'))).not.toHaveProperty('export_selection');
    expect(serializeReport(summary,'html')).toContain('class="report-full-reading"');
  });
  it('retains arbitrary-length source text and more than 160 recorded values without a page/row cap',()=>{
    const view=live();view.findings[0].observation='Long source sentence. '.repeat(4000)+'LONG_SOURCE_END';
    Object.assign(view.evidence[0].value!,Object.fromEntries(Array.from({length:650},(_,i)=>['carried_field_'+i,i])));
    const html=serializeReport(custom(view,['detailed_tables','machine_evidence']),'html');
    expect(html).toContain('carried_field_649');expect(html).toContain('LONG_SOURCE_END');expect(html).toContain('data-machine-appendix="true"');
    expect(html).not.toMatch(/max-pages|line-clamp|text-overflow:\s*ellipsis/);
  });
  it('keeps hostile Markdown inert and the full JSON fence exact for custom exports',()=>{
    const view=live();view.findings[0].observation='~'.repeat(64)+'\n# injected\n![remote](https://external.invalid/a) <script>alert(1)</script>';
    const r=custom(view,optionalSections),markdown=serializeReport(r,'markdown'),html=new HtmlRenderer({safe:false}).render(new Parser().parse(markdown));
    expect(originalFence(markdown)).toEqual([r]);expect(html).not.toMatch(/<(?:img|script|iframe|a)(?:\s|>)/i);
    expect(serializeReport(r,'html')).not.toContain('<script');
  });
  it('renders a bilingual native checkbox panel with disabled reasons and readonly core',()=>{
    for(const locale of ['en','fr'] as const){const html=renderToStaticMarkup(<ExportOptions view={savedView(source)} locale={locale} requested={[]} onChange={vi.fn()} onReset={vi.fn()}/>);
      expect(html.match(/data-export-section=/g)).toHaveLength(optionalSections.length);expect(html).toContain('section-reason-pca_scores');expect(html).toContain('aria-describedby="export-options-help"');expect(html).toContain('disabled');}
  });
});
