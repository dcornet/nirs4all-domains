"""Static presentation-cost inventory of an existing synthetic F4.3 export.

This does not render, fit, truncate, rewrite or qualify the report.
"""
import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time


class Structure(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.tags = Counter()
        self.sections = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        self.tags[tag] += 1
        if tag == "section":
            self.sections.append({"id": dict(attrs).get("id"), "element_count": 0, "tables": 0, "rows": 0, "svg": 0})
            self.stack.append(len(self.sections)-1)
        for index in self.stack:
            record = self.sections[index]
            record["element_count"] += 1
            if tag in ("table", "tr", "svg"):
                record[{"table": "tables", "tr": "rows", "svg": "svg"}[tag]] += 1

    def handle_endtag(self, tag):
        if tag == "section":
            self.stack.pop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    parser.add_argument("--json", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    assert not args.out.exists(), "Preserve earlier profiling receipts"
    start = time.monotonic()
    raw = args.html.read_bytes()
    original = args.json.read_bytes()
    report = json.loads(original)
    assert report["raw_x_included"] is False
    assert "F4.3" in report["dataset"]["name"], "Synthetic qualification report required"
    html = raw.decode("utf-8")
    structure = Structure()
    structure.feed(html)
    assert not structure.stack
    tables = re.findall(r"<table\b.*?</table>", html, re.DOTALL)
    assert all(table.count("<table") == 1 for table in tables), "Nested table assumption failed"
    hashes = Counter(hashlib.sha256(table.encode()).hexdigest() for table in tables)
    sizes = {hashlib.sha256(table.encode()).hexdigest(): len(table.encode()) for table in tables}
    duplicates = [{"sha256": digest, "copies": count, "single_copy_bytes": sizes[digest]}
                  for digest, count in hashes.items() if count > 1]
    receipt = {"protocol_version": "domains.f43_static_report_profile.v1", "status": "profiled_not_rendered",
        "html_bytes": len(raw), "html_sha256": hashlib.sha256(raw).hexdigest(),
        "json_bytes": len(original), "json_sha256": hashlib.sha256(original).hexdigest(),
        "source_elements": sum(structure.tags.values()), "tags": dict(structure.tags),
        "sections": structure.sections, "exact_duplicate_tables": duplicates,
        "duplicate_table_bytes_beyond_first_copy": sum((d["copies"]-1)*d["single_copy_bytes"] for d in duplicates),
        "static_profile_seconds": round(time.monotonic()-start, 3),
        "print_attempted": False, "output_content_changed": False,
        "limitations": ["Source element counts are not a live DOM or renderer-memory measurement.",
                        "Equal tables identify presentation repetition, not permission to omit requested evidence.",
                        "The original 8 MB print guard and complete scientific payload remain unchanged."],
        "new_real_scientific_fits": 0, "new_scientific_reservations": 0}
    args.out.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "html_bytes", "json_bytes", "source_elements", "duplicate_table_bytes_beyond_first_copy", "static_profile_seconds")}))
