"""Record final-HEAD CI, clean delivery and preservation privately, without a Git loop."""
import argparse
import json
from pathlib import Path
import subprocess
from alpha15_common import Context, read
from nirs4all_domains.storage import digest


def git(*args):
    return subprocess.check_output(['git', *args]).decode().strip()


def main():
    parser = argparse.ArgumentParser();parser.add_argument('run_id');args = parser.parse_args()
    context = Context();head = git('rev-parse', 'HEAD')
    context.load('execution-source-attribution.json');context.load('executed-source-snapshot.json')
    assert not git('status', '--porcelain'), 'DELIVERY_WORKTREE_NOT_CLEAN'
    assert git('rev-parse', 'origin/main') == head, 'DELIVERY_REMOTE_HEAD_MISMATCH'
    proof = json.loads(subprocess.check_output(['gh','run','view',args.run_id,'--repo','dcornet/nirs4all-domains',
        '--json','status,conclusion,headSha,url,jobs']))
    assert proof['headSha'] == head and proof['status'] == 'completed' and proof['conclusion'] == 'success'
    assert {j['name'] for j in proof['jobs']} == {'audit (windows-latest)', 'audit (ubuntu-latest)'}
    assert all(j['conclusion'] == 'success' and j['status'] == 'completed' for j in proof['jobs'])
    prior = read(context.root/'baseline-private-preservation.json')
    assert prior['authentication'] == context.store.authenticate(prior['preservation'])
    assert all(digest(context.store.root/p) == sha for p, sha in prior['preservation']['files'].items())
    public = read('docs/audit/alpha15-frozen-output-hashes.json')
    assert all(digest(p) == sha for p, sha in public.items())
    context.save('delivery-validation.json', {'visibility':'local_private', 'final_commit':head,
        'final_HEAD_CI': proof, 'resources':context.guard(), 'worktree_clean':True, 'remote_matches_HEAD':True,
        'historical_public_private_preservation':True, 'no_real_supervised_pilot':True,
        'new_public_scientific_exports':0, 'source_publication_review':'Actual final index/source and package review recorded separately.'})
    print(json.dumps({'status':'delivered','final_commit':head,'CI':proof['url'],
        'platforms':2,'private_scientific_exports':0,'resource_limits_respected':True}))


if __name__ == '__main__':
    try: main()
    except Exception:
        print('ALPHA15_FINAL_DELIVERY_NOT_VERIFIED');raise SystemExit(2)
