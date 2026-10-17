"""Prespecified Perten admission/preparation over public Datasets/Domains APIs.

Local source paths are explicit CLI inputs. No acquisition, solver or canonical
format implementation lives here. Existing files are never overwritten on reuse.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import urllib.request
import zipfile

import numpy as np
import pandas as pd
import yaml

from nirs4all_domains.admission import DIMENSIONS, freeze_admission, verify_admission, target_semantics
from nirs4all_domains.bank import bounded_qualify, file_plan, read, schema_check
from nirs4all_domains.dataset import task_from_dataset
from nirs4all_domains.registry import task_identity
from nirs4all_domains.storage import atomic_json, digest, estimate, fingerprint, tree_bytes

DATASET = "perten_cereals_nir"
REVISION = "e68d1befb6cb8245799e83d4b4e4c41e66287689"
RAW_SHA = "aa90b0df79f8206a491851bb60c102e72c4256ea2744c8d5eb90029d7eab259f"
UNIT = "source percent moisture; wet/dry basis ambiguous"


def immutable(path, value):
    path = Path(path)
    if path.exists():
        if read(path) != value:
            raise ValueError("FROZEN_RECORD_DIFFERS:"+path.name)
    else:
        atomic_json(path, value)


def metadata(leaf):
    m = pd.read_csv(leaf/"M.csv", sep=";", dtype=str).fillna("")
    if m.sample_id.duplicated().any() or m.observation_id.duplicated().any():
        raise ValueError("ORIGINAL_SPECIMEN_KEYS_REQUIRED")
    m["context_block"] = ["context:"+fingerprint(list(v)) for v in m[["instrument", "country", "year"]].itertuples(index=False, name=None)]
    blocks = sorted(m.context_block.unique(), key=lambda k:fingerprint([17, k]))
    retained = set(blocks[:math.ceil(.2*len(blocks))])
    m["partition"] = ["retained" if g in retained else "development" for g in m.context_block]
    return m


def keyed_source_tables(leaf, destination):
    """Use original specimen-keyed reference records; ignore the unkeyed local Y."""
    m = metadata(leaf)
    lookup = m.set_index("sample_id")
    raw = []
    with zipfile.ZipFile(leaf/"raw/sensAIfood_Perten.zip") as archive:
        for name in sorted(archive.namelist()):
            if name.endswith(".csv"):
                raw.extend(csv.DictReader(archive.read(name).decode("utf-8-sig").splitlines()))
    if len({r["ID"] for r in raw}) != len(raw) or {r["ID"] for r in raw} != set(m.sample_id):
        raise ValueError("ORIGINAL_REFERENCE_KEY_SET_MISMATCH")
    axis = list(map(str, range(950, 1651, 5)))
    destination.mkdir(parents=True, exist_ok=False)
    spectra = [{"observation_id":lookup.at[r["ID"],"observation_id"], **{k:r[k] for k in axis}} for r in raw]
    references = [{"observation_id":lookup.at[r["ID"],"observation_id"],"Moisture":r["Moisture"]} for r in raw]
    pd.DataFrame(spectra).to_csv(destination/"X.csv", sep=";", index=False)
    pd.DataFrame(references).to_csv(destination/"Y.csv", sep=";", index=False)
    m.drop(columns="partition").to_csv(destination/"M.csv", sep=";", index=False)
    return {r["ID"]:r for r in raw}


def audit(args):
    archive = args.leaf/"raw/sensAIfood_Perten.zip"
    if digest(archive) != RAW_SHA:
        raise ValueError("UNEXPECTED_ORIGINAL_ARCHIVE")
    with urllib.request.urlopen("https://zenodo.org/api/records/15838136", timeout=30) as response:
        record = json.load(response)
    official = next(f for f in record["files"] if f["key"] == archive.name)
    if official["checksum"] != "md5:"+hashlib.md5(archive.read_bytes()).hexdigest() or official["size"] != archive.stat().st_size:
        raise ValueError("OFFICIAL_SOURCE_CONTENT_DIFFERS")
    if record["metadata"].get("license", {}).get("id") != "cc-by-4.0" or record["metadata"].get("access_right") != "open":
        raise ValueError("LIVE_SOURCE_RIGHTS_DIFFER_FROM_EXPECTED")
    m = metadata(args.leaf)
    by_sample = m.set_index("sample_id")
    raw = []
    with zipfile.ZipFile(archive) as z:
        for name in sorted(z.namelist()):
            if name.endswith(".csv"):
                raw.extend(csv.DictReader(z.read(name).decode("utf-8-sig").splitlines()))
    if len(raw) != 450 or len({r["ID"] for r in raw}) != 450 or {r["ID"] for r in raw} != set(m.sample_id):
        raise ValueError("ORIGINAL_TO_LOCAL_SPECIMEN_KEYS_DIFFER")
    x = pd.read_csv(args.leaf/"X.csv", sep=";").set_index("observation_id")
    axis = list(map(str, range(950, 1651, 5)))
    if list(x.columns) != axis:
        raise ValueError("SOURCE_AXIS_CHANGED")
    for r in raw:
        oid = by_sample.at[r["ID"], "observation_id"]
        if not np.array_equal(np.asarray([r[c] for c in axis], dtype="float32"), x.loc[oid].to_numpy(dtype="float32")):
            raise ValueError("RAW_TO_STANDARD_X_KEYED_PARITY_FAILED")
    policy = read(args.policy)
    plan = file_plan(archive, 32*2**20, 4*2**20)
    budget = estimate(plan, policy, Path.cwd(), args.cache, args.out)
    if budget["status"] != "ready":
        raise ValueError(str(budget))
    source_hashes = {"archive": RAW_SHA, **{p.name:digest(p) for p in (args.leaf/"X.csv", args.leaf/"Y.csv", args.leaf/"M.csv")}}
    attribution = "sensAIfood / Perten; curator Dario Passos; DOI 10.5281/zenodo.15838136, version 1"
    permissions = {k:{"status":"allowed", "evidence":["https://zenodo.org/api/records/15838136: metadata.license.id=cc-by-4.0; access_right=open", attribution]} for k in DIMENSIONS}
    split = {"protocol":"domains.perten.context_block_holdout.v0.1", "seed":17,
             "rule":"ceil(20% context blocks), SHA256 order, before outcomes; remaining blocks form development CV",
             "records":[{k:r[k] for k in ("sample_id", "context_block", "partition")} for r in m.sort_values("sample_id").to_dict("records")]}
    spec = dict(dataset_id=DATASET, catalog_revision=REVISION, content_version="1.0.0", source_hashes=source_hashes,
        scientific_reference=["https://doi.org/10.5281/zenodo.15838136", attribution], permissions=permissions, source_id="X",
        target=dict(name="Moisture", semantic_role="quantitative_measurement", meaning="Oven reference moisture of whole cereal grain", unit=UNIT,
                    evidence=["Original cereal metadata XLSX: Reference Method Moisture=Oven; Units for Moisture=% moisture"]),
        identities={"original_sample_keys":{"status":"verified", "evidence":["450 unique original CSV ID values; all three XLSX Sampling notes: No duplicated in provided data"]},
                    "source_reference_alignment":{"status":"verified", "evidence":["X and Moisture in the same original specimen-keyed CSV record; keyed source adapter v1", "Unkeyed local standardized Y.csv is ignored; development parity uses original CSV ID, never row position"]},
                    "reference_scope":"logical specimen/Moisture record; original assay event IDs and shared assay evidence unavailable"},
        dependencies={"physical_samples":450, "context_blocks":22, "rule":"instrument/country/year tuple; unknown values share their declared tuple",
                      "limits":"Context is a conservative experimental block, not a verified batch; farm, serial instrument, harvest and assay dependencies unknown"},
        factors={"cereal_type":"original Cereal column", "instrument":"original Spectrometer model; 0 is missing",
                 "country":"original Country; growing versus measurement country ambiguous", "year":"original Year; 0 missing"},
        representation="technical_mean (450 singleton specimens, all 141 original channels)", split=split,
        independent_units=22, missing_fields=["assay event IDs", "reference precision", "original lot/farm", "spectrometer serial numbers", "unambiguous moisture basis"],
        budget={"policy_sha256":digest(args.policy), "scratch_upper_bytes":32*2**20, "evidence_upper_bytes":4*2**20,
                "dense_x_bytes":450*141*4, "expected_memory":"bounded 450x141 native matrix and transport; no process RSS hard quota",
                "compute":"3 outer x 3 inner folds; components 1..3; metadata-inadmissible designs skip fits"},
        review_evidence=["Official Zenodo API versus archive MD5/size", "Original CSV IDs and XLSX sampling/reference documentation",
                         "Raw-to-standard float32 X parity by original specimen identity; no model outcomes inspected"])
    admission = freeze_admission(spec)
    schema_check(admission, "task-admission")
    immutable(args.out/"perten-admission.json", admission)
    immutable(args.out/"pre-acquisition-budget.json", budget)
    public = []
    for d in read("docs/audit/catalog-inventory-alpha8.json")["datasets"]:
        if d["tier"] != "public":
            continue
        numeric = [v for v in d["targets"] if v["type"] == "numeric"]
        rejected = [v["name"] for v in numeric if target_semantics({"name":v["name"], "semantic_role":"quantitative_measurement", "meaning":"metadata screen only", "unit":"unverified", "evidence":["card"]})]
        public.append({"dataset_id":d["dataset_id"], "content_version":d["content_version"], "descriptor_sha256":d["descriptor_sha256"],
            "status":"pending", "reasons":["SOURCE_SAMPLE_REFERENCE_AND_GROUP_QUALIFICATION_REQUIRED_BEFORE_FITTING"],
            "numeric_targets":len(numeric), "identifier_like_targets_rejected":rejected,
            "coarse_P1_candidate":d["admission_status"]=="pending_P1", "physical_id_declared":d["ids"]["sample_id_available"],
            "family":"EcoSIS" if d["dataset_id"].startswith("ecosis") else d["dataset_id"],
            "permissions":{k:{"status":"unknown", "evidence":["Catalog declaration "+d["license"]+"; original source rights not independently checked"]} for k in DIMENSIONS},
            "selection":"deferred before prediction; Perten is the first documented non-leaf task"})
    immutable(args.out/"public-candidate-screen.json", {"catalog_revision":REVISION, "n_public":len(public),
        "n_coarse_P1":sum(r["coarse_P1_candidate"] for r in public), "records":public,
        "limitations":["Metadata screen, not admission. CABO revisions/views and CA2023 preparations may share specimens.",
                        "No botanical fallback selected because the non-leaf Perten case is admitted."]})
    print(json.dumps({"admission":admission["status"], "id":admission["admission_id"], "n_development":int((m.partition=="development").sum()),
                      "n_retained":int((m.partition=="retained").sum()), "budget":budget["status"]}))


def prepare(args):
    from nirs4all_datasets.canonical import build_canonical
    from nirs4all_datasets.schema import DatasetDescriptor
    from nirs4all_datasets import get
    record = read(args.out/"perten-admission.json")
    verify_admission(record)
    if (record["status"] != "admitted"
            or digest(args.leaf/"raw/sensAIfood_Perten.zip") != record["specification"]["source_hashes"]["archive"]
            or any(digest(args.leaf/k) != v for k,v in record["specification"]["source_hashes"].items() if k != "archive")):
        raise ValueError("ADMITTED_INPUT_CHANGED")
    # One external shared cache revision; never execute upstream's destructive converter.
    cache = args.cache/"domains-reproductions"/DATASET/(RAW_SHA+"-keyed-v1")
    leaf = cache/"datasets"/DATASET
    descriptor = yaml.safe_load((args.catalog/"catalog/datasets"/(DATASET+".yaml")).read_text(encoding="utf-8"))
    config = read(args.config)
    descriptor["variables"].append({"name":"context_block", "role":"metadata", "type":"categorical"})
    # Record an evidence-backed local descriptor derivation; upstream stays unchanged.
    descriptor["governance"]["license"] = "CC-BY-4.0"
    descriptor["governance"]["permitted_use"] = "Source CC-BY-4.0 with attribution, live API verified in admission"
    parsed = DatasetDescriptor.model_validate(descriptor)
    manifest = cache/"domains-cache-proof.json"
    if manifest.exists():
        proof = read(manifest)
        if proof["admission_id"] != record["admission_id"]:
            raise ValueError("CANONICAL_CACHE_ADMISSION_CONTRACT_MISMATCH")
        for p,v in proof["canonical_hashes"].items():
            if digest(leaf/p) != v:
                raise ValueError("CANONICAL_CACHE_CONTENT_MISMATCH")
    else:
        if leaf.exists():
            raise ValueError("UNKNOWN_PARTIAL_EXTERNAL_CACHE_PRESERVED")
        budget = estimate(file_plan(args.leaf/"X.csv", 4*2**20, 65536), read(args.policy), Path.cwd(), args.cache, args.out)
        if budget["status"] != "ready":
            raise ValueError(str(budget))
        keyed_source_tables(args.leaf, cache/"source-adapter-v1")
        converted = build_canonical(cache/"source-adapter-v1", parsed, leaf)
        if converted.status.value != "ok" or converted.warnings:
            raise ValueError(str(converted.warnings))
        (cache/"catalog/datasets").mkdir(parents=True)
        (cache/"catalog/datasets"/(DATASET+".yaml")).write_text(yaml.safe_dump(descriptor, sort_keys=False), encoding="utf-8")
        proof = {"admission_id":record["admission_id"], "canonical_hashes":{p.relative_to(leaf).as_posix():digest(p) for p in leaf.rglob("*") if p.is_file()},
                 "provider":"nirs4all-datasets 0.3.11 build_canonical", "bytes":tree_bytes([cache]),
                 "descriptor_derivation":"CC-BY-4.0 source permission override and context field declaration; private tier retained; upstream unchanged"}
        immutable(manifest, proof)
    ds = get(DATASET, root=cache)
    m = metadata(args.leaf)
    # Public transport wrapper supplies the frozen explicit experimental split/metadata.
    class View:
        def __getattr__(self, name): return getattr(ds, name)
        def split(self, name): return m[["sample_id", "partition"]]
        def metadata(self):
            frame = ds.metadata().set_index("sample_id")
            frame["context_block"] = m.set_index("sample_id").context_block
            return frame.reset_index()
    identities = {r["sample_id"]:{"physical_sample_id":r["sample_id"], "independence_group":r["context_block"],
        "reference_id":"Perten:Moisture:"+r["sample_id"], "reference_status":"unknown", "reference_unit":UNIT,
        "instrument":r["instrument"] or "unknown_model", "campaign":"source_Perten_Zenodo_v1"} for r in m.to_dict("records")}
    task = task_from_dataset(View(), dict(source_id="X", content_version="1.0.0", target_id="Moisture", target_unit=UNIT,
        split_id="alpha9-context-retained-17", partition_labels={"development":"train", "retained":"test"},
        identity_table=identities, representation="technical_mean", signal_unit="source signal as supplied; physical scale unspecified",
        pca_backend="flexible", pca_max_components=20, provenance={"admission_id":record["admission_id"], "original_archive_sha256":RAW_SHA}))
    # Revalidate against the admitted origin, including on cache reuse. The
    # cached intermediate Y is not independent evidence of original alignment.
    original = {}
    with zipfile.ZipFile(args.leaf/"raw/sensAIfood_Perten.zip") as archive:
        for name in sorted(archive.namelist()):
            if name.endswith(".csv"):
                for row in csv.DictReader(archive.read(name).decode("utf-8-sig").splitlines()):
                    if row["ID"] in original: raise ValueError("AMBIGUOUS_ORIGINAL_SPECIMEN_ID")
                    original[row["ID"]] = row
    if task["axis"] != list(range(950,1651,5)):
        raise ValueError("ORIGINAL_AXIS_PARITY_FAILED")
    if len(task["observations"]) != len(original) or {r["sample_id"] for r in task["observations"]} != set(original):
        raise ValueError("CANONICAL_ORIGINAL_SPECIMEN_KEY_SET_MISMATCH")
    if any(not np.array_equal(np.asarray(r["x"],dtype="float32"),np.asarray([original[r["sample_id"]][str(k)] for k in range(950,1651,5)],dtype="float32")) for r in task["observations"]):
        raise ValueError("CANONICAL_ORIGINAL_X_KEYED_PARITY_FAILED")
    if any(r["y"] != float(original[r["sample_id"]]["Moisture"]) for r in task["observations"] if r["partition"] == "train"):
        raise ValueError("DEVELOPMENT_REFERENCE_KEYED_PARITY_FAILED")
    if any("y" in r for r in task["observations"] if r["partition"] == "test"):
        raise ValueError("RETAINED_TARGET_LEAKAGE")
    task_path = args.out/"perten-task.json"
    immutable(task_path, task)
    identity = task_identity(dict(dataset_id=DATASET, content_version="1.0.0", dataset_revision=fingerprint(record["specification"]["source_hashes"]),
        source_id="X", target_id="Moisture", representation="technical_mean", split_protocol=record["specification"]["split"]["protocol"]+":"+fingerprint(record["specification"]["split"]),
        independence_policy="physical specimen + conservative instrument/country/year context closure v1",
        qualification_protocol="domains.split_stress.v0.1"))
    immutable(args.out/"perten-identity.json", identity)
    immutable(args.out/"perten-fit-admission.json", {"status":"admitted", "task_id":identity["task_id"], "input_sha256":digest(task_path), "record":record})
    immutable(args.out/"preparation.json", proof)
    print(json.dumps({"task_id":identity["task_id"], "rows":len(task["observations"]), "canonical_bytes":proof["bytes"], "test_target_accessed":False}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("audit", "prepare", "qualify"))
    for k in ("leaf", "cache", "catalog", "out", "policy", "config", "binary", "library"):
        p.add_argument("--"+k, type=Path, required=k not in ("binary", "library"))
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.command == "audit": audit(args)
    elif args.command == "prepare": prepare(args)
    else:
        receipts, final = bounded_qualify(args.out/"perten-task.json", read(args.out/"perten-identity.json"), read(args.config), read(args.policy),
            workspace=Path.cwd(), state=args.out/"state", scratch=args.out/"scratch", output=args.out/"evidence", binary=args.binary.resolve(),
            library=args.library.resolve(), domain="real", admission=read(args.out/"perten-fit-admission.json"))
        atomic_json(args.out/"stage-receipts.json", receipts)
        print(json.dumps([{"stage":r.get("stage"), "status":r["status"], "reason":r.get("reason"), "cache_hit":r["cache_hit"]} for r in receipts]))
        if final is None: raise SystemExit(2)


if __name__ == "__main__": main()
