import { describe, expect, it } from 'vitest';
import { reportModel, savedView } from './model';
import { serializeReport } from './export';
import { validateSaved } from './saved';
import source from '../../public/examples/tablet.unknown.saved.json';

describe('Single semantic model and original saved evidence', () => {
  it('validates the original public schema and preserves every supplied companion', () => {
    validateSaved(source); const before = JSON.stringify(source);
    const view = savedView(source), report = reportModel(view, source, 'unknown', 'en');
    expect(report.scientific_report).toBe(source); expect(JSON.stringify(source)).toBe(before);
    expect(report.dataset.variables).toBeNull(); expect(report.provenance.independent_original_study_count).toBeNull();
    expect(report.source_mode).toBe('saved_qualified_report');
    expect(view.findings.find(f => f.id === 'preprocessing_dependent_organization')?.status).toBe('observed');
  });
  it('excludes display X from JSON and renders HTML/Markdown from exactly the same object', () => {
    const view = savedView(source); view.dataset.spectra = [{ id: 'display-only', values: [12345,67890] }];
    const report = reportModel(view, source, 'unknown', 'en');
    const json = serializeReport(report, 'json');
    expect(JSON.parse(json)).toEqual(report); expect(json).not.toContain('display-only');
    expect(serializeReport(report, 'html')).toContain(report.dataset.contentHash);
    expect(serializeReport(report, 'markdown')).toContain(report.dataset.contentHash);
    expect(report.raw_x_included).toBe(false); expect(report.numerical_evidence_recomputed_for_export).toBe(false);
  });
  it('escapes malicious source text without script, network dependency or private filesystem paths', () => {
    const view = savedView(source); view.dataset.name = '<script>globalThis.compromised=true</script>';
    view.findings[0].observation = '<img src=x onerror=alert(1)>';
    const report = reportModel(view, source, 'new_context', 'fr', { population: 'future population', prediction_unit: 'specimen', new_context: '' });
    const html = serializeReport(report, 'html');
    expect(html).not.toContain('<script>'); expect(html).not.toContain('<img src=x');
    expect(html).toContain('&lt;script&gt;'); expect(html).toContain("default-src 'none'");
    expect(html).toContain('lang="fr"'); expect(html).toContain('Comprendre les données');
    expect(report.user_declarations.population).toBe('future population');
    expect(report.user_declarations.new_context).toBeNull();
  });
  it('refuses malformed or incomplete saved reports rather than deriving missing scientific states', () => {
    expect(() => validateSaved({ protocol_version: source.protocol_version, cases: [] })).toThrow();
  });
});
