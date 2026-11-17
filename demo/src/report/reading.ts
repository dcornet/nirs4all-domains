/** Optional reading of the existing F1 model, not a diagnostic or report engine. */
import type { DemoReport } from './model';
import type { ReportPresentation } from './presentation';
import { reportCopy,formatValue,anchor } from './presentation';
import { escape,md,tableHtml,tableMarkdown } from './render';
import { translator } from '../i18n';
import { uxCopy } from '../ux/copy';

export function synthesis(report:DemoReport,p:ReportPresentation,format:'html'|'markdown'):string {
  const locale=report.language,u=uxCopy(locale),c=reportCopy(locale),t=translator(locale);
  const availability={id:'summary-availability',title:t('evidence'),columns:[c.parameter,c.status,c.reason],rows:p.blocks.map(b=>[b.title,t(b.status),b.reason]),note:u.partial};
  if(format==='markdown')return `## ${md(u.summary)}\n\n${md(u.partial)}\n\n${md(u.summaryIntro)}\n\n${p.brief.map(md).join('\n\n')}\n\n${md(report.dataset.name)} · ${md(t(p.mode))}\n\n${formatValue(report.dataset.observations,locale)} ${md(c.observations)} × ${formatValue(report.dataset.variables,locale)} ${md(c.variables)}\n\n${tableMarkdown(availability,locale)}\n\n${p.findings.map(f=>`### ${md(f.title)} · ${md(t(f.status))}\n\n${md(t('observation'))}: ${md(f.observation)}\n\n${md(u.purpose)}: ${md(f.relevance)}\n\n${md(u.next)}: ${md(f.verification)}\n\n${md(c.limits)}: ${md(f.limitation)}\n\n${md(c.reference)}: ${f.resolvedEvidenceIds.map(md).join(' ; ')||md(c.missingLink)}`).join('\n\n')}\n\n${report.limitations.map(l=>'- '+md(l)).join('\n')}\n\n${md(u.privacy)}\n\n`;
  return `<section id="summary-reading" class="partial-synthesis"><h2>${escape(u.summary)}</h2><p class="report-partial">${escape(u.partial)}</p><p>${escape(u.summaryIntro)}</p><p>${escape(report.dataset.name)} · ${escape(t(p.mode))}</p>${tableHtml(availability,locale)}${p.findings.map(f=>`<article class="report-finding"><h3>${escape(f.title)}</h3><p class="report-status">${escape(t(f.status))}</p><dl class="report-reading">${[[t('observation'),f.observation],[u.purpose,f.relevance],[u.next,f.verification],[c.limits,f.limitation]].map(([k,v])=>`<div><dt>${escape(k)}</dt><dd>${escape(v)}</dd></div>`).join('')}</dl><p>${escape(c.reference)}: ${f.resolvedEvidenceIds.map(id=>`<a href="#${anchor(id)}">${escape(id)}</a>`).join(' · ')||escape(c.missingLink)}</p></article>`).join('')}<h3>${escape(c.limits)}</h3><ul>${report.limitations.map(l=>`<li>${escape(l)}</li>`).join('')}</ul><p>${escape(u.privacy)}</p></section>`;
}
