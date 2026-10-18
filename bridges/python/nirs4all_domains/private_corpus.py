"""Explicit local-private evidence/disclosure CLI. Never uploads or fits Y.

Native X execution is supplied by a separately admitted batch controller. This
CLI exposes safe local inspection and explicit reviewed export, independently
of numerical success. Configuration containing machine paths stays outside Git.
"""
import argparse
import json
from pathlib import Path
import sys

from .disclosure import DisclosureBoundary, validate_public
from .privacy import PrivateStore, PrivacyError, fail


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-config',required=True,type=Path)
    commands=p.add_subparsers(dest='command',required=True)
    inspect=commands.add_parser('verify-local');inspect.add_argument('--receipt',required=True)
    review=commands.add_parser('review');review.add_argument('--draft',type=Path,required=True)
    review.add_argument('--clearance',type=Path,required=True)
    export=commands.add_parser('export');export.add_argument('--draft',type=Path,required=True)
    export.add_argument('--out-dir',type=Path,required=True)
    args=p.parse_args()
    try:
        config=json.loads(args.private_config.read_text(encoding='utf-8'))
        store=PrivateStore(config['root'],Path.cwd());boundary=DisclosureBoundary(store)
        if args.command=='verify-local':
            store.get(args.receipt)
            result={'status':'verified','visibility':'local_private','receipt_id':args.receipt}
        else:
            # A draft/review may itself contain confidential review context.
            for path in [args.draft]+([args.clearance] if args.command=='review' else []):
                if not path.resolve().is_relative_to(store.root.resolve()):
                    fail('DISCLOSURE_LOCAL_REVIEW_INPUT_REQUIRED')
            draft=json.loads(args.draft.read_text(encoding='utf-8'));validate_public(draft)
            if args.command=='review':
                clearance=json.loads(args.clearance.read_text(encoding='utf-8'))
                result=boundary.review(draft,clearance['source_receipts'],clearance)
            else:
                result=boundary.export(draft,args.out_dir/(draft['receipt_id']+'.json'))
        print(json.dumps(result));return 0
    except PrivacyError as exc:
        print(json.dumps({'status':'refused','reason':str(exc)}));return 2
    except Exception:
        # Do not echo filenames, source names, values or third-party traceback.
        print(json.dumps({'status':'refused','reason':'PRIVATE_OPERATION_FAILED'}));return 2


if __name__=='__main__':sys.exit(main())
