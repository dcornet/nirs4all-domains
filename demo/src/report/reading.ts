/** Optional reading of the existing F1 model, not a diagnostic or report engine. */
import type { DemoReport } from './model';
import type { ReportPresentation } from './presentation';
import { reportCopy,formatValue,anchor,recordedRows,type DisplayTable } from './presentation';
import { escape,md,tableHtml,tableMarkdown,figureHtml,blocksHtml,readingHtml,recordedScope } from './render';
import {selectionCopy} from './selection-copy';
import type {ExportSelection} from './selection';
import { translator } from '../i18n';
import { uxCopy } from '../ux/copy';

export function synthesis(report:DemoReport,p:ReportPresentation,format:'html'|'markdown'):string {
  const locale=report.language,u=uxCopy(locale),c=reportCopy(locale),t=translator(locale);
  const availability={id:'summary-availability',title:t('evidence'),columns:[c.parameter,c.status,c.reason],rows:p.blocks.map(b=>[b.title,t(b.status),b.reason]),note:u.partial};
  if(format==='markdown')return `## ${md(u.summary)}\n\n${md(u.partial)}\n\n${md(u.summaryIntro)}\n\n${p.brief.map(md).join('\n\n')}\n\n${md(report.dataset.name)} · ${md(t(p.mode))}\n\n${formatValue(report.dataset.observations,locale)} ${md(c.observations)} × ${formatValue(report.dataset.variables,locale)} ${md(c.variables)}\n\n${tableMarkdown(availability,locale)}\n\n${p.findings.map(f=>`### ${md(f.title)} · ${md(t(f.status))}\n\n${md(t('observation'))}: ${md(f.observation)}\n\n${md(u.purpose)}: ${md(f.relevance)}\n\n${md(u.next)}: ${md(f.verification)}\n\n${md(c.limits)}: ${md(f.limitation)}\n\n${md(c.reference)}: ${f.resolvedEvidenceIds.map(md).join(' ; ')||md(c.missingLink)}`).join('\n\n')}\n\n${report.limitations.map(l=>'- '+md(l)).join('\n')}\n\n${md(u.privacy)}\n\n`;
  return `<section id="summary-reading" class="partial-synthesis"><h2>${escape(u.summary)}</h2><p class="report-partial">${escape(u.partial)}</p><p>${escape(u.summaryIntro)}</p><p>${escape(report.dataset.name)} · ${escape(t(p.mode))}</p>${tableHtml(availability,locale)}${p.findings.map(f=>`<article class="report-finding"><h3>${escape(f.title)}</h3><p class="report-status">${escape(t(f.status))}</p><dl class="report-reading">${[[t('observation'),f.observation],[u.purpose,f.relevance],[u.next,f.verification],[c.limits,f.limitation]].map(([k,v])=>`<div><dt>${escape(k)}</dt><dd>${escape(v)}</dd></div>`).join('')}</dl><p>${escape(c.reference)}: ${f.resolvedEvidenceIds.map(id=>`<a href="#${anchor(id)}">${escape(id)}</a>`).join(' · ')||escape(c.missingLink)}</p></article>`).join('')}<h3>${escape(c.limits)}</h3><ul>${report.limitations.map(l=>`<li>${escape(l)}</li>`).join('')}</ul><p>${escape(u.privacy)}</p></section>`;
}

