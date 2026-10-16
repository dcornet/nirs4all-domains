"""EcoSIS pilot: keyed table transport, public Datasets canonicalization and native engines.

No spectral transform, fit, numerical mean or regression metric is implemented here.
Source tables are already wavelength-indexed CSV; all joins use original IDs.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import subprocess
import urllib.request

import pandas as pd
import numpy as np
import yaml

from nirs4all_domains import task_from_dataset
from nirs4all_domains.predictive import fingerprint, native_summary, predictive_sanity

SLUGS = {"freeze": "freeze-dried", "oven": "oven-dried", "fresh": "fresh"}
SUFFIX = "-leaf-spectra-and-measured-traits-from-the-sierra-nevada--ca--in-july-2023"


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fresh_output(path):
    path = Path(path).resolve()
    if path.exists():
        raise ValueError("Output must be a new directory; existing results are preserved")
    path.mkdir(parents=True)
    return path


def read_source(raw_root, kind):
    folder = Path(raw_root) / (SLUGS[kind]+SUFFIX)
    files = list(folder.glob("*.csv"))
    traits = next(p for p in files if "supplemental" in p.name.lower())
    spectra = next(p for p in files if "supplemental" not in p.name.lower())
    x, y = pd.read_csv(spectra), pd.read_csv(traits)
    if x.individualspectra_id.isna().any() or x.individualspectra_id.duplicated().any() or y.sample_id.isna().any() or y.sample_id.duplicated().any():
        raise ValueError("Original acquisition/trait IDs must be nonmissing and unique")
    if x.sample_id.isna().any() or not set(x.sample_id) <= set(y.sample_id):
        raise ValueError("Original spectra have no unique keyed trait record")
    axis = [c for c in x.columns if str(c).isdigit()]
    if axis != list(map(str, range(350, 2501))):
        raise ValueError("Unexpected original wavelength grid")
    return x, y, spectra, traits, axis


def source_audit(raw_root, output):
    result, source = {}, {}
    for kind in SLUGS:
        x, y, xp, yp, axis = read_source(raw_root, kind)
        source[kind] = (x, y)
        selected = y.set_index("sample_id").loc[sorted(set(x.sample_id))]
        result[kind] = {"n_samples": x.sample_id.nunique(), "n_spectra": len(x),
            "repeat_count_distribution": {str(k): v for k,v in Counter(x.groupby("sample_id").size()).items()},
            "n_plots": selected.plot_name.nunique(), "n_wavelengths": len(axis), "axis_nm": [350,2500],
            "nonfinite_spectral_cells":int((~np.isfinite(x[axis].to_numpy())).sum()),
            "repeated_numeric_LMA_across_sample_records":int(selected["LMA_value_g/m2"].dropna().duplicated().sum()),
            "target_nonmissing": {c:int(selected[c].notna().sum()) for c in ("LMA_value_g/m2","leaf_water_content_percent","chlorophyll _mg/m2")},
            "trait_rows_without_spectra": sorted(set(y.sample_id)-set(x.sample_id)),
            "source_hashes": {xp.name:sha(xp), yp.name:sha(yp)},
            "acquisition_ids_sha256": fingerprint(sorted(x.individualspectra_id.tolist())),
            "source_sample_ids": sorted(set(x.sample_id))}
    overlap = {}
    fields = ["sampling_date","plot_name","latitude_of_plot","longitude_of_plot","sample_number"]
    for a,b in (("freeze","oven"),("freeze","fresh"),("oven","fresh")):
        xa,ya=source[a];xb,yb=source[b]; common=sorted(set(xa.sample_id)&set(xb.sample_id))
        ya,yb=ya.set_index("sample_id"),yb.set_index("sample_id")
        same=all(ya.loc[s,fields].fillna("").astype(str).str.strip().equals(yb.loc[s,fields].fillna("").astype(str).str.strip()) for s in common)
        same_traits=all((pd.isna(ya.at[s,"LMA_value_g/m2"]) and pd.isna(yb.at[s,"LMA_value_g/m2"])) or ya.at[s,"LMA_value_g/m2"]==yb.at[s,"LMA_value_g/m2"] for s in common)
        overlap[a+"-"+b]={"shared_sample_codes":len(common),"matching_sampling_records":same,"matching_LMA_records":same_traits,
            "interpretation":"Shared CA2023 origin records corroborated by guides and keyed sampling metadata; material preparations/foreoptics remain distinct. No cross-dataset analysis performed."}
    result["cross_dataset_identity_audit"]=overlap
    write(output/"source-audit.json", result)
    return result


def verify_official(raw_root, output):
    slug=SLUGS["freeze"]+SUFFIX
    with urllib.request.urlopen("https://data.ecosis.org/api/3/action/package_show?id="+slug,timeout=30) as response:
        package=json.load(response)["result"]
    proof={"package_id":package["id"],"source_url":"https://data.ecosis.org/dataset/"+slug,
           "license_id":package["license_id"],"extras":{x["key"]:x["value"] for x in package["extras"]},"resources":[]}
    for resource in package["resources"]:
        with urllib.request.urlopen(resource["url"],timeout=30) as response:
            data=response.read()
        digest=hashlib.sha256(data).hexdigest()
        if resource["name"].lower().endswith(".csv"):
            local=Path(raw_root)/slug/resource["name"]
            if digest!=sha(local):
                raise ValueError("Held original CSV differs from current official resource: "+resource["name"])
        else:
            (output/"source-README.md").write_bytes(data)
        proof["resources"].append({"id":resource["id"],"name":resource["name"],"url":resource["url"],"sha256":digest,"bytes":len(data)})
    write(output/"official-source-proof.json",proof)
    return proof


def prepare(raw_root, descriptor_path, config, output):
    from nirs4all_datasets.canonical import build_canonical
    from nirs4all_datasets.schema import DatasetDescriptor
    x,y,xp,yp,axis=read_source(raw_root,"freeze")
    leaf=output/"keyed";leaf.mkdir()
    # Original acquisition IDs already identify wavelength-indexed records.
    x[["individualspectra_id"]+axis].rename(columns={"individualspectra_id":"observation_id"}).to_csv(leaf/"X.csv",sep=";",index=False)
    mapping=x[["individualspectra_id","sample_id"]].rename(columns={"individualspectra_id":"observation_id"})
    target=mapping.merge(y[["sample_id",config["target_id"]]],on="sample_id",how="left",validate="many_to_one")
    target.drop(columns="sample_id").to_csv(leaf/"Y.csv",sep=";",index=False)
    metadata=mapping.merge(y[["sample_id","plot_name","sampling_date","genus","species","latitude_of_plot","longitude_of_plot"]],on="sample_id",how="left",validate="many_to_one")
    metadata["instrument"]=config["instrument"];metadata["campaign"]=config["campaign"]
    metadata.to_csv(leaf/"M.csv",sep=";",index=False)
    descriptor_payload=yaml.safe_load(Path(descriptor_path).read_text(encoding="utf-8"))
    names={v["name"] for v in descriptor_payload["variables"]}
    for name in ("plot_name","campaign","sampling_date","latitude_of_plot","longitude_of_plot"):
        if name not in names:descriptor_payload["variables"].append({"name":name,"role":"metadata","type":"categorical"})
    descriptor=DatasetDescriptor.model_validate(descriptor_payload)
    catalog=output/"catalog-root"; destination=catalog/"datasets"/config["dataset_id"]
    if destination.exists(): raise ValueError("Canonical destination must be new")
    canonical=build_canonical(leaf,descriptor,destination)
    if canonical.status.value!="ok" or canonical.warnings:
        raise ValueError(f"Canonical qualification failed: {canonical.warnings}")
    card=catalog/"catalog/datasets";card.mkdir(parents=True)
    descriptor_local=card/(config["dataset_id"]+".yaml")
    descriptor_local.write_text(yaml.safe_dump(descriptor_payload,sort_keys=False),encoding="utf-8")
    import nirs4all_datasets as datasets
    ds=datasets.get(config["dataset_id"],root=catalog)
    # Compare by original acquisition IDs, including Datasets' documented float32 storage.
    original=x.set_index("individualspectra_id").loc[list(ds.observation_ids("X")),axis].to_numpy(dtype="float32")
    import numpy as np
    if not np.array_equal(original,ds.x("X"),equal_nan=True):
        raise ValueError("Canonical spectra differ from the keyed original float32 values")
    values=ds.y(config["target_id"]).set_index("sample_id")[config["target_id"]]
    original_y=y.set_index("sample_id")[config["target_id"]].loc[values.index]
    if not np.array_equal(values.to_numpy(),original_y.to_numpy(),equal_nan=True):
        raise ValueError("Canonical targets differ from the original keyed records")
    evidence={"canonical_hashes":canonical.canonical_hashes,"canonical_counts":canonical.row_counts,"canonical_warnings":canonical.warnings,
        "registry_descriptor_sha256":sha(descriptor_path),"local_descriptor_sha256":sha(descriptor_local),
        "descriptor_derivation":"Explicit metadata declarations for original plot/campaign/sampling/coordinates; upstream descriptor unchanged",
        "canonical_converter_version":canonical.converter_version,"original_spectra_sha256":sha(xp),"original_traits_sha256":sha(yp),
        "keyed_original_canonical_float32_parity":True,"historical_registry_canonical_parity":"unavailable; historical arrays not held",
        "signal_summary_as_supplied":native_summary(original.reshape(-1).tolist()),
        "nonfinite_canonical_cells":int((~np.isfinite(ds.x("X"))).sum()),"missing_LMA_samples":values.index[values.isna()].tolist(),
        "n_LMA_available":int(values.notna().sum()),"laboratory_reference_precision":"unavailable",
        "reference_identity":"logical original sample/trait records, not independent laboratory assay event IDs"}
    write(output/"preparation.json",evidence)
    return ds,metadata,evidence


class ExperimentalDataset:
    """Preserve the public getter seam; supply a separately named experimental split."""
    def __init__(self, dataset, split): self.dataset,self.split_table=dataset,split
    def __getattr__(self,name): return getattr(self.dataset,name)
    def split(self,name): return self.split_table


def grouped_split(metadata, seed, fraction):
    samples=metadata[["sample_id","plot_name"]].drop_duplicates()
    if samples.sample_id.duplicated().any() or samples.plot_name.isna().any():
        raise ValueError("Every sample must have exactly one documented plot")
    groups=sorted(samples.plot_name.unique(),key=lambda g:fingerprint([seed,g]))
    retained=set(groups[:math.ceil(fraction*len(groups))])
    return pd.DataFrame({"sample_id":samples.sample_id,"partition":["retained" if g in retained else "development" for g in samples.plot_name]})


def run_pilot(args):
    output=fresh_output(args.out)
    config=yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    source=source_audit(args.raw_root,output)
    proof=verify_official(args.raw_root,output)
    ds,metadata,preparation=prepare(args.raw_root,args.descriptor,config,output)
    binary,library=Path(args.binary).resolve(),Path(args.methods_library).resolve()
    summary={"protocol_version":"domains.repeated_pilot.v0.1","engine_version":"0.1.0-alpha.4","dataset_id":ds.id,
        "config_sha256":sha(args.config),"runner_sha256":sha(__file__),"domains_binary_sha256":sha(binary),"methods_binary_sha256":sha(library),
        "target":config["target_id"],"source_audit":source,"source_proof":proof,"preparation":preparation,"splits":[],
        "identity_assumptions":["Original sample code identifies dried specimen; plant identity and replicate subtype unverified",
            "Plot blocks are conditionally independent within the sampled geographical areas; no new-region generalization claim",
            "Mean of documented spectral replicates is descriptive; pure rescan noise is not identifiable"]}
    mean_task=None
    for seed in [config["primary_seed"]]+config["sensitivity_seeds"]:
        split=grouped_split(metadata,seed,config["test_group_fraction"])
        split_dir=output/f"seed-{seed}";split_dir.mkdir()
        write(split_dir/"split.json",{"seed":seed,"method":"ceil(20% of observed plots), SHA-256 order; no X/Y use", "rows":split.to_dict("records")})
        identities={sid:{"physical_sample_id":sid,"reference_id":"CA2023:LMA:"+sid,
            "reference_status":"unknown","reference_unit":config["target_unit"],"repetition_type":config["repeat_type"]}
            for sid in split.sample_id}
        snapshot={"seed":seed,"n_train_samples":int((split.partition=="development").sum()),"n_test_samples":int((split.partition=="retained").sum()),"policies":{}}
        for policy in ("grouped_native","technical_mean"):
            cfg={**config,"seed":seed,"identity_table":identities,"representation":policy,
                "provenance":{"reference_identity":"logical source sample/trait record, not laboratory event ID", "source_spectra_sha256":preparation["original_spectra_sha256"],
                    "repeat_interpretation":"documented spectral replicates; subtype unknown; descriptive mean only"}}
            task=task_from_dataset(ExperimentalDataset(ds,split),cfg)
            for row in task["observations"]: row["metadata"]["technical_repeat_evidence"]=config["technical_repeat_evidence"]
            path=split_dir/(policy+"-task.json");write(path,task)
            for name in (policy,policy+"-repeat"):
                subprocess.run([str(binary),"analyze",str(path),"--out",str(split_dir/name),"--methods-library",str(library)],check=True)
            first=(split_dir/policy/"report.json").read_bytes()
            if first!=(split_dir/(policy+"-repeat")/"report.json").read_bytes():raise AssertionError("Pilot reports not reproducible")
            report=json.loads(first);metrics={m["metric_id"]:m for m in report["metrics"]}
            coverage=metrics["coverage.test_outside_fraction"]
            if coverage["status"]!="computed" or report["test_target_accessed"]:raise AssertionError("Coverage unavailable or test target accessed")
            within=metrics.get("measurement.native_within_id",{})
            snapshot["policies"][policy]={"report_sha256":hashlib.sha256(first).hexdigest(),"reproducible":True,"unit_counts":{k:report["unit_audit"][k] for k in ("train","test")},
                "metrics":{k:metrics[k]["value"] for k in ("coverage.effective_dimension","domain.centroid_distance","domain.dispersion_ratio","coverage.test_outside_fraction")},
                "coverage_outside":len(coverage["observation_ids"]),"coverage_denominator":coverage["parameters"]["denominator"],
                "n_train_representation_rows":len(report["fit"]["fit_observation_ids"]),
                "coverage_uncertainty":coverage["uncertainty"],"n_components":report["fit"]["n_components"],"retained_variance_fraction":report["fit"]["retained_variance_fraction"],
                "nn_threshold":report["fit"]["nn_threshold"],"q_threshold":report["fit"]["reconstruction_squared_threshold"],
                "native_pooled_sd_summary":native_summary(v for v in within.get("value",{}).get("pooled_sd",[]) if v is not None)}
            if policy=="technical_mean" and seed==config["primary_seed"]:
                mean_path=split_dir/"mean-representation-task.json"
                subprocess.run([str(binary),"represent",str(path),"--out",str(mean_path),"--methods-library",str(library)],check=True)
                mean_task=json.loads(mean_path.read_text(encoding="utf-8"))
                subprocess.run([str(binary),"analyze",str(mean_path),"--out",str(split_dir/"mean-xy"),"--methods-library",str(library)],check=True)
                xy=json.loads((split_dir/"mean-xy/report.json").read_text(encoding="utf-8"))
                snapshot["mean_xy_preflight"]=[m for m in xy["preflight"]["metrics"] if m["metric_id"].startswith("local.")]
            if seed==config["primary_seed"] and config.get("train_refit_bootstrap_draws",0):
                stability_path=split_dir/(policy+"-train-refit-bootstrap.json")
                subprocess.run([str(binary),"stability",str(path),"--out",str(stability_path),"--draws",str(config["train_refit_bootstrap_draws"]),"--methods-library",str(library)],check=True)
                stability=json.loads(stability_path.read_text(encoding="utf-8"))
                snapshot["policies"][policy]["train_refit_bootstrap"]={k:v for k,v in stability.items() if k!="replicates"}
        summary["splits"].append(snapshot)
        write(output/"comparison-checkpoint.json",summary)
        print(f"Coverage seed {seed}: native and mean complete",flush=True)
    predictive=predictive_sanity(mean_task,library,seed=config["primary_seed"],progress=lambda s:print(s,flush=True),**config["predictive"])
    write(output/"predictive-sanity.json",predictive)
    summary["predictive_sanity"]={k:v for k,v in predictive.items() if k not in ("oof","lineage","outer_fold_set")}
    summary["predictive_sanity"]["full_report_sha256"]=sha(output/"predictive-sanity.json")
    write(output/"comparison.json",summary)
    lines=["# EcoSIS repeated-data pilot", "", "| Dataset | Target | N samples | N spectra | N train | N test | Policy | Coverage warnings | Predictive sanity check | Limitations |", "|---|---|---:|---:|---:|---:|---|---|---|---|"]
    for split in summary["splits"]:
        for policy,r in split["policies"].items():
            interval=r["coverage_uncertainty"].get("interval_95")
            probe=f"development nested OOF RMSE {predictive['pls']['rmse']:.4g} vs null {predictive['null']['rmse']:.4g}" if split["seed"]==config["primary_seed"] and policy=="technical_mean" else "not run; prespecified scope"
            lines.append(f"| Freeze Dried (seed {split['seed']}) | LMA g/m2 | 82 | 492 | {split['n_train_samples']} samples / {r['n_train_representation_rows']} rows | {split['n_test_samples']} samples / {r['coverage_denominator']} rows | {policy} | {r['coverage_outside']}/{r['coverage_denominator']}; sample/plot bootstrap 95% {interval} | {probe} | Conditional plot independence; replicate subtype unknown; fixed-fit uncertainty |")
    lines += ["", "All thresholds fit train only. Native warnings count acquisitions; aggregated warnings count physical samples. Their denominators and train-fitted geometries differ. The bootstrap statistic uses one physical-sample vote in either view.", "", "Retained Y_test is not passed to coverage, CV, selection or permutations. The predictive check uses development samples only. Original files matched the current official downloads; canonical float32 parity was checked by acquisition ID. Historical registry arrays remain unavailable."]
    (output/"comparison.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"coverage":[{"seed":s["seed"],"policies":{k:{"outside":v["coverage_outside"],"denominator":v["coverage_denominator"]} for k,v in s["policies"].items()}} for s in summary["splits"]],"pls":predictive["pls"],"null":predictive["null"],"permutation_p":predictive["permutation"]["p_exploratory"]},indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("raw-root","descriptor","binary","methods-library","out"):parser.add_argument("--"+name,required=True)
    parser.add_argument("--config",default="configs/pilots/ecosis_freeze_dried.yaml")
    run_pilot(parser.parse_args())


if __name__=="__main__":main()
