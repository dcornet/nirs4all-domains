"""Explicit published-cohort provenance binding; exact engineering values only."""
import json
from pathlib import Path
import sys

from compare_browser_benchmarks import compare

TRANSITION = ("1.3.13+abi.2.20.0", "1.5.1+abi.2.24.0")


def main():
    before, after, output = map(Path, sys.argv[1:])
    result = compare(json.loads(before.read_bytes()), json.loads(after.read_bytes()),
                     provider_transition=TRANSITION)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, allow_nan=False, indent=2)
        stream.write("\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
