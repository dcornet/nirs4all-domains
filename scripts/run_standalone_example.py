"""Replay two existing public tablet reports with their saved owner companions."""

import argparse
import json
from pathlib import Path

from nirs4all_domains.report_view import export_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    a = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "docs/examples/structural-warnings/tablet.report.json",
        root / "docs/examples/structural-warnings/tablet.annotation.json",
        root / "docs/benchmarks/alpha17/tablet-pilot-summary.json",
        root / "docs/examples/comparison/tablet.annotation.json",
    ]
    original = [p.read_bytes() for p in paths]
    values = [json.loads(b) for b in original]
    cases = [
        {
            "case_id": "tablet-X",
            "label": "Public tablet X evidence — conditional future-batch interpretation",
            "report": values[0],
            "d1": values[1],
        },
        {
            "case_id": "tablet-prediction",
            "label": "Public historical tablet prediction contrast — separate evaluation scope",
            "report": values[2],
            "comparison_report": values[2],
            "d3": values[3],
        },
    ]
    artifacts = export_report(
        cases, a.out, paths, title="A standalone review of existing tablet evidence"
    )
    assert original == [p.read_bytes() for p in paths]
    print(
        json.dumps(
            {
                "cases": 2,
                "new_fits": 0,
                "source_bytes_unchanged": True,
                "artifacts": artifacts,
            }
        )
    )


if __name__ == "__main__":
    main()
