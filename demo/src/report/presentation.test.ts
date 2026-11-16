import { describe,expect,it } from 'vitest';
import { liveView,reportModel,savedView } from './model';
import { presentation,formatValue,anchor } from './presentation';
import { serializeReport } from './export';
import { validateSaved } from './saved';
import type { BrowserReport,LocalDataset } from '../engine/types';
import type { PredictionIntent } from '../ui-types';
import source from '../../public/examples/tablet.unknown.saved.json';
import known from '../../public/examples/tablet.study.saved.json';
import groups from '../../public/examples/tablet.new_groups.saved.json';

// Deliberately artificial presentation contracts; actual engine execution is
// separately exercised by bindings/wasm and the existing real-browser harness.
const slot=(value:unknown)=>({status:'computed',reason:null,value});
const missing=(reason:string)=>({status:'unavailable' as const,reason,value:null});
function fixture() {
  const report={schema_version:1,protocol_version:'domains.browser_x.v1',engine_version:'synthetic-display-fixture',status:'computed',
    scope:{population:'four synthetic acquisitions'},input_sha256:'synthetic',evidence_sha256:'synthetic-evidence',
    metrics:{pca:slot({scores:[[-2,-1],[-1,1],[1,-1],[2,1]],eigenvalues:[8,2],full_moments:[20,68],resolution:1e-12,unresolved:[false,false],n_components_requested:2,n_components_resolved:2,backend_version:'synthetic-display',scope:'full imported X'}),
      density:slot({labels:[0,0,1,-1],membership:[1,.8,.7,0],n_clusters:2,noise_count:1,persistence:[.6,.4],persistence_summary:slot({mean:.5}),min_cluster_size:8,min_samples:4,backend_version:'synthetic-display',qualification:'one artificial fit',support_unit:'acquisition'}),
      raw_neighbors:slot({n_reference:4,n_query:4,k:3,rows_with_neighbor:4,first_neighbor_distance_summary:slot({min:0,max:1,mean:.5}),exclusion:'equal declared group, otherwise observation self'}),
      projected_neighbors:slot({n_reference:4,n_query:4,k:3,rows_with_neighbor:4,first_neighbor_distance_summary:slot({min:0,max:2,mean:1}),exclusion:'equal declared group, otherwise observation self'}),
      metadata_factor_association:missing('METADATA_NOT_CARRIED'),resampling_stability:missing('NOT_QUALIFIED'),parameter_sensitivity:missing('NOT_QUALIFIED'),predictive_performance:missing('NO_TARGET')},
    capabilities:[],findings:[],interpretation:{protocol_version:'domains.browser_reading.v1',prediction_intent:'unknown',declaration_only:true,conditional_scenarios:[],boundaries:{physical_independence_verified:false,predictive_performance_established:false,universally_preferred_split:null,authorization_granted:false,new_execution:false},evidence_sha256:'synthetic-evidence',scope:{},observation:'A contextual declaration',confidence:'synthetic',consequence:'No predictive experiment',action:'Clarify units',readiness:missing('NOT_QUALIFIED'),execution:'not_executed',qualification:'Not independent transfer'},test_target_accessed:false,raw_spectra_included:false,limitations:['Physical identity unknown. No predictive score.'] } as BrowserReport;
  const data:LocalDataset={input:{schema_version:1,dataset_id:'synthetic-report-fixture',source_id:'synthetic',content_sha256:'synthetic',observation_ids:['a','b','c','d'],axis:[1000,1010],axis_unit:'nm',spectra:[[913.123456,712.987654],[4,5],[6,7],[8,9]],group_ids:['g1','g1','g2','g3']},metadata:[],partitions:[],headers:[],warnings:[],importSpec:null,identityOrigin:'acquisition only',license:'synthetic',mode:'synthetic_computed_live'};
  return {report,data};
}

