import { useRef, useState } from 'react';
import type { UiState, UiCallbacks } from './ui-types';
import type { T } from './i18n';

export function Landing({ state, callbacks, t, busy }: { state: UiState; callbacks: UiCallbacks; t: T; busy: boolean }) {
  const picker = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  return <>
    <section className="hero"><div className="hero-grid" aria-hidden="true"/>
      <svg className="hero-spectra" viewBox="0 0 1200 350" aria-hidden="true" preserveAspectRatio="none">
        {['#0d9488', '#06b6d4', '#65a30d', '#8b5cf6', '#d97706'].map((color, i) => <path key={color} stroke={color} transform={`translate(0 ${i * 10})`} d="M0 240 C90 240 100 130 170 160 S290 260 340 175 S400 40 470 140 S560 300 650 160 S740 100 800 190 S920 220 980 90 S1100 170 1200 130"/>)}</svg>
      <div className="container hero-content"><span className="eyebrow">{t('eyebrow')}</span>
        <h1>{t('heroA')}<br/><em>{t('heroB')}</em></h1><p className="hero-intro">{t('intro')}</p>
        <div className={`import-card ${dragging ? 'dragging' : ''}`} onDragOver={event => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); if (!busy) callbacks.onImport(Array.from(event.dataTransfer.files)); }}>
          <span className="upload-icon" aria-hidden="true">↑</span><h2>{t('analyze')}</h2>
          <button className="button primary" disabled={busy} onClick={() => picker.current?.click()}>{t('drop')}</button>
          <input className="visually-hidden" ref={picker} type="file" multiple accept=".csv,.tsv,.txt,.json,.spc,.jdx,.dx" tabIndex={-1} aria-label={t('analyze')} onChange={event => { if (event.target.files?.length) callbacks.onImport(Array.from(event.target.files)); event.target.value = ''; }}/>
          <p className="import-hint">{state.importHint}</p><p className="privacy">◈ {t('local')}</p>
        </div><small className="illustration-label">{t('illustration')}</small>
      </div>
    </section>
    <section className="container examples"><div className="section-heading"><div><span className="eyebrow">{t('examples')}</span><h2>{t('examples')}</h2><p>{t('examplesSub')}</p></div></div>
      <div className="example-grid">{state.examples.map((example, i) => <button className="example-card" key={example.id} disabled={busy} onClick={() => callbacks.onExample(example.id)}>
        <span className="example-number">0{i + 1}</span><span className="example-body"><span className={`mode-label ${example.mode}`}>{t(example.mode)}</span><strong>{example.name}</strong><span>{example.description}</span><small>{example.dimensions} · {example.license}</small></span><span className="example-arrow" aria-hidden="true">↗</span>
      </button>)}</div>
    </section>
    <section className="how"><div className="container how-grid">{(['1', '2', '3'] as const).map(number => <div className="how-step" key={number}><span>0{number}</span><h3>{t(`step${number}`)}</h3><p>{t(`step${number}d`)}</p></div>)}</div></section>
    <div className="container boundary"><span aria-hidden="true">↳</span><p>{t('boundary')}</p></div>
  </>;
}
