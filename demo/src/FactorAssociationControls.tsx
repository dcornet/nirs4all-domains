import { useEffect, useRef, useState } from 'react';
import type { Locale } from './ui-types';

export type FactorAssociationPopulation = 'train' | 'unpartitioned' | 'global_transductive';
export type FactorAssociationFactor = {
  id: string;
  label: string;
  kind: 'categorical' | 'continuous' | 'unknown';
  unit: string | null;
  origin: string;
  derivedFromTarget: boolean | 'unknown';
};
export type FactorAssociationRun = {
  factorId: string;
  population: FactorAssociationPopulation;
  correlationMethod: 'pearson' | 'spearman';
  inference: 'descriptive' | 'exact_if_qualified';
  explicitTransductive: boolean;
};

export interface FactorAssociationControlsProps {
  datasetKey: string;
  factors: FactorAssociationFactor[];
  populations: { id: FactorAssociationPopulation; label: string; ready: boolean; reason?: string }[];
  busy: boolean;
  inferenceRecordAvailable: boolean;
  onRun: (request: FactorAssociationRun) => void;
  onColor: (factorId: string) => void;
  exportColorAuthorized: boolean;
  onAuthorizeColorExport: (factorId: string, authorized: boolean) => void;
  locale: Locale;
  unavailablePcaReason?: string | null;
}

const words = {
  en: {
    title: 'Which factors are associated with spectral structure?',
    factor: 'Factor', placeholder: 'Select a factor', kind: 'Type', unit: 'Unit', origin: 'Origin',
    categorical: 'Categorical', continuous: 'Continuous', unknown: 'Unknown', noUnit: 'No unit declared',
    population: 'PCA population', unavailable: 'Unavailable', pcaUnavailable: 'PCA unavailable:',
    method: 'Continuous association measure', pearson: 'Pearson (linear; default)', spearman: 'Spearman (monotone rank)',
    analysis: 'Analysis', descriptive: 'Descriptive only (default)', exact: 'Request exact inference if qualified',
    inferenceHint: 'Inference is conditional on an external design record and has not been independently verified.',
    inferenceMissing: 'No external qualification record is available; inference cannot be requested.',
    transductive: 'I explicitly authorize a separate descriptive analysis on train + test.',
    run: 'Run factor association', color: 'Color PCA by this factor (display only)',
    export: 'Authorize this factor’s observation-level colors in this report export.',
    exportHint: 'Individual membership or value colors can disclose source data; confirm source permission. Select all report sections does not grant this authorization.',
    targetHidden: 'Y-derived fields are excluded from factor choices.',
    pcaReason: 'PCA is unavailable for this population:',
    colorHint: 'Coloring changes the display only. It does not run an analysis.',
  },
  fr: {
    title: 'Quels facteurs sont associés à la structure spectrale ?',
    factor: 'Facteur', placeholder: 'Sélectionner un facteur', kind: 'Type', unit: 'Unité', origin: 'Origine',
    categorical: 'Catégoriel', continuous: 'Continu', unknown: 'Inconnu', noUnit: 'Aucune unité déclarée',
    population: 'Population de l’ACP', unavailable: 'Indisponible', pcaUnavailable: 'ACP indisponible :',
    method: 'Mesure d’association continue', pearson: 'Pearson (linéaire ; par défaut)', spearman: 'Spearman (rangs monotones)',
    analysis: 'Analyse', descriptive: 'Descriptive uniquement (par défaut)', exact: 'Demander une inférence exacte si qualifiée',
    inferenceHint: 'L’inférence dépend d’un dossier de plan externe et n’a pas été vérifiée de façon indépendante.',
    inferenceMissing: 'Aucun dossier externe de qualification ; l’inférence ne peut pas être demandée.',
    transductive: 'J’autorise explicitement une analyse descriptive distincte sur train + test.',
    run: 'Calculer l’association du facteur', color: 'Colorer l’ACP par ce facteur (affichage uniquement)',
    export: 'Autoriser les couleurs par observation de ce facteur dans cet export.',
    exportHint: 'Les couleurs de membres ou de valeurs individuelles peuvent divulguer des données source ; confirmez les droits. Tout sélectionner dans le rapport ne donne pas cette autorisation.',
    targetHidden: 'Les champs dérivés de Y sont exclus des choix de facteurs.',
    pcaReason: 'ACP indisponible pour cette population :',
    colorHint: 'La couleur modifie uniquement l’affichage. Elle ne lance aucune analyse.',
  },
} as const;

const supported = (factor: FactorAssociationFactor) => factor.kind !== 'unknown' && factor.derivedFromTarget !== true;

