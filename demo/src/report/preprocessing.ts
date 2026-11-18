/** Documentary display of owner results only: no preprocessing, scores, statistics or ranking. */
import type {SensitivityHistory} from '../engine/preprocessing';
import type {UiResult,UiEvidence,Locale} from '../ui-types';
import type {DisplayTable,DisplayFigure} from './presentation';
import {factorAssociationTables} from './factor-association';
import {supportTables,supportFigures} from './support';
const object=(v:unknown):Record<string,any>=>v!==null&&typeof v==='object'&&!Array.isArray(v)?v as Record<string,any>:{};
export const sensitivityTitle=(locale:Locale)=>locale==='fr'?'Quels constats changent avec la repr\u00e9sentation spectrale ?':'Which observations change with spectral representation?';
export const sensitivityLimit=(locale:Locale)=>locale==='fr'?'La persistance d\u2019un constat d\u00e9pend du panel, de la population et du diagnostic. Elle ne prouve ni pertinence chimique, ni ind\u00e9pendance, ni utilit\u00e9 pr\u00e9dictive. Une disparition ne d\u00e9montre pas du bruit. Aucune repr\u00e9sentation n\u2019est recommand\u00e9e ou class\u00e9e.':'Persistence is conditional on the panel, population and diagnostic. It establishes neither chemical relevance, independence nor predictive utility. Disappearance does not establish noise. No representation is recommended or ranked.';
/** Uncapped traversal of transported documentary values; original paths retain their exact identity. */
function literalRows(value:unknown,path='',rows:unknown[][]=[]):unknown[][]{
 if(value!==null&&typeof value==='object'){
  const entries=Object.entries(value);if(!entries.length)rows.push([path,Array.isArray(value)?[]:{}]);
  for(const [key,item] of entries)literalRows(item,path?`${path}.${key}`:key,rows);
 }else rows.push([path,value??null]);
 return rows;
}
export function appendSensitivity(view:UiResult,results:readonly SensitivityHistory[]):UiResult{
 const evidence:UiEvidence[]=results.map((r,i)=>({id:`preprocessing-sensitivity-${i+1}`,method:r.protocol_version,status:r.status,reason:r.reason,value:r,
  scope:'Declared reference only; test audit only after an explicit frozen-plan action',representation:'Named derived sources; no common PCA basis is asserted',
  provider:r.protocol_version==='domains.browser_preprocessing_sensitivity_local_refusal.v1'?'Local documentary refusal; no provider execution inferred':'Domains F4.3; Methods 1.3.13 / ABI 2.20',pointer:`/preprocessing_sensitivity/${i}`}));
 return {...view,sensitivityResults:[...results],evidence:[...view.evidence,...evidence],findings:[...view.findings,...results.map((r,i)=>({
  id:`sensitivity-finding-${i+1}`,title:'Preprocessing sensitivity: conditional comparison',status:r.status==='computed'?'observed' as const:'unavailable' as const,
  observation:r.protocol_version==='domains.browser_preprocessing_sensitivity_result.v1'?`Stage: ${r.stage}. Requested representations: ${r.representations.map(entry=>`${entry.id}: ${entry.status}${entry.reason?' ('+entry.reason+')':''}`).join('; ')}.`:`Local documentary refusal: ${r.reason}. No provider execution is inferred.`,
  hypothesis:'Differences can motivate checks of acquisition, instrument and preparation context; no cause is assigned.',
  relevance:'Read PCA geometry, raw/PCA neighbor retention, density partition comparisons, factor associations and optional test support separately.',
  verification:'Inspect every representation, unavailable result, comparison denominator and source/fit lineage. Record any revised plan as exploratory.',
  limitation:sensitivityLimit('en'),confidence:r.status==='computed'?'Recorded provider outputs; no calibrated probability or causal attribution.':'Documentary local refusal; no provider certification.',evidenceIds:[evidence[i].id]}))],
  limitations:[...view.limitations,...results.flatMap(r=>r.limitations),...(results.length?[sensitivityLimit('en')]:[])],
  provenance:{...view.provenance,preprocessing_sensitivity_evidence_ids:evidence.map(e=>e.id)}};
}
export function sensitivityTables(input:unknown,locale:Locale):DisplayTable[]{
 const r=object(input),fr=locale==='fr',representations=Array.isArray(r.representations)?r.representations:[],note=sensitivityLimit(locale);
 const table=(id:string,title:string,value:unknown):DisplayTable=>({id,title,columns:fr?['Champ source','Valeur']:['Source field','Value'],rows:literalRows(value),note});
 const tables:DisplayTable[]=[{id:'sensitivity-panel',title:fr?'Panel et disponibilit\u00e9':'Panel and availability',columns:fr?['Repr\u00e9sentation','Famille','Statut','Raison']:['Representation','Family','Status','Reason'],rows:representations.map((entry:any)=>[entry.id,entry.family,entry.status,entry.reason]),note},
 table('sensitivity-findings',fr?'Constats et limites transport\u00e9s':'Transported findings and limitations',{findings:r.findings,limitations:r.limitations}),table('sensitivity-plan',fr?'Plan fix\u00e9 avant ex\u00e9cution':'Plan fixed before execution',r.plan),table('sensitivity-receipt',fr?'Provenance et acc\u00e8s':'Provenance and access',r.receipt)];
 for(const entry of representations){
  const e=object(entry),v=object(e.value),prefix=String(e.id);
  tables.push(table(prefix+'-source',prefix+' / '+(fr?'source d\u00e9riv\u00e9e et transformations':'derived source and transformations'),{status:e.status,reason:e.reason,steps:e.steps,source:v.source,axis:v.axis,axis_unit:v.axis_unit,original_axis_sha256:v.original_axis_sha256,reference_matrix_sha256:v.reference_matrix_sha256,query_matrix_sha256:v.query_matrix_sha256,transformations:v.transformations}));
  tables.push(table(prefix+'-comparisons',prefix+' / '+(fr?'comparaisons document\u00e9es':'recorded comparisons'),v.comparisons));
  tables.push(table(prefix+'-structure',prefix+' / '+(fr?'structure enregistr\u00e9e':'recorded structure'),v.structure));
  for(const [i,factor] of (Array.isArray(v.factors)?v.factors:[]).entries()){
   tables.push(...factorAssociationTables(factor,locale).map(t=>({...t,id:`${prefix}-factor-${i}-${t.id}`,title:prefix+' / '+t.title})));
   tables.push(table(`${prefix}-factor-${i}-original`,prefix+' / '+(fr?'facteur original':'original factor'),factor));
  }
  const support=object(v.support);if(support.value!==null&&support.value!==undefined)tables.push(...supportTables(support.value,locale).map(t=>({...t,id:prefix+'-'+t.id,title:prefix+' / '+t.title})));
  else tables.push(table(prefix+'-support',prefix+' / '+(fr?'support train/test':'train/test support'),support));
 }
 return tables;
}
export function sensitivityFigures(input:unknown,id:string,locale:Locale):DisplayFigure[]{
 const r=object(input),keys=object(r.receipt).reference_keys,fr=locale==='fr',figures:DisplayFigure[]=[];
 for(const entry of (Array.isArray(r.representations)?r.representations:[])){
  const e=object(entry),v=object(e.value),structure=object(v.structure),report=object(object(structure.value).report),pca=object(object(report.metrics).pca),p=object(pca.value),prefix=id+'-'+String(e.id);
  const scores=p.scores;
  if(e.status==='computed'&&pca.status==='computed'&&Array.isArray(scores)&&scores.length&&Array.isArray(keys)&&keys.length===scores.length&&keys.every(k=>typeof k==='string'&&k.length>0)&&new Set(keys).size===keys.length&&Array.isArray(p.eigenvalues)&&p.eigenvalues.length){
   const one=p.eigenvalues.length===1,points=scores.map((row:number[],i:number)=>({id:keys[i],x:row[0],y:one?0:row[1]}));
   if(points.every(point=>Number.isFinite(point.x)&&Number.isFinite(point.y))){
    const shared={evidenceId:id,population:String(r.population??'unknown')+' / '+keys.length,representation:String(e.id)+' / '+String(object(v.source).source_id??'unknown'),unit:fr?'Unit\u00e9s enregistr\u00e9es':'Recorded units',definition:fr?'PCA propre \u00e0 cette source d\u00e9riv\u00e9e et sa population de r\u00e9f\u00e9rence.':'PCA specific to this derived source and reference population.',read:fr?'Les bases PCA diff\u00e8rent ; aucune comparaison coordonn\u00e9e par coordonn\u00e9e.':'PCA bases differ; no coordinate-by-coordinate comparison.',observed:`${keys.length} / ${e.id}`,relevance:fr?'Description conditionnelle \u00e0 la repr\u00e9sentation.':'Representation-conditional description.',limitations:[sensitivityLimit(locale),...(one?[fr?'Rail vertical d\u2019affichage ; PC2 indisponible.':'Vertical display rail; PC2 unavailable.']:[])]};
    figures.push({...shared,id:prefix+'-scores',title:String(e.id)+' / PCA',kind:one?'scores1d':'scores',points,xLabel:'PC1',yLabel:one?(fr?'Rail d\u2019affichage':'Display rail'):'PC2'});
    figures.push({...shared,id:prefix+'-scree',title:String(e.id)+' / '+(fr?'valeurs propres':'eigenvalues'),kind:'scree',eigenvalues:p.eigenvalues,xLabel:fr?'Composante':'Component',yLabel:fr?'Valeur propre':'Eigenvalue'});
   }
  }
  const support=object(v.support);if(support.value!==null&&support.value!==undefined)figures.push(...supportFigures(support.value,prefix+'-support',locale).map(f=>({...f,evidenceId:id,title:String(e.id)+' / '+f.title,representation:String(e.id)+' / '+f.representation})));
 }
 return figures;
}
