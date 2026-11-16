import type { Locale } from '../ui-types';
import type { DisplayFigure, DisplayTable, Reading, ReportPresentation } from './presentation';
import { anchor, axisValue, formatValue, metricName, reportCopy } from './presentation';
import { translator } from '../i18n';

export const escape = (text: unknown) => String(text ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
export const md = (text: unknown) => String(text ?? '').replace(/[\r\n\t]+/g,' ').trim().replace(/[\u0021-\u002f\u003a-\u0040\u005b-\u0060\u007b-\u007e]/g,'\\$&');
export function tableHtml(table: DisplayTable, locale: Locale): string {
  return `<div class="report-table-wrap"><table data-columns="${table.columns.length}"><caption>${escape(table.title)}</caption><thead><tr>${table.columns.map(c=>`<th scope="col">${escape(c)}</th>`).join('')}</tr></thead><tbody>${table.rows.map(row=>`<tr>${row.map((cell,i)=>i===0?`<th scope="row">${escape(typeof cell==='string'?metricName(cell,locale):formatValue(cell,locale))}${typeof cell==='string'&&metricName(cell,locale)!==cell?`<small class="metric-id">${escape(cell)}</small>`:''}</th>`:`<td>${escape(formatValue(cell,locale))}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p class="report-note">${escape(table.note)}</p>`;
}
export function tableMarkdown(table: DisplayTable, locale: Locale): string {
  return `#### ${md(table.title)}\n\n| ${table.columns.map(md).join(' | ')} |\n| ${table.columns.map(()=> '---').join(' | ')} |\n${table.rows.map(row=>`| ${row.map(v=>md(formatValue(v,locale))).join(' | ')} |`).join('\n')}\n\n${md(table.note)}\n`;
}
export function readingHtml(reading: Reading, locale: Locale): string {
  const c=reportCopy(locale);
  return `<dl class="report-reading">${[[c.definition,reading.definition],[c.read,reading.read],[c.observed,reading.observed],[c.meaning,reading.relevance],[c.limits,reading.limitations.join(' ')]].map(([key,value])=>`<div><dt>${escape(key)}</dt><dd>${escape(value)}</dd></div>`).join('')}</dl>`;
}
export function figureSvg(figure: DisplayFigure, locale: Locale): string {
  const c=reportCopy(locale), x0=80,y0=260,width=610,height=220;
  const text=(x:number,y:number,value:unknown,attrs='')=>`<text x="${x}" y="${y}" ${attrs}>${escape(value)}</text>`;
  const line=(x1:number,y1:number,x2:number,y2:number,cls='')=>`<line class="${cls}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"/>`;
  let drawing='';
  if (figure.kind==='scree') {
    const values=figure.eigenvalues??[],max=Math.max(...values,0)||1,band=width/Math.max(values.length,1);
    for(let tick=0;tick<=4;tick++) {const y=y0-height*tick/4;drawing+=line(x0,y,x0+width,y,'grid')+text(x0-8,y+4,formatValue(max*tick/4,locale),'text-anchor="end"');}
    values.forEach((v,i)=>{const h=height*(v/max),x=x0+band*i+band*.2;drawing+=`<rect x="${x}" y="${y0-h}" width="${band*.6}" height="${h}" fill="#0f766e"><title>PC${i+1}: ${escape(v)}</title></rect>`+text(x+band*.3,y0+20,i+1,'text-anchor="middle"');});
  } else {
    const points=figure.points??[],xs=points.map(p=>p.x),ys=points.map(p=>p.y);
    const limits=(values:number[])=>[Math.min(...values),Math.max(...values)];
    const [xmin,xmax]=limits(xs),[ymin,ymax]=limits(ys);
    const position=(v:number,min:number,max:number)=>{const normalizer=Math.max(Math.abs(min),Math.abs(max),1);const a=min/normalizer,b=max/normalizer;return a===b?.5:(v/normalizer-a)/(b-a);};
    for(let tick=0;tick<=4;tick++) {
      const f=tick/4,x=x0+width*f;
      drawing+=line(x,y0,x,y0-height,'grid')+text(x,y0+20,axisValue(xmin*(1-f)+xmax*f,locale),'text-anchor="middle"');
      if(figure.kind==='scores'){const y=y0-height*f;drawing+=line(x0,y,x0+width,y,'grid')+text(x0-8,y+4,axisValue(ymin*(1-f)+ymax*f,locale),'text-anchor="end"');}
    }
    drawing+=points.map(p=>`<circle cx="${x0+width*position(p.x,xmin,xmax)}" cy="${figure.kind==='scores1d'?y0-height/2:y0-height*position(p.y,ymin,ymax)}" r="3.5" fill="${escape(p.group===undefined?'#0f766e':figure.groupColors?.[p.group]??'#0f766e')}" fill-opacity=".65"><title>${escape(p.id)}: ${escape(p.x)}${figure.kind==='scores'?`, ${escape(p.y)}`:''} ${escape(p.group??'')}</title></circle>`).join('');
  }
  const label=figure.kind==='scores1d'?c.oneLimit:figure.yLabel;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 740 350" role="img" aria-labelledby="${figure.id}-title ${figure.id}-desc"><title id="${figure.id}-title">${escape(figure.title)}</title><desc id="${figure.id}-desc">${escape(figure.definition+' '+figure.observed+' '+figure.limitations.join(' '))}</desc><style>text{font:11px system-ui;fill:#31474b}line{stroke:#55686d;stroke-width:1}.grid{stroke:#dce5e2;stroke-width:.6}</style>${drawing}${line(x0,y0,x0+width,y0)}${figure.kind==='scores1d'?'':line(x0,y0,x0,y0-height)}${text(x0+width/2,310,figure.xLabel,'text-anchor="middle"')}${figure.kind==='scores1d'?text(x0+width/2,335,label,'text-anchor="middle" font-size="10"'):text(18,150,label,'text-anchor="middle" transform="rotate(-90 18 150)"')}</svg>`;
}
export function figureHtml(figure: DisplayFigure, locale: Locale): string {
  const c=reportCopy(locale);
  const legend=Object.entries(figure.groupColors??{}).map(([group,color])=>`<span style="color:${color}">● ${escape(group)}</span>`).join(' · ');
  return `<figure id="${figure.id}" class="report-figure"><h3>${escape(figure.title)}</h3>${figureSvg(figure,locale)}<figcaption>${escape(figure.population)} · ${escape(figure.representation)} · ${escape(figure.unit)}<span class="report-legend">● ${escape(c.observations)} · ${escape(c.noExecution)} ${legend}</span></figcaption>${readingHtml(figure,locale)}<p>${escape(c.reference)}: <a href="#${anchor(figure.evidenceId)}">${escape(figure.evidenceId)}</a></p></figure>`;
}
export function blocksHtml(p: ReportPresentation, locale: Locale): string {
  const c=reportCopy(locale),t=translator(locale);
  return p.blocks.map(b=>`<article id="${anchor(b.id)}" class="report-evidence"><h3>${escape(b.title)}</h3><p class="report-status status status-${b.status}">${escape(t(b.status))} · <code>${escape(b.id)}</code></p><dl class="report-meta">${[[c.population,b.scope],[c.representation,b.representation],[c.provider,b.provider],[c.reference,b.pointer??c.noValue],[c.unit,c.unknownUnit],[c.reason,b.reason??'—']].map(([k,v])=>`<div><dt>${escape(k)}</dt><dd>${escape(v)}</dd></div>`).join('')}</dl>${readingHtml(b,locale)}${b.tables.filter(t=>t.rows.length).map(t=>tableHtml(t,locale)).join('')}<details><summary>${escape(c.original)}</summary><pre>${escape(JSON.stringify(b.original,null,2))}</pre></details></article>`).join('');
}
