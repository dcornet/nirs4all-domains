"""Inspect every generated PDF's actual text/pages and rasterize representative pages.

Engineering only; PyMuPDF is pinned with canonical wheel hashes and is never
part of the application. No OCR, model, spectral processing or page-count cap.
"""
import json
from pathlib import Path
import re

import pymupdf

folder=Path('demo/test-results/browser/f3_5')
manifest=json.loads((folder/'pdf-manifest.json').read_bytes())
assert manifest['page_limit'] is None and manifest['new_real_source_fits']==0
assert len(manifest['cases'])==16
reviews=[]
for case in manifest['cases']:
    path=folder/case['file']
    with pymupdf.open(path) as document:
        assert document.page_count>0
        texts=[page.get_text() for page in document]
        assert all(text.strip() for text in texts),f"Accidentally blank page in {path.name}"
        text=re.sub(r'\s+',' ',' '.join(texts))
        assert 'Report section selection' in text
        assert ('numerical_evidence_recomputed_for_export' in text)==case['machine'],path.name
        for fragment in case['required_text']:assert re.sub(r'\s+','',fragment) in re.sub(r'\s+','',text),(path.name,fragment)
        if case['name'].startswith('long-'):assert document.page_count>10,'Stress fixture must exercise long pagination'
        dimensions=[]
        for page in document:
            width,height=page.rect.width,page.rect.height
            expected=(595.28,841.89) if case['format']=='A4' else (612,792)
            assert abs(width-expected[0])<2 and abs(height-expected[1])<2
            words=page.get_text('words')
            assert all(x0>=-2 and y0>=-2 and x1<=width+2 and y1<=height+2 for x0,y0,x1,y1,*_ in words),(path.name,page.number,'visible text outside page')
            dimensions.append([width,height])
        captures=[]
        # Inspect actual PDF pixels, not screenshots pretending to be PDF pages.
        if case['format']=='A4' or case['name'] in ['live-figures','long-documentary-reading']:
            index=max(range(len(texts)),key=lambda i:len(texts[i])) if case['name']!='live-core' else 0
            if case['name']=='live-figures':index=next(i for i,t in enumerate(texts) if 'PCA coordinates figure' in re.sub(r'\s+',' ',t))
            if case['name']=='saved-some':index=next(i for i,t in enumerate(texts) if 'Complete verification readiness' in re.sub(r'\s+',' ',t))
            if case['name']=='long-documentary-reading':index=next(i for i,t in enumerate(texts) if 'documentary_field_649' in re.sub(r'\s+','',t))
            capture=f"{path.stem}-page-{index+1}.png";document[index].get_pixmap(dpi=96).save(folder/capture);captures.append(capture)
        reviews.append({'file':case['file'],'pages':document.page_count,'bytes':path.stat().st_size,'format':case['format'],
                        'machine_appendix_printed':case['machine'],'source_end_markers_preserved':case['required_text'],
                        'no_blank_page':True,'visible_text_bounds_checked':True,'raster_pages':captures})
result={'protocol':'domains.export_selection_pdf_review.v1','pymupdf':pymupdf.VersionBind,'reviews':reviews,'page_limit':None,
        'limitations':'Text/bounds and sampled real PDF raster checks are not tagged-PDF or complete typographic/accessibility certification.'}
(folder/'pdf-review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
