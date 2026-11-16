import { describe,expect,it,vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { Parser,HtmlRenderer } from 'commonmark';
import { reportModel,savedView } from '../report/model';
import { serializeReport } from '../report/export';
import { ErrorFeedback,Processing } from './Feedback';
import { ContextHelp,helpIds } from './Help';
import { translator } from '../i18n';
import { Workspace } from '../Workspace';
import source from '../../public/examples/tablet.unknown.saved.json';

describe('F2 readings of unchanged F1 scientific evidence',()=>{
  it.each(['en','fr'] as const)('retains exact original evidence in partial HTML, JSON and CommonMark (%s)',locale=>{
    const view=savedView(source),before=JSON.stringify(source);
    const partial=reportModel(view,source,'unknown',locale,undefined,'summary');
    const html=serializeReport(partial,'html'),markdown=serializeReport(partial,'markdown');
    const root=new Parser().parse(markdown),walker=root.walker();let node;const originals=[];
    while((node=walker.next()))if(node.entering&&node.node.type==='code_block'&&node.node.info==='json')originals.push(JSON.parse(node.node.literal!));
    expect(originals).toEqual([partial]);expect(JSON.parse(serializeReport(partial,'json')).scientific_report).toEqual(source);
    expect(html).toContain('data-reading="summary"');expect(html).toContain('class="report-full-reading"');
    expect(html).not.toContain('class="report-full-reading" open');expect(html).toContain('class="report-partial"');
    expect(html).toContain("default-src 'none'");expect(html).not.toContain('<script');
    const complete=reportModel(view,source,'unknown',locale);
    expect(complete.reading_mode).toBe('complete');expect(partial.scientific_report).toBe(complete.scientific_report);
    expect(partial.findings).toEqual(complete.findings);expect(partial.evidence).toEqual(complete.evidence);
    expect(JSON.stringify(source)).toBe(before);expect(partial.raw_x_included).toBe(false);
  });
  it('escapes adversarial source text in the new partial reading and keeps the full JSON fence intact',()=>{
    const view=savedView(source),payload='~~~~\n# injected\n![remote](https://external.invalid/image) <script>alert(1)</script>';
    view.dataset.name=payload;Object.assign(view.findings[0],{observation:payload,relevance:payload,verification:payload});
    const report=reportModel(view,source,'unknown','en',undefined,'summary');
    const html=serializeReport(report,'html'),markdown=serializeReport(report,'markdown');
    expect(html).not.toContain('<script>');expect(/<img[^>]+src=["']https?:/.test(html)).toBe(false);
    const rendered=new HtmlRenderer().render(new Parser().parse(markdown));
    expect(rendered).not.toContain('<img');expect(rendered).not.toContain('href="https://external.invalid');
    const walker=new Parser().parse(markdown).walker();let event;const objects=[];
    while((event=walker.next()))if(event.entering&&event.node.type==='code_block'&&event.node.info==='json')objects.push(JSON.parse(event.node.literal!));
    expect(objects).toEqual([report]);
  });
  it('keeps all F1 availability and contradictory states in both readings',()=>{
    const view=savedView(source);view.findings[0].status='contradicted';view.findings[0].verification='Not executed';
    const report=reportModel(view,source,'unknown','en',undefined,'summary');
    const html=serializeReport(report,'html');
    for(const block of report.presentation!.blocks)expect(html).toContain(block.reason??'');
    expect(html).toContain('Contradicted');expect(html).toContain('Not executed');
    expect(report.presentation!.findings[0].status).toBe('contradicted');
  });
});

describe('F2 accessible guidance without numerical rules',()=>{
  it.each(['en','fr'] as const)('provides keyboard-native four-part definitions and original refusal details (%s)',locale=>{
    const help=renderToStaticMarkup(<ContextHelp ids={helpIds} locale={locale}/>);
    expect(helpIds).toHaveLength(16);expect(help.match(/class="help-card"/g)).toHaveLength(16);expect(help.match(/<dt>/g)).toHaveLength(64);
    const exact='X_NONFINITE: <source.csv> row 7';
    const error=renderToStaticMarkup(<ErrorFeedback error={{code:'INPUT_REFUSED',message:exact}} locale={locale}/>);
    expect(error).toContain('role="alert"');expect(error).toContain('tabindex="-1"');expect(error).toContain('X_NONFINITE: &lt;source.csv&gt; row 7');
    expect(error).not.toContain('<source.csv>');expect(error).toContain('href="#import-guide"');
  });
  it('announces only the actual stage with real cancellation, without a percent estimate',()=>{
    const html=renderToStaticMarkup(<Processing state={{phase:"running",progress:"Original provider stage",processingStage:"compute",error:null,result:null,examples:[],intent:"unknown",importHint:""}} locale="en" onCancel={vi.fn()}/>);
    expect(html).toContain('Original provider stage');expect(html).toContain('aria-live="polite"');
    expect(html.match(/aria-current="step"/g)).toHaveLength(1);expect(html).not.toContain('%');expect(html).toContain('Cancel');
  });
  it('keeps four open steps, exact scientific anchors and unverified declarations without adding a split choice',()=>{
    const view=savedView(source),callbacks={onImport:vi.fn(),onExample:vi.fn(),onCancel:vi.fn(),onReset:vi.fn(),onIntent:vi.fn(),onExport:vi.fn()};
    const before=JSON.stringify(view),html=renderToStaticMarkup(<Workspace result={view} intent="unknown" callbacks={callbacks} locale="en" t={translator('en')}/>);
    for(let i=1;i<=4;i++)expect(html).toContain(`id="journey-${i}"`);
    expect(html).toContain('id="report-summary"');expect(html).toContain('href="#data"');expect(html).toContain('Optional user declarations, not verified evidence.');
    for(const block of reportModel(view,source,'unknown','en').presentation!.blocks)expect(html.match(new RegExp(`id="evidence-${block.id}"`,'g'))).toHaveLength(1);
    expect(JSON.stringify(view)).toBe(before);expect(html).not.toContain('name="split"');
  });
});
