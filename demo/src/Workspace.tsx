import { useState, type ReactNode } from 'react';
import { EigenvalueScree, ScoreMap, SpectraExplorer } from 'nirs4all-ui/qualification';
import type { EvidenceStatus, Locale, PredictionIntent, UiCallbacks, UiDeclarations, UiResult } from './ui-types';
import type { T } from './i18n';

const colors = ['#0d9488', '#7c3aed', '#d97706', '#0284c7', '#db2777', '#65a30d'];
const sections = ['data', 'spectra', 'geometry', 'warnings', 'intent', 'evidence', 'export'] as const;
const intents: PredictionIntent[] = ['unknown', 'study', 'known_acquisitions', 'new_specimens', 'new_groups', 'new_context'];
function Badge({ status, t }: { status: EvidenceStatus; t: T }) { return <span className={`status status-${status}`}>{t(status)}</span>; }
function Section({ id, number, title, intro, children }: { id: string; number: string; title: string; intro?: string; children: ReactNode }) {
  return <section className="workspace-section" id={id}><div className="section-heading"><span className="section-number">{number}</span><div><h2>{title}</h2>{intro && <p>{intro}</p>}</div></div>{children}</section>;
}
export function Workspace({ result, intent, declarations, callbacks, locale, t }: { result: UiResult; intent: PredictionIntent; declarations?: UiDeclarations; callbacks: UiCallbacks; locale: Locale; t: T }) {
  const { dataset } = result;
  const [selected, setSelected] = useState<string | null>(null);
  const [colorByGroup, setColorByGroup] = useState(false);
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(Math.max(0, dataset.axis.length - 1));
  const selectedSeries = dataset.spectra.find(series => series.id === selected);
  const series = dataset.spectra.map((s, i) => ({ id: s.id, label: s.group, values: s.values.slice(start, end + 1), color: colors[i % colors.length]! }));
  return <>
    <div className="workspace-header"><div className="container"><div className="workspace-title"><div><span className={`mode-label ${result.mode}`}>{t(result.mode)}</span><h1>{dataset.name}</h1></div><button className="button secondary" onClick={callbacks.onReset}>← {t('newData')}</button></div>
      <p className="workspace-summary">{result.summary}</p><div className="workspace-facts"><span><strong>{dataset.observations.toLocaleString(locale)}</strong> {t('samples')}</span><span><strong>{dataset.variables === null || (result.mode === 'saved' && dataset.variables === 0) ? t('notCarried') : dataset.variables.toLocaleString(locale)}</strong> {t('variables')}</span><span>{result.protocol}</span></div>
    </div></div>
    <nav className="section-nav" aria-label={t('tagline')}><div className="container">{sections.map((section, i) => <a key={section} href={`#${section}`}><span>0{i + 1}</span>{t(section)}</a>)}</div></nav>
    <div className="container workspace-content">
      <Section id="data" number="01" title={t('data')}>
        <div className="data-grid"><div className="panel"><dl className="facts"><div><dt>{t('source')}</dt><dd>{dataset.source}</dd></div><div><dt>{t('axis')}</dt><dd>{dataset.axis.length ? `${dataset.axis[0]} → ${dataset.axis[dataset.axis.length - 1]} ${dataset.axisUnit}` : '—'}</dd></div><div><dt>{t('identity')}</dt><dd>{dataset.identity}</dd></div><div><dt>{t('license')}</dt><dd>{dataset.license}</dd></div></dl></div>
        <div className="panel metadata-panel"><h3>{t('metadata')}</h3>{dataset.metadata.length ? <div className="chips">{dataset.metadata.map(column => <span key={column}>{column}</span>)}</div> : <p>{t('unknownMetadata')}</p>}<details><summary>{t('provenance')}</summary><p>{dataset.provenance}</p><dl><dt>Dataset ID</dt><dd><code>{dataset.id}</code></dd><dt>SHA-256</dt><dd><code className="hash">{dataset.contentHash}</code></dd></dl></details></div></div>
      </Section>
      <Section id="spectra" number="02" title={t('spectra')} intro={t('spectralIntro')}>
        <div className="panel chart-panel"><div className="chart-toolbar"><label>{t('select')}<select value={selected ?? ''} onChange={event => setSelected(event.target.value || null)}><option value="">{t('all')}</option>{dataset.spectra.map(s => <option key={s.id} value={s.id}>{s.id}{s.group ? ` · ${s.group}` : ''}</option>)}</select></label>
          <div className="range-fields"><span>{t('zoom')}</span><label className="visually-hidden" htmlFor="axis-from">{t('from')}</label><input id="axis-from" type="number" min={0} max={Math.max(0, end - 1)} value={start} onChange={event => setStart(Math.max(0, Math.min(end - 1, Number(event.target.value))))}/><span>—</span><label className="visually-hidden" htmlFor="axis-to">{t('to')}</label><input id="axis-to" type="number" min={start + 1} max={dataset.axis.length - 1} value={end} onChange={event => setEnd(Math.max(start + 1, Math.min(dataset.axis.length - 1, Number(event.target.value))))}/><button className="text-button" onClick={() => { setStart(0); setEnd(dataset.axis.length - 1); }}>{t('resetZoom')}</button></div></div>
          <SpectraExplorer axis={dataset.axis.slice(start, end + 1)} series={series} axisUnit={dataset.axisUnit} title={t('spectra')} selected={selected ? [selected] : []} onSelect={setSelected} locale={locale}/>
          <p className="chart-caption">{t('displayOnly')}</p>{selectedSeries && <p className="selection" role="status">{t('selected')}: <strong>{selectedSeries.id}</strong>{selectedSeries.group ? ` · ${selectedSeries.group}` : ''}</p>}
        </div>
      </Section>
      <Section id="geometry" number="03" title={t('geometry')} intro={t('geometryIntro')}>
        {result.pca ? <><div className="chart-toolbar"><label className="check"><input type="checkbox" checked={colorByGroup} onChange={event => setColorByGroup(event.target.checked)}/>{t('group')}</label></div><div className="geometry-grid"><div className="panel chart-panel"><h3>{t('scores')}</h3><ScoreMap title={t('scores')} points={result.pca.points} xLabel={result.pca.xLabel} yLabel={result.pca.yLabel} colorBy={colorByGroup ? 'group' : 'none'} locale={locale}/></div><div className="panel chart-panel"><h3>{t('scree')}</h3><EigenvalueScree title={t('scree')} eigenvalues={result.pca.eigenvalues} totalVariance={result.pca.totalVariance} locale={locale}/></div></div></> : <div className="unavailable panel"><Badge status="unavailable" t={t}/><h3>{t('noGeometry')}</h3><p>{result.geometryReason}</p></div>}
      </Section>
      <Section id="warnings" number="04" title={t('warnings')} intro={t('warningIntro')}>
        <p className="source-language">{t('sourceLanguage')}</p>
        <div className="findings">{result.findings.length === 0 && <p className="panel">{t('noFindings')}</p>}{result.findings.map(finding => <article className={`finding panel finding-${finding.status}`} key={finding.id}><div className="finding-header"><h3>{finding.title}</h3><Badge status={finding.status} t={t}/></div><span className="field-label">{t('observation')}</span><p>{finding.observation}</p><details><summary>{t('more')}</summary><dl className="finding-details">{(['hypothesis', 'relevance', 'verification', 'limitation'] as const).map(field => <div key={field}><dt>{t(field)}</dt><dd>{finding[field]}</dd></div>)}</dl><details><summary>{t('technical')}</summary><p>{t('confidence')}: {finding.confidence}</p><div className="evidence-links">{finding.evidenceIds.map(id => <a key={id} href={`#evidence-${id}`}>{id} ↗</a>)}</div><code>{finding.id}</code></details></details></article>)}</div>
      </Section>
      <Section id="intent" number="05" title={t('intent')} intro={t('intentIntro')}>
        <fieldset className="intent-options"><legend className="visually-hidden">{t('intent')}</legend>{intents.map(option => <label key={option} className={intent === option ? 'active' : ''}><input type="radio" name="intent" value={option} checked={intent === option} onChange={() => callbacks.onIntent(option)}/><span>{t(option)}</span></label>)}</fieldset>
        <div className="declaration-fields"><p id="declaration-hint">{t('declarationHint')}</p>{(['population', 'prediction_unit', 'new_context'] as const).map(key => <label key={key}>{t(key === 'new_context' ? 'new_context_declaration' : key)}<input type="text" maxLength={2000} value={declarations?.[key] ?? ''} aria-describedby="declaration-hint" onChange={event => callbacks.onDeclaration?.(key, event.target.value)} readOnly={!callbacks.onDeclaration}/></label>)}</div><p className="notice">{t('intentLimit')}</p>
      </Section>
      <Section id="evidence" number="06" title={t('evidence')} intro={t('evidenceIntro')}>
        <div className="table-wrap"><table><caption className="visually-hidden">{t('evidence')}</caption><thead><tr><th>{t('method')}</th><th>{t('status')}</th><th>{t('scope')}</th><th>{t('value')}</th></tr></thead><tbody>{result.evidence.map(evidence => <tr id={`evidence-${evidence.id}`} key={evidence.id}><th scope="row"><strong>{evidence.method}</strong><small>{evidence.id}</small><small>{t('provider')}: {evidence.provider}</small></th><td><Badge status={evidence.status} t={t}/>{evidence.reason && <p className="evidence-reason">{evidence.reason}</p>}</td><td>{evidence.scope}</td><td><details><summary>{t('technical')}</summary><pre>{JSON.stringify(evidence.value, null, 2)}</pre></details></td></tr>)}</tbody></table></div>
        <details className="panel provenance-details"><summary>{t('provenance')}</summary><pre>{JSON.stringify(result.provenance, null, 2)}</pre></details>
        {result.limitations.length > 0 && <div className="panel limitations"><h3>{t('limitation')}</h3><ul>{result.limitations.map((limitation, i) => <li key={i}>{limitation}</li>)}</ul></div>}
      </Section>
      <Section id="export" number="07" title={t('export')} intro={t('exportIntro')}><div className="export-panel panel"><div className="export-actions"><button className="button primary" onClick={() => callbacks.onExport('html', locale)}>↓ {t('html')}</button><button className="button secondary" onClick={() => callbacks.onExport('markdown', locale)}>↓ {t('markdown')}</button><button className="button secondary" onClick={() => callbacks.onExport('json', locale)}>↓ {t('json')}</button><button className="button secondary" onClick={() => window.print()}>{t('print')}</button></div><span className={`mode-label ${result.mode}`}>{t(result.mode)}</span></div></Section>
      <aside className="glossary panel"><h3>{t('glossary')}</h3><p>{t('pcaDefinition')}</p><p>{t('leakageDefinition')}</p><p>{t('supportDefinition')}</p></aside>
    </div>
  </>;
}