describe('F1 live scientific presentation',()=>{
  it('uses the full trace for variance percentages and preserves all point coordinates',()=>{
    const {report,data}=fixture(),view=liveView(report,data),before=JSON.stringify(report),p=presentation(view,'en','unknown');
    expect(p.figures[0].points?.map(({x,y})=>[x,y])).toEqual(report.metrics.pca.value!.scores);
    expect(p.figures[0].xLabel).toContain('40 %');expect(p.figures[0].xLabel).not.toContain('80 %');
    expect(p.figures[1].eigenvalues).toEqual([8,2]);expect(p.figures[1].observed).toContain('20');
    expect(p.brief.join(' ')).toContain('conditional');expect(JSON.stringify(report)).toBe(before);
  });
  it('uses a display rail for one component without a PC2 axis or fabricated variance',()=>{
    const {report,data}=fixture();Object.assign(report.metrics.pca.value!,{scores:[[-2],[-1],[1],[2]],eigenvalues:[8],n_components_resolved:1});
    const model=reportModel(liveView(report,data),report,'study','en'),html=serializeReport(model,'html');
    expect(model.presentation!.figures[0].kind).toBe('scores1d');expect(html).toContain('PC2 is unavailable');
    expect(html).toContain('display rail');expect(model.scientific_report).toBe(report);
  });
  it('does not draw points for unavailable PCA and retains other measured distances',()=>{
    const {report,data}=fixture();report.metrics.pca=missing('ZERO_VARIANCE');
    const p=presentation(liveView(report,data),'fr','study');expect(p.figures).toEqual([]);
    expect(p.blocks.find(b=>b.id==='pca')?.reason).toBe('ZERO_VARIANCE');
    expect(p.blocks.find(b=>b.id==='raw_neighbors')?.status).toBe('computed');
  });
  it('distinguishes raw/PCA first-neighbor summaries, reference counts and group exclusions',()=>{
    const {report,data}=fixture(),p=presentation(liveView(report,data),'en','new_specimens');
    for(const id of ['raw_neighbors','projected_neighbors']) {
      const b=p.blocks.find(b=>b.id===id)!;expect(b.read).toContain('different representations');
      expect(b.tables[0].rows).toContainEqual(['n_reference',4]);
      expect(b.tables[0].rows).toContainEqual(['exclusion','equal declared group, otherwise observation self']);
      expect(b.limitations.join(' ')).toContain('neither specimen identity');
    }
    expect(p.blocks.find(b=>b.id==='raw_neighbors')?.representation).toBe('raw');
    expect(p.blocks.find(b=>b.id==='projected_neighbors')?.representation).toBe('resolved PCA scores');
  });
  it.each([[[-1,-1,-1,-1],0,4,'All carried labels'],[[0,0,0,0],1,0,'at most one cluster'],[[0,0,1,-1],2,1,'Computed']])('keeps computed density state for %j', (labels,clusters,noise,prose)=>{
    const {report,data}=fixture();Object.assign(report.metrics.density.value!,{labels,n_clusters:clusters,noise_count:noise});
    const b=presentation(liveView(report,data),'en','unknown').blocks.find(b=>b.id==='density')!;
    expect(b.status).toBe('computed');expect(b.observed).toContain(prose);
    expect(b.tables[0].rows.reduce((n,row)=>n+Number(row[1]),0)).toBe(4);
    expect(b.limitations.join(' ')).toContain('One fit does not establish resampling stability');
  });
  it('keeps physical identities, signal units and an unexecuted prediction unknown',()=>{
    const {report,data}=fixture(),view=liveView(report,data),p=presentation(view,'en','unknown');
    expect(view.provenance.physical_independence).toBe('unknown');expect(p.spectra.join(' ')).toContain('not carried');
    expect(p.brief.join(' ')).toContain('No target or prediction score');
    expect(p.brief.join(' ')).toContain('within-study description, new specimens and new contexts');
  });
});

