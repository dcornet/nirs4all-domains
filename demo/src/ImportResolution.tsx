import { useEffect, useState } from 'react';
import { type DatasetSource, type DatasetExportConfig, type DatasetRole } from 'nirs4all-ui/datasetBuilder';
import type { ImportSession } from './engine/one-shot';
import type { Locale } from './ui-types';
import { DatasetImport, editedImportConfig } from './DatasetImport';

/** Displays only runtime-reported questions. All answers are revalidated by IO. */
export function ImportResolution({ session, locale, busy, onConfirm, onDismiss }: {
  session: ImportSession; locale: Locale; busy: boolean;
  onConfirm: (config: DatasetExportConfig, sources: DatasetSource[]) => void; onDismiss: () => void;
}) {
  const fr = locale === 'fr';
  const [sources, setSources] = useState(session.sources);
  useEffect(() => { setSources(session.sources); }, [session]);
  const update = (id: string, change: (source: DatasetSource) => DatasetSource) => setSources(previous => previous.map(source => source.id === id ? change(source) : source));
  const chooseRole = (source: DatasetSource, role: DatasetRole): DatasetSource => ({ ...source, columns: source.columns.map(column => {
    const original = session.sources.find(item => item.id === source.id)?.columns.find(item => item.id === column.id);
    const identity = original && ['id','group','replicate','partition'].includes(original.assignedRole) ? original.assignedRole : undefined;
    return { ...column, assignedRole: role === 'ignored' ? role : identity ?? role, manual: true };
  }) });
  const chooseColumn = (source: DatasetSource, name: string, role: DatasetRole): DatasetSource => ({ ...source, columns: source.columns.map(column => ({ ...column, assignedRole: column.name === name ? role : role === 'id' && column.assignedRole === role ? 'metadata' : column.assignedRole, manual: column.name === name || column.manual })) });
  if(session.issues.length === 0) return <section className="container import-resolution" aria-labelledby="import-settings-title">
    <h2 id="import-settings-title">{fr ? 'Paramètres d’import des données' : 'Data import settings'}</h2>
    <p>{fr ? 'Vous avez demandé les paramètres avancés avant le chargement. Les sources identifiées par IO sont préremplies ; appliquer les modifications lance la validation et l’assemblage.' : 'You requested advanced settings before loading. Sources identified by IO are prefilled; applying changes runs validation and assembly.'}</p>
    <DatasetImport draft={session.draft} initialSources={session.sources} initialConfig={session.config} locale={locale} busy={busy} onConfirm={onConfirm} onCancel={onDismiss}/>
  </section>;
  return <section className="container import-resolution" aria-labelledby="import-resolution-title">
    <h2 id="import-resolution-title">{fr ? 'Préciser le chargement' : 'Complete dataset loading'}</h2>
    <p>{fr ? 'Répondez aux seules questions signalées par IO. Les autres paramètres sont conservés.' : 'Answer the questions reported by IO. Other settings are preserved.'}</p>
    <fieldset disabled={busy}>
      <legend className="visually-hidden">{fr ? 'Corrections nécessaires' : 'Required corrections'}</legend>
      {session.issues.map((issue, index) => <div className="import-issue" key={`${issue.code}:${issue.source_id ?? ''}:${index}`}>
        <p role={issue.blocking ? 'alert' : 'status'}><code>{issue.code}</code> · {issue.message}</p>
        {sources.filter(source => !issue.source_id || source.id === issue.source_id).map(source => <div className="import-correction" key={source.id}>
          {issue.kind === 'source_role' && <label>{source.name} · {fr ? 'Rôle de la source' : 'Source role'}<select value={source.columns.every(column => column.assignedRole === 'ignored') ? 'ignored' : source.columns.some(column => column.assignedRole === 'x') ? 'x' : source.columns.some(column => column.assignedRole === 'y') ? 'y' : 'metadata'} onChange={event => update(source.id, current => chooseRole(current, event.target.value as DatasetRole))}>
            <option value="x">X</option><option value="y">Y</option><option value="metadata">M</option><option value="ignored">{fr ? 'Conserver séparément' : 'Keep source separate'}</option>
          </select></label>}
          {issue.kind === 'target' && source.columns.filter(column => column.assignedRole === 'y' && (!issue.column || column.name === issue.column)).map(column => <label key={column.id}>{column.name} · {fr ? 'Type de cible' : 'Target type'}<select value={column.semanticType === 'classification' || column.semanticType === 'regression' ? column.semanticType : ''} onChange={event => update(source.id, current => ({ ...current, columns: current.columns.map(item => item.id === column.id ? { ...item, semanticType: event.target.value as 'regression' | 'classification', manual: true } : item) }))}>
            <option value="">{fr ? 'Choisir un type' : 'Choose a type'}</option><option value="regression">{fr ? 'Régression' : 'Regression'}</option><option value="classification">Classification</option>
          </select></label>)}
          {(issue.kind === 'join_key' || issue.kind === 'target') && <label>{source.name} · {issue.kind === 'join_key' ? (fr ? 'Identifiant de jointure' : 'Join key') : (fr ? 'Colonne cible' : 'Target column')}<select value={source.columns.find(column => column.assignedRole === (issue.kind === 'join_key' ? 'id' : 'y'))?.name ?? ''} onChange={event => update(source.id, current => chooseColumn(current, event.target.value, issue.kind === 'join_key' ? 'id' : 'y'))}>
            <option value="">{fr ? 'Choisir une colonne' : 'Choose a column'}</option>{source.columns.map(column => <option value={column.name} key={column.id}>{column.name}</option>)}
          </select></label>}
          {issue.kind === 'partition' && <label>{source.name} · Partition<select value={source.usage.useAs ?? ''} onChange={event => update(source.id, current => ({ ...current, usage: { ...current.usage, useAs: event.target.value as DatasetSource['usage']['useAs'] } }))}>
            <option value="">{fr ? 'Choisir une partition' : 'Choose a partition'}</option><option value="x_train">X · train</option><option value="x_test">X · test</option><option value="y_train">Y · train</option><option value="y_test">Y · test</option><option value="x_train_test">{fr ? 'Sans partition X déclarée' : 'No declared X partition'}</option><option value="metadata">M</option>
          </select></label>}
          {issue.kind === 'delimiter' && <label>{source.name} · {fr ? 'Séparateur' : 'Delimiter'}<select value={source.parsing.separator ?? ''} onChange={event => update(source.id, current => ({ ...current, parsing: { ...current.parsing, separator: event.target.value } }))}>
            <option value="">{fr ? 'Choisir un séparateur' : 'Choose a delimiter'}</option><option value=",">{fr ? 'Virgule' : 'Comma'} (,)</option><option value=";">{fr ? 'Point-virgule' : 'Semicolon'} (;)</option><option value={'\t'}>{fr ? 'Tabulation' : 'Tab'}</option><option value=" ">{fr ? 'Espace' : 'Space'}</option><option value="|">|</option>
          </select></label>}
        </div>)}
        {issue.kind === 'advanced' && <p>{fr ? 'Consultez les paramètres avancés ci-dessous pour corriger ce constat.' : 'Open advanced settings below to correct this issue.'}</p>}
      </div>)}
      <button className="button primary" onClick={() => onConfirm(editedImportConfig(session.config.name, sources, session.config, session.sources), sources)}>{fr ? 'Appliquer les corrections' : 'Apply corrections'}</button>
    </fieldset>
    <button className="text-button" onClick={onDismiss}>{fr ? 'Fermer les corrections' : 'Dismiss corrections'}</button>
    <details className="data-settings"><summary>{fr ? 'Paramètres avancés' : 'Advanced settings'}</summary><DatasetImport key={JSON.stringify(sources)} draft={session.draft} initialSources={sources} initialConfig={session.config} locale={locale} busy={busy} onConfirm={onConfirm} onCancel={onDismiss}/></details>
  </section>;
}
