"""Validate structural schema and availability invariants on a real CLI report."""
import json
from pathlib import Path
import sys
import jsonschema

root = Path(__file__).resolve().parents[1]
report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
jsonschema.validate(report, json.loads((root/"schemas/report.v1.schema.json").read_text(encoding="utf-8")))
for metric in report["metrics"]:
    if metric["status"] != "computed":
        assert metric["value"] is None and metric["reason"], metric["metric_id"]
    else:
        assert metric["value"] is not None and metric["reason"] is None, metric["metric_id"]
assert report["fit"] is None or report["fit"]["fit_partition"] == "train"
print("Report schema and availability invariants valid")
