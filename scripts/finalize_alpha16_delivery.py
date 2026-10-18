"""Verify final-HEAD delivery privately without a recursive proof commit."""
import argparse
import json
import subprocess

from alpha16_common import Context, read
from check_alpha16_results import verify_private
from nirs4all_domains.storage import digest


def git(*args):
    return subprocess.check_output(['git', *args]).decode().strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id')
    args = parser.parse_args()
    context = Context()
    head = git('rev-parse', 'HEAD')
    assert not git('status', '--porcelain'), 'DELIVERY_WORKTREE_NOT_CLEAN'
    assert git('rev-parse', 'origin/main') == head, 'DELIVERY_REMOTE_HEAD_MISMATCH'
    proof = json.loads(subprocess.check_output(['gh', 'run', 'view', args.run_id,
        '--repo', 'dcornet/nirs4all-domains', '--json', 'status,conclusion,headSha,url,jobs']))
    assert proof['headSha'] == head and proof['status'] == 'completed' and proof['conclusion'] == 'success'
    assert {job['name'] for job in proof['jobs']} == {'audit (windows-latest)', 'audit (ubuntu-latest)'}
    assert all(job['status'] == 'completed' and job['conclusion'] == 'success' for job in proof['jobs'])
    verify_private(context)
    assert all(digest(path) == sha for path, sha in read('docs/audit/alpha16-frozen-output-hashes.json').items())
    context.save('delivery-validation.json', {'visibility': 'local_private', 'final_commit': head,
        'final_HEAD_CI': proof, 'resources': context.guard(), 'worktree_clean': True,
        'remote_matches_HEAD': True, 'historical_public_private_preservation': True,
        'no_real_supervised_pilot': True, 'new_public_scientific_exports': 0})
    entry = context.root/'CONFIDENTIAL_REPORT.md'
    text = entry.read_text(encoding='utf-8')
    if 'Final release verification' not in text:
        entry.write_text(text+'\n\nFinal release verification: [signed final-HEAD CI, preservation and resource evidence](delivery-validation.json).\n', encoding='utf-8')
    context.guard()
    print(json.dumps({'status': 'delivered', 'final_commit': head, 'CI': proof['url'],
        'platforms': 2, 'private_scientific_exports': 0, 'resource_limits_respected': True}))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('ALPHA16_FINAL_DELIVERY_NOT_VERIFIED')
        raise SystemExit(2) from None
