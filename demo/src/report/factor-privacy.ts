import type {UiResult} from '../ui-types';
/** Separate, current-report declaration; optional section selection never grants it. */
export interface FactorColorExportGrant {
  protocol_version:'domains.factor_color_export.v1';
  dataset_content_sha256:string; pca_evidence_sha256:string; factor_id:string;
  source_permission_confirmed:true;
}
export function colorExportView(view:UiResult,grant?:FactorColorExportGrant|null):UiResult{
  const field=view.factorLegend?.factor_id??view.provenance.display_color_field??view.provenance.declared_m_group_field;
  if(!field)return view; // Preserve original X-derived density/group figures and historical objects.
  const allowed=!!grant&&grant.protocol_version==='domains.factor_color_export.v1'&&grant.source_permission_confirmed===true
    &&grant.dataset_content_sha256===view.dataset.contentHash&&grant.pca_evidence_sha256===view.provenance.evidence_sha256
    &&grant.factor_id===field;
  if(allowed)return {...view,provenance:{...view.provenance,factor_color_export:grant}};
  const {factorLegend:_legend,factorGroupColors:_colors,...rest}=view;
  return {...rest,pca:view.pca?{...view.pca,points:view.pca.points.map(({group:_group,...point})=>point)}:null,
    provenance:{...view.provenance,factor_color_export:{status:'unavailable',reason:'OBSERVATION_LEVEL_FACTOR_COLORS_NOT_AUTHORIZED'},
      display_color_status:'OMITTED_FROM_EXPORT_WITHOUT_SEPARATE_SOURCE_PERMISSION'}};
}
