import type { Locale } from '../ui-types';
import type { T } from '../i18n';
import type { ReportPresentation } from '../report/presentation';
import { anchor,reportCopy } from '../report/presentation';
import { uxCopy } from './copy';

export function Findings({report,locale,t}:{report:ReportPresentation;locale:Locale;t:T}){
  const c=uxCopy(locale),f1=reportCopy(locale);
  return <div className="findings">{report.findings.length===0&&<p className="panel">{t('noFindings')}</p>}{report.findings.map(f=><article className={`finding panel finding-${f.status}`} key={f.id}>
    <div className="finding-header"><h3>{f.title}</h3><span className={`status status-${f.status}`}>{t(f.status)}</span></div>
    <dl className="finding-route"><div><dt>{t('observation')}</dt><dd>{f.observation}</dd></div><div><dt>{c.purpose}</dt><dd>{f.relevance}</dd></div><div><dt>{c.next}</dt><dd>{f.verification}</dd></div></dl>
    <details><summary>{t('more')}</summary><dl className="finding-details"><div><dt>{t('hypothesis')}</dt><dd>{f.hypothesis}</dd></div><div><dt>{t('limitation')}</dt><dd>{f.limitation}</dd></div></dl>
      <h4>{c.requirements}</h4>{f.prerequisites?.length?<ul>{f.prerequisites.map((v,i)=><li key={i}>{v}</li>)}</ul>:<p>{t('notCarried')}</p>}
      <p>{c.notExecuted}</p><details><summary>{c.execution}</summary><pre>{JSON.stringify(f.execution??null,null,2)}</pre></details>
      <p>{t('confidence')}: {f.confidence}</p><div className="evidence-links">{f.resolvedEvidenceIds.map(id=><a key={id} href={`#${anchor(id)}`}>{f1.reference}: {id}</a>)}{(!f.resolvedEvidenceIds.length||f.unresolvedEvidenceIds.length>0)&&<p>{f1.missingLink} {f.unresolvedEvidenceIds.join('; ')}</p>}</div><code>{f.id}</code>
    </details>
  </article>)}</div>;
}
