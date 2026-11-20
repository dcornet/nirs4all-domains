"""Published Methods 1.5.1 cohort binding over the unchanged F4.3 v2 rules."""
import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path

import check_preprocessing_parity_v2 as rules

VERSION = "1.5.1+abi.2.24.0"
PROTOCOL = "domains.browser_preprocessing_sensitivity_parity.v3"


@contextmanager
def candidate_binding():
    # Single-process test transport only. Restore the historical module even
    # on refusal, so original v1/v2 adversaries keep their exact cohort.
    previous = rules.v1.VERSION
    try:
        rules.v1.VERSION = VERSION
        yield
    finally:
        rules.v1.VERSION = previous


def qualify(wasm, native, wasm_sha256):
    with candidate_binding():
        receipt = rules.qualify(wasm, native, wasm_sha256)
    return {**receipt, "protocol_version": PROTOCOL, "provider": VERSION,
            "historical_rules_unchanged": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("wasm", "native", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = qualify(rules.v1.read(args.wasm), rules.v1.read(args.native),
                          hashlib.sha256(args.wasm.read_bytes()).hexdigest())
    except (AssertionError, KeyError, ValueError, TypeError) as error:
        receipt = {"protocol_version": PROTOCOL, "provider": VERSION, "status": "failed",
                   "integrity": "failed", "numeric_parity": "not_evaluated", "reason": str(error)}
    receipt["source_sha256"] = {Path(p).name: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                                for p in (__file__, rules.__file__, rules.v1.__file__)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")
    print(json.dumps({k: receipt.get(k) for k in ("protocol_version", "provider", "status", "integrity", "numeric_parity", "cases", "numeric_comparisons", "reason")}) + " failures=" + str(len(receipt.get("failures", []))))
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
