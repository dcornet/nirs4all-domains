import type {SupportRun} from '../engine/support';
import type {UiResult,UiEvidence,Locale} from '../ui-types';
import type {DisplayTable,DisplayFigure} from './presentation';
const object=(v:unknown):Record<string,any>=>v!==null&&typeof v==='object'&&!Array.isArray(v)?v as Record<string,any>:{};
const validKeys=(keys:unknown,length:number):keys is string[]=>Array.isArray(keys)&&keys.length===length&&keys.every(k=>typeof k==='string'&&k.trim().length>0)&&new Set(keys).size===keys.length;
export const supportTitle=(locale:Locale)=>locale==='fr'?'Comment les observations test se situent-elles par rapport au train ?':'How do test observations sit relative to train?';
export const supportLimit=(locale:Locale)=>locale==='fr'?'Une position PCA ou un dépassement descriptif ne mesure ni performance prédictive, ni probabilité de fuite. Les folds utilisent l’indice de ligne modulo le nombre de folds ; aucune indépendance physique n’est certifiée.':'PCA position or a descriptive exceedance measures neither predictive performance nor leakage probability. Folds use row index modulo the number of folds; physical independence is not certified.';
export function appendSupport(view:UiResult,results:readonly SupportRun[]):UiResult{
  const evidence:UiEvidence[]=results.map((r,i)=>({id:`train-fitted-support-${i+1}`,method:r.protocol_version,
    status:r.status==='partial'?'conditional':r.status,reason:r.reason,value:r,scope:'Fit: declared train only; projection: declared test only',
    representation:'raw; train-fitted FlexiblePCA projection and separate statsPcaMonitor protocol',provider:r.protocol_version==='domains.browser_train_fitted_support_local_refusal.v1'?'Local documentary refusal; no provider execution receipt returned':'Methods 1.3.13 / ABI 2.20; Domains access and qualification',pointer:`/train_fitted_support/${i}`}));
  return {...view,supportResults:[...results],evidence:[...view.evidence,...evidence],limitations:[...view.limitations,...results.flatMap(r=>r.limitations)],
    findings:[...view.findings,...results.map((r,i)=>({id:`support-finding-${i+1}`,title:'Train-fitted test positioning',status:r.protocol_version==='domains.browser_train_fitted_support_local_refusal.v1'?'unavailable' as const:'observed' as const,
      observation:r.protocol_version==='domains.browser_train_fitted_support_local_refusal.v1'?`Local documentary refusal: ${r.reason}. No successful provider execution is inferred.`:`Projection: ${r.projection.status}; monitoring: ${r.monitoring.status}; limit qualification: ${r.limit_qualification.status}.`,
      hypothesis:'Positioning may motivate review of acquisition context and dependencies.',relevance:'Descriptive geometry and monitoring remain separate protocols.',
      verification:'Inspect provider receipts, declared dependencies and external experimental design before interpreting limits.',
      limitation:supportLimit('en'),confidence:r.protocol_version==='domains.browser_train_fitted_support_local_refusal.v1'?'Documentary local failure only; no owner certification or evidence hash.':'Provider-recorded observation; no calibrated probability.',evidenceIds:[evidence[i].id]}))],
    provenance:{...view.provenance,train_fitted_support_evidence_ids:evidence.map(e=>e.id)}};
}
/** Owner arrays and summaries are displayed literally. No PCA/statistics/threshold selection in the presentation. */
export function supportTables(input:unknown,locale:Locale):DisplayTable[]{
  const r=object(input),p=object(r.projection),v=object(p.value),m=object(r.monitoring),monitor=object(m.value),q=object(r.limit_qualification),fr=locale==='fr';
  const note=supportLimit(locale),tables:DisplayTable[]=[{id:'support-status',title:fr?'Protocoles et qualification':'Protocols and qualification',columns:fr?['Protocole','Statut','Raison']:['Protocol','Status','Reason'],
    rows:[['FlexiblePCA',p.status,p.reason],['statsPcaMonitor',m.status,m.reason],['Empirical limits',q.status,q.reasons]],note},
    {id:'support-components',title:fr?'Dispersion des composantes de référence':'Reference component dispersions',columns:fr?['Composante','R\u00e9sum\u00e9 Methods']:['Component','Methods summary'],
      rows:(v.component_summaries??[]).map((summary:unknown,i:number)=>[i+1,summary]),note:fr?'Résumés Methods ; la variance expliquée FlexiblePCA est indisponible.':'Methods summaries; FlexiblePCA explained variance is unavailable.'},
    {id:'support-qualification',title:fr?'Conditions des limites':'Limit conditions',columns:fr?['Champ','Valeur']:['Field','Value'],rows:Object.entries(q),note}];
  if(m.value!==null&&m.value!==undefined)tables.push({id:'support-monitoring',title:fr?'Monitoring descriptif T²/Q':'Descriptive T²/Q monitoring',columns:fr?['Champ fournisseur','Valeur']:['Owner field','Value'],rows:Object.entries(monitor).filter(([key])=>!['reference_t2','reference_q','monitored_t2','monitored_q','descriptive_fractions'].includes(key)),
    note:(q.status==='conditional_external'?(fr?'Limites conditionnelles au dossier externe déclaré.':'Limits conditional on the declared external record.'):(fr?'Seuils bruts descriptifs ; limites non qualifiées.':'Raw descriptive thresholds; limits unqualified.'))+' '+note});
  if(m.value!==null&&m.value!==undefined){
    const receipt=object(r.receipt),annotation={status:q.status,reasons:q.reasons,source:q.source};
    for(const population of ['reference','monitored']){
      const keys=receipt[population==='reference'?'fit_keys':'query_keys'],t2=monitor[population+'_t2'],residual=monitor[population+'_q'];
      const mapped=Array.isArray(t2)&&Array.isArray(residual)&&t2.length===residual.length&&validKeys(keys,t2.length);
      tables.push({id:'support-observations-'+population,title:population==='reference'?(fr?'Observations train hors fold':'Train out-of-fold observations'):(fr?'Observations test surveill\u00e9es':'Monitored test observations'),
        columns:fr?['Cl\u00e9 originale','T\u00b2','Q','Qualification des limites']:['Original key','T\u00b2','Q','Limit qualification'],
        rows:mapped?keys.map((key:string,i:number)=>[key,t2[i],residual[i],annotation]):[],
        note:(mapped?'': 'OBSERVATION_KEY_MAPPING_UNAVAILABLE. ')+note});
    }
    const fractions=object(monitor.descriptive_fractions);
    if(Object.keys(fractions).length)tables.push({id:'support-fractions',title:fr?'Fractions descriptives du fournisseur':'Owner descriptive fractions',
      columns:fr?['Mesure','Num\u00e9rateur','D\u00e9nominateur','Fraction']:['Measure','Numerator','Denominator','Fraction'],
      rows:Object.entries(fractions).map(([measure,value])=>{const fraction=object(value);return [measure,fraction.numerator,fraction.denominator,fraction.value];}),
      note:fr?'D\u00e9nominateur pond\u00e9r\u00e9 par acquisition ; pas un effectif d\u2019unit\u00e9s ind\u00e9pendantes ni une probabilit\u00e9.':'Acquisition-weighted denominator; neither a count of independent units nor a probability.'});
  }
  return tables;
}
function projectionFigures(input:unknown,id:string,locale:Locale):DisplayFigure[]{
  const r=object(input),p=object(r.projection),v=object(p.value),components=v.display_components;
  if(p.status!=='computed'||!Array.isArray(components)||!components.length)return [];
  const one=components.length===1,x=components[0],y=components[1],receipt=object(r.receipt);
  // display_components are actual zero-based score column indices, never invented PC2.
  if(['train','test'].some(population=>!Array.isArray(v[population+'_scores'])||!validKeys(receipt[population==='train'?'fit_keys':'query_keys'],v[population+'_scores'].length)))return [];
  const points=['train','test'].flatMap(population=>{
    const scores=v[population+'_scores'],keys=receipt[population==='train'?'fit_keys':'query_keys'];
    return Array.isArray(scores)?scores.map((row:number[],i:number)=>({id:keys[i],x:row[x],y:one?0:row[y],group:population})):[];
  });
  if(!points.length||points.some(p=>!Number.isFinite(p.x)||!Number.isFinite(p.y)))return [];
  return [{id:id+'-projection',title:locale==='fr'?'Projection test sur la référence train':'Test projection on train reference',kind:one?'scores1d':'scores',evidenceId:id,
    xLabel:`PC${x+1}`,yLabel:one?(locale==='fr'?'Rail d\u2019affichage':'Display rail'):`PC${y+1}`,points,groupColors:{train:'#0f766e',test:'#c2410c'},population:locale==='fr'?'Train (cercle) / test (carr\u00e9)':'Train (circle) / test (square)',representation:locale==='fr'?'FlexiblePCA ajust\u00e9e sur train uniquement':'FlexiblePCA fitted on train only',unit:locale==='fr'?'Unit\u00e9s des scores enregistr\u00e9s':'Recorded score units',
    populationMarkers:true,definition:locale==='fr'?'Scores FlexiblePCA ajust\u00e9s sur train ; le monitoring utilise un protocole Methods distinct.':'Train-fitted FlexiblePCA scores; monitoring uses a separate Methods protocol.',read:one?(locale==='fr'?'Une coordonn\u00e9e retourn\u00e9e non constante ; r\u00e9solution du rang num\u00e9rique indisponible. Le placement vertical est un rail.':'One nonconstant returned coordinate; numerical rank resolution unavailable. Vertical placement is a display rail.'):(locale==='fr'?'Lire les coordonn\u00e9es train et test enregistr\u00e9es.':'Read the recorded train and test coordinates.'),
    observed:`${v.train_scores?.length??0} train; ${v.test_scores?.length??0} test.`,relevance:locale==='fr'?'Positionnement descriptif dans le sous-espace train fixe.':'Descriptive positioning in the fixed train subspace.',limitations:[supportLimit(locale),locale==='fr'?'La variance expliqu\u00e9e est indisponible via cette API FlexiblePCA.':'Explained variance is unavailable from this FlexiblePCA API.']}];
}

