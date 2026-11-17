import type { Locale, UiResult } from '../ui-types';
import {defaultSections,sectionAvailability,type OptionalSection} from './selection';
import {selectionCopy} from './selection-copy';
export function ExportOptions({view,locale,requested,onChange,onReset,busy=false}:{view:UiResult;locale:Locale;requested:readonly OptionalSection[]|undefined;onChange:(ids:OptionalSection[],action:'toggle'|'select_all'|'clear')=>void;onReset:()=>void;busy?:boolean}){
  const c=selectionCopy(locale),sections=sectionAvailability(view),selected=requested??defaultSections(view);
  return <fieldset className="export-options" disabled={busy} aria-describedby="export-options-help"><legend>{c.title}</legend>
    <h3>{c.mandatory}</h3><p>{c.core}</p><p id="export-options-help">{c.help}</p>
    <div className="export-option-actions"><button type="button" className="button secondary" onClick={()=>onChange(sections.filter(s=>s.available).map(s=>s.id),'select_all')}>{c.all}</button><button type="button" className="button secondary" onClick={()=>onChange([],'clear')}>{c.none}</button><button type="button" className="button secondary" onClick={onReset}>{c.reset}</button></div>
    <h3>{c.optional}</h3><div className="export-option-grid">{sections.map(s=><div key={s.id}><label><input type="checkbox" data-export-section={s.id} checked={selected.includes(s.id)} disabled={!s.available} aria-describedby={!s.available?`section-reason-${s.id}`:undefined} onChange={e=>onChange(e.target.checked?[...selected,s.id]:selected.filter(id=>id!==s.id),'toggle')}/>{c[s.id]}</label>{!s.available&&<p id={`section-reason-${s.id}`} className="section-unavailable">{c.unavailable}: <code>{s.reason}</code></p>}</div>)}</div>
    <details className="export-selection-preview"><summary>{c.preview}</summary><p>{c.mandatory}</p><ul>{sections.filter(s=>selected.includes(s.id)&&s.available).map(s=><li key={s.id}>{c[s.id]}</li>)}</ul></details>
  </fieldset>;
}