describe('F1 saved evidence and scientific boundaries',()=>{
  it.each([[known,'study'],[groups,'new_groups'],[source,'unknown']] as const)('retains exact saved source for %s', (saved,intent)=>{
    validateSaved(saved);const before=JSON.stringify(saved),view=savedView(saved),model=reportModel(view,saved,intent,'en');
    expect(model.scientific_report).toBe(saved);expect(JSON.stringify(saved)).toBe(before);
    expect(model.presentation!.figures).toEqual([]);expect(model.presentation!.mode).toBe('saved');
    expect(view.dataset.spectra).toEqual([]);expect(view.dataset.metadata).toEqual([]);
    expect(model.provenance.browser_numerical_execution).toBe(false);
  });
  it('displays factor eta-squared separately from cluster ARI with uncertified memberships',()=>{
    const p=presentation(savedView(source),'en','unknown');
    const table=p.blocks.find(b=>b.id==='decision_summary')!.tables.find(t=>t.id==='factor-correspondence')!;
    expect(table.rows[0]).toEqual(['batch',31,0,source.cases[0].decision_summary.factor_questions[0].values.eta_squared,0.038110815186653484,false]);
    expect(table.note).toContain('distinct');
  });
  it('does not relabel tablet density settings as a measured preprocessing effect',()=>{
    const p=presentation(savedView(source),'en','study');
    const table=p.blocks.find(b=>b.id==='decision_summary')!.tables.find(t=>t.id==='sensitivity-mechanisms')!;
    expect(table.rows[0].slice(0,4)).toEqual(['density_parameter','observed',[5,4],0.986250843778543]);
    expect(p.findings.find(f=>f.id==='preprocessing_dependent_organization')!.observation).toBe(source.cases[0].companions.d1.value.warnings[2].observation.value!.description);
  });
  it('keeps original missing D3, partial readiness and unexecuted/unauthorized checks',()=>{
    const p=presentation(savedView(source),'fr','unknown'),d3=p.blocks.find(b=>b.id==='d3')!;
    expect(d3.status).toBe('unavailable');expect(d3.original).toBeNull();
    const table=p.blocks.find(b=>b.id==='decision_summary')!.tables.find(t=>t.id==='readiness-checks')!;
    expect(table.rows[0]).toContain('requires_data');expect(table.rows[0]).toContain('not_qualified');
    expect(table.rows[0]).toContain('not_authorized');expect(table.rows[0]).toContain('not_executed');
  });
  it('does not activate contradicted or unavailable findings or invent a missing reference',()=>{
    const view=savedView(source);view.findings[0].status='contradicted';view.findings[1].status='unavailable';
    view.findings[0].evidenceIds=['missing-evidence'];const p=presentation(view,'en','unknown');
    expect(p.findings[0].status).toBe('contradicted');expect(p.findings[1].status).toBe('unavailable');
    expect(p.findings[0].resolvedEvidenceIds).toEqual([]);expect(p.findings[0].unresolvedEvidenceIds).toEqual(['missing-evidence']);
    const html=serializeReport(reportModel(view,source,'unknown','en'),'html');
    expect(html).not.toContain('href="#evidence-missing-evidence"');expect(html).toContain('No admissible evidence link');
  });
  it('rejects an explicitly stale source binding without claiming source authentication',()=>{
    const stale=structuredClone(source);stale.cases[0].source_reports.reference.sha256='0'.repeat(64);
    expect(()=>validateSaved(stale)).toThrow('STALE_SAVED_SOURCE_BINDING');
  });
  it('keeps recorded representation measures distinct from density parameters',()=>{
    const view=savedView(source),slot=view.evidence.find(e=>e.id==='decision_summary')!;
    slot.value={mechanisms:[{kind:'representation',finding:'contradicted',description:'Synthetic matched representation contract; no favorable outcome selected.',values:{partition_ari:0,full_x_neighbor_overlap:1,projected_neighbor_overlap:.5}}]};
    const block=presentation(view,'en','study').blocks.find(b=>b.id==='decision_summary')!;
    expect(block.tables.find(t=>t.id==='mechanism-0')!.rows).toEqual([['partition_ari',0],['full_x_neighbor_overlap',1],['projected_neighbor_overlap',.5]]);
    expect(block.tables.find(t=>t.id==='sensitivity-mechanisms')!.rows[0]).toEqual(['representation','contradicted',null,null,null]);
  });
  it('retains three original conditional D2 interpretations without selecting one',()=>{
    const p=presentation(savedView(source),'en','unknown'),table=p.blocks.find(b=>b.id==='d2')!.tables.find(t=>t.id==='conditional-intents')!;
    expect(table.rows.map(row=>row[0])).toEqual(['proof_of_concept','known_context','outside_context']);
    expect(table.rows[2][3]).toEqual(source.cases[0].companions.d2.value.interpretations[2].stronger_claims_not_established);
  });
  it('keeps unavailable metadata and coordinates absent in the saved adapter',()=>{
    const view=savedView(source);expect(view.pca).toBeNull();expect(view.dataset.axis).toEqual([]);
    expect(view.dataset.metadata).toEqual([]);expect(view.provenance.independent_original_study_count).toBeNull();
    expect(view.geometryReason).toContain('NOT_REDISTRIBUTED');
  });
});

