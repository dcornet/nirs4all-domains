"""Inspect actual synthetic F4.1 PDFs; use the already pinned CI-only PyMuPDF."""
import json
from pathlib import Path
import re

import pymupdf

folder = Path("demo/test-results/browser/f4.1/chromium")
reviews = []
for paper, expected in [("a4", (595.28, 841.89)), ("letter", (612, 792))]:
    path = folder / f"factor-association-{paper}.pdf"
    with pymupdf.open(path) as document:
        assert document.page_count > 0
        texts = [page.get_text() for page in document]
        assert all(t.strip() for t in texts), (path.name, "blank page")
        text = re.sub(r"\s+", " ", " ".join(texts))
        for marker in ["Descriptive associations by component", "Conditional inference", "batch", "dose", "not total spectral variance"]:
            assert marker in text, (path.name, marker)
        for page in document:
            width, height = page.rect.width, page.rect.height
            assert abs(width-expected[0]) < 2 and abs(height-expected[1]) < 2
            assert all(x0 >= -2 and y0 >= -2 and x1 <= width+2 and y1 <= height+2
                       for x0, y0, x1, y1, *_ in page.get_text("words")), (path.name, page.number, "text bounds")
        index = next(i for i, t in enumerate(texts) if "Descriptive associations by component" in re.sub(r"\s+", " ", t))
        image = f"factor-association-{paper}-table-page-{index+1}.png"
        document[index].get_pixmap(dpi=96).save(folder/image)
        reviews.append({"file": path.name, "pages": document.page_count, "bytes": path.stat().st_size,
                        "paper": paper, "no_blank_pages": True, "text_bounds_checked": True,
                        "scientific_markers_checked": True, "table_raster": image})
result = {"protocol_version": "domains.factor_pdf_review.v1", "status": "passed", "reviews": reviews,
          "page_limit": None, "new_real_source_fits": 0,
          "limitations": "Text/bounds plus sampled real PDF rasters; not tagged-PDF or complete typography/accessibility certification."}
(folder/"factor-pdf-review.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
print(json.dumps(result))
