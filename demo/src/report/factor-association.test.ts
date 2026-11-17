import { describe, expect, it } from 'vitest';
import type { FactorResult } from '@nirs4all/domains';
import type { UiResult } from '../ui-types';
import { appendFactorAssociations, factorAssociationTables } from './factor-association';
import {presentation} from './presentation';

function view(): UiResult {
  return { mode:'live', protocol:'fixture', dataset:{name:'d',id:'d',source:'s',contentHash:'h',observations:3,variables:2,axisUnit:'nm',axis:[1,2],spectra:[],metadata:[],identity:'declared',provenance:'fixture',license:'fixture'},
    summary:'existing summary', findings:[], evidence:[{id:'pca',method:'PCA',status:'computed',reason:null,value:{immutable:true},scope:'train',provider:'owner',pointer:'/metrics/pca'}],
    pca:null,geometryReason:null,limitations:['existing limitation'],provenance:{source_mode:'fixture',existing:'preserved'} };
}
const externalEvidence = { uri:'https://example.invalid/design', content_sha256:'design-hash', qualification:'externally_qualified', basis:'synthetic fixture' };
const exact = { p_value:1/3, n_arrangements:6, minimum_p_value:1/3, maximum_statistic:0.8 };
const result = {
  protocol_version:'domains.browser_factor_association_result.v1', status:'computed', reason:null,
  value:{ population:'train', representation:'recorded raw-PCA scores', pca_id:'pca-id', scores_sha256:'scores-hash',
    analysis_unit:{ calculation_unit:'observations/acquisitions', n_observations:4, n_independent_units:null, physical_independence_verified_by_domains:false, qualification:'No independent-unit evidence supplied.' },
    inference:{ level:'conditionally_admissible', reason:null, family:{ factor_ids:['batch'], components:'all_resolved', correction:'holm', external_evidence:externalEvidence }, no_global_risk_or_causal_claim:true },
    factors:[{ factor_id:'batch', kind:'categorical', role:'factor', unit:null, origin:'declared', evidence:'declared', derived_from_target:false,
      n_fit_observations:4, n_used:3, n_missing:1, used_keys_sha256:'used-keys-hash', values_sha256:'factor-values-hash', n_levels:2,
      level_counts:[{level_id:'level-1',value:'A',label:'A',count:2},{level_id:'level-2',value:'B',label:'B',count:1}],
      range:{status:'unavailable',reason:'NOT_A_CONTINUOUS_NONEMPTY_FACTOR',value:null}, owner_summary:{status:'unavailable',reason:'NOT_A_CONTINUOUS_NONEMPTY_FACTOR',value:null}, warnings:[],
      components:[{component:1,n_used:3,
        descriptive:{status:'computed',reason:null,value:{measure:'eta_squared',estimate:0.8,owner_output:{eta_squared:0.8,f_statistic:54,df1:1,df2:4,n_levels:2,n_score_values:3,log10_distinct_arrangements:0.4771,p_value:null,n_permutations_executed:0,n_at_least_observed:0,backend_version:'1.3.13'}}},
        inference:{status:'computed',reason:null,value:{qualification:'conditional_on_supplied_external_exchangeability_record',test:'exact_eta_squared',owner_exact:exact,holm_adjusted_p:1/3,family_size:1,external_evidence:externalEvidence}},
        exact_owner_evidence:{status:'computed',reason:null,value:exact}},
        {component:2,n_used:3,descriptive:{status:'unavailable',reason:'PCA_COMPONENT_NOT_RESOLVED',value:null},
          inference:{status:'unavailable',reason:'PCA_COMPONENT_NOT_RESOLVED',value:null},exact_owner_evidence:{status:'unavailable',reason:'PCA_COMPONENT_NOT_RESOLVED',value:null}}]}],
    dependency_audit:{fields:[{name:'specimen',role:'identity',kind:'categorical',n_rows:4,n_missing:0,n_distinct_nonmissing:2,n_repeated_rows_beyond_first:2,independent_units_established:false}],
      pairwise_context_tables:[{left:'batch',right:'lot',n_complete_pairs:4,n_missing_pairs:0,observed_combinations:[{left_level:'level-1',right_level:'level-1',count:4}],absent_combination_count:1,left_nested_in_right:true,right_nested_in_left:true,literal_total_confounding:true,qualification:'Literal combinations.'}],qualification:'Literal metadata.'}},
  receipt:{receipt_sha256:'receipt-hash',fit_keys:['row-1','row-2'],provider_calls:[{operation:'factor_descriptive',request_sha256:'request-hash',backend_version:'1.3.13',parameters:{n_permutations:0,seed:0},inputs:{codes:{count:3,sha256:'codes-hash'},scores:{count:3,sha256:'scores-hash'}},status:'computed',reason:null,response_sha256:'response-hash'}],fields_read:{x:false,y:[],m:[{name:'batch',role:'factor',n_rows:4,keys_sha256:'keys-hash',values_sha256:'values-hash'}]}},
  supported_claims:['Descriptive association'], limitations:['No causality'], action:'Review the design.'
} satisfies FactorResult;

