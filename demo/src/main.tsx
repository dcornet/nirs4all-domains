import { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import {sanitizedWorkerDiagnostic,type WorkerDiagnostic} from './engine/runtime-diagnostic';
import { BrowserEngine } from './engine/client';
import { MAX_IMPORT_BYTES, MAX_IMPORT_FILES } from './engine/dataset-io';
import type { BrowserReport, LocalDataset } from './engine/types';
import type { SensitivityResult,BrowserReading,ScopedOperation,ScopedResult,SupportResult,FactorResult,FactorPopulation,FactorInferencePlan } from '@nirs4all/domains';
import type {DatasetDraft} from './engine/import-draft';
import {defaultImportConfig,summarizeImport,type ImportOutcome,type ImportSession} from './engine/one-shot';
import {scopedRequest,structureDataset,type ScopeOptions} from './engine/scoped';
import {scopedInventory,scopedView} from './report/scoped';
import { examples, synthetic } from './examples';
import { liveView, reportModel, savedView } from './report/model';
import { loadPublicSaved, validateSaved } from './report/saved';
import { downloadReport } from './report/export';
import {supportRequest,recordSupportReply,type SupportParameters,type SupportRun} from './engine/support';
import {preprocessingRequest,sensitivityFactors,sensitivitySignature,type SensitivityHistory,type SensitivityRun} from './engine/preprocessing';
import {appendSensitivity} from './report/preprocessing';
import {appendSupport} from './report/support';
import {factorRequest,factorSource,factorChoices,parseFactorInferencePlan} from './engine/factor';
import type {FactorAssociationRun} from './FactorAssociationControls';
import {appendFactorAssociations} from './report/factor-association';
import {colorFactorPoints} from './report/factor-colors';
import type {FactorColorExportGrant} from './report/factor-privacy';
import type { UiCallbacks, UiState, UiResult,PredictionIntent,ProcessingStage } from './ui-types';

function Controller() {
  const [state, setState] = useState<UiState>({ phase: 'idle', progress: '', error: null, result: null,
    examples, intent: 'unknown', importHint: 'Drop local X/Y/M files or a folder. IO validates the import; settings are optional. Nothing is uploaded.',
    declarations: { population: '', prediction_unit: '', new_context: '' } });
  const engine = useRef(new BrowserEngine());
  const epoch = useRef(0);
  const dataset = useRef<LocalDataset | null>(null);
  const scientific = useRef<unknown>(null);
  const selectedExample = useRef<string | null>(null);
  const operations=useRef<ScopedResult[]>([]),baseView=useRef<UiResult|undefined>(undefined);
  const baseReport=useRef<BrowserReport|null>(null),baseData=useRef<LocalDataset|null>(null),color=useRef('');
  const associations=useRef<FactorResult[]>([]),associationColor=useRef<FactorResult|null>(null),colorGrant=useRef<FactorColorExportGrant|null>(null);
  const supportResults=useRef<SupportRun[]>([]);
  const sensitivityResults=useRef<SensitivityHistory[]>([]),sensitivityFrozen=useRef<{result:SensitivityResult;signature:string}|null>(null);
  const importFiles=useRef<File[]|null>(null);
  const loadedImport=useRef<ImportSession|null>(null),pendingImport=useRef<ImportSession|null>(null);
  const externalPlan=useRef<FactorInferencePlan|null>(null);
  useEffect(() => () => engine.current.cancel(), []);
  const clearEvidence=()=>{scientific.current=null;dataset.current=null;operations.current=[];supportResults.current=[];sensitivityResults.current=[];sensitivityFrozen.current=null;baseView.current=undefined;baseReport.current=null;baseData.current=null;color.current='';associations.current=[];associationColor.current=null;colorGrant.current=null;externalPlan.current=null;};
  const start = () => { const token = ++epoch.current; engine.current.cancel();clearEvidence();loadedImport.current=null;pendingImport.current=null;setState(s => ({ ...s, importDraft:undefined,importSession:undefined,pendingImport:undefined,importSummary:undefined,result: null, error: null,workerDiagnostic:undefined,canRetryImport:false,phase: 'loading', processingStage:'prepare',progress: 'Preparing local data' })); return token; };
  const progress = (token: number) => (stage: string,step?:ProcessingStage,diagnostic?:WorkerDiagnostic) => { if (token === epoch.current) setState(s => ({ ...s,progress:stage,processingStage:step??s.processingStage,...(diagnostic?{workerDiagnostic:sanitizedWorkerDiagnostic(diagnostic)}:{}) })); };
  const failed = (token: number, error: unknown) => {
    if (token !== epoch.current) return;
    const e = error as {code?:string;message?:string;diagnostic?:WorkerDiagnostic};
    const diagnostic=e.diagnostic?sanitizedWorkerDiagnostic(e.diagnostic):undefined;
    setState(s=>({...s,phase:'error',canRetryImport:!!importFiles.current&&diagnostic?.operation==='prepare_import'&&diagnostic.recoverable&&diagnostic.remediation==='retry',error:{code:diagnostic?.code??e.code??'LOCAL_ANALYSIS_REFUSED',message:diagnostic?.rt_error.message??e.message??String(error),...(diagnostic?{diagnostic}:{})}}));
  };
  const analyze = async (data: LocalDataset, token: number) => {
    if (token !== epoch.current) return;
    dataset.current = data;
    setState(s => ({ ...s, phase: 'running' }));
    const report = await engine.current.request<BrowserReport>('analyze', { ...data.input, prediction_intent: state.intent }, progress(token));
    if (token !== epoch.current) return;
    scientific.current = report;
    setState(s => ({ ...s, phase: 'idle', result: liveView(report, data), processingStage:'report',progress: '' }));
  };
  const publishScoped=(data:LocalDataset)=>{
    let result=appendFactorAssociations(scopedView(baseView.current,data,operations.current,associationColor.current?undefined:color.current||undefined),associations.current);
    const unpartitioned=data.rowManifest?.every(r=>r.partition==='unpartitioned')===true;
    const source=(population:FactorPopulation)=>factorSource(population,operations.current,unpartitioned?baseReport.current:null);
    result.factorControls={datasetKey:data.input.content_sha256,factors:factorChoices(data),
      populations:(unpartitioned?['unpartitioned']:['train','global_transductive']).map(p=>{
        const candidate=source(p as FactorPopulation),pca=candidate?.report.metrics.pca;
        const ready=pca?.status==='computed'&&pca.value!==null;
        return {id:p as FactorPopulation,label:p,ready,reason:ready?undefined:pca?.reason??'PCA_EXECUTION_PROVENANCE_REQUIRED'};
      }),
      inferenceRecordAvailable:externalPlan.current!==null,
      exportColorAuthorized:!!colorGrant.current};
    result.factorAssociations=associations.current;
    result=appendSensitivity(appendSupport(result,supportResults.current),sensitivityResults.current);
    result.sensitivityControls={factors:sensitivityFactors(data),hasTest:data.rowManifest?.some(r=>r.partition==='test')===true,frozen:sensitivityFrozen.current};
    const selected=associationColor.current;
    if(selected&&result.pca&&selected.receipt.source_pca_evidence_sha256===result.provenance.evidence_sha256){
      const f=selected.value.factors.find(f=>f.factor_id===color.current),m=data.metadata.find(f=>f.name===color.current);
      if(f&&m&&(f.kind==='categorical'||f.kind==='continuous')){
        const keys=selected.receipt.fit_keys as string[],positions=new Map(data.rowManifest!.map((r,i)=>[r.key,i]));
        const display=colorFactorPoints(result.pca.points,{id:f.factor_id,kind:f.kind,unit:f.unit,origin:f.origin,
          row_keys:keys,values:keys.map(k=>m.values[positions.get(k)!]??null),levels:f.level_counts??undefined,range:f.range.value},'en');
        result={...result,pca:{...result.pca,points:display.points},factorLegend:display.legend,factorGroupColors:display.groupColors,
          provenance:{...result.provenance,display_color_field:f.factor_id,display_color_status:'DISPLAY_ONLY_NO_REFIT',factor_color_pca_id:selected.value.pca_id}};
      }
    }
    scientific.current={protocol_version:'domains.browser_scoped_report.v1',raw_X_Y_exported:false,inventory:scopedInventory(data),
      scoped_operations:operations.current,train_fitted_support:supportResults.current,preprocessing_sensitivity:sensitivityResults.current,factor_associations:associations.current,unpartitioned_structure:baseReport.current&&baseData.current?.rowManifest?.every(row=>row.partition==='unpartitioned')?baseReport.current:null};
    setState(s=>({...s,phase:'idle',result,importDraft:undefined,error:null,processingStage:'report',progress:''}));
  };
  const acceptImport=(outcome:ImportOutcome,token:number)=>{
    if(token!==epoch.current)return;
    if(outcome.dataset){
      clearEvidence();dataset.current=outcome.dataset;loadedImport.current=outcome.session;
      publishScoped(outcome.dataset);
      setState(s=>({...s,importSession:outcome.session,importSummary:summarizeImport(outcome.dataset!,outcome.session)}));
    }
    pendingImport.current=outcome.status==='needs_input'?outcome.session:null;
    setState(s=>({...s,phase:'idle',error:null,canRetryImport:false,progress:'',
      importDraft:outcome.status==='needs_input'?outcome.session.draft:undefined,
      pendingImport:outcome.status==='needs_input'?outcome.session:undefined}));
  };
  const applySettings=async(session:ImportSession,config:ImportSession['config'],sources:ImportSession['sources'])=>{
    const token=++epoch.current;engine.current.cancel();
    setState(s=>({...s,phase:'loading',error:null,processingStage:'import',progress:'Validating changed data settings with IO'}));
    try{acceptImport(await engine.current.request<ImportOutcome>('assemble_import',{draft:session.draft,config,sources,mode:'one_shot',automatic:false},progress(token)),token);}
    catch(error){failed(token,error);}
  };
  const scoped=async(operation:ScopedOperation,options:ScopeOptions={})=>{
    const data=dataset.current;if(!data?.rowManifest)return;
    if(operation==='train_structure'||operation==='global_descriptive_transductive'){color.current='';associationColor.current=null;colorGrant.current=null;}
    const token=++epoch.current;engine.current.cancel();
    setState(s=>({...s,phase:'running',error:null,processingStage:'validate',progress:'Executing only the selected scientific operation'}));
    try{
      // The unchanged legacy descriptive protocol remains valid for explicitly unpartitioned X.
      if(operation==='train_structure'&&data.rowManifest.every(row=>row.partition==='unpartitioned')){
        if(!data.rawX||data.rawX.some(row=>row.some(value=>value===null)))throw new Error('MISSING_X_NO_IMPLICIT_IMPUTATION');
        const projected={...data,input:{...data.input,spectra:data.rawX as number[][]}};
        const report=await engine.current.request<BrowserReport>('analyze',{...projected.input,prediction_intent:state.intent},progress(token));
        if(token!==epoch.current)return;
        baseReport.current=report;baseData.current=projected;baseView.current=liveView(report,projected);
      }else{
        const request=scopedRequest(data,operation,options);
        const result=await engine.current.request<ScopedResult>('scoped',request,progress(token));
        if(token!==epoch.current)return;
        operations.current=[...operations.current,result];
        const subset=structureDataset(data,result);
        if(subset&&result.value?.structure){
          baseReport.current=result.value.structure;baseData.current=subset;baseView.current=liveView(result.value.structure,subset);
          baseView.current.dataset.population=operation==='train_structure'?'Declared train only; other partitions not used for this fit':'Explicitly selected train + test; transductive fit';
          baseView.current.summary=baseView.current.dataset.population;
        }
      }
      publishScoped(data);
    }catch(error){
      if(token!==epoch.current)return;
      const reason=error instanceof Error?error.message:String(error);
      operations.current=[...operations.current,{protocol_version:'domains.browser_scoped_result.v1',operation,
        diagnostic:options.diagnostic??null,status:'error',reason,value:null,
        receipt:{dataset_id:data.input.dataset_id,content_sha256:data.input.content_sha256,
          execution_receipt:'not_returned; no successful execution is inferred',provider_calls:null},
        supported_claims:[],limitations:['No successful provider receipt was returned. Earlier operation results retain their original scopes.'],
        action:'Read the operation refusal and its prerequisite; imported X/Y/M remain available.'}];
      publishScoped(data);
      if((error as {diagnostic?:unknown})?.diagnostic)failed(token,error);
    }
  };
  const associate=async(run:FactorAssociationRun)=>{
    const data=dataset.current;if(!data?.rowManifest)return;
    const token=++epoch.current;engine.current.cancel();
    setState(s=>({...s,phase:'running',error:null,processingStage:'validate',progress:'Validating recorded PCA and M population; no fit'}));
    try{
      const source=factorSource(run.population,operations.current,data.rowManifest.every(r=>r.partition==='unpartitioned')?baseReport.current:null);
      if(!source)throw new Error('PCA_EXECUTION_PROVENANCE_REQUIRED');
      const result=await engine.current.request<FactorResult>('factor_association',factorRequest(data,source,run,externalPlan.current),progress(token));
      if(token!==epoch.current)return;
      associations.current=[...associations.current,result];publishScoped(data);
    }catch(error){failed(token,error);}
  };
  const support=async(parameters:SupportParameters)=>{
    const data=dataset.current;if(!data?.rowManifest)return;
    const token=++epoch.current;engine.current.cancel();
    setState(s=>({...s,phase:'running',error:null,processingStage:'validate',progress:'Validating train-only fit and test projection access'}));
    try{
      const result=await engine.current.request<SupportResult>('train_fitted_support',supportRequest(data,parameters),progress(token));
      if(token!==epoch.current)return;
      supportResults.current=recordSupportReply(epoch.current,token,supportResults.current,result);publishScoped(data);
    }catch(error){
      if(token!==epoch.current)return;
      const reason=error instanceof Error?error.message:String(error);
      supportResults.current=[...supportResults.current,{
        protocol_version:'domains.browser_train_fitted_support_local_refusal.v1',status:'unavailable',reason,local_refusal:true,evidence_sha256:null,
        projection:{status:'unavailable',reason,value:null},monitoring:{status:'unavailable',reason,value:null},
        limit_qualification:{status:'unknown',reasons:['NO_SUCCESSFUL_PROVIDER_RECEIPT'],source:null,fold_scheme:'row_index_modulo_n_folds',independent_units_certified:false,interpretation:'No provider receipt returned; limits unavailable.'},
        dependence:{},receipt:{dataset_id:data.input.dataset_id,content_sha256:data.input.content_sha256,execution_receipt:'not_returned; no successful execution inferred'},
        supported_claims:[],limitations:['Operation refused locally. Earlier results and imported data remain available.']
      }];publishScoped(data);
      if((error as {diagnostic?:unknown})?.diagnostic)failed(token,error);
    }
  };
  const sensitivity=async(run:SensitivityRun)=>{
    const data=dataset.current;if(!data?.rowManifest)return;
    const token=++epoch.current;engine.current.cancel();
    setState(s=>({...s,phase:'running',error:null,processingStage:'validate',progress:run.stage==='reference_only'?'Executing the declared panel on reference only':'Validating frozen reference before explicit test audit'}));
    try{
      const signature=sensitivitySignature(run.plan,run.factorIds,run.reuseExactPrefixes);
      if(run.stage==='test_audit'&&(!sensitivityFrozen.current||sensitivityFrozen.current.signature!==signature||run.frozenReference?.evidence_sha256!==sensitivityFrozen.current.result.evidence_sha256))throw new Error('SENSITIVITY_FROZEN_CONTROLS_MISMATCH');
      const request=preprocessingRequest(data,run);
      const result=await engine.current.request<SensitivityResult>('preprocessing_sensitivity',request,progress(token));
      if(token!==epoch.current||dataset.current!==data)return;
      sensitivityResults.current=[...sensitivityResults.current,result];
      if(run.stage==='reference_only')sensitivityFrozen.current={result,signature};
      publishScoped(data);
    }catch(error){
      if(token!==epoch.current||dataset.current!==data)return;
      const reason=error instanceof Error?error.message:String(error);
      sensitivityResults.current=[...sensitivityResults.current,{protocol_version:'domains.browser_preprocessing_sensitivity_local_refusal.v1',status:'unavailable',reason,stage:run.stage,plan:structuredClone(run.plan),evidence_sha256:null,local_refusal:true,receipt:{execution_receipt:'not_returned; no successful execution inferred'},limitations:['Local documentary refusal. Earlier F4.0/F4.1/F4.2 and sensitivity results remain unchanged.']}];publishScoped(data);
      if((error as {diagnostic?:unknown})?.diagnostic)failed(token,error);
    }
  };
  const callbacks: UiCallbacks = {
    onSensitivity:sensitivity,
    onImportOptionsChange(editImportFirst){setState(s=>({...s,editImportFirst}));},
    onDismissImport(){++epoch.current;engine.current.cancel();pendingImport.current=null;setState(s=>({...s,pendingImport:undefined,importDraft:undefined,error:null,phase:'idle',progress:''}));},
    onApplyDataSettings(config,sources,session){if(session&&session===loadedImport.current)void applySettings(session,config,sources);},
    onRetryImport(){const files=importFiles.current;if(files)void callbacks.onImport([...files]);},
    onSupport:support,
    async onFactorInferencePlan(file){
      const data=dataset.current;if(!data?.rowManifest)return;
      const token=epoch.current;externalPlan.current=null;publishScoped(data);
      try{
        if(file.size>65_536)throw new Error('FACTOR_DESIGN_RECORD_64_KIB_BUDGET_EXCEEDED');
        const plan=await parseFactorInferencePlan(await file.text());
        if(token!==epoch.current||dataset.current!==data)return;
        externalPlan.current=plan;publishScoped(data);
      }catch(error){failed(token,error);}
    },
    async onImport(files) {
      importFiles.current=[...files];
      const token=++epoch.current;engine.current.cancel();pendingImport.current=null;selectedExample.current=null;
      setState(s=>({...s,phase:'loading',error:null,workerDiagnostic:undefined,canRetryImport:false,pendingImport:undefined,importDraft:undefined,processingStage:'prepare',progress:'Reading local files and inferring the dataset with IO'}));
      try {
        if (files.length > MAX_IMPORT_FILES || files.reduce((n, f) => n + f.size, 0) > MAX_IMPORT_BYTES) throw new Error('IMPORT_BYTE_OR_FILE_BUDGET_EXCEEDED: maximum 8 MiB and 32 files; no silent sampling.');
        if (files.length === 1 && /\.json$/i.test(files[0].name) && !files[0].name.endsWith('.nirs4all.json')) {
          const source = JSON.parse(await files[0].text()); validateSaved(source);
          if (token !== epoch.current) return;
          const view = savedView(source); view.provenance.source_mode = 'user_saved_schema_validated';
          view.dataset.provenance = 'User-supplied saved evidence; structural validation only';
          view.dataset.license = 'Retain the supplied source terms; no redistribution permission is inferred';
          view.findings.forEach(finding => { finding.confidence = 'Declared by the supplied report; not independently authenticated'; });
          view.provenance.source_qualification = 'User-supplied saved evidence; schema validated, authorship and numerical qualification not authenticated.';
          view.limitations.push('Imported saved report: structural validation is not a new scientific analysis or source-authenticity check.');
          clearEvidence();loadedImport.current=null;scientific.current = source;
          setState(s => ({ ...s, phase: 'idle', result: view,importSession:undefined,pendingImport:undefined,importSummary:undefined })); return;
        }
        const payload = await Promise.all(files.map(async file => ({ name: file.webkitRelativePath || file.name, bytes: new Uint8Array(await file.arrayBuffer()) })));
        if (token !== epoch.current) return;
        const draft=await engine.current.request<DatasetDraft>('prepare_import',payload,progress(token));
        if(token!==epoch.current)return;
        if(state.editImportFirst){
          const session:ImportSession={draft,config:defaultImportConfig(draft),sources:draft.sources,issues:[]};
          pendingImport.current=session;setState(s=>({...s,phase:'idle',importDraft:draft,pendingImport:session,progress:''}));return;
        }
        const outcome=await engine.current.request<ImportOutcome>('assemble_import',{draft,config:defaultImportConfig(draft),sources:draft.sources,mode:'one_shot',automatic:true},progress(token));
        acceptImport(outcome,token);
      } catch (error) { failed(token, error); }
    },
    async onConfirmImport(config,sources,session){
      if(session&&session===pendingImport.current)await applySettings(session,config,sources);
    },
    onScopedOperation:scoped,
    onFactorAssociation:associate,
    onColorFactor(field){const data=dataset.current;if(!data?.rowManifest)return;color.current=field;associationColor.current=null;colorGrant.current=null;publishScoped(data);},
    onAssociationColor(field){
      const data=dataset.current;if(!data?.rowManifest)return;
      const recorded=[...associations.current].reverse().find(r=>r.value.factors.some(f=>f.factor_id===field));
      if(!recorded){setState(s=>({...s,error:{code:'FACTOR_ASSOCIATION_REQUIRED',message:'Run the factor association first to obtain owner level counts or range. Coloring never fits a PCA.'}}));return;}
      const factor=recorded.value.factors.find(f=>f.factor_id===field)!;
      if(factor.kind==='continuous'&&factor.range.status!=='computed'){setState(s=>({...s,error:{code:'FACTOR_COLOR_RANGE_UNAVAILABLE',message:`Continuous factor coloring is unavailable: ${factor.range.reason}. Association evidence remains unchanged.`}}));return;}
      const source=factorSource(recorded.value.population,operations.current,data.rowManifest.every(r=>r.partition==='unpartitioned')?baseReport.current:null);
      if(!source||source.report.evidence_sha256!==recorded.receipt.source_pca_evidence_sha256)return;
      const subset=recorded.value.population==='unpartitioned'?data:structureDataset(data,[...operations.current].reverse().find(r=>r.receipt.receipt_sha256===source.receipt?.receipt_sha256)!);
      if(!subset)return;
      baseReport.current=source.report;baseData.current=subset;baseView.current=liveView(source.report,subset);
      color.current=field;associationColor.current=recorded;colorGrant.current=null;
      try{publishScoped(data);}catch(error){color.current='';associationColor.current=null;publishScoped(data);failed(epoch.current,error);}
    },
    onAuthorizeFactorColorExport(field,authorized){
      const data=dataset.current;if(!data)return;
      colorGrant.current=authorized&&field===color.current&&baseReport.current?{protocol_version:'domains.factor_color_export.v1',dataset_content_sha256:data.input.content_sha256,pca_evidence_sha256:baseReport.current.evidence_sha256,factor_id:field,source_permission_confirmed:true}:null;
      publishScoped(data);
    },
    async onExample(id) {
      importFiles.current=null;const token = start(); selectedExample.current = id;
      try {
        if (id === 'tablet-saved') {
          const source = await loadPublicSaved(state.intent);
          if (token !== epoch.current) return;
          scientific.current = source; dataset.current = null;
          setState(s => ({ ...s, phase: 'idle', result: savedView(source) }));
        } else await analyze(await synthetic(id), token);
      } catch (error) { failed(token, error); }
    },
    onCancel() { ++epoch.current; engine.current.cancel();
      if(dataset.current?.rowManifest){publishScoped(dataset.current);setState(s=>({...s,phase:'cancelled'}));return;}
      scientific.current = null; dataset.current = null;
      setState(s => ({ ...s, importDraft:undefined,phase: 'cancelled', result: null, progress: '' })); },
    onReset() { importFiles.current=null;++epoch.current; engine.current.cancel(); scientific.current = null; dataset.current = null; selectedExample.current = null;
      loadedImport.current=null;pendingImport.current=null;
      clearEvidence();
      associations.current=[];associationColor.current=null;colorGrant.current=null;externalPlan.current=null;
      setState(s => ({ ...s, importDraft:undefined,importSession:undefined,pendingImport:undefined,importSummary:undefined,editImportFirst:false,phase: 'idle', result:null,error:null,workerDiagnostic:undefined,canRetryImport:false,progress:'' })); },
    async onIntent(intent: PredictionIntent) {
      if (!scientific.current) return; // A queued old control cannot cancel a new dataset import.
      const token = ++epoch.current; engine.current.cancel();
      setState(s => ({ ...s, intent, error: null }));
      try {
        if (selectedExample.current === 'tablet-saved') {
          setState(s=>({...s,phase:'loading',processingStage:'interpret',progress:'Loading the original saved reading; no fit'}));
          const source = await loadPublicSaved(intent);
          if (token !== epoch.current) return;
          scientific.current = source; setState(s => ({ ...s, phase:'idle',result: savedView(source),processingStage:'report',progress:'' })); return;
        }
        if (!dataset.current) {
          setState(s => ({ ...s, error: { code: 'SAVED_DECLARATION_ONLY', message: 'The new intention is recorded as a user declaration. Imported original companions remain unchanged; regenerate them through the qualified Domains API to obtain another saved reading.' } })); return;
        }
        if(dataset.current.rowManifest){
          if(baseReport.current&&baseData.current){
            const reading=await engine.current.request<BrowserReading>('interpret',{report:baseReport.current,intent},progress(token));
            if(token!==epoch.current)return;
            baseView.current=liveView({...baseReport.current,interpretation:reading},baseData.current);
          }
          publishScoped(dataset.current);return;
        }
        const report = scientific.current as BrowserReport;
        setState(s=>({...s,phase:'running',processingStage:'interpret',progress:'Reading the declared objective; no fit'}));
        const reading = await engine.current.request<BrowserReading>('interpret', { report, intent },progress(token));
        if (token !== epoch.current) return;
        const updated = { ...report, interpretation: reading };
        scientific.current = updated;
        setState(s => ({ ...s, phase:'idle',result: liveView(updated, dataset.current!),processingStage:'report',progress:'' }));
      } catch (error) { failed(token, error); }
    },
    onDeclaration(key, value) { setState(s => ({ ...s, declarations: { ...s.declarations!, [key]: value } })); },
    onExport(format, locale, reading='complete',selection) {
      if (!state.result || !scientific.current) return;
      downloadReport(reportModel(state.result, scientific.current, state.intent, locale, state.declarations,reading,selection,colorGrant.current), format);
    },
  };
  return <App state={state} callbacks={callbacks} />;
}

createRoot(document.getElementById('root')!).render(<Controller />);
