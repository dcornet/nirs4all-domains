/** Presentation choices only. Availability follows transported contracts, never metric thresholds. */
import type { UiResult } from '../ui-types';

export const mandatorySections = Object.freeze(['identity_context','observations_checks','limitations_missing_information','evidence_core'] as const);
export const optionalSections = Object.freeze(['pca_scores','pca_scree','detailed_tables','methods_parameters','neighborhood','clustering','experimental_factors','representation_sensitivity','readiness','extended_provenance','glossary','machine_evidence'] as const);
export type OptionalSection = typeof optionalSections[number];
export interface SectionAvailability { id: OptionalSection; available: boolean; reason: string | null; evidence_ids: string[]; pointers: string[]; }
export interface ExportSelection {
  protocol_version: 'domains.report_export_selection.v1';
  scope: { dataset_id: string; source_id: string; content_sha256: string; report_protocol: string };
  mode: UiResult['mode']; mandatory_sections: readonly typeof mandatorySections[number][];
  optional_sections: readonly OptionalSection[]; available_sections: OptionalSection[];
  requested_sections: OptionalSection[]; selected_sections: OptionalSection[];
  unavailable_sections: { id: OptionalSection; reason: string }[];
  sections: SectionAvailability[];
  provenance: { origin: 'user' | 'defaults' | 'programmatic'; action: 'toggle' | 'select_all' | 'clear' | 'reset_defaults'; storage: 'current_report_memory_only' };
}
export function sectionAvailability(view: UiResult): SectionAvailability[] {
  const carried = (ids: string[]) => view.evidence.filter(e => ids.includes(e.id) && e.value !== null && e.value !== undefined);
  const decision = view.provenance.decision_summary as { factor_questions?: unknown[]; mechanisms?: {kind?: string}[] } | undefined;
  const references: Record<OptionalSection,string[]> = {
    pca_scores:['pca'],pca_scree:['pca'],detailed_tables:view.evidence.map(e=>e.id),methods_parameters:view.evidence.map(e=>e.id),
    neighborhood:['raw_neighbors','projected_neighbors'],clustering:['density',...(decision?.mechanisms?.some(m=>m.kind==='density_parameter')?['decision_summary']:[])],
    experimental_factors:['experimental_factor_structure',...view.evidence.filter(e=>e.id.startsWith('factor-association-')).map(e=>e.id),...(decision?.factor_questions?.length?['decision_summary']:[])],
    representation_sensitivity:['preprocessing_dependent_organization','parameter_sensitivity'],readiness:['readiness'],extended_provenance:[],glossary:[],machine_evidence:[],
  };
  return optionalSections.map(id=>{
    const evidence = carried(references[id]);
    let available = evidence.length>0;
    if(id==='pca_scores') available=!!view.pca?.points.length&&evidence.length>0;
    if(id==='pca_scree') available=!!view.pca?.points.length&&!!view.pca.eigenvalues.length&&evidence.length>0;
    if(id==='methods_parameters') available=view.evidence.length>0;
    if(id==='readiness') available=evidence.some(e=>Array.isArray((e.value as {records?:unknown[]}).records));
    if(id==='extended_provenance') available=Object.keys(view.provenance).length>0;
    if(id==='glossary'||id==='machine_evidence') available=true;
    const reason=available?null:view.evidence.find(e=>references[id].includes(e.id)&&e.reason)?.reason
      ?? (id.startsWith('pca_')?'PCA_COORDINATES_OR_SOURCE_NOT_CARRIED':'SECTION_DATA_NOT_CARRIED');
    return {id,available,reason,evidence_ids:evidence.map(e=>e.id),pointers:evidence.flatMap(e=>e.pointer?[e.pointer]:[])};
  });
}
export const selectionScope = (view: UiResult) => ({dataset_id:view.dataset.id,source_id:view.dataset.source,content_sha256:view.dataset.contentHash,report_protocol:view.protocol});
export const selectionOwner = (view: UiResult) => JSON.stringify([view.mode,selectionScope(view)]);
export const defaultSections = (view: UiResult): OptionalSection[] => sectionAvailability(view).filter(s=>s.available&&s.id!=='machine_evidence').map(s=>s.id);
export function createSelection(view: UiResult, requested: readonly OptionalSection[], action: ExportSelection['provenance']['action']='toggle', origin: ExportSelection['provenance']['origin']='user'): ExportSelection {
  if(!Array.isArray(requested)||requested.some(id=>!optionalSections.includes(id)))throw new Error('EXPORT_SELECTION_UNKNOWN_SECTION');
  const sections=sectionAvailability(view), requested_sections=optionalSections.filter(id=>requested.includes(id));
  return {protocol_version:'domains.report_export_selection.v1',scope:selectionScope(view),mode:view.mode,
    mandatory_sections:mandatorySections,optional_sections:optionalSections,available_sections:sections.filter(s=>s.available).map(s=>s.id),
    requested_sections,selected_sections:requested_sections.filter(id=>sections.find(s=>s.id===id)!.available),
    unavailable_sections:sections.filter(s=>!s.available).map(s=>({id:s.id,reason:s.reason!})),sections,
    provenance:{origin,action,storage:'current_report_memory_only'}};
}
export function validateSelection(view: UiResult, selection: ExportSelection): void {
  if(selection.protocol_version!=='domains.report_export_selection.v1')throw new Error('EXPORT_SELECTION_VERSION_UNSUPPORTED');
  if(!selection.provenance||!['user','defaults','programmatic'].includes(selection.provenance.origin)||!['toggle','select_all','clear','reset_defaults'].includes(selection.provenance.action))throw new Error('EXPORT_SELECTION_INVALID_PROVENANCE');
  const expected=createSelection(view,selection.requested_sections,selection.provenance.action,selection.provenance.origin);
  const ordered=(value:unknown):unknown=>Array.isArray(value)?value.map(ordered):value&&typeof value==='object'?Object.fromEntries(Object.entries(value).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>[k,ordered(v)])):value;
  if(JSON.stringify(ordered(selection))!==JSON.stringify(ordered(expected)))throw new Error('EXPORT_SELECTION_SCOPE_OR_AVAILABILITY_MISMATCH');
}
