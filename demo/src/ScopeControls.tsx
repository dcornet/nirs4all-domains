import { useState } from 'react';
import type { ScopedOperation } from '../../bindings/wasm/scoped';
import type { Locale, UiResult } from './ui-types';

type SelectionContext = 'pre_selection_integrity_audit' | 'post_evaluation_explanation' | 'unspecified';
type OperationOptions = {
  diagnostic?: 'exact_spectra' | 'declared_identities';
  explicit_transductive?: boolean;
  selection_context?: SelectionContext;
};

export interface ScopeControlsProps {
  result: UiResult;
  locale: Locale;
  busy: boolean;
  hideInventory?: boolean;
  onOperation: (operation: ScopedOperation, options?: OperationOptions) => void;
  onColor?: (field: string) => void;
}

type Inventory = {
  loaded: {
    x: { rows: number; variables: number };
    y: { name: string; unit: string | null; type: string; rows: number; missing: number }[];
    metadata: { name: string; role: string; kind: string; origin: string; derived_from_target: boolean | 'unknown'; evidence: string; rows: number; missing: number }[];
    partitions: { name: string; rows: number }[];
  };
};

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function inventoryOf(result: UiResult): Inventory | null {
  const candidate = result.provenance.scoped_inventory;
  if (!object(candidate) || !object(candidate.loaded)) return null;
  const loaded = candidate.loaded;
  if (!object(loaded.x) || !Array.isArray(loaded.y) || !Array.isArray(loaded.metadata) || !Array.isArray(loaded.partitions)) return null;
  const x = loaded.x;
  if (typeof x.rows !== 'number' || typeof x.variables !== 'number') return null;
  const partitions = loaded.partitions.filter((p): p is Inventory['loaded']['partitions'][number] =>
    object(p) && typeof p.name === 'string' && typeof p.rows === 'number');
  const metadata = loaded.metadata.filter((m): m is Inventory['loaded']['metadata'][number] =>
    object(m) && typeof m.name === 'string' && typeof m.role === 'string' && typeof m.kind === 'string' &&
    typeof m.origin === 'string' && typeof m.evidence === 'string' && typeof m.rows === 'number' &&
    typeof m.missing === 'number' && (typeof m.derived_from_target === 'boolean' || m.derived_from_target === 'unknown'));
  const y = loaded.y.filter((field): field is Inventory['loaded']['y'][number] =>
    object(field) && typeof field.name === 'string' && (typeof field.unit === 'string' || field.unit === null) &&
    typeof field.type === 'string' && typeof field.rows === 'number' && typeof field.missing === 'number');
  return { loaded: { x: { rows: x.rows, variables: x.variables }, y, metadata, partitions } };
}

const copy = {
  en: {
    title: 'Scoped analysis', inventory: 'Loaded inventory', x: 'X', y: 'Y target fields', m: 'M metadata fields', variables: 'variables', rows: 'rows', missing: 'missing',
    partition: 'Partition', role: 'role', actions: 'Available operations', train: 'Train structure', exact: 'Exact spectra train/test audit', identities: 'Identity audit (no X)', factors: 'Train M factors', cross: 'Cross-partition M audit', support: 'Raw support: train reference → test query',
    context: 'Timing context', unspecified: 'Unspecified', before: 'Before selection: integrity audit', after: 'After evaluation: explanation',
    globalConsent: 'I explicitly authorize a descriptive fit on train + test; prediction rows remain excluded.', global: 'Global descriptive analysis',
    boundary: 'Test X can be audited. A train-reference PCA fits train alone; the separate global action fits train + test transductively. Inspecting test X can influence decisions even when no Y values are used.',
    color: 'Color PCA display by M field', noColor: 'Choose a metadata field', colorNote: 'Color is display only, not a statistical test. Unknown origin limits interpretation.',
  },
  fr: {
    title: 'Analyse à périmètre défini', inventory: 'Inventaire chargé', x: 'X', y: 'Champs cibles Y', m: 'Champs de métadonnées M', variables: 'variables', rows: 'lignes', missing: 'manquantes',
    partition: 'Partition', role: 'rôle', actions: 'Opérations disponibles', train: 'Structure de train', exact: 'Audit exact des spectres train/test', identities: 'Audit des identités (sans X)', factors: 'Facteurs M de train', cross: 'Audit M entre partitions', support: 'Support brut : référence train → requête test',
    context: 'Contexte temporel', unspecified: 'Non précisé', before: 'Avant sélection : audit d’intégrité', after: 'Après évaluation : explication',
    globalConsent: 'J’autorise explicitement un ajustement descriptif sur train + test ; les lignes de prédiction restent exclues.', global: 'Analyse descriptive globale',
    boundary: 'X de test peut être audité. Une ACP de référence est ajustée sur train seul ; l’action globale distincte ajuste train + test de façon transductive. Consulter X de test peut influencer les décisions même sans utiliser Y.',
    color: 'Colorer l’affichage PCA par un champ M', noColor: 'Choisir un champ de métadonnées', colorNote: 'La couleur est uniquement visuelle, ce n’est pas un test statistique. Une origine inconnue limite l’interprétation.',
  },
} as const;

