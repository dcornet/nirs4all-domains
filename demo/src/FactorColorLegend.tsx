import type { Locale } from './ui-types';
import type { FactorColorLegendDescriptor } from './report/factor-colors';

export interface FactorColorLegendProps {
  legend: FactorColorLegendDescriptor;
  locale: Locale;
}

const copy = {
  en: { missing: 'Missing', display: 'Display only; this is not a risk score.', range: 'Color scale', from: 'Minimum', to: 'Maximum', categorical: 'Factor color legend', continuous: 'Continuous factor color scale' },
  fr: { missing: 'Manquant', display: 'Affichage uniquement ; ce n’est pas un score de risque.', range: 'Échelle de couleur', from: 'Minimum', to: 'Maximum', categorical: 'Légende des couleurs du facteur', continuous: 'Échelle de couleur du facteur continu' },
} as const;

export function FactorColorLegend({ legend, locale }: FactorColorLegendProps) {
  const t = copy[locale];
  const number = (value: number) => new Intl.NumberFormat(locale, { maximumSignificantDigits: 6 }).format(value);
  return <section className="factor-color-legend" aria-label={legend.kind === 'categorical' ? t.categorical : t.continuous}>
    {legend.kind === 'categorical' ? <ul className="factor-color-levels">
      {legend.levels.map(level => <li key={level.level_id}>
        <span aria-hidden="true" className="factor-color-swatch" style={{ backgroundColor: level.color }} />
        <span>{level.label}</span> <span>({number(level.count)})</span>
      </li>)}
    </ul> : <div className="factor-color-continuous">
      <span>{t.range}{legend.unit ? ` · ${legend.unit}` : ''}</span>
      <div className="factor-color-gradient" role="img" aria-label={`${t.from} ${legend.domain ? number(legend.domain.min) : ''}; ${t.to} ${legend.domain ? number(legend.domain.max) : ''}`} style={{ background: 'linear-gradient(to right, #2563eb, #0f766e)' }} />
      <div className="factor-color-endpoints"><span>{legend.domain ? number(legend.domain.min) : '—'}</span><span>{legend.domain ? number(legend.domain.max) : '—'}</span></div>
    </div>}
    <p><span aria-hidden="true" className="factor-color-swatch" style={{ backgroundColor: legend.missing_color }} /> {t.missing} ({number(legend.missing_count)})</p>
    <p>{t.display}</p>
  </section>;
}
