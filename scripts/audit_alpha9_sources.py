"""Read-only source re-audit; publishes provenance decisions, never source arrays."""
import argparse
import json
from pathlib import Path
import urllib.request

import yaml

from nirs4all_domains.admission import DIMENSIONS
from nirs4all_domains.storage import atomic_json, digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root",type=Path,required=True)
    parser.add_argument("--pilot",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    screen=json.loads((args.pilot/"public-candidate-screen.json").read_text())
    records={r["dataset_id"]:r for r in screen["records"]}
    for r in records.values():
        descriptor=yaml.safe_load((Path(".audit/datasets/catalog/datasets")/(r["dataset_id"]+".yaml")).read_text(encoding="utf-8"))
        r.update(catalog_revision=screen["catalog_revision"],source_hashes={"descriptor_sha256":r["descriptor_sha256"],"raw":"unknown; not acquired"},
            scientific_reference=[s["locator"] for s in descriptor.get("origin_sources",[]) if s["kind"]!="script"],
            source_x=[s["source_id"] for s in descriptor["sources"]], target_y="not frozen; semantic/source screening pending",
            target_units="unverified",verified_sample_reference_identities="unverified; descriptor keys are declarations",
            dependencies="technical/biological/assay dependencies unverified",factor_provenance="catalog declarations only",
            representation="not frozen",split="not frozen",independent_units=None,
            missing_fields=["original specimen/reference equivalence","qualified independent units","target-specific unit/semantics","source rights evidence"],
            expected_budget={"acquisition_bytes":None,"scratch_bytes":None,"fit_count":0,"compute":"not scheduled"})
    def candidate(name, reference, blockers, permissions, **extra):
        descriptor=yaml.safe_load((Path(".audit/datasets/catalog/datasets")/(name+".yaml")).read_text(encoding="utf-8"))
        leaf=args.source_root/name
        return dict(dataset_id=name,catalog_revision=screen["catalog_revision"],content_version=descriptor["versions"]["content"],
            source_hashes={p.name:digest(p) for p in (leaf/"source_to_standard.py",leaf/"M.csv") if p.exists()},
            scientific_reference=reference,permissions=permissions,source_x=[s["source_id"] for s in descriptor["sources"]],
            target_y=[v["name"] for v in descriptor["variables"] if v["role"]=="target"],target_units="not independently qualified",
            verified_sample_reference_identities="pending original-source equivalence",dependencies="pending original dependency audit",
            factor_provenance="catalog/source declarations, not qualified deployment factors",representation="not frozen",split="not frozen",
            independent_units=None,missing_fields=blockers,expected_budget={"acquisition_bytes":None,"scratch_bytes":None,"fit_count":0},
            status="pending",reasons=blockers,**extra)
    def permissions(access, explanation):
        return {k:{"status":"allowed" if k=="access" and access else "unknown", "evidence":[explanation]} for k in DIMENSIONS}
    corn=args.source_root/"corn_eigenvector_nir/raw/corn.mat"
    from scipy.io import loadmat  # container decoding only, no scientific kernel
    data=loadmat(corn,struct_as_record=False,squeeze_me=True)
    identity_fields={}
    for name in ("m5spec","mp5spec","mp6spec","propvals"):
        item=data[name]
        identity_fields[name]={"row_labels_size":int(item.label[0,0].size),"row_axis_size":int(item.axisscale[0,0].size),
                               "shape":list(item.data.shape)}
    if any(v["row_labels_size"] or v["row_axis_size"] for v in identity_fields.values()):
        raise ValueError("CORN_SOURCE_IDENTITY_AUDIT_CHANGED_REVIEW_REQUIRED")
    records["corn_eigenvector_nir"]=candidate("corn_eigenvector_nir",["https://eigenvector.com/resources/data-sets/"],
        ["NO_ORIGINAL_ROW_SAMPLE_KEYS_IN_ALL_THREE_SOURCES_OR_PROPERTY_OBJECT","ANALYSIS_AND_PUBLICATION_PERMISSION_UNRESOLVED","TARGET_UNITS_AND_ASSAY_KEYS_UNVERIFIED"],
        permissions(True,"Eigenvector offers 80 corn samples on three instruments for standardization benchmarking; no explicit reuse license found"),
        original_mat={"sha256":digest(corn),"bytes":corn.stat().st_size,"objects":identity_fields},
        resolution="Original key table mapping each instrument and property record to a specimen/assay; explicit analysis/result publication permission. 80 samples, never 240.")
    records["ucph_tablet_nir"]=candidate("ucph_tablet_nir",["https://ucphchemometrics.com/tablet/"],
        ["PHYSICAL_SPECIMEN_KEYS_UNVERIFIED","SHARED_BATCH_REPLICATE_IS_NOT_A_SPECIMEN_KEY","ANALYSIS_PUBLICATION_REDISTRIBUTION_PERMISSION_UNKNOWN"],
        permissions(True,"Official UCPH page provides a Matlab download and Dyrby et al. 2002 reference; no explicit reuse license on inspected page"),
        resolution="Provider specimen and assay mapping for NIR/NIT/Raman, with allowed analysis/publication scope; do not reconstruct identities from batch and replicate alone.")
    records["pharmaceutical_tablets_nir_shootout_eigenvector"]=candidate("pharmaceutical_tablets_nir_shootout_eigenvector",["https://eigenvector.com/resources/data-sets/"],
        ["ORIGINAL_TO_CANONICAL_SPECIMEN_REFERENCE_EQUIVALENCE_UNVERIFIED","PAIRED_PROTOCOL_ANALYSIS_PUBLICATION_PERMISSION_UNKNOWN"],
        permissions(True,"Eigenvector offers Shootout for training/algorithm testing; original announcement says 654, local conversion says 655; explicit license not found"),
        resolution="Resolve 654/655 count and original keyed partition/reference mapping; historical X1 analysis remains preserved, not promoted to paired qualification.")
    with urllib.request.urlopen("https://api.figshare.com/v2/articles/7803845",timeout=30) as response:
        cartilage=json.load(response)
    if cartilage["license"]["name"]!="CC0":raise ValueError("CARTILAGE_ORIGINAL_RIGHTS_CHANGED_REVIEW_REQUIRED")
    records["cartilage_spectroscopy_scientificdata_nir"]=candidate("cartilage_spectroscopy_scientificdata_nir",
        ["https://doi.org/10.1038/s41597-019-0170-y","https://doi.org/10.6084/m9.figshare.7803845.v2"],
        ["LOCAL_DERIVED_X_Y_JOIN_NOT_VERIFIED_AGAINST_ORIGINAL_MAT_KEYS","JOINT_LOCATION_REGION_AND_DONOR_CLOSURE_REQUIRES_ORIGINAL_ADAPTER","FULL_869_LOCATION_DEEP_WORKFLOW_EXCEEDS_SOFTWARE_500_ROW_GUARD"],
        {k:{"status":"allowed","evidence":["Figshare article 7803845 version 2 license CC0, live API verified; article itself CC-BY-4.0"]} for k in DIMENSIONS},
        original_files=[{k:f[k] for k in ("name","size","computed_md5")} for f in cartilage["files"]],
        prior_prediction_concern="Previously reported poor prediction is retained as unresolved; not evidence of misalignment, not a reason for score-based rejection.",
        resolution="Use original Figshare nirs_and_references_revised.mat, not the Springer ISA-Tab metadata ZIP. Verify 869 location keys, three spectra per location, 44 regions/five joints and donor links. Qualify scale or retain unavailable deep stages; never truncate to 500.")
    perten=json.loads((args.pilot/"perten-admission.json").read_text())
    records["perten_cereals_nir"]={"dataset_id":"perten_cereals_nir","status":"admitted",
        "admission_id":perten["admission_id"],"admission_ref":"docs/benchmarks/alpha9/perten-admission.json",
        "admission_sha256":digest(args.pilot/"perten-admission.json"),
        "resolved":["Live CC-BY-4.0 source overrides stale private/LicenseRef catalog inference for this task",
                    "450 original distinct specimen IDs; repeated original_row_id is a local counter",
                    "Original CSV identity adapter replaces unkeyed standardized Y, with no positional pairing"],
        "remaining":perten["specification"]["missing_fields"]}
    atomic_json(args.out,{"protocol_version":"domains.alpha9.source_admission_audit.v0.1","catalog_revision":screen["catalog_revision"],
        "n_public_screened":42,"n_coarse_P1":33,"additional_real_tasks_admitted":1,"records":list(records.values()),
        "limits":["Single-agent source audit corroborates official rights and original metadata; no independent human review is claimed.",
                  "No acquisition/model fitting for pending cases. Owner explicitly chose to keep CORN pending without a rights justification; missing original keys independently block pairing."]})
    print(json.dumps({"reviewed_records":len(records),"admitted_new_real_tasks":1,"out_bytes":args.out.stat().st_size}))


if __name__=="__main__":main()