function InventoryMarkup({inventory,locale}:{inventory:Inventory;locale:Locale}) {
  const t=copy[locale];
  const cells=locale==='fr'?'cellules':'cells';
  return <section aria-labelledby="scope-inventory-title">
    <h3 id="scope-inventory-title">{t.inventory}</h3>
    <ul>
      <li>{t.x}: {inventory.loaded.x.rows} {t.rows}, {inventory.loaded.x.variables} {t.variables}</li>
      <li>{t.y}: {inventory.loaded.y.length} ({inventory.loaded.y.reduce((n, field) => n + field.rows, 0)} {cells})</li>
      <li>{t.m}: {inventory.loaded.metadata.length} ({inventory.loaded.metadata.reduce((n, field) => n + field.rows, 0)} {cells})</li>
    </ul>
    <ul aria-label={t.partition}>
      {inventory.loaded.partitions.map(partition => <li key={partition.name}>{partition.name}: {partition.rows} {t.rows} · {t.role}: {partition.name}</li>)}
    </ul>
    {inventory.loaded.y.map(field => <p key={`y-${field.name}`}>{field.name}: {field.type}, {field.rows} {t.rows}, {field.missing} {t.missing}</p>)}
    {inventory.loaded.metadata.map(field => <p key={`m-${field.name}`}>{field.name}: {field.role}, {field.kind}, {field.origin}, {field.evidence}; {field.rows} {t.rows}, {field.missing} {t.missing}</p>)}
  </section>;
}

export function ScopeInventory({result,locale}:{result:UiResult;locale:Locale}) {
  const inventory=inventoryOf(result);
  if(!inventory)return null;
  return <section className="scope-inventory" aria-labelledby="scope-inventory-region-title">
    <h3 id="scope-inventory-region-title">{copy[locale].inventory}</h3>
    <InventoryMarkup inventory={inventory} locale={locale}/>
  </section>;
}

export function ScopeControls({ result, locale, busy, onOperation, onColor, hideInventory=false }: ScopeControlsProps) {
  const inventory = inventoryOf(result);
  const [context, setContext] = useState<SelectionContext>('unspecified');
  const [allowGlobal, setAllowGlobal] = useState(false);
  const [colorField, setColorField] = useState('');
  if (!inventory) return null;
  const t = copy[locale];
  const operationOptions: OperationOptions = { selection_context: context };
  const factors = inventory.loaded.metadata.filter(field => field.derived_from_target !== true);
  const action = (operation: ScopedOperation, extra: OperationOptions = {}) => onOperation(operation, { ...operationOptions, ...extra });

  return <section className="scope-controls" aria-labelledby="scope-controls-title">
    <h2 id="scope-controls-title">{t.title}</h2>
    {!hideInventory&&<InventoryMarkup inventory={inventory} locale={locale}/>}

    <label>{t.context}
      <select value={context} disabled={busy} onChange={event => setContext(event.target.value as SelectionContext)}>
        <option value="unspecified">{t.unspecified}</option>
        <option value="pre_selection_integrity_audit">{t.before}</option>
        <option value="post_evaluation_explanation">{t.after}</option>
      </select>
    </label>
    <p>{t.boundary}</p>
    <section aria-labelledby="scope-actions-title">
      <h3 id="scope-actions-title">{t.actions}</h3>
      <button type="button" disabled={busy} onClick={() => action('train_structure')}>{t.train}</button>
      <button type="button" disabled={busy} onClick={() => action('integrity_audit', { diagnostic: 'exact_spectra' })}>{t.exact}</button>
      <button type="button" disabled={busy} onClick={() => action('integrity_audit', { diagnostic: 'declared_identities' })}>{t.identities}</button>
      <button type="button" disabled={busy} onClick={() => action('metadata_factor_audit')}>{t.factors}</button>
      <button type="button" disabled={busy} onClick={() => action('cross_partition_metadata_audit')}>{t.cross}</button>
      <button type="button" disabled={busy} onClick={() => action('train_reference_test_query')}>{t.support}</button>
    </section>
    <fieldset>
      <legend>{t.global}</legend>
      <label><input type="checkbox" checked={allowGlobal} disabled={busy} onChange={event => setAllowGlobal(event.target.checked)} /> {t.globalConsent}</label>
      <button type="button" disabled={busy || !allowGlobal} onClick={() => action('global_descriptive_transductive', { explicit_transductive: true })}>{t.global}</button>
    </fieldset>
    <section aria-label={t.color}>
      <label>{t.color}
        <select value={colorField} disabled={busy || !onColor || !result.pca} onChange={event => { const field = event.target.value; setColorField(field); onColor?.(field); }}>
          <option value="">{t.noColor}</option>
          {factors.map(field => <option key={field.name} value={field.name}>{field.name}{field.origin === 'unknown' || field.derived_from_target === 'unknown' ? ' · unknown origin' : ''}</option>)}
        </select>
      </label>
      <p>{t.colorNote}</p>
    </section>
  </section>;
}
