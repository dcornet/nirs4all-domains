import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { DatasetLoadedSummary } from './DatasetLoadedSummary';
import { ImportResolution } from './ImportResolution';
import { DatasetImport } from './DatasetImport';
import { Landing } from './Landing';
import { translator } from './i18n';
import { App } from './App';
import { savedView } from './report/model';
import saved from '../public/examples/tablet.unknown.saved.json';
import type { ImportSession, ImportSummary } from './engine/one-shot';
import type { UiCallbacks } from './ui-types';

const source: ImportSession['sources'][number] = {
  id: 'x', name: 'folder/x.csv', kind: 'file', fileType: 'csv', signalType: 'spectra', status: 'parsed',
  parsing: { separator: ',' }, usage: { useAs: 'x_train_test' },
  columns: [{id:'key',name:'sample',detectedType:'text',assignedRole:'id'}, {id:'x1',name:'1100',detectedType:'float',assignedRole:'x'}],
};
const session: ImportSession = {
  draft: { files: [], records: [], spec: { schema_version:1, sources: [{id:'x', input:'folder/x.csv',role:'features'}] }, sources: [source], warnings: [], taskType: null },
  config: {name:'Fixture',sources:[],targets:[],metadata:[],joins:[]}, sources: [source],
  issues: [{ code:'KEY_REQUIRED',kind:'join_key',source_id:'x',message:'Select a declared key <sample>.',blocking:true }],
};
const summary: ImportSummary = {observations:7,variables:13,targets:[{name:'response',type:'regression',missing:3,rows:7}],metadata:[{name:'campaign',missing:7,rows:7}],partitions:[{name:'train',rows:5},{name:'test',rows:2}],missing_x:0,alignment:'restricted',unresolved_sources:1,content_sha256:'fixture'};
const callbacks: UiCallbacks = {onImport:vi.fn(),onExample:vi.fn(),onCancel:vi.fn(),onReset:vi.fn(),onIntent:vi.fn(),onExport:vi.fn(),onConfirmImport:vi.fn(),onDismissImport:vi.fn()};

describe('one-shot import presentation', () => {
  it.each(['en','fr'] as const)('opens optional pre-import settings through an actual option, separate from help (%s)', locale => {
    const html = renderToStaticMarkup(<Landing state={{phase:'idle',progress:'',error:null,result:null,examples:[],intent:'unknown',importHint:'',editImportFirst:false}} callbacks={{...callbacks,onImportOptionsChange:vi.fn()}} t={translator(locale)} busy={false} locale={locale}/>);
    expect(html).toContain('<details class="import-settings-before"><summary');
    expect(html).toContain(locale === 'fr' ? 'Ouvrir les paramètres avancés après l’identification des sources par IO' : 'Open advanced settings after IO identifies the sources');
    expect(html).toContain('type="checkbox"');expect(html).not.toContain('checked=""');
    expect(html).toContain('id="import-guide"');
  });
  it('shows the requested optional editor directly when IO has no issue questions', () => {
    const html = renderToStaticMarkup(<ImportResolution session={{...session,issues:[]}} locale="en" busy={false} onConfirm={vi.fn()} onDismiss={vi.fn()}/>);
    expect(html).toContain('Data import settings');expect(html).toContain('Dataset Builder');expect(html).toContain('Apply changes');
    expect(html).not.toContain('Required corrections');expect(html).not.toContain('Apply corrections');expect(html).not.toContain('Complete dataset loading');
  });
  it.each(['en','fr'] as const)('renders runtime counts, missingness and restrictions without invented qualification (%s)', locale => {
    const html = renderToStaticMarkup(<DatasetLoadedSummary summary={summary} locale={locale}/>);
    for(const value of ['>7</dd>','>13</dd>','>5</dd>','>2</dd>','response','campaign','3 / 7','7 / 7']) expect(html).toContain(value);
    expect(html).toContain(locale === 'fr' ? 'restrictions identifiées' : 'restrictions identified');
    expect(html).toContain(locale === 'fr' ? 'aucune indépendance physique' : 'physical independence is not established');
    expect(html).not.toContain('420');
  });
  it('asks only the runtime-reported question and retains inferred answers', () => {
    const html = renderToStaticMarkup(<ImportResolution session={session} locale="en" busy={false} onConfirm={vi.fn()} onDismiss={vi.fn()}/>);
    expect(html).toContain('KEY_REQUIRED');expect(html).toContain('Select a declared key &lt;sample&gt;.');
    expect(html).toContain('folder/x.csv · Join key');expect(html).toContain('value="sample" selected=""');
    // Only the focused correction is visible; the shared full editor is optional.
    expect(html).not.toContain('· Source role');expect(html).not.toContain('· Delimiter');
    expect(html).toContain('<details class="data-settings"><summary>Advanced settings</summary>');
    expect(html).not.toContain('I confirm the displayed roles');
  });
  it.each(['en','fr'] as const)('keeps the advanced editor optional with immediate revalidation action and no global acceptance checkbox (%s)', locale => {
    const html = renderToStaticMarkup(<DatasetImport locale={locale} draft={session.draft} initialSources={session.sources} initialConfig={session.config} onConfirm={vi.fn()} onCancel={vi.fn()}/>);
    expect(html).toContain(locale === 'fr' ? 'Appliquer les modifications' : 'Apply changes');expect(html).toContain(locale === 'fr' ? 'IO validera à nouveau' : 'IO will validate the data again');
    expect(html).not.toContain('I confirm the displayed roles');
    expect(html).toContain(locale === 'fr' ? 'Origine et rôles des métadonnées' : 'Metadata origin and roles');
  });
  it('keeps the last valid dataset visible during a failed replacement with targeted correction', () => {
    const result = savedView(saved);
    const html = renderToStaticMarkup(<App callbacks={callbacks} state={{phase:'error',progress:'',error:{code:'KEY_REQUIRED',message:'Native join failure'},result,examples:[],intent:'unknown',importHint:'',importDraft:session.draft,importSession:session}}/>);
    expect(html).toContain('Complete dataset loading');expect(html).toContain('Native join failure');
    expect(html).toContain('id="workspace-title"');expect(html).toContain('Saved evidence');
  });
});
