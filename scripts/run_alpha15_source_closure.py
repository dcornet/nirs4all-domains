"""Targeted local original-file investigation, with no target-cell decoding."""
import ast
import csv
import re
from pathlib import Path
import zipfile

from alpha15_common import Context, read
from nirs4all_domains.confrontation import admit
from nirs4all_domains.dependence import state
from nirs4all_domains.storage import digest, fingerprint


def header(path):
    with Path(path).open(encoding='utf-8-sig') as stream:
        line = stream.readline()
    delimiter = ';' if line.count(';') > line.count(',') else ','
    return next(csv.reader([line], delimiter=delimiter)), delimiter


def investigate(context, folder):
    source_root = Path(context.cfg['source_root'])
    cohort = read(context.load('cohort.json')['artifact_path'])
    inventory = {e['dataset_id']: e for e in read('docs/benchmarks/alpha13/source-diversity-inventory.json')['entries']}
    # Closure criteria are fixed before any Y cell or predictive score is read.
    # Reopen a genuinely different owner-supplied study, rather than the old
    # tablet/soil/cartilage/CORN admission loop. Target presence is a card lead.
    excluded = {'corn_eigenvector_nir', 'ucph_tablet_nir', 'ohpl_soil_nir',
        'cartilage_spectroscopy_scientificdata_nir'}
    rankings = []
    for entry in context.audit['entries']:
        name = entry['dataset_id']; directory = source_root/name
        targets = inventory[name].get('target_descriptors', [])
        eligible = entry['access_analysis_eligible'] and name not in excluded and bool(targets)
        files = {p.name: p for p in directory.iterdir() if p.is_file()} if directory.is_dir() else {}
        original_driver = files.get('source_to_standard.py')
        # Lexical ordering within a prespecified, source-closure-based tier;
        # geometry, stability, family outcomes and model scores are not used.
        tier = (not bool(original_driver), not bool(files.get('raw_manifest.csv')),
            not bool(files.get('M.csv')), not any(t.get('unit') or t.get('units') for t in targets), name)
        rankings.append({'dataset_id': name, 'eligible_for_investigation': eligible,
            'rank_key': list(tier), 'target_card_leads': targets,
            'original_driver_available': original_driver is not None,
            'canonical_metadata_available': 'M.csv' in files, 'canonical_Y_available': 'Y.csv' in files,
            'analysis_authorized': entry['access_analysis_eligible'], 'exclusion': name in excluded})
    candidates = sorted([r for r in rankings if r['eligible_for_investigation']], key=lambda r: r['rank_key'])
    assert candidates, 'NO_AUTHORIZED_ALTERNATIVE_SOURCE_WITH_TARGET_LEAD'
    investigations = []
    # Three bounded alternatives prevent a single convenient source from hiding
    # wider admission gaps. All original documents remain local.
    documents_read = 0
    for candidate in candidates[:3]:
        name = candidate['dataset_id']; directory = source_root/name
        record = {'dataset_id': name, 'selection': candidate, 'files': [], 'headers': {},
            'numeric_target_cells_decoded': 0, 'target_read_scope': 'headers_and_original_schema_only',
            'retained_Y_accessed': False}
        texts = []
        for filename in ['source_to_standard.py', 'conversion_report.md', 'raw_manifest.csv',
                'datapackage.json', 'dataset_card.json', 'PRIVATE_USE_ONLY.md']:
            p = directory/filename
            if not p.is_file(): continue
            assert documents_read+p.stat().st_size <= 8*1024*1024, 'SOURCE_DOCUMENT_BOUND'
            text = p.read_text(encoding='utf-8-sig');documents_read += p.stat().st_size
            texts.append((filename, text))
            record['files'].append({'path': str(p), 'sha256': digest(p), 'bytes': p.stat().st_size,
                'scope': 'Existing original/local conversion provenance; not a new rights grant.'})
        for filename in ['X.csv', 'Y.csv', 'M.csv']:
            p = directory/filename
            if p.is_file():
                columns, delimiter = header(p)
                record['headers'][filename] = {'columns': columns, 'delimiter': delimiter,
                    'identity_candidates': [c for c in columns if any(t in c.lower() for t in ['id', 'key', 'sample', 'ref', 'batch'])]}
        original_strings = set()
        for filename, text in texts:
            if filename == 'source_to_standard.py':
                try:
                    tree = ast.parse(text)
                    original_strings.update(n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str))
                except SyntaxError: record['driver_parse'] = 'SYNTAX_NOT_EXECUTED'
            if filename == 'raw_manifest.csv':
                original_strings.update(value for row in csv.reader(text.splitlines(), delimiter=';' if text.splitlines()[0].count(';') else ',') for value in row)
        existing = []
        for value in original_strings:
            if len(value) < 240:
                p = Path(value)
                if p.is_absolute() and p.is_file() and not p.is_relative_to(directory): existing.append(p)
        basenames = {Path(v.replace('\\', '/')).name for v in original_strings if len(v) < 240 and
            Path(v).suffix.lower() in ['.mat', '.csv', '.txt', '.rda', '.rdata', '.zip', '.xlsx', '.pdf']}
        for raw_root in ['manual_download', 'manual_download_extracted', 'raw_todo', 'nirs_datasets_ready']:
            base = source_root.parent/raw_root
            if base.is_dir():
                existing.extend(p for p in base.rglob('*') if p.is_file() and p.name in basenames and p.name not in ['X.csv', 'Y.csv', 'M.csv'])
        # Existing source locators only; no broad filesystem content search.
        record['original_file_inspections'] = []
        for p in sorted(set(existing))[:8]:
            item = {'path': str(p), 'bytes': p.stat().st_size, 'original_content_binding': 'original_export_link_not_numeric_equivalence'}
            if p.suffix.lower() == '.mat':
                from scipy.io import whosmat
                try:
                    item['variable_schema'] = [{'name': n, 'shape': list(shape), 'matlab_class': kind} for n, shape, kind in whosmat(p)]
                    item['inspection'] = 'ORIGINAL_MAT_VARIABLE_SCHEMA_NO_ARRAY_DECODE'
                except Exception: item['inspection'] = 'MAT_SCHEMA_READER_UNAVAILABLE'
            elif zipfile.is_zipfile(p):
                with zipfile.ZipFile(p) as archive:
                    item['archive_members'] = [{'name': x.filename, 'bytes': x.file_size} for x in archive.infolist()][:100]
                item['inspection'] = 'ORIGINAL_ARCHIVE_MEMBER_SCHEMA_NO_EXTRACTION'
            elif p.suffix.lower() in ['.csv', '.tsv', '.txt']:
                try:
                    columns, delimiter = header(p);item['original_header'] = columns;item['inspection'] = 'ORIGINAL_HEADER_NO_TARGET_CELLS'
                except Exception: item['inspection'] = 'ORIGINAL_HEADER_UNAVAILABLE'
            else: item['inspection'] = 'ORIGINAL_FILE_STAT_ONLY_NOT_CONTENT_CLOSURE'
            record['original_file_inspections'].append(item)
        # Preserve exact evidence excerpts as leads, including row-order joins;
        # never certify independence merely because a converter generates IDs.
        record['provenance_excerpts'] = [{'document': filename,
            'lines': [line for line in text.splitlines() if re.search(r'(?i)sample|assay|batch|reference|merge|join|index|arange|unit|protein|moisture|physical|replic', line)][:50]}
            for filename, text in texts]
        record['closure'] = {'analysis_authorized': True,
            'complete_X_qualified': any(v['catalog_id'] == name and any(e['view_id'] == v['view_id'] and e['status'] == 'computed'
                for e in cohort['executions']) for v in cohort['views']),
            'original_keyed_XY_verified': False, 'target_meaning_units_verified': False,
            'development_scope_frozen_before_target_decode': False,
            'original_study_verified': False, 'physical_specimen_ownership_verified': False,
            'reference_assay_ownership_verified': False, 'dependency_map_verified': False,
            'component_safe_split_feasible': False}
        record['decision'] = admit(record['closure'])
        record['finding'] = {'observation': 'Original conversion documentation and available original file schemas inspected; canonical identity fields do not establish keyed numeric X/Y equivalence or assay ownership.',
            'confidence': 'Bounded local inspection of the exact listed files; not an assertion that evidence is absent elsewhere.',
            'consequence': 'No numeric XY description or predictive fold admission from card/schema evidence alone.',
            'action': 'Obtain original specimen-to-spectrum-to-reference/assay crosswalk, target definitions/units and explicit development membership; then verify keyed numerical correspondence before Y use.'}
        investigations.append(record)
    return {'visibility': 'local_private', 'protocol': 'domains.alpha15.source_closure.v0.1',
        'rankings': rankings, 'investigations': investigations, 'existing_document_bytes_read': documents_read,
        'document_download_bytes': 0, 'spectral_bytes_acquired': 0, 'target_cells_decoded': 0,
        'new_supervised_fits': 0, 'public_participation_approved': False,
        'pilot': state(reason='ORIGINAL_KEYED_XY_AND_REFERENCE_ASSAY_CLOSURE_NOT_QUALIFIED'),
        'no_claim_of_global_evidence_absence': True}


def main():
    context = Context()
    context.run('source-closure-v2', {'audit': fingerprint(context.audit), 'selection_rule': 'closure-v1-pre-outcome',
        'original_locator_resolution_revision': 2},
        lambda folder: investigate(context, folder))
    context.record_closure_inputs()
    print('ALPHA15_TARGETED_SOURCE_CLOSURE_COMPLETE; NO_TARGET_CELLS_OR_PILOT_FITS')


if __name__ == '__main__':
    try: main()
    except Exception:
        print('ALPHA15_SOURCE_CLOSURE_REFUSED; DETAILS_PROTECTED');raise SystemExit(2)
