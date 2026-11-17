/** Descriptive display projection only. No provider, fitting or scientific threshold. */
import type { EvidenceStatus, Locale, PredictionIntent, UiEvidence, UiResult } from '../ui-types';
import { translator } from '../i18n';
import {factorAssociationTables} from './factor-association';
import type {FactorColorLegendDescriptor} from './factor-colors';

const copy = {
  en: {
    brief: 'In brief', structure: 'Spectral structure', data: 'Understand the data', checks: 'Checks and prerequisites',
    read: 'How to read', observed: 'What is actually observed', meaning: 'Why it may matter', limits: 'Not established',
    definition: 'What this measures', original: 'Original source text / exact object', reference: 'Evidence reference',
    missingLink: 'No admissible evidence link was supplied. The source statement is retained, without substituting another metric.',
    population: 'Population', representation: 'Representation', unit: 'Unit', parameter: 'Parameter / metric', value: 'Value',
    unknownUnit: 'Not carried / not qualified', status: 'Status', provider: 'Provider', reason: 'Availability reason',
    noValue: 'Not carried', raw: 'Raw spectra remain screen-only; no spectral curves or raw X cells are included in this export.',
    spectraRead: 'Each curve is one acquisition. Similar curves do not establish the same specimen; visible changes do not identify a physical, instrumental or chemical cause.',
    scores: 'PCA observation coordinates', one: 'One-dimensional PCA coordinates', scree: 'Recorded PCA eigenvalues',
    scoreDefinition: 'PCA projects the centered X variation onto mathematical directions. Points are acquisitions, not certified specimens.',
    scoreRead: 'Read coordinates along the labeled components. The map alone does not measure separation or assign physical groups.',
    scoreLimit: 'Full-X descriptive/transductive fit, not train-fitted external projection, predictive performance or chemical attribution.',
    oneLimit: 'PC2 is unavailable. The vertical placement is a display rail, not a second measured component.',
    screeDefinition: 'Eigenvalues describe spectral variance. Percentages, when shown, use the full covariance trace, never the sum of retained components.',
    screeRead: 'Compare the heights of the recorded eigenvalues. Only resolved components are drawn; requested and unresolved information remains in the evidence table.',
    screeLimit: 'A limited component set does not account for all variance by construction. Variance is not target relevance or guaranteed calibration ease.',
    neighbors: 'Nearest-neighbor distances', neighborDefinition: 'Recorded first admissible neighbor Euclidean-distance summary, not a distribution recomputed by the UI.',
    neighborRead: 'Raw and PCA distances concern different representations; use their recorded reference, query counts, exclusions and provider summaries.',
    neighborLimit: 'A small distance is neither specimen identity, a leakage rate nor a physical-similarity probability. No cross-representation comparison is inferred.',
    density: 'One recorded HDBSCAN partition', densityDefinition: 'One density-based exploratory partition in the resolved PCA coordinates; labels, strengths and persistence retain their original definitions.',
    densityRead: 'Cluster sizes below count the supplied labels; negative labels are noise. All-noise is a computed partition, not an execution failure.',
    densityLimit: 'A cluster is not a physical batch, chemical class, independent unit, leakage risk or recommended calibration population. One fit does not establish resampling stability.',
    allNoise: 'All carried labels are noise. This does not exclude continuous structure.',
    trivial: 'This single-fit partition has at most one cluster. This does not establish absence of structure.',
    unavailable: 'No values are drawn for this unavailable evidence. Read the exact source reason; other available observations remain usable.',
    saved: 'Saved source-scoped evidence; no browser refit. Spectra and PCA coordinates are not reconstructed.',
    live: 'Complete imported X, descriptive/transductive analysis. No target or prediction score was evaluated.',
    scopedTrain: 'Train-only structure evidence. Other loaded partitions were not used for this fit.',
    scopedGlobal: 'Explicit global descriptive/transductive structure over the selected train and test populations.',
    scopedTrainLimit: 'A descriptive train-only fit does not establish test support, physical independence, predictive performance or transfer to a new context.',
    scopedGlobalLimit: 'A global train+test fit does not establish a train-only reference, prospective test performance, physical independence or transfer to a new context.',
    scopedUnknown: 'The numerical structure scope could not be matched to an operation receipt.',
    factor: 'Documented factor correspondence', sensitivity: 'Recorded sensitivity mechanisms', readiness: 'Verification readiness', decision: 'Original decision reading',
    savedRead: 'Read the recorded metric and its exact scope. Factor-PC correspondence, partition ARI, neighborhood change and density-parameter sensitivity are distinct.',
    savedLimit: 'Categorical factors and X-derived clusters do not certify physical units or causality. Original proposal, prerequisites and actual execution remain separate.',
    overview: 'Readable overview of at most 160 scalar fields; large arrays and nested prose remain in the complete original object. No values are silently replaced by summaries.',
    observations: 'Observations', variables: 'Variables', signal: 'Signal unit/type: not carried', noCoordinates: 'Coordinates are not carried; no score map is reconstructed.',
    total: 'Full covariance trace', resolved: 'Resolved components', variance: 'Explained variance (%)', component: 'Component', eigenvalue: 'Eigenvalue',
    cluster: 'Cluster label', count: 'Observation count', noise: 'Noise', glossary: 'Glossary', units: 'Axis / units',
    next: 'Choose a prediction unit and context, then check the corresponding documented dependencies. No split is universally preferred.',
    unknownIntent: 'Intended use is unknown: within-study description, new specimens and new contexts remain separate conditional questions.',
    noExecution: 'Presentation only: no verification is authorized, scheduled or executed here.',
    tableNote: 'Values retain original status, population, representation, parameters and provenance. Exact precision is available in the original object.',
    machinePrint: 'The complete machine evidence remains in this HTML and in the JSON export. Print includes the scientific tables, parameters, provenance and limits; duplicate machine payloads are omitted from paper.',
  },
  fr: {
    brief: 'En bref', structure: 'Structure spectrale', data: 'Comprendre les données', checks: 'Vérifications et prérequis',
    read: 'Comment lire', observed: 'Ce qui est effectivement observé', meaning: 'Pourquoi cela peut compter', limits: 'Non démontré',
    definition: 'Ce que cela mesure', original: 'Texte source / objet original exact', reference: 'Référence de preuve',
    missingLink: 'Aucun lien de preuve admissible fourni. La formulation source est conservée sans lui substituer une autre métrique.',
    population: 'Population', representation: 'Représentation', unit: 'Unité', parameter: 'Paramètre / métrique', value: 'Valeur',
    unknownUnit: 'Non transportée / non qualifiée', status: 'Statut', provider: 'Fournisseur', reason: 'Raison de disponibilité',
    noValue: 'Non transporté', raw: 'Les spectres bruts restent à l’écran ; aucune courbe spectrale ni cellule X brute ne figure dans cet export.',
    spectraRead: 'Chaque courbe représente une acquisition. Des courbes similaires ne prouvent pas un même spécimen ; une variation visible ne démontre pas sa cause physique, instrumentale ou chimique.',
    scores: 'Coordonnées PCA des observations', one: 'Coordonnées PCA unidimensionnelles', scree: 'Valeurs propres PCA enregistrées',
    scoreDefinition: 'La PCA projette la variation de X centré sur des directions mathématiques. Les points sont des acquisitions, pas des spécimens certifiés.',
    scoreRead: 'Lisez les coordonnées sur les composantes indiquées. La carte seule ne mesure pas une séparation et n’attribue pas de groupes physiques.',
    scoreLimit: 'Ajustement descriptif/transductif sur tout X, pas une projection externe ajustée sur train, une performance prédictive ou une attribution chimique.',
    oneLimit: 'PC2 est indisponible. La position verticale est un rail d’affichage, pas une seconde composante mesurée.',
    screeDefinition: 'Les valeurs propres décrivent la variance spectrale. Les pourcentages éventuels utilisent la trace complète de covariance, jamais la somme des composantes retenues.',
    screeRead: 'Comparez les hauteurs des valeurs propres enregistrées. Seules les composantes résolues sont dessinées ; les informations demandées et non résolues restent dans le tableau des preuves.',
    screeLimit: 'Un ensemble limité de composantes ne représente pas toute la variance par construction. La variance n’est ni la pertinence pour Y ni une garantie de calibration facile.',
    neighbors: 'Distances aux plus proches voisins', neighborDefinition: 'Résumé enregistré des distances euclidiennes au premier voisin admissible, pas une distribution recalculée par l’interface.',
    neighborRead: 'Les distances brutes et PCA concernent des représentations différentes ; consultez références, requêtes, exclusions et résumés du fournisseur.',
    neighborLimit: 'Une faible distance n’est ni une identité de spécimen, ni un taux de fuite, ni une probabilité de similarité physique. Aucune comparaison entre représentations n’est inférée.',
    density: 'Une partition HDBSCAN enregistrée', densityDefinition: 'Une partition exploratoire de densité dans les coordonnées PCA résolues ; labels, forces d’appartenance et persistance conservent leurs définitions originales.',
    densityRead: 'Les effectifs comptent les labels fournis ; les labels négatifs sont du bruit. Une partition tout-bruit est calculée, pas un échec d’exécution.',
    densityLimit: 'Un cluster n’est ni un lot physique, ni une classe chimique, ni une unité indépendante, ni un risque de fuite, ni une population de calibration conseillée. Un ajustement ne prouve pas une stabilité par rééchantillonnage.',
    allNoise: 'Tous les labels transportés sont du bruit. Cela n’exclut pas une structure continue.',
    trivial: 'Cette partition à un seul ajustement comporte au plus un cluster. Cela ne démontre pas l’absence de structure.',
    unavailable: 'Aucune valeur artificielle n’est dessinée. Consultez la raison source exacte ; les autres observations disponibles restent utilisables.',
    saved: 'Preuves enregistrées dans leur périmètre source ; aucun réajustement dans le navigateur. Les spectres et coordonnées PCA ne sont pas reconstruits.',
    live: 'Tout X importé, analyse descriptive/transductive. Aucune cible ni performance prédictive évaluée.',
    scopedTrain: 'Structure calculée uniquement sur train. Les autres partitions chargées ne participent pas à cet ajustement.',
    scopedGlobal: 'Structure descriptive/transductive globale sur les populations train et test explicitement sélectionnées.',
    scopedTrainLimit: 'Un ajustement descriptif sur train ne prouve ni le support de test, ni l’indépendance physique, ni la performance prédictive, ni le transfert vers un nouveau contexte.',
    scopedGlobalLimit: 'Un ajustement global train + test ne valide ni une référence limitée à train, ni une performance prospective sur test, ni l’indépendance physique, ni le transfert vers un nouveau contexte.',
    scopedUnknown: 'Le périmètre de la structure ne correspond à aucune preuve d’opération.',
    factor: 'Correspondances de facteurs documentées', sensitivity: 'Mécanismes de sensibilité enregistrés', readiness: 'Prérequis des vérifications', decision: 'Lecture décisionnelle originale',
    savedRead: 'Lisez la mesure enregistrée et son périmètre exact. Correspondance facteur-PC, ARI de partition, voisinages et sensibilité aux paramètres de densité sont distincts.',
    savedLimit: 'Les facteurs catégoriels et clusters de X ne certifient ni unités physiques ni causalité. Proposition originale, prérequis et exécution effective restent séparés.',
    overview: 'Vue lisible d’au plus 160 champs simples ; les grands tableaux et textes imbriqués restent dans l’objet original complet. Aucune valeur n’est remplacée silencieusement par un résumé.',
    observations: 'Observations', variables: 'Variables', signal: 'Unité/type du signal : non transportés', noCoordinates: 'Coordonnées non transportées ; aucune carte des scores reconstruite.',
    total: 'Trace complète de covariance', resolved: 'Composantes résolues', variance: 'Variance expliquée (%)', component: 'Composante', eigenvalue: 'Valeur propre',
    cluster: 'Label du cluster', count: 'Nombre d’observations', noise: 'Bruit', glossary: 'Glossaire', units: 'Axes / unités',
    next: 'Précisez l’unité de prédiction et le contexte, puis vérifiez les dépendances documentées correspondantes. Aucune partition n’est universellement préférable.',
    unknownIntent: 'Objectif inconnu : description dans l’étude, nouveaux spécimens et nouveaux contextes restent des questions conditionnelles distinctes.',
    noExecution: 'Présentation uniquement : aucune vérification autorisée, planifiée ou exécutée ici.',
    tableNote: 'Les valeurs gardent leur statut, population, représentation, paramètres et provenance. La précision exacte reste dans l’objet original.',
    machinePrint: 'Les preuves machine complètes restent dans cet HTML et l’export JSON. L’impression conserve tableaux scientifiques, paramètres, provenance et limites ; les duplications des objets machine sont omises sur papier.',
  },
};
export type Copy = typeof copy.en;
export const reportCopy = (locale: Locale): Copy => copy[locale];
export const anchor = (id: string) => `evidence-${encodeURIComponent(id)}`;
export function metricName(key: string,locale:Locale): string {
  const names:Record<string,[string,string]>={n_reference:['Reference observations','Observations de référence'],n_query:['Query observations','Observations requêtes'],k:['Requested neighbors per query','Voisins demandés par requête'],rows_with_neighbor:['Queries with an admissible neighbor','Requêtes avec voisin admissible'],count:['Values in the original summary','Valeurs du résumé original'],min:['Minimum','Minimum'],max:['Maximum','Maximum'],mean:['Mean','Moyenne'],median:['Median','Médiane'],q1:['First quartile','Premier quartile'],q3:['Third quartile','Troisième quartile'],stddev:['Standard deviation','Écart-type'],eigenvalues:['Resolved eigenvalues','Valeurs propres résolues'],full_moments:['Full spectral moments','Moments spectraux complets'],resolution:['Numerical resolution','Résolution numérique'],n_components_requested:['Requested components','Composantes demandées'],n_components_resolved:['Resolved components','Composantes résolues'],n_clusters:['Recorded clusters','Clusters enregistrés'],noise_count:['Noise observations','Observations de bruit'],min_cluster_size:['Minimum cluster size','Effectif minimal de cluster'],min_samples:['Density min_samples setting','Paramètre de densité min_samples'],exclusion:['Excluded references','Références exclues'],approximate:['Approximate search','Recherche approximative'],backend_version:['Original provider version','Version originale du fournisseur']};
  return names[key.split('.').at(-1)!]?.[locale==='fr'?1:0]??key;
}
export function axisValue(value:number,locale:Locale): string {
  const scientific=value!==0&&(Math.abs(value)<1e-4||Math.abs(value)>=1e6);
  return new Intl.NumberFormat(locale,{maximumSignificantDigits:6,notation:scientific?'scientific':'standard'}).format(value);
}
export function formatValue(value: unknown, locale: Locale): string {
  if (value === null || value === undefined) return copy[locale].noValue;
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return copy[locale].noValue;
    if (value !== 0 && (Math.abs(value) < 1e-6 || Math.abs(value) >= 1e9)) return value.toExponential(16).replace('.', locale === 'fr' ? ',' : '.');
    return new Intl.NumberFormat(locale, { maximumSignificantDigits: 17 }).format(value);
  }
  if (typeof value === 'boolean') return locale === 'fr' ? value ? 'Oui' : 'Non' : value ? 'Yes' : 'No';
  if (Array.isArray(value)) return value.length <= 20 && value.every(v => v === null || typeof v !== 'object') ? value.map(v => formatValue(v, locale)).join(' ; ') : `${value.length} · ${copy[locale].original}`;
  return typeof value === 'object' ? copy[locale].original : String(value);
}
export interface Reading { definition: string; read: string; observed: string; relevance: string; limitations: string[]; }
export interface DisplayTable { id: string; title: string; columns: string[]; rows: unknown[][]; note: string; }
export interface DisplayFigure extends Reading {
  id: string; title: string; kind: 'scores' | 'scores1d' | 'scree'; evidenceId: string;
  xLabel: string; yLabel: string; unit: string; population: string; representation: string;
  points?: NonNullable<UiResult['pca']>['points']; eigenvalues?: number[];
  groupColors?: Record<string,string>;
  factorLegend?:FactorColorLegendDescriptor;
}
export interface EvidenceBlock extends Reading {
  id: string; title: string; status: EvidenceStatus; reason: string | null; scope: string;
  representation: string; provider: string; pointer: string | null; tables: DisplayTable[]; original: unknown;
}
export interface ReportPresentation {
  protocol_version: 'domains.report_presentation.v1'; language: Locale; mode: UiResult['mode'];
  brief: string[]; spectra: string[]; figures: DisplayFigure[]; blocks: EvidenceBlock[];
  findings: (UiResult['findings'][number] & { resolvedEvidenceIds: string[]; unresolvedEvidenceIds: string[] })[];
  glossary: { term: string; definition: string }[];
}
function scalarRows(value: unknown, prefix = '', rows: unknown[][] = [],limit=160): unknown[][] {
  if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
    for (const [key, item] of Object.entries(value)) {
      if (['scores','labels','membership','persistence','warnings','request','scientific_basis','source_report','parent_annotation'].includes(key)||(key==='reason'&&item===null)) continue;
      scalarRows(item, prefix ? `${prefix}.${key}` : key, rows,limit);
    }
  } else if (rows.length < limit) rows.push([prefix || 'value', value]);
  return rows;
}
/** Uncapped documentary projection for explicit F3.5 reading; transport arrays remain in technical evidence. */
export const recordedRows=(value:unknown)=>scalarRows(value,'',[],Infinity);
function metricTitle(id: string, c: Copy): string {
  return ({ pca: c.scores, density: c.density, raw_neighbors: `${c.neighbors} · raw`, projected_neighbors: `${c.neighbors} · PCA`,
    experimental_factor_structure: c.factor, preprocessing_dependent_organization: c.sensitivity, decision_summary: c.decision, readiness: c.readiness })[id] ?? id;
}
export function presentation(view: UiResult, locale: Locale, intent: PredictionIntent,options:{uncapped?:boolean}={}): ReportPresentation {
  const c = copy[locale], t = translator(locale);
  const rows=(value:unknown)=>scalarRows(value,'',[],options.uncapped?Infinity:160);
  const overview=options.uncapped?(locale==='fr'?'Champs enregistrés sans plafond de lignes ; tableaux de transport conservés dans les preuves originales.':'Recorded fields without a row cap; transport arrays remain in original evidence.'):c.overview;
  const blocks = view.evidence.map((e): EvidenceBlock => {
    const v = e.value as Record<string, any> | null, neighbor = e.id.endsWith('_neighbors'), density = e.id === 'density';
    const tables: DisplayTable[] = [{ id: `${e.id}-values`, title: metricTitle(e.id,c), columns: [c.parameter,c.value], rows: rows(e.value), note: overview }];
    if(e.id.startsWith('factor-association-'))tables.unshift(...factorAssociationTables(e.value,locale).map(table=>({...table,id:`${e.id}-${table.id}`})));
    if (density && e.status === 'computed' && Array.isArray(v?.labels)) {
      const counts = new Map<number,number>(); for (const label of v.labels) counts.set(label,(counts.get(label)??0)+1);
      tables.unshift({ id: 'cluster-sizes', title: c.density, columns: [c.cluster,c.count], rows: [...counts].sort((a,b)=>a[0]-b[0]).map(([label,n])=>[label<0?`${c.noise} (${label})`:label,n]), note: c.densityRead });
    }
    // Only an actually carried D6.1 object can provide these scientific tables.
    if (e.id === 'decision_summary' && v) {
      if (v.factor_questions?.length) tables.unshift({ id:'factor-correspondence',title:c.factor,columns:['factor','n_levels','n_missing','eta_squared (PC order)','partition_ari','membership_evidence'],rows:v.factor_questions.map((f:any)=>[f.factor,f.values?.n_levels??null,f.values?.n_missing??null,f.values?.eta_squared??null,f.values?.partition_ari??null,f.membership_evidence??null]),note:c.savedRead });
      if (v.mechanisms?.length) tables.unshift({ id:'sensitivity-mechanisms',title:c.sensitivity,columns:['kind','finding','cluster_counts','parameter_ari_min','noise_fractions'],rows:v.mechanisms.map((m:any)=>[m.kind,m.finding,m.values?.cluster_counts??null,m.values?.parameter_ari_min??null,m.values?.noise_fractions??null]),note:c.savedLimit });
      for(const [i,m] of (v.mechanisms??[]).entries()) tables.push({id:`mechanism-${i}`,title:`${c.sensitivity} · ${m.kind}`,columns:[c.parameter,c.value],rows:rows(m.values),note:String(m.description??c.savedRead)});
      if(v.paired_representation_counts?.length)tables.push({id:'paired-representations',title:c.sensitivity,columns:[c.parameter,c.value],rows:rows({paired_representation_counts:v.paired_representation_counts}),note:c.savedRead});
      if (v.selected_readiness_checks?.length) tables.unshift({ id:'readiness-checks',title:c.readiness,columns:['record_id','inputs','protocol','authorization','execution','applicability'],rows:v.selected_readiness_checks.map((r:any)=>[r.record_id,r.inputs,r.protocol,r.authorization,r.execution,r.applicability]),note:c.noExecution });
    }
    if(e.id==='readiness'&&v?.records?.length)tables.unshift({id:'original-readiness',title:c.readiness,columns:['record_id','observation.status','inputs','protocol','authorization','execution'],rows:v.records.map((r:any)=>[r.record_id,r.observation_evidence?.measurement?.status??null,r.inputs?.value??null,r.protocol?.value??null,r.authorization?.value??null,r.execution?.value??null]),note:c.noExecution});
    if(e.id==='d2'&&v?.interpretations?.length)tables.unshift({id:'conditional-intents',title:c.decision,columns:['intended_use','conditions','supported_claims','stronger_claims_not_established'],rows:v.interpretations.map((r:any)=>[r.intended_use,r.conditions,r.supported_claims,r.stronger_claims_not_established]),note:c.savedLimit});
    return { id:e.id,title:metricTitle(e.id,c),status:e.status,reason:e.reason,scope:e.scope,representation:e.representation??view.dataset.representation??c.noValue,
      provider:e.provider,pointer:e.pointer??null,tables,original:e.value,
      definition:neighbor?c.neighborDefinition:density?c.densityDefinition:e.id==='pca'?c.scoreDefinition:c.tableNote,
      read:neighbor?c.neighborRead:density?c.densityRead:e.id==='pca'?c.scoreRead:c.savedRead,
      observed:e.value===null?c.unavailable:density&&v?.n_clusters===0?c.allNoise:density&&v?.n_clusters===1?c.trivial:`${t(e.status)} · ${metricTitle(e.id,c)}`,
      relevance:c.next,limitations:[neighbor?c.neighborLimit:density?c.densityLimit:e.id==='pca'?c.scoreLimit:c.savedLimit] };
  });
  const figures: DisplayFigure[] = [], pca = view.pca;
  const structureScope = view.provenance.scoped_structure_scope;
  const scopedPopulation = structureScope === 'train_only' ? c.scopedTrain
    : structureScope === 'global_transductive' ? c.scopedGlobal
    : structureScope === 'unpartitioned_descriptive' ? c.live
    : structureScope === 'unknown' ? c.scopedUnknown : null;
  const metric = view.evidence.find(e=>e.id==='pca');
  if (pca?.points.length && metric?.status !== 'unavailable') {
    const one = (pca.resolvedComponents??pca.eigenvalues.length)===1;
    const percent = (i:number) => pca.totalVariance!==null && pca.totalVariance>0 && pca.eigenvalues[i]!==undefined ? ` (${axisValue(100*pca.eigenvalues[i]/pca.totalVariance,locale)} %)` : '';
    const groups=[...new Set(pca.points.flatMap(p=>p.group===undefined?[]:[p.group]))].sort();
    const palette=['#0f766e','#7c3aed','#b45309','#0369a1','#be185d','#4d7c0f'];
    const groupColors=view.factorGroupColors??(groups.length<=6?Object.fromEntries(groups.map((g,i)=>[g,palette[i]])):undefined);
    figures.push({id:'pca-scores',title:one?c.one:c.scores,kind:one?'scores1d':'scores',evidenceId:'pca',xLabel:pca.xLabel+percent(0),yLabel:one?c.oneLimit:pca.yLabel+percent(1),groupColors,
      unit:c.unknownUnit,population:`${formatValue(view.dataset.observations,locale)} · ${scopedPopulation??view.dataset.population??c.noValue}`,representation:view.dataset.representation??'raw',
      points:pca.points,factorLegend:view.factorLegend,definition:c.scoreDefinition,read:c.scoreRead,observed:`${pca.points.length} · ${c.observations}`,relevance:c.next,limitations:[...(structureScope==='train_only'?[c.scopedTrainLimit]:structureScope==='global_transductive'?[c.scopedGlobalLimit]:structureScope==='unknown'?[c.scopedUnknown]:[c.scoreLimit]),...(one?[c.oneLimit]:[])]});
    figures.push({id:'pca-scree',title:c.scree,kind:'scree',evidenceId:'pca',xLabel:c.component,yLabel:c.eigenvalue,unit:c.unknownUnit,population:figures[0].population,representation:figures[0].representation,
      eigenvalues:pca.eigenvalues,definition:c.screeDefinition,read:c.screeRead,observed:`${c.resolved}: ${pca.eigenvalues.length}; ${c.total}: ${formatValue(pca.totalVariance,locale)}`,relevance:c.next,limitations:[c.screeLimit]});
  }
  const existing = new Set(view.evidence.map(e=>e.id));
  const density=view.evidence.find(e=>e.id==='density'),d=density?.value as {n_clusters?:number;noise_count?:number}|null;
  const facts=`${formatValue(view.dataset.observations,locale)} ${c.observations}; ${formatValue(view.dataset.variables,locale)} ${c.variables}. ${pca?`${c.resolved}: ${pca.eigenvalues.length}.`:c.noCoordinates} ${density?`${c.density}: ${t(density.status)}${d?`; ${c.cluster}: ${formatValue(d.n_clusters,locale)}; ${c.noise}: ${formatValue(d.noise_count,locale)}`:''}.`:''}`;
  return { protocol_version:'domains.report_presentation.v1',language:locale,mode:view.mode,
    brief:[view.mode==='saved'?c.saved:scopedPopulation??c.live,facts,intent==='unknown'?c.unknownIntent:t(intent),c.next+' '+c.noExecution],
    spectra:[c.spectraRead,c.signal,c.raw],figures,blocks,
    findings:view.findings.map(f=>({...f,resolvedEvidenceIds:f.evidenceIds.filter(id=>existing.has(id)),unresolvedEvidenceIds:f.evidenceIds.filter(id=>!existing.has(id))})),
    glossary:[{term:'PCA',definition:t('pcaDefinition')},{term:'HDBSCAN',definition:c.densityDefinition+' '+c.densityLimit},{term:locale==='fr'?'Voisinage':'Neighborhood',definition:c.neighborDefinition+' '+c.neighborLimit},{term:locale==='fr'?'Support spectral':'Spectral support',definition:t('supportDefinition')},{term:'ARI / eta²',definition:c.savedRead+' '+c.savedLimit},{term:'D6',definition:c.noExecution}] };
}
