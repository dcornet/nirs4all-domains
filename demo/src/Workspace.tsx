import { useEffect,useMemo,useState, type ReactNode } from 'react';
import { EigenvalueScree, ScoreMap, SpectraExplorer } from 'nirs4all-ui/qualification';
import type { EvidenceStatus, Locale, PredictionIntent, UiCallbacks, UiDeclarations, UiResult,ReadingMode } from './ui-types';
import type { T } from './i18n';
import { presentation, reportCopy, anchor } from './report/presentation';
import { blocksHtml, readingHtml, figureSvg } from './report/render';
import { uxCopy,intentDescriptions } from './ux/copy';
import { ContextHelp,helpIds } from './ux/Help';
import { Findings } from './ux/Findings';
import {ExportOptions} from './report/ExportOptions';
import {createSelection,selectionOwner,type OptionalSection} from './report/selection';
import {selectionCopy} from './report/selection-copy';
import {ScopeControls,ScopeInventory} from './ScopeControls';
import {FactorAssociationControls} from './FactorAssociationControls';
import {FactorAssociationResults} from './FactorAssociationResults';
import {SensitivityPanel} from './SensitivityPanel';
import {SupportPanel} from './SupportPanel';
import {FactorColorLegend} from './FactorColorLegend';

const colors = ['#0d9488', '#7c3aed', '#d97706', '#0284c7', '#db2777', '#65a30d'];
const sections = ['data', 'spectra', 'geometry', 'warnings', 'intent', 'evidence', 'export'] as const;
const intents: PredictionIntent[] = ['unknown', 'study', 'known_acquisitions', 'new_specimens', 'new_groups', 'new_context'];
function Badge({ status, t }: { status: EvidenceStatus; t: T }) { return <span className={`status status-${status}`}>{t(status)}</span>; }
function Section({ id, number, title, intro, children }: { id: string; number: string; title: string; intro?: string; children: ReactNode }) {
  return <section className="workspace-section" id={id} tabIndex={-1}><div className="section-heading"><span className="section-number">{number}</span><div><h2>{title}</h2>{intro && <p>{intro}</p>}</div></div>{children}</section>;
}
export function Workspace({ result, intent, declarations, callbacks, locale, t,busy=false }: { result: UiResult; intent: PredictionIntent; declarations?: UiDeclarations; callbacks: UiCallbacks; locale: Locale; t: T;busy?:boolean }) {
  const { dataset } = result;
  const report = useMemo(()=>presentation(result, locale, intent),[result,locale,intent]), c = reportCopy(locale),u=uxCopy(locale);
  const [reading,setReading]=useState<ReadingMode>('complete');
  const [choices,setChoices]=useState<{owner:string;ids:OptionalSection[];action:'toggle'|'select_all'|'clear'}|null>(null);
  const owner=selectionOwner(result),requested=choices?.owner===owner?choices.ids:undefined;
  const selection=requested?createSelection(result,requested,choices!.action):undefined;
  const selectionLabels=selectionCopy(locale);
  const {structureHtml,otherHtml}=useMemo(()=>{
    const ids=new Set(['pca','density','raw_neighbors','projected_neighbors','metadata_factor_association','resampling_stability','parameter_sensitivity','predictive_performance']);
    return {structureHtml:blocksHtml({...report,blocks:report.blocks.filter(b=>ids.has(b.id))},locale),otherHtml:blocksHtml({...report,blocks:report.blocks.filter(b=>!ids.has(b.id))},locale)};
  },[report,locale]);
  const [selected, setSelected] = useState<string | null>(null);
  const [colorByGroup, setColorByGroup] = useState(false);
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(Math.max(0, dataset.axis.length - 1));
  useEffect(()=>{
    const reveal=(hash=location.hash)=>{const id=hash.slice(1);if(!id)return;let node=document.getElementById(id);if(!node){try{node=document.getElementById(decodeURIComponent(id));}catch{return;}}if(!node)return;for(let parent=node.parentElement;parent;parent=parent.parentElement)if(parent instanceof HTMLDetailsElement)parent.open=true;node.setAttribute('tabindex','-1');node.focus({preventScroll:true});node.scrollIntoView({block:'start',behavior:'instant'});};
    const onHash=()=>reveal();const onClick=(event:MouseEvent)=>{const link=event.target instanceof Element?event.target.closest('a[href^="#"]'):null;const hash=link?.getAttribute('href');if(hash)reveal(hash);};window.addEventListener('hashchange',onHash);window.addEventListener('click',onClick);return()=>{window.removeEventListener('hashchange',onHash);window.removeEventListener('click',onClick);};
  },[]);
  const selectedSeries = dataset.spectra.find(series => series.id === selected);
  const series = dataset.spectra.map((s, i) => ({ id: s.id, label: s.group, values: s.values.slice(start, end + 1), color: colors[i % colors.length]! }));
  return <>
    <div className="workspace-header"><div className="container"><div className="workspace-title"><div><span className={`mode-label ${result.mode}`}>{t(result.mode)}</span><h1 id="workspace-title" tabIndex={-1}>{dataset.name}</h1></div><button className="button secondary" onClick={callbacks.onReset}>← {t('newData')}</button></div>
      <p className="workspace-summary">{report.brief[0]}</p><details className="source-summary"><summary>{c.original}</summary><p>{result.summary}</p></details><div className="workspace-facts"><span><strong>{dataset.observations === null ? t('notCarried') : dataset.observations.toLocaleString(locale)}</strong> {t('samples')}</span><span><strong>{dataset.variables === null ? t('notCarried') : dataset.variables.toLocaleString(locale)}</strong> {t('variables')}</span><span>{result.protocol}</span></div>
    </div></div>
    <nav className="journey-nav" aria-label={u.route}><div className="container">{u.steps.map((title,index)=><a key={index} href={`#journey-${index+1}`}><span>0{index+1}</span>{title}</a>)}</div></nav>
    <details className="container direct-navigation"><summary>{u.direct}</summary><nav aria-label={u.direct}>{sections.map(section=><a key={section} href={`#${section}`}>{t(section)}</a>)}<a href="#report-summary">{u.returnSummary}</a></nav></details>
    <div className="container workspace-content">
      <section id="journey-1" className="journey-step" tabIndex={-1} aria-label={u.steps[0]}><span className="journey-label">01 · {u.steps[0]}</span>
      <Section id="data" number="01" title={t('data')}>
        <div className="data-grid"><div className="panel"><dl className="facts"><div><dt>{t('source')}</dt><dd>{dataset.source}</dd></div><div><dt>{t('axis')}</dt><dd>{dataset.axis.length ? `${dataset.axis[0]} → ${dataset.axis[dataset.axis.length - 1]} ${dataset.axisUnit}` : '—'}</dd></div><div><dt>{t('identity')}</dt><dd>{dataset.identity}</dd></div><div><dt>{t('license')}</dt><dd>{dataset.license}</dd></div></dl></div>
        <div className="panel metadata-panel"><h3>{t('metadata')}</h3>{dataset.metadata.length ? <div className="chips">{dataset.metadata.map(column => <span key={column}>{column}</span>)}</div> : <p>{t('unknownMetadata')}</p>}<details><summary>{t('provenance')}</summary><p>{dataset.provenance}</p><dl><dt>Dataset ID</dt><dd><code>{dataset.id}</code></dd><dt>SHA-256</dt><dd><code className="hash">{dataset.contentHash}</code></dd></dl></details></div></div>
      </Section>
      <ScopeInventory result={result} locale={locale}/>
      <aside className="notice"><h3>{u.missing}</h3><p>{u.documentationLimit}</p><p>{t('intentLimit')}</p><h3>{u.populations}</h3>{Array.isArray(result.provenance.imported_partitions)?<ul>{(result.provenance.imported_partitions as {name:string;observation_ids:string[]}[]).map(p=><li key={p.name}>{p.name}: {p.observation_ids.length} · {t('samples')}</li>)}</ul>:<p>{u.noPopulations}</p>}</aside><ContextHelp ids={['metadata','physical','batch']} locale={locale}/></section>
      <section id="journey-2" className="journey-step" tabIndex={-1} aria-label={u.steps[1]}><span className="journey-label">02 · {u.steps[1]}</span>
      <Section id="spectra" number="02" title={t('spectra')} intro={t('spectralIntro')}>
        <p>{c.spectraRead}</p><p className="chart-caption">{c.signal} · {c.raw}</p>
        {dataset.spectra.length ? <div className="panel chart-panel"><div className="chart-toolbar"><label>{t('select')}<select value={selected ?? ''} onChange={event => setSelected(event.target.value || null)}><option value="">{t('all')}</option>{dataset.spectra.map(s => <option key={s.id} value={s.id}>{s.id}{s.group ? ` · ${s.group}` : ''}</option>)}</select></label>
          <div className="range-fields"><span>{t('zoom')}</span><label className="visually-hidden" htmlFor="axis-from">{t('from')}</label><input id="axis-from" type="number" min={0} max={Math.max(0, end - 1)} value={start} onChange={event => setStart(Math.max(0, Math.min(end - 1, Number(event.target.value))))}/><span>—</span><label className="visually-hidden" htmlFor="axis-to">{t('to')}</label><input id="axis-to" type="number" min={start + 1} max={dataset.axis.length - 1} value={end} onChange={event => setEnd(Math.max(start + 1, Math.min(dataset.axis.length - 1, Number(event.target.value))))}/><button className="text-button" onClick={() => { setStart(0); setEnd(dataset.axis.length - 1); }}>{t('resetZoom')}</button></div></div>
          <SpectraExplorer axis={dataset.axis.slice(start, end + 1)} series={series} axisUnit={dataset.axisUnit} title={t('spectra')} selected={selected ? [selected] : []} onSelect={setSelected} locale={locale}/>
          <p className="chart-caption">{t('displayOnly')}</p>{selectedSeries && <p className="selection" role="status">{t('selected')}: <strong>{selectedSeries.id}</strong>{selectedSeries.group ? ` · ${selectedSeries.group}` : ''}</p>}
        </div> : <div className="unavailable panel"><Badge status="unavailable" t={t}/><p>{result.provenance.scoped_inventory?(locale==='fr'?'Données importées conservées ; choisir une opération admissible. Aucune coordonnée n’est reconstruite.':'Imported data retained; choose an admitted operation. No coordinates are reconstructed.'):c.saved}</p></div>}
      </Section>
      {callbacks.onScopedOperation&&<ScopeControls result={result} locale={locale} busy={busy} hideInventory onOperation={callbacks.onScopedOperation} onColor={callbacks.onColorFactor}/>}
      {callbacks.onSensitivity&&result.sensitivityControls&&<SensitivityPanel results={result.sensitivityResults??[]} controls={result.sensitivityControls} locale={locale} busy={busy} onRun={callbacks.onSensitivity}/>}
      {callbacks.onSupport&&<SupportPanel results={result.supportResults??[]} locale={locale} busy={busy} onRun={callbacks.onSupport}/>}
      {result.factorControls&&callbacks.onFactorAssociation&&<FactorAssociationControls {...result.factorControls} locale={locale} busy={busy}
        onRun={callbacks.onFactorAssociation} onColor={callbacks.onAssociationColor??(()=>{})} onAuthorizeColorExport={callbacks.onAuthorizeFactorColorExport??(()=>{})} onLoadInferencePlan={callbacks.onFactorInferencePlan}/>}
      {result.factorAssociations?.map((association,index)=><FactorAssociationResults key={index} result={association} locale={locale}/>)}
      <ContextHelp ids={['pca','component','variance']} locale={locale}/><Section id="geometry" number="03" title={t('geometry')} intro={t('geometryIntro')}>
        {result.pca ? <><div className="chart-toolbar"><label className="check"><input type="checkbox" checked={colorByGroup} onChange={event => setColorByGroup(event.target.checked)}/>{t('group')}</label></div><div className="geometry-grid">{report.figures.filter(figure=>!figure.populationMarkers&&!figure.evidenceId.startsWith('preprocessing-sensitivity-')).map(figure=><figure className="panel chart-panel report-figure" key={figure.id}><h3>{figure.title}</h3>{figure.kind==='scores'?<ScoreMap title={figure.title} points={figure.points!} xLabel={figure.xLabel} yLabel={figure.yLabel} colorBy={colorByGroup||!!result.factorLegend?'group':'none'} groupColors={figure.groupColors} locale={locale}/>:figure.kind==='scree'?<EigenvalueScree title={figure.title} eigenvalues={figure.eigenvalues!} totalVariance={null} locale={locale}/>:<div dangerouslySetInnerHTML={{__html:figureSvg(figure,locale)}}/>}{figure.factorLegend&&<FactorColorLegend legend={figure.factorLegend} locale={locale}/>}<figcaption>{figure.population} · {figure.representation} · {figure.unit}</figcaption><p className="chart-caption">{figure.observed}</p><details><summary>{c.read}</summary><div dangerouslySetInnerHTML={{__html:readingHtml(figure,locale)}}/></details><a href={`#${anchor(figure.evidenceId)}`}>{c.reference}: {figure.evidenceId}</a></figure>)}</div></> : <div className="unavailable panel"><Badge status="unavailable" t={t}/><h3>{t('noGeometry')}</h3><p>{result.geometryReason}</p><p>{c.noCoordinates}</p></div>}
      </Section>
      <ContextHelp ids={['neighbor','distance','cluster','noise','preprocessing']} locale={locale}/>
      <Section id="structure-evidence" number="03" title={u.details}><details className="science-disclosure"><summary>{u.details}</summary><div className="report-evidence-sections" dangerouslySetInnerHTML={{__html:structureHtml}}/></details></Section></section>
      <section id="journey-3" className="journey-step" tabIndex={-1} aria-label={u.steps[2]}><span className="journey-label">03 · {u.steps[2]}</span>
      <Section id="warnings" number="04" title={t('warnings')} intro={t('warningIntro')}>
        <p className="source-language">{t('sourceLanguage')}</p>
        <Findings report={report} locale={locale} t={t}/>
      </Section>
      <Section id="intent" number="05" title={t('intent')} intro={t('intentIntro')}>
        <fieldset className="intent-options"><legend className="visually-hidden">{t('intent')}</legend>{intents.map(option => <label key={option} className={intent === option ? 'active' : ''}><input type="radio" name="intent" value={option} checked={intent === option} disabled={busy} onChange={() => callbacks.onIntent(option)}/><span><strong>{t(option)}</strong><small>{intentDescriptions[locale][option]}</small></span></label>)}</fieldset>
        <div className="declaration-fields"><p id="declaration-hint">{t('declarationHint')}</p>{(['population', 'prediction_unit', 'new_context'] as const).map(key => <label key={key}>{t(key === 'new_context' ? 'new_context_declaration' : key)}<input type="text" maxLength={2000} value={declarations?.[key] ?? ''} aria-describedby="declaration-hint" onChange={event => callbacks.onDeclaration?.(key, event.target.value)} readOnly={!callbacks.onDeclaration}/></label>)}</div><p className="notice">{t('intentLimit')}</p>
      </Section>
      <p className="notice">{intent==='unknown'?u.intentUnknown:u.modelAbsent}</p><ContextHelp ids={['calibration','validation','domain','environment','leakage']} locale={locale}/></section>
      <section id="journey-4" className="journey-step" tabIndex={-1} aria-label={u.steps[3]}><span className="journey-label">04 · {u.steps[3]}</span>
      <section className="panel report-synthesis" id="report-summary" tabIndex={-1}><h2>{u.begin}</h2><span className={`mode-label ${result.mode}`}>{t(result.mode)}</span><h3>{dataset.name}</h3>{report.brief.map((line,i)=><p key={i}>{line}</p>)}<p>{u.summaryIntro}</p><a href="#data">{u.back}</a><a href="#warnings">{t('warnings')}</a></section>
      <Section id="evidence" number="06" title={t('evidence')} intro={t('evidenceIntro')}>
        <div className="report-evidence-sections" dangerouslySetInnerHTML={{__html:otherHtml}}/>
        <details className="panel provenance-details"><summary>{t('provenance')}</summary><pre>{JSON.stringify(result.provenance, null, 2)}</pre></details>
        {result.limitations.length > 0 && <div className="panel limitations"><h3>{t('limitation')}</h3><ul>{result.limitations.map((limitation, i) => <li key={i}>{limitation}</li>)}</ul></div>}
      </Section>
      <Section id="export" number="07" title={t('export')} intro={t('exportIntro')}><ExportOptions view={result} locale={locale} requested={requested} busy={busy} onChange={(ids,action)=>{setChoices({owner,ids,action});setReading('complete');}} onReset={()=>{setChoices(null);setReading('complete');}}/><fieldset className="reading-choice" disabled={!!selection}><legend>{u.reading}</legend>{(['summary','complete'] as const).map(mode=><label key={mode}><input type="radio" name="reading" value={mode} checked={reading===mode} onChange={()=>setReading(mode)}/>{u[mode]}</label>)}</fieldset><p className="notice">{selection?selectionLabels.custom:reading==='summary'?u.partial:u.printHelp}</p><details className="sharing-help"><summary>{u.share}</summary><p>{u.privacy}</p></details><div className="export-panel panel"><div className="export-actions"><button className="button primary" disabled={busy} onClick={() => callbacks.onExport('html', locale,reading,selection)}>↓ {t('html')}</button><button className="button secondary" disabled={busy} onClick={() => callbacks.onExport('markdown', locale,reading,selection)}>↓ {t('markdown')}</button><button className="button secondary" disabled={busy} onClick={() => callbacks.onExport('json', locale,reading,selection)}>↓ {t('json')}</button><button className="button secondary" disabled={busy} onClick={() => callbacks.onExport('html',locale,reading,selection)}>{u.print}</button></div><span className={`mode-label ${result.mode}`}>{t(result.mode)}</span></div></Section>
      </section><aside className="glossary panel"><h3>{t('glossary')}</h3><dl>{report.glossary.map(entry=><div key={entry.term}><dt>{entry.term}</dt><dd>{entry.definition}</dd></div>)}</dl><ContextHelp ids={helpIds} locale={locale}/></aside>
    </div>
  </>;
}