describe('F1 localisation, format parity and export safety',()=>{
  it.each(['en','fr'] as const)('keeps the same exact scientific evidence with %s pedagogy',locale=>{
    const {report,data}=fixture(),view=liveView(report,data),before=JSON.stringify(report),model=reportModel(view,report,'unknown',locale);
    const html=serializeReport(model,'html'),markdown=serializeReport(model,'markdown'),json=JSON.parse(serializeReport(model,'json'));
    expect(json.scientific_report).toEqual(report);expect(JSON.stringify(report)).toBe(before);
    for(const b of model.presentation!.blocks) {expect(html).toContain(anchor(b.id));expect(markdown).toContain(b.id.replaceAll('_','\\_'));}
    expect(html).not.toContain('<script');expect(html).toContain("default-src 'none'");
    expect(html).not.toContain('913.123456');expect(markdown).not.toContain('712.987654');
    expect(JSON.stringify(json)).not.toContain('913.123456');expect(json.raw_x_included).toBe(false);
  });
  it.each([null,0,1e-20,-1e-20,1e25,-1e25])('formats %j without confusing zero and unavailable',value=>{
    const en=formatValue(value,'en'),fr=formatValue(value,'fr');
    expect(en).not.toMatch(/NaN|undefined|Infinity/);expect(fr).not.toMatch(/NaN|undefined|Infinity/);
    if(value===0){expect(en).toBe('0');expect(fr).toBe('0');}
    if(value===null)expect(en).toBe('Not carried');
    if(value!==null&&value!==0)expect(en).toContain('e');
  });
  it('keeps exact zero variables and original French/English prose',()=>{
    const view=savedView(source);view.dataset.variables=0;view.findings[0].observation='Texte source / original evidence';
    const model=reportModel(view,source,'unknown','fr'),html=serializeReport(model,'html');
    expect(html).toContain('0 Variables');expect(html).toContain('Texte source / original evidence');
    expect(model.findings[0].observation).toBe(view.findings[0].observation);
  });
  it('escapes hostile/long table content and every source label with no foreign resource',()=>{
    const view=savedView(source),hostile='<img src="https://evil.invalid/" onerror="alert(1)">';
    view.evidence.push({id:'hostile',status:'computed',reason:null,value:{malicious:hostile,long:'long'.repeat(4000)},method:hostile,scope:hostile,provider:hostile});
    const html=serializeReport(reportModel(view,source,'unknown','fr'),'html');
    expect(html).not.toContain('<img src="https://evil');expect(html).not.toContain('onerror="alert');
    expect(html).toContain('&lt;img');expect(html).toContain('long'.repeat(4000));
  });
  it('retains exact original objects, offline disclosure and print-expansion instructions',()=>{
    const model=reportModel(savedView(source),source,'unknown','en'),html=serializeReport(model,'html');
    expect(html).toContain('content-visibility:visible');expect(html).toContain('@page');expect(html).toContain('table-header-group');
    expect(html).toContain('Technical disclosure sections are expanded for print');
    expect(html).toContain('No values are silently replaced');
    expect(JSON.parse(serializeReport(model,'json')).scientific_report).toEqual(source);
  });
  it('distinguishes a provider error from an all-noise computed result',()=>{
    const {report,data}=fixture();report.metrics.density={status:'error',reason:'SYNTHETIC_PROVIDER_REFUSAL',value:null};
    const block=presentation(liveView(report,data),'en','study').blocks.find(b=>b.id==='density')!;
    expect(block.status).toBe('error');expect(block.reason).toBe('SYNTHETIC_PROVIDER_REFUSAL');
    expect(block.tables.find(t=>t.id==='cluster-sizes')).toBeUndefined();expect(block.original).toBeNull();
  });
  it('preserves live interpretation identity links without substituting a metric',()=>{
    const {report,data}=fixture(),p=presentation(liveView(report,data),'en','unknown');
    const finding=p.findings.find(f=>f.id==='intended-use')!;
    expect(finding.resolvedEvidenceIds).toEqual(['interpretation']);
    expect(p.blocks.find(b=>b.id==='interpretation')!.original).toBe(report.interpretation);
  });
});
