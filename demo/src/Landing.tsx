import { useState } from 'react';
import { DatasetDropzone } from 'nirs4all-ui/components';
import type { UiState, UiCallbacks,Locale } from './ui-types';
import type { T } from './i18n';
import { uxCopy } from './ux/copy';
import { ContextHelp } from './ux/Help';

export function DatasetFileDropzone({ callbacks, t, busy, locale, progress = '' }: { callbacks: UiCallbacks; t: T; busy: boolean; locale: Locale; progress?: string }) {
  const [dropError, setDropError] = useState<string | null>(null);
  return <DatasetDropzone className="import-card" busy={busy} error={dropError}
    title={t('drop')} hint={locale === 'fr' ? 'X seul, X/Y/M, train/test ou configuration .nirs4all.json avec ses fichiers' : 'X alone, X/Y/M, train/test, or .nirs4all.json configuration with its files'}
    folderLabel={locale === 'fr' ? 'Choisir un dossier' : 'Choose a folder'} note={t('local')}
    busyTitle={locale === 'fr' ? 'Chargement du dataset…' : 'Loading dataset…'} busyHint={progress}
    onError={error => setDropError(error instanceof Error ? error.message : String(error))}
    onFiles={files => { setDropError(null); callbacks.onImport(files.map(({name,file}) => name === file.name ? file : new File([file], name, {type:file.type,lastModified:file.lastModified}))); }}/>
}

export function Landing({ state, callbacks, t, busy,locale='en' }: { state: UiState; callbacks: UiCallbacks; t: T; busy: boolean;locale?:Locale }) {
  const c=uxCopy(locale);
  return <>
    <section className="hero"><div className="hero-grid" aria-hidden="true"/>
      <svg className="hero-spectra" viewBox="0 0 1200 350" aria-hidden="true" preserveAspectRatio="none">
        {['#0d9488', '#06b6d4', '#65a30d', '#8b5cf6', '#d97706'].map((color, i) => <path key={color} stroke={color} transform={`translate(0 ${i * 10})`} d="M0 240 C90 240 100 130 170 160 S290 260 340 175 S400 40 470 140 S560 300 650 160 S740 100 800 190 S920 220 980 90 S1100 170 1200 130"/>)}</svg>
      <div className="container hero-content"><span className="eyebrow">{t('eyebrow')}</span>
        <h1>{locale === 'fr' ? 'Charger mon dataset' : 'Load my dataset'}</h1>
        <p className="hero-intro">{locale === 'fr' ? 'Déposez vos fichiers ou un dossier. IO vérifie et assemble les données localement.' : 'Drop your files or a folder. IO validates and assembles your data locally.'}</p>
        <DatasetFileDropzone callbacks={callbacks} t={t} busy={busy} locale={locale} progress={state.progress}/>
        <details className="import-settings-before"><summary className="import-settings-link">{locale === 'fr' ? "Paramètres d’import" : 'Import settings'}</summary>
          <label><input type="checkbox" checked={state.editImportFirst ?? false} disabled={busy || !callbacks.onImportOptionsChange} onChange={event => callbacks.onImportOptionsChange?.(event.target.checked)}/>{locale === 'fr' ? 'Ouvrir les paramètres avancés après l’identification des sources par IO' : 'Open advanced settings after IO identifies the sources'}</label>
          <p>{locale === 'fr' ? 'Option facultative. Par défaut, les données non ambiguës sont chargées directement.' : 'Optional. By default, unambiguous data loads directly.'}</p>
        </details>
        <small className="illustration-label">{t('illustration')}</small>
      </div>
    </section>
    <section className="container import-guide" id="import-guide" tabIndex={-1} aria-labelledby="import-guide-title"><details><summary id="import-guide-title">{c.importHelp}</summary><h2>{c.formats}</h2><p>{c.csv}</p><p>{c.metadata}</p><p>{c.saved}</p><p>{c.retained}</p><p>{c.limits}</p><p>{c.noRepair}</p><ContextHelp ids={['metadata','physical','calibration','validation']} locale={locale}/></details></section>
    <section className="container examples"><div className="section-heading"><div><span className="eyebrow">{t('examples')}</span><h2>{t('examples')}</h2><p>{t('examplesSub')}</p></div></div>
      <div className="example-grid">{state.examples.map((example, i) => <button className="example-card" key={example.id} disabled={busy} onClick={() => callbacks.onExample(example.id)}>
        <span className="example-number">0{i + 1}</span><span className="example-body"><span className={`mode-label ${example.mode}`}>{t(example.mode)}</span><strong>{example.name}</strong><span>{example.description}</span><small>{example.dimensions} · {example.license}</small></span><span className="example-arrow" aria-hidden="true">↗</span>
      </button>)}</div>
    </section>
    <div className="container boundary"><span aria-hidden="true">↳</span><p>{t('boundary')}</p></div>
  </>;
}
