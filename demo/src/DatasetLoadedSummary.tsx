import type { ImportSummary } from './engine/one-shot';
import type { Locale } from './ui-types';

export function DatasetLoadedSummary({ summary, locale }: { summary: ImportSummary; locale: Locale }) {
  const fr = locale === 'fr';
  const count = (value: number) => value.toLocaleString(locale);
  return <section className="dataset-loaded-summary" aria-labelledby="dataset-loaded-title">
    <h2 id="dataset-loaded-title">{fr ? 'Dataset chargé' : 'Dataset loaded'}</h2>
    <dl className="import-summary-facts">
      <div><dt>{fr ? 'Observations' : 'Observations'}</dt><dd>{count(summary.observations)}</dd></div>
      <div><dt>{fr ? 'Variables spectrales' : 'Spectral variables'}</dt><dd>{count(summary.variables)}</dd></div>
      <div><dt>{fr ? 'Cibles Y' : 'Y targets'}</dt><dd>{count(summary.targets.length)}</dd></div>
      <div><dt>{fr ? 'Facteurs M' : 'M factors'}</dt><dd>{count(summary.metadata.length)}</dd></div>
      {summary.partitions.map(partition => <div key={partition.name}><dt>{partition.name}</dt><dd>{count(partition.rows)}</dd></div>)}
    </dl>
    <p>{fr ? 'Correspondances' : 'Alignment'}: {summary.alignment === 'validated' ? (fr ? 'validées par IO' : 'validated by IO') : (fr ? 'restrictions identifiées' : 'restrictions identified')} · {fr ? 'Sources non résolues' : 'Unresolved sources'}: {summary.unresolved_sources}</p>
    <p>{fr ? 'Valeurs X manquantes' : 'Missing X values'}: {count(summary.missing_x)}</p>
    <details><summary>{fr ? 'Cibles, métadonnées et valeurs manquantes' : 'Targets, metadata and missing values'}</summary>
      <ul>{summary.targets.map(target => <li key={target.name}>Y · {target.name} · {target.type} · {fr ? 'manquantes' : 'missing'}: {count(target.missing)} / {count(target.rows)}</li>)}
        {summary.metadata.map(column => <li key={column.name}>M · {column.name} · {fr ? 'manquantes' : 'missing'}: {count(column.missing)} / {count(column.rows)}</li>)}</ul>
    </details>
    <p className="import-boundary">{fr ? 'Le chargement valide la structure technique des données. Les opérations admissibles restent contrôlées séparément ; aucune indépendance physique n’est établie.' : 'Loading validates the technical data structure. Admitted operations remain separately controlled; physical independence is not established.'}</p>
  </section>;
}
