import { useEffect, useState } from 'react';
import logo from 'nirs4all-ui/assets/brands/nirs4all/horizontal.svg';
import darkLogo from 'nirs4all-ui/assets/brands/nirs4all/horizontal-dark.svg';
import { Landing } from './Landing';
import { Workspace } from './Workspace';
import { translator } from './i18n';
import type { AppProps, Locale } from './ui-types';
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
  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('domains-language', locale); localStorage.setItem('domains-theme', theme); } catch { /* Preferences are optional. */ }
  }, [locale, theme]);
  const busy = state.phase === 'loading' || state.phase === 'running';
  return <div className="app">
    <a className="skip" href="#main">{t('skip')}</a>
    <header className="nav"><div className="container nav-inner">
      <button className="brand" onClick={callbacks.onReset} aria-label={`Domains · ${t('home')}`}><img src={theme === 'dark' ? darkLogo : logo} alt="nirs4all" /><span>Domains</span></button>
      <span className="nav-tag">exploratory</span>
      <div className="nav-actions"><div className="seg" aria-label="Language / Langue">
        {(['en', 'fr'] as const).map(language => <button key={language} lang={language} aria-pressed={locale === language} onClick={() => setLocale(language)}>{language.toUpperCase()}</button>)}
      </div><button className="icon-button" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} aria-label={t('theme')}>{theme === 'dark' ? '☀' : '☾'}</button>
      <a className="github-link" href="https://github.com/dcornet/nirs4all-domains" target="_blank" rel="noreferrer">GitHub ↗</a></div>
    </div></header>
    <main id="main" tabIndex={-1}>
      {busy && <div className="run-banner container" role="status"><span className="spinner" aria-hidden="true"/><div><strong>{t('busy')}</strong><p>{state.progress}</p></div><button className="button secondary" onClick={callbacks.onCancel}>{t('cancel')}</button></div>}
      {state.error && <div className="container"><div className="alert" role="alert"><strong>{t('error')}</strong><p>{state.error.message}</p><code>{state.error.code}</code></div></div>}
      {state.phase === 'cancelled' && <p className="container notice" role="status">{t('cancelled')}</p>}
      {state.result ? <Workspace key={state.result.dataset.contentHash} result={state.result} intent={state.intent} declarations={state.declarations} callbacks={callbacks} locale={locale} t={t}/> : <Landing state={state} callbacks={callbacks} t={t} busy={busy}/>}
    </main>
    <footer className="footer container"><span>nirs4all <strong>Domains</strong></span><p>{t('footer')}</p><a href="https://github.com/dcornet/nirs4all-domains/blob/main/LICENSING.md">CeCILL 2.1 / AGPL 3.0</a></footer>
  </div>;
}
