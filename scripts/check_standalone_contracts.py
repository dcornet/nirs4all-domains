"""Focused read-only consumer/intent/comparison tests with no numerical runtime."""

import argparse
import json
import sys
import unittest
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    suite = unittest.TestSuite()
    for pattern in (
        "test_report_view.py",
        "test_warning_utility.py",
        "test_verification_readiness.py",
        "test_validation_intent.py",
        "test_comparison.py",
    ):
        suite.addTests(
            unittest.defaultTestLoader.discover(
                str(root / "tests/integration"), pattern=pattern
            )
        )
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    numerical = [
        name
        for name in sys.modules
        if name.split(".")[0] in ("n4m", "numpy", "dag_ml", "nirs4all_preflight")
    ]
    receipt = {
        "tests_run": result.testsRun,
        "failures": [t.id() for t, _ in result.failures],
        "errors": [t.id() for t, _ in result.errors],
        "skipped": [(t.id(), reason) for t, reason in result.skipped],
        "numerical_runtime_imports": numerical,
        "scientific_fits": 0,
        "scope": "Standalone/report/intent/comparison contracts only; legacy numerical/fitting suites not relaunched",
    }
    if args.receipt:
        p = Path(args.receipt)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))
    return 0 if result.wasSuccessful() and not numerical else 1


if __name__ == "__main__":
    raise SystemExit(main())
