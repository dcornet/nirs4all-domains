"""Inspect configuration validity without returning locations to the shell tool."""
import json
from pathlib import Path
import sys


def load_private_roots(path):
    """Validate privately; callers must never print the returned locators."""
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8'))
        required = {'root', 'report_root', 'previous_report_root', 'source_root', 'visibility'}
        if not isinstance(value, dict) or set(value) != required or value['visibility'] != 'local_private':
            raise ValueError()
        if not all(isinstance(value[k], str) and value[k].strip() for k in required):
            raise ValueError()
        return value
    except Exception:
        raise ValueError('PRIVATE_ROOT_CONFIG_UNAVAILABLE') from None


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    try:
        if len(arguments) != 1:
            raise ValueError()
        load_private_roots(arguments[0])
    except Exception:
        print('PRIVATE_ROOT_CONFIG_UNAVAILABLE')
        return 2
    print('PRIVATE_ROOT_CONFIG_VALID')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
