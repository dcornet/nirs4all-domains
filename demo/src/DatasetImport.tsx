import { useState } from 'react';
import { DatasetBuilder, buildExportConfig, type DatasetExportConfig, type DatasetSource } from 'nirs4all-ui/datasetBuilder';
import 'nirs4all-ui/assets/datasetBuilder.css';
import type { DatasetDraft, MetadataDeclaration, ReviewedDatasetConfig } from './engine/import-draft';
import type { MetadataRole } from './engine/types';
import type { Locale } from './ui-types';

export interface DatasetImportProps {
  draft: DatasetDraft; locale?: Locale; busy?: boolean; error?: string | null;
  onConfirm: (config: DatasetExportConfig, sources: DatasetSource[]) => void;
  onCancel: () => void;
}
/** Shared published builder reviews roles; the host confirms this import explicitly. */
export function DatasetImport({ draft, locale = 'en', busy = false, error, onConfirm, onCancel }: DatasetImportProps) {
  const [sources, setSources] = useState(draft.sources);
  const [name, setName] = useState(draft.spec.name || 'Imported dataset');
  const [accepted, setAccepted] = useState(false);
  const [declarations, setDeclarations] = useState<Record<string, MetadataDeclaration>>((draft.spec.metadata_declarations as Record<string,MetadataDeclaration>|undefined)??{});
  const update = (next: DatasetSource[]) => { setAccepted(false); setSources(next); };
  const text = locale === 'fr' ? {
    title: 'Vérifier les rôles X / Y / M', intro: 'Les rôles proposés par IO doivent être vérifiés. Les valeurs restent dans ce navigateur. Cet import ne lance aucune analyse.',
    partitions: 'Partitions déclarées', absent: 'Sans partition déclarée : source descriptive complète. Aucune partition train/test ne sera créée.',
    targets: 'Y est conservé localement et exclu de toutes les requêtes scientifiques F4.0. Les identités partagées sont conservées et ne prouvent pas l’indépendance.',
    confirm: 'Je confirme les rôles, les identifiants de jointure et les partitions affichés.', submit: 'Importer les données vérifiées', cancel: 'Annuler',
    advisory: 'Le panneau partagé peut proposer des options d’apprentissage. Domains conserve X seul et les partitions déclarées ; aucune cible Y n’est obligatoire.',
  } : {
    title: 'Review X / Y / M roles', intro: 'Review the roles proposed by IO. Values stay in this browser. Import does not start an analysis.',
    partitions: 'Declared partitions', absent: 'No declared partition: complete descriptive source. No train/test partition will be generated.',
    targets: 'Y is retained locally and excluded from all F4.0 scientific requests. Shared source identities are preserved and do not prove independence.',
    confirm: 'I confirm the displayed roles, join identifiers and partitions.', submit: 'Import reviewed data', cancel: 'Cancel',
    advisory: 'The shared panel may display training options. Domains supports X alone and preserves declared partitions; no Y target is required.',
  };
  const explicit = Boolean(draft.spec.partitions) || draft.spec.sources.some(source => source.partition) || sources.some(source => source.columns.some(column => column.assignedRole === 'partition'));
  const metadataRoles: MetadataRole[] = ['unknown', 'factor', 'observation_id', 'specimen', 'group', 'reference', 'repetition', 'instrument', 'campaign'];
  const confirm = () => {
    const config: ReviewedDatasetConfig = { ...buildExportConfig(name, sources), metadata_declarations: declarations };
    onConfirm(config, sources);
  };
  return <section aria-label={text.title} className="dataset-import">
    <h2>{text.title}</h2><p>{text.intro}</p><p>{text.targets}</p>
    <p>{text.advisory}</p>
    <h3>{text.partitions}</h3>
    {explicit ? <ul>{sources.map(source => {
      const original = draft.spec.sources.find(item => item.id === source.id);
      const partitionColumn = source.columns.find(column => column.assignedRole === 'partition');
      const use = source.usage.useAs;
      const partition = partitionColumn ? `column: ${partitionColumn.name}` : use === 'x_test' || use === 'y_test' ? 'test'
        : use === 'x_train' || use === 'y_train' ? 'train' : original?.partition || 'unpartitioned';
      return <li key={source.id}>{source.name}: {partition}</li>;
    })}</ul> : <p>{text.absent}</p>}
    {draft.warnings.length > 0 && <ul>{draft.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>}
    <DatasetBuilder sources={sources} onChange={update} autoDetectOnLoad={false} datasetName={name}
      onDatasetNameChange={setName} locale={locale} />
    <details><summary>{locale === 'fr' ? 'Origine et rôles des métadonnées' : 'Metadata origin and roles'}</summary>
      <p>{locale === 'fr' ? 'Déclarer les identités et les variables dérivées de Y. Une origine inconnue reste inconnue.' : 'Declare identities and variables derived from Y. An unknown origin remains unknown.'}</p>
      {sources.flatMap(source => source.columns.filter(column => ['metadata', 'id', 'group', 'replicate'].includes(column.assignedRole)).map(column => {
        const key = `${source.id}__${column.name}`;
        const declaration: MetadataDeclaration = declarations[key] ?? { role: column.assignedRole === 'id' ? 'observation_id' : column.assignedRole === 'group' ? 'group' : column.assignedRole === 'replicate' ? 'repetition' : 'factor', derived_from_target: 'unknown' };
        const change = (next: MetadataDeclaration) => { setAccepted(false); setDeclarations(previous => ({ ...previous, [key]: next })); };
        return <div key={key}><span>{source.name} / {column.name} </span>
          <label>{locale === 'fr' ? 'Rôle ' : 'Role '}<select aria-label={`${column.name} metadata role`} value={declaration.role}
            onChange={event => change({ ...declaration, role: event.target.value as MetadataRole })}>
            {metadataRoles.map(role => <option key={role} value={role}>{role}</option>)}
          </select></label>
          <label>{locale === 'fr' ? ' Dérivée de Y ' : ' Derived from Y '}<select aria-label={`${column.name} derived from Y`} value={String(declaration.derived_from_target)}
            onChange={event => change({ ...declaration, derived_from_target: event.target.value === 'unknown' ? 'unknown' : event.target.value === 'true' })}>
            <option value="unknown">{locale === 'fr' ? 'Inconnu' : 'Unknown'}</option><option value="true">{locale === 'fr' ? 'Oui' : 'Yes'}</option><option value="false">{locale === 'fr' ? 'Non' : 'No'}</option>
          </select></label></div>;
      }))}
    </details>
    {error && <p role="alert">{error}</p>}
    <label><input type="checkbox" checked={accepted} disabled={busy} onChange={event => setAccepted(event.target.checked)} />{text.confirm}</label>
    <div><button type="button" disabled={busy || !accepted} onClick={confirm}>{text.submit}</button>
      <button type="button" onClick={onCancel}>{text.cancel}</button></div>
  </section>;
}
