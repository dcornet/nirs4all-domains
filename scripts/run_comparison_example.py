"""Read-only replay of two public historical tablet context results. No fits."""
import argparse
import json
from pathlib import Path

from nirs4all_domains.comparison_interpretation import interpret, markdown, validate_annotation
from nirs4all_domains.storage import atomic_json, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "docs/benchmarks/alpha17/tablet-pilot-summary.json"
    request = root / "docs/examples/comparison/tablet.request.json"
    protected = {source.resolve(), request.resolve()}
    outputs = [args.out / "tablet.annotation.json", args.out / "tablet.annotation.md"]
    if any(p.resolve() in protected or p.exists() for p in outputs):
        parser.error("Choose unused output paths distinct from source and request")
    before = digest(source)
    report = json.loads(source.read_text(encoding="utf-8"))
    annotation = interpret(report, report, json.loads(request.read_text(encoding="utf-8")))
    validate_annotation(report, report, annotation)
    atomic_json(outputs[0], annotation)
    outputs[1].write_text(markdown(annotation), encoding="utf-8", newline="\n")
    assert digest(source) == before
    print(json.dumps({"source_sha256": before, "new_fits": 0,
                      "direct_comparison": annotation["direct_comparison"],
                      "evaluation_matching": annotation["evaluation_matching"],
                      "null_comparison": annotation["null_comparison"]}))


if __name__ == "__main__":
    main()
