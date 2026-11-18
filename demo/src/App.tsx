import { useEffect, useState,useRef } from 'react';
import logo from 'nirs4all-ui/assets/brands/nirs4all/horizontal.svg';
import darkLogo from 'nirs4all-ui/assets/brands/nirs4all/horizontal-dark.svg';
import { Landing } from './Landing';
import { Workspace } from './Workspace';
import {ImportResolution} from './ImportResolution';
import { translator } from './i18n';
import type { AppProps, Locale } from './ui-types';
import {TechnicalDiagnostic} from './ux/TechnicalDiagnostic';
import { Processing,ErrorFeedback } from './ux/Feedback';
import 'nirs4all-ui/assets/theme.css';
import 'nirs4all-ui/assets/qualification.css';
import './styles.css';

function preference(key: string): string | null {
  try { return localStorage.getItem(key); } catch { return null; }
}
export function App({ state, callbacks }: AppProps) {
  const [locale, setLocale] = useState<Locale>(() => preference('domains-language') === 'fr' ? 'fr' : 'en');
  const [theme, setTheme] = useState(() => {
    const saved = preference('domains-theme');
    if (saved === 'dark' || saved === 'light') return saved;
    return typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });
  const t = translator(locale);
  const lastDataset=useRef<string|null>(null);
  useEffect(()=>{
    const key=state.result?.dataset.contentHash??null;
    if(key&&key!==lastDataset.current){document.getElementById('workspace-title')?.focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});}
    lastDataset.current=key;
  },[state.result?.dataset.contentHash]);
  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('domains-language', locale); localStorage.setItem('domains-theme', theme); } catch { /* Preferences are optional. */ }
  }, [locale, theme]);
  const busy = state.phase === 'loading' || state.phase === 'running';
  const pendingImport = state.pendingImport ?? (state.importDraft ? state.importSession : undefined);
  return <div className="app">
    <a className="skip" href="#main">{t('skip')}</a>
    <header className="nav"><div className="container nav-inner">
      <button className="brand" onClick={callbacks.onReset} aria-label={`Domains · ${t('home')}`}><img src={theme === 'dark' ? darkLogo : logo} alt="nirs4all" /><span>Domains</span></button>
      <span className="nav-tag">exploratory</span>
      <div className="nav-actions"><div className="seg" role="group" aria-label="Language / Langue">
        {(['en', 'fr'] as const).map(language => <button key={language} lang={language} aria-pressed={locale === language} onClick={() => setLocale(language)}>{language.toUpperCase()}</button>)}
      </div><button className="icon-button" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} aria-label={t('theme')}>{theme === 'dark' ? '☀' : '☾'}</button>
      <a className="github-link" href="https://github.com/dcornet/nirs4all-domains" target="_blank" rel="noreferrer">GitHub ↗</a></div>
    </div></header>
    <main id="main" tabIndex={-1}>
      {busy && <Processing state={state} onCancel={callbacks.onCancel} locale={locale}/>}
      {state.error?.diagnostic?<div className="container"><h2>{t('error')}</h2><TechnicalDiagnostic diagnostic={state.error.diagnostic} locale={locale} error onRetryImport={state.canRetryImport?callbacks.onRetryImport:undefined}/></div>:state.error&&<ErrorFeedback error={state.error} locale={locale} hasResult={!!state.result}/>}
      {busy&&state.workerDiagnostic&&<div className="container"><TechnicalDiagnostic diagnostic={state.workerDiagnostic} locale={locale}/></div>}
      {state.phase === 'cancelled' && <p className="container notice" role="status">{t('cancelled')}</p>}
      {pendingImport && callbacks.onConfirmImport && <ImportResolution key={pendingImport.draft.files.map(f => f.name).join('|')} session={pendingImport} locale={locale} busy={busy} onConfirm={(config,sources) => callbacks.onConfirmImport?.(config,sources,pendingImport)} onDismiss={callbacks.onDismissImport ?? callbacks.onCancel}/>}
      {state.result ? <Workspace key={state.result.dataset.contentHash} result={state.result} intent={state.intent} declarations={state.declarations} callbacks={callbacks} locale={locale} t={t} busy={busy} importSummary={state.importSummary} importSession={state.pendingImport ? state.importSession : state.importDraft ? undefined : state.importSession}/> : !pendingImport && <Landing state={state} callbacks={callbacks} t={t} busy={busy} locale={locale}/>}
    </main>
    <footer className="footer container"><span>nirs4all <strong>Domains</strong></span><p>{t('footer')}</p><a href="https://github.com/dcornet/nirs4all-domains/blob/main/LICENSING.md">CeCILL 2.1 / AGPL 3.0</a></footer>
  </div>;
}