/** A selected reading of the same F1 blocks, figures and source objects. No scientific classification. */
export function selectedReading(report:DemoReport,p:ReportPresentation,selection:ExportSelection,format:'html'|'markdown'):string{
  const locale=report.language,c=reportCopy(locale),s=selectionCopy(locale),t=translator(locale),html=format==='html';
  const prose=(value:unknown)=>typeof value==='string'?value:JSON.stringify(value??null);
  const paragraph=(value:unknown)=>html?`<p>${escape(prose(value))}</p>`:md(prose(value))+'\n\n';
  const section=(id:string,title:string,body:string)=>html?`<section id="${id}"><h2>${escape(title)}</h2>${body}</section>`:`## ${md(title)}\n\n${body}`;
  const table=(value:DisplayTable)=>html?tableHtml(value,locale,{structured:true}):tableMarkdown(value,locale,{structured:true});
  const pairTable=(id:string,title:string,rows:unknown[][])=>table({id,title,columns:[c.parameter,c.value],rows,note:c.tableNote});
  const reference=(id:string)=>html?`<p>${escape(c.reference)}: <a href="#${anchor(id)}">${escape(id)}</a></p>`:paragraph(`${c.reference}: ${id}`);
  const sourceRows=(value:unknown)=>recordedRows(value);
  const identity=report.provenance.identity as Record<string,unknown>|undefined;
  const context={...report.dataset,source_mode:report.source_mode,intended_use:report.intended_use,user_declarations:report.user_declarations,
    report_protocol:report.protocol_version,source_report_protocol:(report.scientific_report as {protocol_version?:string}|null)?.protocol_version??null,
    carried_case_count:Array.isArray((report.scientific_report as {cases?:unknown[]}|null)?.cases)?(report.scientific_report as {cases:unknown[]}).cases.length:1,
    independent_original_study_count:report.provenance.independent_original_study_count??null,
    source_reports:report.provenance.source_reports??null,original_source_ref:report.provenance.original_source_ref??null,source_identity:identity??null,
    verification_execution:report.provenance.verification_execution??null,browser_numerical_execution:report.provenance.browser_numerical_execution??null};
  let output=section('data',c.data,paragraph(report.summary)+pairTable('required-context',c.data,sourceRows(context)));
  const findings=p.findings.map(f=>{
    const execution=Array.isArray(f.execution)?f.execution.map((item:{record_id?:unknown;execution?:unknown})=>({record_id:item.record_id,execution:item.execution})):f.execution;
    const rows=[[t('observation'),f.observation],[t('hypothesis'),f.hypothesis],[c.meaning,f.relevance],[c.checks,f.verification],[locale==='fr'?'Prérequis':'Prerequisites',f.prerequisites??c.noValue],[locale==='fr'?'Exécution':'Execution',execution??c.noValue],[c.limits,f.limitation],[t('confidence'),f.confidence],[c.status,f.status]];
    return (html?`<article class="report-finding"><h3>${escape(f.title)}</h3>`:`### ${md(f.title)}\n\n`)+pairTable(f.id,f.title,rows)+f.resolvedEvidenceIds.map(reference).join('')+(f.unresolvedEvidenceIds.length?paragraph(c.missingLink+' '+f.unresolvedEvidenceIds.join('; ')):'')+(html?'</article>':'');
  }).join('');
  output+=section('findings',t('warnings'),findings||paragraph(t('noFindings')));
  output+=section('limits',c.limits,report.limitations.map(paragraph).join('')+paragraph(c.noExecution)+paragraph(c.raw));
  // Every block has a canonical anchor, exact status/reason/scope and recorded values,
  // even if its detailed annex is unchecked. No magnitude or risk rule selects it.
  output+=section('proof',t('evidence'),p.blocks.map(b=>{
    const coreTables=b.tables.filter(tab=>['original-readiness','readiness-checks'].includes(tab.id));
    const rows=sourceRows(b.original).filter(row=>!coreTables.length||!['records','selected_readiness_checks'].includes(String(row[0])));
    const body=pairTable(`${b.id}-core`,b.title,[[c.status,b.status],[c.reason,b.reason],[c.population,recordedScope(b.scope)],[c.representation,b.representation],[c.provider,b.provider],[c.reference,b.pointer],[c.definition,b.definition],[c.read,b.read],[c.observed,b.observed],[c.meaning,b.relevance],[c.limits,b.limitations],...rows])+coreTables.map(table).join('');
    return html?`<article id="${anchor(b.id)}" class="report-evidence"><h3>${escape(b.title)}</h3>${body}</article>`:`### ${md(b.title)} · ${md(b.id)}\n\n${body}`;
  }).join(''));
  const details=(ids:readonly string[],tableFilter?:(id:string)=>boolean)=>{
    const blocks=p.blocks.filter(b=>ids.includes(b.id)).map(b=>({...b,tables:tableFilter?b.tables.filter(tab=>tableFilter(tab.id)):b.tables}));
    if(html)return blocksHtml({...p,blocks},locale,{anchors:false,originals:false,uncapped:true})+blocks.map(b=>reference(b.id)).join('');
    return blocks.map(b=>`### ${md(b.title)}\n\n`+[b.definition,b.read,b.observed,...b.limitations].map(paragraph).join('')+b.tables.map(tab=>table(tab.id===`${b.id}-values`?{...tab,rows:sourceRows(b.original)}:tab)).join('')+reference(b.id)).join('');
  };
  for(const id of selection.selected_sections){
    let body='';
    if(id==='pca_scores'||id==='pca_scree'){
      const f=p.figures.find(f=>id==='pca_scree'?f.kind==='scree':f.kind!=='scree');
      if(f)body=html?figureHtml(f,locale):[f.title,f.definition,f.read,f.observed,f.population,f.representation,f.unit,f.xLabel,f.yLabel,...f.limitations].map(paragraph).join('')+pairTable(f.id,f.title,sourceRows({points:f.points,eigenvalues:f.eigenvalues}))+reference(f.evidenceId);
    }else if(id==='detailed_tables'){
      body=p.blocks.map(b=>b.tables.filter(tab=>!tab.id.endsWith('-values')).map(table).join('')+reference(b.id)).join('');
      if(report.pca?.points.length)body+=table({id:'pca-coordinate-table',title:c.scores,columns:['observation_id','PC1','PC2 (display rail if unavailable)','group'],rows:report.pca.points.map(point=>[point.id,point.x,point.y,point.group??null]),note:report.pca.resolvedComponents===1?c.oneLimit:c.scoreLimit});
      // Complete recorded fields, without the legacy display overview's 160-field cap.
      body+=details(p.blocks.map(b=>b.id),id=>id.endsWith('-values'));
    }else if(id==='methods_parameters'){
      body=p.blocks.map(b=>paragraph(b.title)+(html?readingHtml(b,locale):[b.definition,b.read,b.observed,...b.limitations].map(paragraph).join(''))+pairTable(b.id,b.title,[[c.provider,b.provider],[c.reference,b.pointer],[c.population,recordedScope(b.scope)],[c.representation,b.representation],...sourceRows(b.original).filter(row=>/param|requested|resolved|resolution|backend|scope|exclusion|min_samples|min_cluster_size|^k$|policy/i.test(String(row[0])))])+reference(b.id)).join('');
    }else if(id==='neighborhood')body=details(['raw_neighbors','projected_neighbors']);
    else if(id==='clustering'){
      body=details(['density'])+details(['decision_summary'],id=>id==='sensitivity-mechanisms');
      const v=p.blocks.find(b=>b.id==='density')?.original as {labels?:number[];membership?:number[];persistence?:number[]}|undefined;
      if(v?.labels)body+=table({id:'cluster-labels',title:c.density,columns:['observation_index','label','membership'],rows:v.labels.map((label,i)=>[i,label,v.membership?.[i]??null]),note:c.densityLimit});
      if(v?.persistence)body+=pairTable('cluster-persistence','persistence',v.persistence.map((value,i)=>[i,value]));
    }else if(id==='experimental_factors')body=details(['experimental_factor_structure'])+details(['decision_summary'],id=>id==='factor-correspondence');
    else if(id==='representation_sensitivity')body=details(['preprocessing_dependent_organization','parameter_sensitivity'])+details(['decision_summary'],id=>id==='sensitivity-mechanisms'||id.startsWith('mechanism-')||id==='paired-representations');
    else if(id==='readiness'){
      body=details(['readiness'],id=>!id.endsWith('-values'));
      const records=(p.blocks.find(b=>b.id==='readiness')?.original as {records?:unknown[]}|null)?.records??[];
      body+=records.map((r,i)=>pairTable(`readiness-record-${i}`,`${c.readiness} · ${i+1}`,sourceRows(r))).join('');
    }else if(id==='extended_provenance')body=pairTable('extended-provenance',t('provenance'),sourceRows(report.provenance));
    else if(id==='glossary')body=pairTable('full-glossary',c.glossary,p.glossary.map(g=>[g.term,g.definition]));
    // The complete payload is appended once by export.ts, never duplicated here.
    if(id!=='machine_evidence')output+=section(`supplement-${id}`,s[id],body);
  }
  const unavailable=selection.unavailable_sections.filter(s=>selection.requested_sections.includes(s.id));
  const preview=paragraph(s.core)+paragraph(s.help)+paragraph('domains.report_export_selection.v1')+
    selection.selected_sections.map(id=>paragraph(s[id])).join('')+
    unavailable.map(item=>paragraph(`${s.requestedUnavailable}: ${s[item.id]} · ${item.reason}`)).join('');
  output+=section('export-selection',s.selection,preview);
  // Required references always resolve in the core, irrespective of selected annexes.
  return output;
}
