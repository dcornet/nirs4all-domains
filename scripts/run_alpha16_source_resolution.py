"""Bounded original-reference resolution. No target-cell decoding or real fits."""
import argparse
import ast
import csv
import io
from pathlib import Path
import re
import zipfile

from alpha16_common import Context, read
from nirs4all_domains.confrontation import admit
from nirs4all_domains.original_source import manifest_file, manifest_locator
from nirs4all_domains.storage import digest, fingerprint


def manifest_rows(text):
    first = text.splitlines()[0]
    return list(csv.DictReader(io.StringIO(text), delimiter=';' if first.count(';') > first.count(',') else ','))


def driver_path(source, filename):
    """Evaluate only the generated Path(__file__).resolve().parents[k]/literal."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not any(isinstance(t, ast.Name) and t.id == 'root_script' for t in node.targets):
            continue
        expr = node.value
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Div) and isinstance(expr.right, ast.Constant) and isinstance(expr.right.value, str):
            base = expr.left
            if isinstance(base, ast.Subscript) and isinstance(base.value, ast.Attribute) and base.value.attr == 'parents' and isinstance(base.slice, ast.Constant) and isinstance(base.slice.value, int):
                if ast.unparse(base.value.value) == 'Path(__file__).resolve()':
                    return Path(filename).resolve().parents[base.slice.value]/expr.right.value
    return None


def inspect_locators(context, identity):
    directory = Path(context.cfg['source_root'])/identity
    files = [directory/x for x in ['source_to_standard.py', 'raw_manifest.csv', 'conversion_report.md',
        'dataset_card.json', 'datapackage.json'] if (directory/x).is_file()]
    context.participate(files)
    value = {'dataset_id': identity, 'documents': {}, 'driver_links': [], 'target_cells_decoded': 0}
    for path in files:
        text = path.read_text(encoding='utf-8-sig')
        value['documents'][path.name] = {'path': str(path), 'sha256': digest(path), 'text': text}
        if path.suffix == '.py':
            link = driver_path(text, path)
            if link is not None and link.is_file():
                context.participate([link])
                value['driver_links'].append({'path': str(link), 'sha256': digest(link), 'text': link.read_text(encoding='utf-8-sig')})
    return value


def inspect_original(path):
    item = {'path': str(path), 'sha256': digest(path), 'bytes': path.stat().st_size}
    if path.suffix.lower() == '.mat':
        from scipy.io import whosmat
        try:
            item['schema'] = [{'name': n, 'shape': list(shape), 'storage_class': kind} for n, shape, kind in whosmat(path)]
            item['scope'] = 'top_level_variable_schema_only_no_mixed_object_load'
        except Exception:
            item['scope'] = 'qualified_selective_reader_required'
    elif zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            item['members'] = [{'name': m.filename, 'bytes': m.file_size} for m in archive.infolist()]
        item['scope'] = 'member_metadata_only_no_target_extraction'
    elif path.suffix.lower() in ['.csv', '.tsv', '.txt']:
        with path.open(encoding='utf-8-sig') as stream:
            first = stream.readline()
        separator = '\t' if '\t' in first else ';' if first.count(';') > first.count(',') else ','
        item['columns'] = next(csv.reader([first], delimiter=separator))
        item['scope'] = 'header_only_no_target_cells'
    else:
        item['scope'] = 'bytes_bound_no_unqualified_structured_decode'
    return item


def resolve_candidate(context, identity, locators, prior=None):
    """Resolve only declared originals; retain precise evidence and stopping requests."""
    directory = Path(context.cfg['source_root'])/identity
    roots = [Path(context.cfg['source_root']).parent]
    manifest = locators['documents'].get('raw_manifest.csv')
    rows = manifest_rows(manifest['text']) if manifest else []
    record = {'dataset_id': identity, 'prior_receipt': fingerprint(prior) if prior else None,
        'documents': [{'name': n, 'path': v['path'], 'sha256': v['sha256']} for n, v in locators['documents'].items()],
        'original_bindings': [], 'driver_resolution': [], 'canonical_identity_projection': {},
        'target_cells_decoded': 0, 'retained_Y_accessed': False, 'supervised_fits': 0}
    for doc in locators['documents'].values():
        if doc['path'].endswith('.py'):
            path = driver_path(doc['text'], doc['path'])
            record['driver_resolution'].append({'declared_path': str(path) if path is not None else None,
                'exists': bool(path and path.is_file()), 'executed': False})
    for row in rows:
        if row.get('used_for_conversion', '').lower() != 'yes' or row.get('file_role') != 'raw_data':
            continue
        item = {'manifest_row': row, 'original_manifest_receipt': manifest['sha256']}
        try:
            # Bound full files before hashing or projecting any original content.
            declared, _ = manifest_locator(row, identity, roots)
            context.participate([declared])
            path = manifest_file(row, identity, roots)
            context.participate([path])
            item.update(status='bound', inspection=inspect_original(path))
        except (ValueError, OSError) as exc:
            item.update(status='unavailable', reason=str(exc))
        record['original_bindings'].append(item)
    # Identity-only canonical metadata projection. No source values become assay evidence.
    metadata = directory/'M.csv'
    if metadata.is_file():
        context.participate([metadata])
        with metadata.open(encoding='utf-8-sig') as stream:
            first = stream.readline()
        separator = ';' if first.count(';') > first.count(',') else ','
        fields = next(csv.reader([first], delimiter=separator))
        identity_fields = [f for f in fields if f in ['observation_id', 'sample_id', 'source_sample_id',
            'physical_sample_id', 'reference_id', 'assay_event_id', 'reference_batch_id', 'batch_id',
            'donor_id', 'partition', 'split', 'validation_component_id']]
        import pandas as pd
        table = pd.read_csv(metadata, sep=separator, usecols=identity_fields, dtype=str, keep_default_na=False) if identity_fields else None
        record['canonical_identity_projection'] = {'fields': identity_fields,
            'rows': table.to_dict('records') if table is not None else [],
            'authority': 'canonical_conversion_metadata_only_not_original_ownership', 'sha256': digest(metadata)}
    # Original docs are cited for each distinct unresolved relationship. A card
    # or unique generated index cannot fill these gates. Unknown is not absence.
    evidence = dict(prior['closure']) if prior else {'analysis_authorized': True, 'complete_X_qualified': False}
    record['admission_evidence'] = evidence
    record['admission'] = admit(evidence)
    bound = [v for v in record['original_bindings'] if v['status'] == 'bound']
    required = [
        ('source_original', 'Exact original files declared in raw_manifest.csv and the missing delegated converter, with source ownership and full content binding.',
         any(not v['exists'] for v in record['driver_resolution']) or not bound),
        ('observation_X_reference_join', 'Original observation key -> original specimen/reference key crosswalk, plus the original wavelength axis and target association; no generated row-number join.', True),
        ('target_semantics_and_scope', 'Original target definition, quantitative meaning, units, conversion and missing-reference rules; original development/retained membership before any target decode.', True),
        ('physical_assay_dependency', 'Original acquisition -> specimen -> assay event/reference batch relationships and known donor/site/batch ownership, with unknown links explicitly marked.', True),
        ('study_overlap_and_folds', 'Original study/population provenance and overlap against historical discovery sources; whole-component split support and source-defined stress context.', True)]
    record['requests'] = [{'relationship': kind, 'exact_inspected_documents': record['documents'],
        'declared_original_evidence': record['original_bindings'], 'evidence_required': text,
        'obtainable_from_current_inspected_evidence': False,
        'source_owner_clarification_required': True,
        'tier_consequences': {'X_only': 'Existing qualified X receipt remains usable; file presence is not qualification.',
            'XY_descriptive': 'Requires exact original-keyed numeric correspondence, target units and predecode development access freeze; physical independence is a separate claim.',
            'exploratory_supervised': 'Requires original physical/assay closure and feasible component-safe reference/stress/control designs.',
            'independent_confirmation': 'Additionally requires untouched verified study/population separation and adequate independent study support.'},
        'next_action': 'Owner supplies the exact cited missing original file/crosswalk or source-owner documentation; verify only this relationship before attempting numeric access.'}
        for kind, text, missing in required if missing]
    record['stopping_decision'] = {'stop_unchanged_search': True,
        'reason': 'Bounded exact-locator and original-schema inspection does not verify the original reference/access/dependency contract; owner evidence is now required.',
        'absence_elsewhere_claimed': False, 'target_decode_allowed': False, 'real_fitting_allowed': False}
    return record


def alternative_selection(context, old):
    """Metadata-only shortlist from already screened entries, before any outcomes."""
    prior = context.prior('source-closure-v2')
    excluded = {r['dataset_id'] for r in old} | {'corn_eigenvector_nir', 'ucph_tablet_nir',
        'ohpl_soil_nir', 'cartilage_spectroscopy_scientificdata_nir'}
    by_id = {e['dataset_id']: e for e in context.audit['entries']}
    ranked = []
    eligible = [v for v in prior['rankings'] if v['eligible_for_investigation'] and v['dataset_id'] not in excluded]
    manifests = [Path(context.cfg['source_root'])/v['dataset_id']/'raw_manifest.csv' for v in eligible]
    context.participate([p for p in manifests if p.is_file()])
    # Reuse the previously frozen eligibility roster, not prediction performance.
    for candidate in eligible:
        identity = candidate['dataset_id']
        if not candidate['eligible_for_investigation'] or identity in excluded:
            continue
        entry = by_id[identity]
        directory = Path(context.cfg['source_root'])/identity
        path = directory/'raw_manifest.csv'
        if not path.is_file():
            continue
        rows = manifest_rows(path.read_text(encoding='utf-8-sig'))
        used = [r for r in rows if r.get('used_for_conversion', '').lower() == 'yes' and r.get('file_role') == 'raw_data' and r.get('dataset_id') == identity]
        available = [r for r in used if r.get('local_path_if_any') and Path(r['local_path_if_any']).is_file()
            and Path(r['local_path_if_any']).stat().st_size <= 64*1024*1024
            and re.fullmatch('[0-9a-f]{64}', r.get('sha256_or_partial_hash', '').strip().lower().removeprefix('sha256:'))]
        group_leads = entry.get('physical_reference_dependencies', {})
        tier = (not bool(available), not bool(candidate.get('target_card_leads')),
            not bool(group_leads), not candidate['canonical_metadata_available'], identity)
        ranked.append({'dataset_id': identity, 'rank': list(tier),
            'manifest_receipt': digest(path), 'declared_available_originals': available,
            'source_dependency_leads': group_leads, 'selection_uses_model_performance': False})
    selected = sorted(ranked, key=lambda v: v['rank'])[:2]
    return {'ranking': ranked, 'selected': selected,
        'scope': 'Existing authorized catalog metadata only; no spectra, target values, new acquisition or private/published model scores.',
        'prior_candidates_have_explicit_stopping_decisions': all(r['stopping_decision']['stop_unchanged_search'] for r in old)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prior-only', action='store_true')
    args = parser.parse_args()
    context = Context()
    prior = context.prior('source-closure-v2')
    records = []
    for candidate in prior['investigations']:
        identity = candidate['dataset_id']; token = context.store.authenticate(identity)[:20]
        locators = context.run('original-locators-'+token, identity,
            {'prior_receipt': fingerprint(candidate), 'projection': 'manifest_and_delegated_converter_only'},
            lambda folder: inspect_locators(context, identity))
        record = context.run('original-reference-'+token, identity,
            {'locators': fingerprint(locators), 'policy': 'exact-original-v1'},
            lambda folder: resolve_candidate(context, identity, locators, candidate), reserve=4194304)
        records.append(record)
    context.save('source-resolution-prior.json', {'investigations': records, 'visibility': 'local_private'})
    if args.prior_only:
        print('ALPHA16_PRIOR_REFERENCE_PROJECTIONS_CHECKPOINTED; NO_TARGET_DECODE_OR_REAL_FIT')
        return
    shortlist = context.run('alternative-shortlist', 'integrated-report',
        {'stopped': fingerprint(records), 'selection': 'existing-manifest-original-availability-and-source-closure-v1'},
        lambda folder: alternative_selection(context, records))
    for candidate in shortlist['selected']:
        identity = candidate['dataset_id']; token = context.store.authenticate(identity)[:20]
        locators = context.run('original-locators-'+token, identity,
            {'selected': fingerprint(candidate), 'projection': 'manifest_and_delegated_converter_only'},
            lambda folder: inspect_locators(context, identity))
        records.append(context.run('original-reference-'+token, identity,
            {'locators': fingerprint(locators), 'policy': 'exact-original-v1'},
            lambda folder: resolve_candidate(context, identity, locators), reserve=4194304))
    context.save('source-resolution.json', {'visibility': 'local_private', 'investigations': records,
        'alternative_shortlist_receipt': fingerprint(shortlist), 'target_cells_decoded': 0,
        'real_supervised_fits': 0, 'new_spectral_campaigns': 0, 'new_public_scientific_exports': 0})
    print('ALPHA16_PROTECTED_SOURCE_RESOLUTION_CHECKPOINTED; NO_TARGET_DECODE_OR_REAL_FIT')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        try:
            Context().save('controller-failure.json', {'type': type(exc).__name__, 'detail': str(exc)})
        except Exception:
            pass
        print('ALPHA16_SOURCE_RESOLUTION_REFUSED; DETAILS_PROTECTED')
        raise SystemExit(2) from None