describe('factor association report preparation',()=>{
  it('appends aggregate evidence and findings while preserving the source view',()=>{
    const source=view(), before=structuredClone(source);
    const next=appendFactorAssociations(source,[result]);
    expect(source).toEqual(before);
    expect(next.evidence[0]).toEqual(source.evidence[0]);
    expect(presentation(next,'en','unknown').blocks[0].id).toBe('factor-association-1');
    expect(next.findings[0]?.observation).toContain('3 pairs used');
    const attached=next.evidence.at(-1)!;
    expect(attached.id).toBe('factor-association-1');
    expect(attached.value).toBe(result);
    expect(attached.value).toEqual(result);
    expect(next.provenance).toMatchObject({existing:'preserved',factor_association_evidence_ids:['factor-association-1']});
    expect(appendFactorAssociations(source,[result],'fr').findings[0]?.confidence).toContain('conditionnelle');
  });
  it('prepares practical per-PC, level, dependency, and confounding tables in both locales',()=>{
    const en=factorAssociationTables(result,'en'),fr=factorAssociationTables(result,'fr');
    expect(en[0].columns).toHaveLength(7);
    expect(en[0].rows).toEqual([['batch','PC1','eta_squared',0.8,3,'computed',null],['batch','PC2',null,null,3,'unavailable','PCA_COMPONENT_NOT_RESOLVED']]);
    expect(en.find(t=>t.id==='factor-association-summary')?.rows[0]).toEqual(['batch','categorical',null,1,2,'declared',4]);
    expect(en.find(t=>t.id==='factor-association-inference')?.rows[0]).toEqual(['batch','PC1',1/3,1/3,'computed',null,'Conditional on supplied external design record']);
    expect(en.find(t=>t.id==='factor-association-anova')?.rows[0]).toEqual(['batch','PC1',54,1,4]);
    expect(en.find(t=>t.id==='factor-association-levels')?.rows).toEqual([['batch','A',2],['batch','B',1]]);
    expect(en.find(t=>t.id==='factor-association-dependencies')?.rows[0]).toEqual(['specimen','identity','categorical',0,2,2,null,false,null]);
    expect(en.find(t=>t.id==='factor-association-crossings')?.rows[0]).toEqual(['batch','lot',4,[{left_level:'level-1',right_level:'level-1',count:4}],true,
      {absent_combination_count:1,absent_combinations:null,left_nested_in_right:true,right_nested_in_left:true,n_missing_pairs:0,qualification:'Literal combinations.'}]);
    expect(fr[0].columns[0]).toBe('Facteur');
    expect(fr[0].note).toContain('Eta²');
    expect(fr.find(t=>t.id==='factor-association-inference')?.rows[0][6]).toContain('externe');
  });
});
