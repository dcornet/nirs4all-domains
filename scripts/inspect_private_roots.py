"""Inspect configuration validity without returning locations to the shell tool."""
import json
from pathlib import Path
import sys


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    try:
        if len(arguments) != 1:
            raise ValueError()
        value = json.loads(Path(arguments[0]).read_text(encoding='utf-8'))
        required = {'root', 'report_root', 'previous_report_root', 'source_root', 'visibility'}
        if set(value) != required or value['visibility'] != 'local_private':
            raise ValueError()
        if not all(isinstance(value[k], str) and value[k].strip() for k in required):
            raise ValueError()
    except Exception:
        print('PRIVATE_ROOT_CONFIG_UNAVAILABLE')
        return 2
    print('PRIVATE_ROOT_CONFIG_VALID')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
