"""Operator entry point; private locations and subprocess output are never emitted."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bridges' / 'python'))
from inspect_private_roots import load_private_roots
from nirs4all_domains.engineering_storage import EngineeringStorage
from nirs4all_domains.privacy import PrivateStore
from nirs4all_domains.storage import atomic_json


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError('ENGINEERING_ARGUMENTS_INVALID') from None


def main(arguments=None):
    parser = SafeParser(description=__doc__)
    parser.add_argument('operation', choices=('activate', 'snapshot', 'admit'))
    parser.add_argument('--workspace', required=True, help='Original Domains workspace used by the qualified recipe')
    parser.add_argument('--private-config', required=True, help='Existing validated private-root locator configuration')
    parser.add_argument('--measurement-recipe', required=True, help='Previously qualified immutable numeric measurement script')
    parser.add_argument('--out', required=True, help='Sanitized JSON result destination')
    parser.add_argument('--requested-bytes', type=int, default=0, help='Prospective engineering bytes for admit')
    parser.add_argument('--effective-bytes', type=int, help='Explicit owner effective aggregate cap for activate')
    parser.add_argument('--engineering-bytes', type=int, help='Explicit owner additional engineering allowance for activate')
    parser.add_argument('--authorized-max-bytes', type=int, help='Explicit owner maximum, bounded by the 50 GB grant')
    parser.add_argument('--reserve-free-bytes', type=int, help='Per-volume physical reserve, at least 2 GiB')
    parser.add_argument('--owner-request-sha256', help='Owner decision evidence digest for activate')
    parser.add_argument('--decision-date', help='Owner decision date YYYY-MM-DD for activate')
    parser.add_argument('--recipe-sha256', help='Explicit qualified measurement script digest for activate')
    try:
        args = parser.parse_args(arguments)
        activation = {k: getattr(args, k) for k in ('effective_bytes', 'engineering_bytes', 'authorized_max_bytes',
                      'reserve_free_bytes', 'owner_request_sha256', 'decision_date', 'recipe_sha256')}
        if args.operation == 'activate' and any(v is None for v in activation.values()):
            raise ValueError('ENGINEERING_ACTIVATION_ARGUMENTS_REQUIRED')
        if args.operation != 'admit' and args.requested_bytes != 0:
            raise ValueError('ENGINEERING_REQUEST_REQUIRES_ADMIT')
        config = load_private_roots(args.private_config)
        key = Path(config['root']) / 'keys' / 'scope.key'
        if not key.is_file() or key.is_symlink():
            raise ValueError('EXISTING_PRIVATE_STORE_KEY_REQUIRED')
        controller = EngineeringStorage(PrivateStore(config['root'], args.workspace), args.workspace, args.measurement_recipe)
        result = controller.activate(**activation) if args.operation == 'activate' else controller.snapshot(args.requested_bytes)
        atomic_json(args.out, result)
        print('ENGINEERING_STORAGE_' + result['status'].upper())
        return 0 if result['status'] == 'ready' else 3
    except Exception:
        print('ENGINEERING_STORAGE_UNAVAILABLE')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
