"""Bounded X-first campaign over the pinned public cohort; no target-table reads."""
import argparse
import json
from pathlib import Path
import time
import urllib.request

from nirs4all_domains.adaptive import PROTOCOL, coverage_record, spectral_request, x_characterization
from nirs4all_domains.dependence import state
from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leaf-root", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--only")
    args = parser.parse_args()
    public = Path("docs/benchmarks/alpha11/public")
    root = Path(".audit/alpha11")
    policy = json.loads(Path("configs/bank/storage-policy-alpha11.json").read_text())
    store = StageStore("results/alpha9-perten-keyed/state", root/"scratch", root/"evidence", Path.cwd(), policy)
    inventory = json.loads(Path("docs/audit/catalog-inventory-alpha8.json").read_text())
    records = [r for r in inventory["datasets"] if r["tier"] == "public"]
    if len(records) != 42:
        raise ValueError("PINNED_PUBLIC_COHORT_CHANGED")
    binary, library = args.binary.resolve(), args.library.resolve()
    for record in records:
        name = record["dataset_id"]
        if args.only and args.only not in name:
            continue
        destination = public/(name+".json")
        if destination.exists():
            print(json.dumps({"dataset": name, "existing": True}), flush=True)
            continue
        leaf = args.leaf_root/name
        card = json.loads((leaf/"dataset_card.json").read_text(encoding="utf-8"))
        original = card.get("official_source", {})
        api = original.get("api_url")
        rights = {"status": "unavailable", "reason": "ORIGINAL_RIGHTS_NOT_VERIFIED", "value": None}
        if api:
            meta = root/"source"/(name+"-package.json")
            try:
                if not meta.exists():
                    raw = urllib.request.urlopen(api, timeout=30).read(2**20)
                    meta.parent.mkdir(parents=True, exist_ok=True)
                    meta.write_bytes(raw)
                data = json.loads(meta.read_bytes())["result"]
                if data.get("license_id") in ("odc-by", "odc-odbl", "cc-by", "cc-by-sa", "cc-zero"):
                    rights = state({"source": api, "license_id": data["license_id"], "metadata_sha256": digest(meta),
                                    "attribution": data.get("author", data.get("title"))})
            except Exception as error:
                rights = state(reason=f"ORIGINAL_RIGHTS_CHECK_FAILED:{type(error).__name__}:{error}")
        elif name == "cartilage_spectroscopy_scientificdata_nir":
            rights = state({"source": "10.6084/m9.figshare.7803845.v2", "license": "CC0", "evidence": "alpha10 original-source audit"})
        source = record["sources"][0]
        path = leaf/("X.csv" if source["source_id"] == "X" else source["source_id"]+".csv")
        identity = "declared_but_unverified_identity" if record["ids"]["sample_id_available"] else "observation_identity_only"
        levels = {k: state(reason=v) for k, v in {"X0": "NOT_EXECUTED", "X1": "NO_VERIFIED_NATIVE_EVALUATION_PARTITION",
            "XY": "ORIGINAL_KEYED_TARGET_ALIGNMENT_NOT_ADMITTED", "XYM": "TARGET_OR_FACTOR_PROVENANCE_NOT_ADMITTED",
            "MODEL": "INDEPENDENT_PHYSICAL_REFERENCE_POLICY_NOT_ADMITTED"}.items()}
        report, receipt = None, None
        cost = {"seconds": 0, "model_fits": 0, "pca_fits": 0, "new_matrix_bytes": 0}
        if rights["status"] != "computed":
            levels["X0"] = state(reason=rights["reason"])
        elif not path.exists():
            levels["X0"] = state(reason="LOCAL_SPECTRAL_INPUT_UNAVAILABLE; NO_AUTOMATIC_ACQUISITION")
        elif source["n_observations"]*source["n_variables"] > 10_000_000 or source["n_observations"]**2*min(20,source["n_variables"]) > 250_000_000:
            levels["X0"] = state(reason="FULL_POPULATION_NATIVE_GEOMETRY_BUDGET_EXCEEDED")
        else:
            contract = {"task": {"task_id": fingerprint([name, source["source_id"], PROTOCOL])},
                "input_sha256": digest(path), "rights": rights, "protocol": PROTOCOL,
                "binary_sha256": digest(binary), "library_sha256": digest(library),
                "controller_sha256": digest(__file__), "adapter_sha256": digest("bridges/python/nirs4all_domains/adaptive.py")}
            plan = {"inputs": [{"path": str(path.resolve()), "sha256": digest(path), "bytes": path.stat().st_size}],
                "scratch_bytes": 4096, "evidence_bytes": 196608, "expected_fits": 1, "expected_permutations": 0,
                "uncertainty": "Streamed full X; no persistent matrix. Native process <=10M cells, <=250M neighbor products. Peak memory estimated <1.5GiB, not a hard OS quota."}
            def run(folder):
                request = spectral_request(path, source["source_id"], identity)
                request["axis_unit"] = source["axis_unit"]
                begin = time.perf_counter()
                result = x_characterization(request, binary, library)
                result["elapsed_seconds"] = time.perf_counter()-begin
                return result
            receipt, report = store.run(contract, "P2", plan, run)
            if report is None:
                levels["X0"] = state(reason=receipt["reason"], status="failed" if receipt["status"]=="failed" else "unavailable")
            else:
                levels["X0"] = state({"protocol": PROTOCOL, "input_sha256": report["input_sha256"]})
                cost.update(seconds=report["elapsed_seconds"], pca_fits=1, hdbscan_fits=sum(x["status"]=="computed" for x in report["cluster_settings"]))
        value = coverage_record(name, source["source_id"], identity, levels, report, target=None, rights=rights,
            catalog_revision=inventory["catalog_revision"], descriptor_sha256=record["descriptor_sha256"],
            cohort_unit="catalog entry; variants not independent scientific populations", source_dimensions=source,
            metadata_fields_available=record["metadata_fields"], declared_targets=[r["name"] for r in record["targets"]],
            computational_cost=cost, stage_receipt=receipt)
        atomic_json(destination, value, 4194304)
        print(json.dumps({"dataset": name, "X0": levels["X0"]["status"], "reason": levels["X0"]["reason"], "seconds": cost["seconds"]}), flush=True)


if __name__ == "__main__":
    main()