/** Plots use literal owner T2/Q values; unqualified thresholds are never drawn as contours. */
export function supportFigures(input:unknown,id:string,locale:Locale):DisplayFigure[]{
 const r=object(input),m=object(r.monitoring),v=object(m.value),fr=locale==='fr';
 const figures=projectionFigures(input,id,locale),receipt=object(r.receipt);
 if(m.status!=='computed')return figures;
 for(const [field,label] of [['t2','T²'],['q','Q']]){
  if(['reference','monitored'].some(population=>!Array.isArray(v[population+'_'+field])||!validKeys(receipt[population==='reference'?'fit_keys':'query_keys'],v[population+'_'+field].length)))continue;
  const points=['reference','monitored'].flatMap(population=>{
   const values=v[population+'_'+field];
   return Array.isArray(values)?values.map((y:unknown,i:number)=>({id:receipt[population==='reference'?'fit_keys':'query_keys'][i],x:i+1,y:y as number,group:population==='reference'?'train':'test'})):[];
  });
  if(!points.length||points.some(p=>!Number.isFinite(p.y)))continue;
  figures.push({id:id+'-'+field,title:(fr?'Monitoring descriptif ':'Descriptive monitoring ')+label,kind:'scores',evidenceId:id,xLabel:fr?'Indice dans la population':'Index within population',yLabel:label,points,
   groupColors:{train:'#0f766e',test:'#c2410c'},populationMarkers:true,population:fr?'R\u00e9f\u00e9rence train hors fold (cercle) / test (carr\u00e9)':'Train out-of-fold reference (circle) / test (square)',representation:fr?'Protocole statsPcaMonitor distinct':'Separate statsPcaMonitor protocol',unit:fr?'Unit\u00e9s des statistiques du fournisseur':'Owner statistic units',
   definition:fr?'Valeurs exactes de r\u00e9f\u00e9rence hors fold et de test retourn\u00e9es par le fournisseur.':'Literal owner out-of-fold reference and monitored values.',read:fr?'Les seuils empiriques et leur qualification restent dans le tableau.':'Empirical thresholds and qualification remain in the table.',
   observed:`${points.filter(p=>p.group==='train').length} ${fr?'r\u00e9f\u00e9rence':'reference'}; ${points.filter(p=>p.group==='test').length} ${fr?'test':'monitored'}.`,relevance:fr?'Positionnement descriptif selon ce protocole de r\u00e9f\u00e9rence.':'Descriptive positioning relative to this reference protocol.',limitations:[supportLimit(locale)]});
 }
 return figures;
}
