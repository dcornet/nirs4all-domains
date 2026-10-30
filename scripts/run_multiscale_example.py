"""Bounded public synthetic example through the existing native X-profile path."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from nirs4all_domains.multiscale import describe, markdown
from nirs4all_domains.storage import atomic_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('results/multiscale-example'))
    parser.add_argument('--binary', default=os.environ.get('N4DOMAINS_BIN'))
    parser.add_argument('--library', default=os.environ.get('N4DOMAINS_METHODS_LIBRARY'))
    args = parser.parse_args()
    if not args.binary or not args.library:
        parser.error('Supply --binary/--library or N4DOMAINS_BIN/N4DOMAINS_METHODS_LIBRARY')
    case = json.loads(Path('tests/fixtures/multiscale/methods-hdbscan-v1.json').read_text())['cases'][0]
    flat = [struct.unpack('>d', bytes.fromhex(v))[0] for v in case['input_hex']]
    spectral = {'source_id': 'public-synthetic-blobs',
                'observation_ids': [f'o{i}' for i in range(case['rows'])],
                'identity_evidence': 'observation_identity_only',
                'axis': [1, 2], 'axis_unit': 'logical',
                'spectra': [flat[i:i+2] for i in range(0, len(flat), 2)]}
    request = {'spectral': spectral, 'representation': 'raw', 'query_ids': [], 'include_neighbors': False}
    run = subprocess.run([args.binary, 'x-profile', '--include-hierarchy', '--methods-library', args.library],
        input=json.dumps(request, allow_nan=False), text=True, capture_output=True, timeout=60, check=True)
    source = json.loads(run.stdout)
    # Keep original native tree/labels, but avoid duplicating PCA score transport.
    source.pop('transport_only_scores')
    result = describe(source)
    atomic_json(args.out/'source-report.json', source)
    atomic_json(args.out/'descriptor.json', result)
    (args.out/'descriptor.md').write_text(markdown(result), encoding='utf-8')
    print('Public synthetic example: 1 PCA, 2 HDBSCAN calls, no Y or supervised fit.')


if __name__ == '__main__':
    main()