export function FactorAssociationControls({
  datasetKey, factors, populations, busy, inferenceRecordAvailable, onRun, onColor,
  exportColorAuthorized, onAuthorizeColorExport, locale, unavailablePcaReason,
}: FactorAssociationControlsProps) {
  const t = words[locale];
  const eligibleFactors = factors.filter(supported);
  const [factorId, setFactorId] = useState('');
  const [population, setPopulation] = useState<FactorAssociationPopulation>(() =>
    populations.find(p => p.id === 'train')?.id ?? populations.find(p => p.id === 'unpartitioned')?.id ?? 'train');
  const [method, setMethod] = useState<'pearson' | 'spearman'>('pearson');
  const [inference, setInference] = useState<'descriptive' | 'exact_if_qualified'>('descriptive');
  const [globalConsent, setGlobalConsent] = useState(false);
  const authorizedFactor = useRef<string | null>(null);
  const priorDataset = useRef(datasetKey);

  useEffect(() => {
    if (priorDataset.current === datasetKey) return;
    if (authorizedFactor.current) onAuthorizeColorExport(authorizedFactor.current, false);
    authorizedFactor.current = null;
    priorDataset.current = datasetKey;
    setFactorId('');
    setPopulation(populations.find(p => p.id === 'train')?.id ?? populations.find(p => p.id === 'unpartitioned')?.id ?? 'train');
    setMethod('pearson');
    setInference('descriptive');
    setGlobalConsent(false);
  }, [datasetKey, populations, onAuthorizeColorExport]);

  const selectedFactor = eligibleFactors.find(f => f.id === factorId);
  const selectedPopulation = populations.find(p => p.id === population);
  const ready = !!selectedFactor && !!selectedPopulation?.ready && !busy && !(population === 'global_transductive' && !globalConsent);
  const changeFactor = (next: string) => {
    if (authorizedFactor.current && authorizedFactor.current !== next) onAuthorizeColorExport(authorizedFactor.current, false);
    authorizedFactor.current = null;
    setFactorId(next);
  };
  const changeExportAuthorization = (authorized: boolean) => {
    if (!selectedFactor) return;
    authorizedFactor.current = authorized ? selectedFactor.id : null;
    onAuthorizeColorExport(selectedFactor.id, authorized);
  };

  return <section className="factor-association-controls" aria-labelledby="factor-association-title">
    <h2 id="factor-association-title">{t.title}</h2>
    <p>{t.targetHidden}</p>
    <label>{t.factor}
      <select aria-label={t.factor} value={factorId} disabled={busy} onChange={event => changeFactor(event.target.value)}>
        <option value="">{t.placeholder}</option>
        {eligibleFactors.map(f => <option key={f.id} value={f.id}>{f.label} · {t[f.kind]} · {f.unit ?? t.noUnit} · {f.origin}</option>)}
      </select>
    </label>
    {selectedFactor && <dl className="factor-association-metadata">
      <div><dt>{t.kind}</dt><dd>{t[selectedFactor.kind]}</dd></div>
      <div><dt>{t.unit}</dt><dd>{selectedFactor.unit ?? t.noUnit}</dd></div>
      <div><dt>{t.origin}</dt><dd>{selectedFactor.origin}</dd></div>
    </dl>}
    <label>{t.population}
      <select aria-label={t.population} value={population} disabled={busy} onChange={event => setPopulation(event.target.value as FactorAssociationPopulation)}>
        {populations.map(p => <option key={p.id} value={p.id} disabled={!p.ready}>{p.label}{p.ready ? '' : ` · ${t.unavailable}`}</option>)}
      </select>
    </label>
    {selectedPopulation && !selectedPopulation.ready && <p className="notice">{unavailablePcaReason ? `${t.pcaReason} ${unavailablePcaReason}` : selectedPopulation.reason ?? t.unavailable}</p>}
    <label>{t.method}
      <select aria-label={t.method} value={method} disabled={busy || selectedFactor?.kind !== 'continuous'} onChange={event => setMethod(event.target.value as 'pearson' | 'spearman')}>
        <option value="pearson">{t.pearson}</option><option value="spearman">{t.spearman}</option>
      </select>
    </label>
    <fieldset>
      <legend>{t.analysis}</legend>
      <label><input type="radio" name={`factor-inference-${datasetKey}`} value="descriptive" checked={inference === 'descriptive'} disabled={busy} onChange={() => setInference('descriptive')} /> {t.descriptive}</label>
      {inferenceRecordAvailable
        ? <label><input type="radio" name={`factor-inference-${datasetKey}`} value="exact_if_qualified" checked={inference === 'exact_if_qualified'} disabled={busy} onChange={() => setInference('exact_if_qualified')} /> {t.exact}</label>
        : <p>{t.inferenceMissing}</p>}
      <p>{t.inferenceHint}</p>
    </fieldset>
    {population === 'global_transductive' && <label><input type="checkbox" checked={globalConsent} disabled={busy} onChange={event => setGlobalConsent(event.target.checked)} /> {t.transductive}</label>}
    <button type="button" className="button secondary" disabled={!ready} onClick={() => selectedFactor && selectedPopulation && onRun({
      factorId: selectedFactor.id, population, correlationMethod: method, inference,
      explicitTransductive: population === 'global_transductive' && globalConsent,
    })}>{t.run}</button>
    <section className="factor-association-color" aria-label={t.color}>
      <button type="button" className="button secondary" disabled={!selectedFactor || busy} onClick={() => selectedFactor && onColor(selectedFactor.id)}>{t.color}</button>
      <p>{t.colorHint}</p>
      {selectedFactor && <label><input type="checkbox" checked={exportColorAuthorized && authorizedFactor.current === selectedFactor.id} disabled={busy} onChange={event => changeExportAuthorization(event.target.checked)} /> {t.export}</label>}
      <p>{t.exportHint}</p>
    </section>
  </section>;
}
