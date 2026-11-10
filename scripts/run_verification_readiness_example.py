"""Public saved-report example; observation available, verification not yet feasible."""

import argparse
import json
from copy import deepcopy
from pathlib import Path

from nirs4all_domains.report_view import export_report
from nirs4all_domains.storage import fingerprint
from nirs4all_domains.verification_readiness import interpret


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / "docs/examples/structural-warnings"
    report = json.loads((root / "tablet.report.json").read_text(encoding="utf-8"))
    parent = json.loads((root / "tablet.annotation.json").read_text(encoding="utf-8"))
    before = deepcopy((report, parent))
    warning = next(
        w
        for w in parent["warnings"]
        if w["warning_id"] == "experimental_factor_structure"
    )
    check = warning["recommended_checks"][0]

    def state(value=None, **extra):
        return {
            "status": "computed" if value else "unavailable",
            "reason": None if value else "NOT_QUALIFIED",
            "value": value,
            **extra,
        }

    request = {
        "source_report_sha256": fingerprint(report),
        "parent_annotation_sha256": fingerprint(parent),
        "checks": [
            {
                "record_id": "conditional-factor-contrast",
                "warning_id": warning["warning_id"],
                "check_id": check["check_id"],
                "scope": warning["evidence_scope"],
                "action_kind": "new_analysis",
                "action": check["description"],
                "applicability": state(
                    reference=None,
                    rationale="The exact deployment and original unit mappings require qualification",
                ),
                "inputs": state(
                    "requires_data",
                    requirements=[
                        {
                            "name": n,
                            "accessible": False,
                            "reference": "Memberships not supplied by this aggregate report",
                        }
                        for n in check["required_information"]
                    ],
                ),
                "protocol": state(
                    "not_qualified",
                    reference="No new contrast protocol specified by this example",
                    details=None,
                ),
                "authorization": state(
                    "not_authorized",
                    reference="Read-only example; no calibration authorized",
                    source_rights_reference=None,
                    resource_limits_reference=None,
                ),
                "execution": state("not_executed", receipt=None),
            }
        ],
    }
    annotation = interpret(report, parent, request)
    artifacts = export_report(
        [
            {
                "case_id": "tablet-example",
                "report": report,
                "d1": parent,
                "readiness": annotation,
            }
        ],
        args.out,
    )
    assert (report, parent) == before
    print(
        json.dumps(
            {
                "artifacts": artifacts,
                "new_scientific_fits": 0,
                "original_inputs_unchanged": True,
            }
        )
    )


if __name__ == "__main__":
    main()
