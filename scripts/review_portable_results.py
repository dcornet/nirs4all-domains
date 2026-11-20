"""Inspect actual extracted A4/Letter PDFs and complete typed CSV/JSON counterparts."""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import zipfile

import pymupdf

root = Path(__file__).resolve().parents[1]
output = Path(os.environ.get('DOMAINS_BROWSER_RESULTS', root / 'demo/test-results/browser'))
reviews = []


def resolve_pointer(value, pointer):
    for token in pointer.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


for engine in ('chromium', 'firefox'):
    folder = output / 'f4.3' / engine
    archive = folder / 'domains-results.zip'
    assert archive.is_file(), ('Missing supported engine package', engine)
    extracted = folder / 'portable-package'
    extracted.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None
        assert all(re.fullmatch(r'[a-zA-Z0-9_./-]+', name) and not Path(name).is_absolute() and '..' not in Path(name).parts and '\\' not in name for name in package.namelist())
        assert sum(info.file_size for info in package.infolist()) < 100_000_000
        package.extractall(extracted)
    manifest = json.loads((extracted / 'manifest.json').read_text(encoding='utf-8'))
    report = json.loads((extracted / 'report.json').read_text(encoding='utf-8'))
    assert manifest['protocol_version'] == 'domains.portable_report.v2'
    assert report['raw_x_included'] is False and report['numerical_evidence_recomputed_for_export'] is False
    for record in manifest['files']:
        data = (extracted / record['path']).read_bytes()
        assert len(data) == record['bytes'] and hashlib.sha256(data).hexdigest() == record['sha256']
    csv_data = (extracted / manifest['csv']['file']).read_bytes()
    reader = csv.DictReader(io.StringIO(csv_data.decode('utf-8'), newline=''))
    assert reader.fieldnames == manifest['csv']['columns']
    rows = 0
    pointers = set()
    sections_by_id = {s['id']: s for s in manifest['sections']}
    section_counts = {}
    for row in reader:
        rows += 1
        assert row['json_pointer'] not in pointers, 'Duplicated CSV source cell'
        pointers.add(row['json_pointer'])
        section_id = json.loads(row['section_id'])
        if 'section_status' in row:
            assert row['section_status'] == sections_by_id[section_id]['status']
            assert json.loads(row['section_reason_json']) == sections_by_id[section_id]['reason']
            assert json.loads(row['unit_json']) == (report['dataset']['axisUnit'] if re.search(r'/axis/\d+$', row['json_pointer']) else None)
        section_counts[section_id] = section_counts.get(section_id, 0) + 1
        value = resolve_pointer(report, row['json_pointer'])
        assert json.loads(row['value_json']) == value, (engine, row['json_pointer'])
        assert row['value_type'] in ('string', 'number', 'boolean', 'null', 'array', 'object')
    assert rows == manifest['csv']['row_count']
    def leaves(value):
        if isinstance(value, dict) and value:
            return sum(leaves(v) for v in value.values())
        if isinstance(value, list) and value:
            return sum(leaves(v) for v in value)
        return 1
    assert rows == sum(leaves(e['value']) for e in report['evidence']), 'Missing CSV values'
    assert sum(s['row_count'] for s in manifest['sections']) == rows
    for section in manifest['sections']:
        assert section_counts[section['id']] == section['row_count']
        assert (extracted / section['file']).is_file()
    for paper, dimensions in [('a4', (595.28, 841.89)), ('letter', (612, 792))]:
        pdf_path = extracted / f'report-{paper}.pdf'
        with pymupdf.open(pdf_path) as document:
            assert 1 <= document.page_count <= 300
            text = re.sub(r'\s+', ' ', ' '.join(page.get_text() for page in document))
            for marker in ['Domains', 'sg_invalid_polyorder', 'csv', 'manifest.json', 'Limitations and provenance', 'No representation is recommended or ranked.', 'Stage: test_audit']:
                assert marker in text, (engine, paper, 'missing marker', marker)
            links = []
            images = 0
            for page in document:
                assert abs(page.rect.width - dimensions[0]) < 2 and abs(page.rect.height - dimensions[1]) < 2
                words = page.get_text('words')
                assert words, 'Blank page'
                assert all(x0 >= -1 and y0 >= -1 and x1 <= dimensions[0]+1 and y1 <= dimensions[1]+1 for x0,y0,x1,y1,*_ in words), 'Text clipping'
                images += len(page.get_images())
                for link in page.get_links():
                    target = link.get('uri') or link.get('file')
                    assert target and not re.match(r'^[a-z]+:', target), ('Nonportable link', link)
                    assert (pdf_path.parent / target).is_file(), ('Missing linked companion', target)
                    links.append(target)
            assert images > 0 and manifest['csv']['file'] in links and 'manifest.json' in links and 'report.json' in links
            samples = sorted({0, document.page_count//2, document.page_count-1})
            for index in samples:
                document[index].get_pixmap(dpi=100).save(folder / f'portable-{paper}-page-{index+1}.png')
            reviews.append({'engine': engine, 'paper': paper, 'pages': document.page_count, 'pdf_bytes': pdf_path.stat().st_size,
                            'images': images, 'relative_link_count': len(links), 'csv_rows_verified_against_json': rows,
                            'text_bounds': 'passed', 'zip_integrity': 'passed', 'sampled_pages': [i+1 for i in samples]})
result = {'protocol_version': 'domains.portable_report_review.v2', 'status': 'structural_checks_passed', 'reviews': reviews,
          'new_real_scientific_fits': 0, 'visual_review': 'Representative rasters emitted for inspection; not every-page visual certification.'}
(output / 'portable-report-review.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
