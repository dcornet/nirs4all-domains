"""Inspect F4.2 synthetic browser PDFs; emit representative rasters for human review."""
import json
import os
from pathlib import Path
import re

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(os.environ.get("DOMAINS_BROWSER_RESULTS", ROOT / "demo/test-results/browser"))
FOLDER = RESULTS / "f4.2" / "chromium"
EXPECTED = {"a4": (595.28, 841.89), "letter": (612.0, 792.0)}
MARKERS = (
    "Test projection on train reference",
    "Reference component dispersions",
    "Descriptive T²/Q monitoring",
    "statsPcaMonitor",
    "No predictive validation",
)
reviews = []

for paper, size in EXPECTED.items():
    path = FOLDER / f"train-fitted-support-{paper}.pdf"
    with pymupdf.open(path) as document:
        assert document.page_count > 0, (path.name, "no pages")
        page_texts = [page.get_text() for page in document]
        assert all(text.strip() for text in page_texts), (path.name, "blank page")
        combined = re.sub(r"\s+", " ", " ".join(page_texts))
        for marker in MARKERS:
            assert marker in combined, (path.name, "missing scientific marker", marker)
        for page in document:
            width, height = page.rect.width, page.rect.height
            assert abs(width - size[0]) < 2 and abs(height - size[1]) < 2, (path.name, page.number, "paper size")
            words = page.get_text("words")
            assert words, (path.name, page.number, "no extractable text")
            assert all(x0 >= -2 and y0 >= -2 and x1 <= width + 2 and y1 <= height + 2
                       for x0, y0, x1, y1, *_ in words), (path.name, page.number, "text bounds")

        # Emit deterministic first/content/last samples; the full document remains uncapped.
        content_page = next(i for i, text in enumerate(page_texts) if MARKERS[0] in re.sub(r"\s+", " ", text))
        sampled = sorted({0, content_page, document.page_count - 1})
        rasters = []
        for index in sampled:
            name = f"train-fitted-support-{paper}-sample-page-{index + 1}.png"
            document[index].get_pixmap(dpi=96).save(FOLDER / name)
            rasters.append({"file": name, "page": index + 1})
        reviews.append({"file": path.name, "pages": document.page_count, "bytes": path.stat().st_size,
                        "paper": paper, "no_blank_pages": True, "all_page_text_bounds_checked": True,
                        "scientific_markers_checked": list(MARKERS), "sampled_rasters": rasters})

result = {
    "protocol_version": "domains.f4_2_support_pdf_review.v1",
    "status": "structural_checks_passed",
    "reviews": reviews,
    "page_limit": None,
    "new_real_source_fits": 0,
    "visual_review": "pending human inspection of emitted sampled rasters",
    "limitations": "Checks page dimensions, extractable text, text bounds and requested scientific markers; representative rasters are emitted for visual inspection. This does not certify typography, tagged PDF, accessibility or every-page visual quality.",
}
(FOLDER / "support-pdf-review.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
