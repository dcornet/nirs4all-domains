"""Audit canonical/source/Task factor transport before any alpha.6 outcome analysis."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from nirs4all_domains.dependence import audit_factors, development_rows
from nirs4all_domains.predictive import group_folds


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(task_path, catalog, traits, config_path, out):
    import nirs4all_datasets as datasets
    import pandas as pd
    out.mkdir(parents=True,exist_ok=False)
    task=json.loads(task_path.read_text())
    ds=datasets.get(task["context"]["dataset_id"],root=catalog)
    with traits.open(encoding="utf-8-sig",newline="") as handle:
        source=list(csv.DictReader(handle))
    raw={r["sample_id"]:r for r in source}
    if len(raw)!=len(source):raise ValueError("Ambiguous original sample IDs")
    canonical_metadata=ds.metadata()
    original_keys=set(canonical_metadata.columns)
    transport=[]
    for field in ("genus","species"):
        # These explanatory variables were declared as targets by the source descriptor.
        # No LMA/test-target accessor is used here.
        frame=ds.y(field)
        if frame["sample_id"].duplicated().any():raise ValueError("Ambiguous canonical factor IDs")
        keyed=frame.set_index("sample_id")[field].to_dict()
        for row in task["observations"]:
            if row["partition"]!="train":continue
            sid=row["sample_id"]
            value=keyed[sid]
            if pd.isna(value):
                if raw[sid][field].strip():raise ValueError("Missing canonical factor with nonempty source")
                continue
            if str(value)!=raw[sid][field]:raise ValueError("Source/canonical factor mismatch")
            # Prespecified lexical cleanup only; no taxonomic/outcome-driven merge.
            if str(value).strip():row["metadata"][field]=str(value).strip()
        transport.append({"field":field,"canonical_getter":"y("+field+")",
                          "descriptor_role":"target","in_old_metadata":field in original_keys,
                          "old_task_present":False,"join":"exact sample_id; never position",
                          "source_canonical_parity":True,"normalization":"strip leading/trailing whitespace; source blanks remain missing"})
    old=json.loads(task_path.read_text())
    if any({k:v for k,v in a.items() if k!="metadata"}!={k:v for k,v in b.items() if k!="metadata"} for a,b in zip(old["observations"],task["observations"],strict=True)):
        raise ValueError("Metadata augmentation altered scientific rows")
    rows=development_rows(task)
    config=json.loads(config_path.read_text())
    folds=group_folds(rows,config["outer_folds"],config["seed"],"outer")
    report={"protocol_version":"domains.structural_dependence.v0.1","phase":"metadata audit before new outcome experiments",
            "input_task_sha256":sha(task_path),"source_traits_sha256":sha(traits),
            "canonical_metadata_columns":sorted(original_keys),"transport":transport,
            "unchanged_X_Y_axis_partitions_order":True,"test_target_accessed":False,
            "factors":audit_factors(rows,config["factors"],folds),
            "coordinates":{"latitude_column":"latitude_of_plot","longitude_column":"longitude_of_plot",
                "missing_development_ids":[r["physical_sample_id"] for r in rows if not r["metadata"].get("latitude_of_plot") or not r["metadata"].get("longitude_of_plot")],
                "use":"audited only; no coordinate bins or invented regional groups"},
            "independence":"plot constraints retained; original plant/assay independence and precision remain unverified",
            "cluster_factors":"unavailable; no qualified fold-local held-out assignment"}
    for name,value in (("factor-transport-audit.json",report),("augmented-task.json",task)):
        (out/name).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("task","catalog","traits","config","out"):p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    report=prepare(a.task,a.catalog,a.traits,a.config,a.out)
    print(json.dumps([{k:f[k] for k in ("field","n_levels","seen_count","fallback_fraction","eligible_conditional_evidence")} for f in report["factors"]],indent=2))
