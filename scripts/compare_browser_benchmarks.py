"""Compare technical measurements only after exact scientific evidence equality."""
import json
from pathlib import Path
import statistics
import sys

before, after, output = map(Path, sys.argv[1:])
a, b = (json.loads(path.read_bytes()) for path in [before, after])
assert a["success"] and b["success"] and a["browser"] == b["browser"] and a["node"] == b["node"]
assert len(a["samples"]) == len(b["samples"]) == 3
for left, right in zip(a["samples"], b["samples"]):
    assert left["rank_one"] == right["rank_one"], "CSV scientific values or hashes changed"
    assert left["live"] == right["live"], "Synthetic example scientific values or hashes changed"
    assert len(left["network"]) == 4 and len(right["network"]) == 3, "CSV must avoid only the unused Formats module"
    assert left["workers"][0]["transferred_bytes"] == 0 and right["workers"][0]["transferred_bytes"] > 0
    assert right["workers"][0]["sender_detached"] is True
keys = ["landing_ms", "import_to_visible_ms", "declaration_edit_ms", "main_thread_script_delta_ms", "layout_delta_ms", "main_thread_heap_sample_bytes", "offline_render_ms"]
timings = {key: {"before": statistics.median(s[key] for s in a["samples"]), "after": statistics.median(s[key] for s in b["samples"])} for key in keys}
for kind in ["json_export", "html_export", "markdown_export"]:
    timings[kind + "_ms"] = {"before": statistics.median(s[kind]["ms"] for s in a["samples"]), "after": statistics.median(s[kind]["ms"] for s in b["samples"])}
result = {"protocol": "domains.technical_comparison.v1", "scientific_values_and_hashes_equal": True,
          "browser": b["browser"], "node": b["node"], "repetitions_each": 3,
          "assets": {"before_bytes": sum(x["bytes"] for x in a["assets"]), "after_bytes": sum(x["bytes"] for x in b["assets"]),
                     "before_wasm": [x for x in a["assets"] if x["file"].endswith(".wasm")], "after_wasm": [x for x in b["assets"] if x["file"].endswith(".wasm")]},
          "csv_loaded_wasm_modules": {"before": 4, "after": 3}, "medians": timings,
          "limits": b["measurement_limits"], "statistical_significance_or_whole_bank_claimed": False}
output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
