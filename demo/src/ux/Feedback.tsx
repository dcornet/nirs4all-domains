import { useEffect,useRef } from 'react';
import type { Locale,UiState } from '../ui-types';
import { errorGuidance,uxCopy } from './copy';
import { translator } from '../i18n';

export function Processing({state,onCancel,locale}:{state:UiState;onCancel():void;locale:Locale}){
  const c=uxCopy(locale),t=translator(locale),stage=state.processingStage??'prepare';
  return <div className="run-banner container" role="status" aria-live="polite"><span className="spinner" aria-hidden="true"/><div className="processing-content"><strong>{c.stageTitle}</strong><p>{c.stages[stage]}</p><ol className="processing-stages" aria-label={c.stageTitle}>{Object.entries(c.stages).map(([id,label])=><li key={id} aria-current={id===stage?'step':undefined}>{label}</li>)}</ol><details><summary>{c.technical}</summary><p>{state.progress}</p><p>{c.limits}</p></details></div><button className="button secondary" onClick={onCancel}>{t('cancel')}</button></div>;
}
export function ErrorFeedback({error,locale,hasResult=false}:{error:NonNullable<UiState['error']>;locale:Locale;hasResult?:boolean}){
  const ref=useRef<HTMLDivElement>(null),c=uxCopy(locale),t=translator(locale),guidance=errorGuidance(error.code,error.message,locale);
  const originalReasonId=error.message.match(/^[A-Z][A-Z0-9_]+/)?.[0]??error.code;
  useEffect(()=>{ref.current?.focus();},[error.code,error.message]);
  return <div className="container"><div className="alert" role="alert" ref={ref} tabIndex={-1} aria-labelledby="error-title"><h2 id="error-title">{t('error')}</h2><p>{guidance.description}</p><h3>{c.action}</h3><p>{guidance.action}</p><code className="refusal-code">{originalReasonId}</code><details><summary>{c.technical}</summary><p>{c.source}</p><code>{error.code}</code><pre>{error.message}</pre></details><a href={hasResult?'#data':'#import-guide'}>{hasResult?c.back:c.importHelp}</a></div></div>;
}
