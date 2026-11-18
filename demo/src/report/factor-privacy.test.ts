import {describe,it,expect} from 'vitest';
import type {UiResult} from '../ui-types';
import {colorExportView,type FactorColorExportGrant} from './factor-privacy';
import {reportModel} from './model';
import {createSelection,optionalSections} from './selection';
function view():UiResult{return {mode:'live',protocol:'fixture',dataset:{name:'d',id:'d',source:'X',contentHash:'a'.repeat(64),observations:3,variables:1,axisUnit:'nm',axis:[1000],spectra:[],metadata:[],identity:'declared',provenance:'fixture',license:'synthetic'},summary:'fixture',findings:[],evidence:[{id:'pca',method:'PCA',status:'computed',reason:null,value:{scores:[[-1],[0],[1]]},scope:'train',provider:'Methods'}],pca:{points:[{id:'a',x:-1,y:0,group:'factor-level-0'},{id:'b',x:0,y:0,group:'factor-level-1'},{id:'c',x:1,y:0,group:'factor-missing'}],eigenvalues:[1],totalVariance:1,xLabel:'PC1',yLabel:'unresolved',resolvedComponents:1},geometryReason:null,limitations:[],provenance:{source_mode:'fixture',evidence_sha256:'b'.repeat(64),display_color_field:'batch'},factorGroupColors:{'factor-level-0':'#0f766e'}};}
const grant:FactorColorExportGrant={protocol_version:'domains.factor_color_export.v1',dataset_content_sha256:'a'.repeat(64),pca_evidence_sha256:'b'.repeat(64),factor_id:'batch',source_permission_confirmed:true};
describe('factor colors have independent export permission',()=>{
  it('select all cannot export observation membership and does not alter source evidence',()=>{
    const v=view(),before=structuredClone(v),scientific={original:'unchanged'};
    const exported=reportModel(v,scientific,'unknown','en',undefined,'complete',createSelection(v,optionalSections,'select_all'));
    expect(exported.pca?.points.every(p=>p.group===undefined)).toBe(true);
    expect(JSON.stringify(exported)).not.toContain('factor-level-0');expect(exported.scientific_report).toBe(scientific);expect(v).toEqual(before);
    expect(exported.evidence).toBe(v.evidence);expect(exported.presentation?.figures[0].groupColors).toEqual({});
  });
  it('only a current content/PCA/factor-bound separate declaration retains colors',()=>{
    const v=view();expect(colorExportView(v,grant).pca).toBe(v.pca);
    for(const g of [{...grant,factor_id:'other'},{...grant,pca_evidence_sha256:'stale'},{...grant,dataset_content_sha256:'stale'}])expect(colorExportView(v,g).pca?.points[0].group).toBeUndefined();
  });
  it('omits implicit declared M group coloring but retains X-derived source colors',()=>{
    const v=view();delete v.provenance.display_color_field;delete v.factorGroupColors;
    expect(colorExportView(v)).toBe(v);
    v.provenance.declared_m_group_field='specimen';expect(colorExportView(v).pca?.points[0].group).toBeUndefined();
  });
});
