"""Bounded original-source acquisition via the published Datasets provider."""
import hashlib
import json
from pathlib import Path
import urllib.request

from nirs4all_domains.storage import StageStore, atomic_json, digest, fingerprint


def main():
    api = "https://api.figshare.com/v2/articles/7803845/versions/2"
    metadata = json.load(urllib.request.urlopen(api, timeout=40))
    item, = [f for f in metadata["files"] if f["name"] == "nirs_and_references_revised.mat"]
    if metadata["license"]["name"] != "CC0" or item["size"] != 26657431 or item["computed_md5"] != "0c43074bc039fcd93a38999a9af76d26":
        raise ValueError("ORIGINAL_SOURCE_CONTRACT_CHANGED")
    root = Path(".audit/alpha10")
    atomic_json(root/"figshare-v2.json", metadata)
    source = {"doi": "10.6084/m9.figshare.7803845.v2", "license": "CC0", "api_sha256": digest(root/"figshare-v2.json"),
              "name": item["name"], "bytes": item["size"], "md5": item["computed_md5"]}
    contract = {"task": {"task_id": fingerprint(["cartilage", "original-admission-alpha10", source])},
                "source": source, "runner_sha256": digest(__file__), "protocol": "domains.alpha10.cartilage_admission.v0.1"}
    policy = json.loads(Path("configs/bank/storage-policy-alpha10.json").read_text())
    store = StageStore("results/alpha9-perten-keyed/state", root/"scratch", root/"evidence", Path.cwd(), policy)
    plan = {"inputs": [{"sha256": "official-md5:"+source["md5"], "bytes": source["bytes"]}],
            "scratch_bytes": 65536, "evidence_bytes": 16384, "expected_fits": 0, "expected_permutations": 0,
            "uncertainty": "Original compressed MAT size pinned; no canonical conversion or model fits."}

    def acquire(folder):
        from nirs4all_datasets._acquire import retrieve_raw
        route = {"id": "figshare-revised-v2", "provider": "figshare", "method": "raw_retrieve", "access": "open",
                 "locator": source["doi"], "resources": [{"id": "original-mat", "role": "raw", "required": True,
                 "selector": {"kind": "direct_url", "value": item["download_url"]}, "file_name": item["name"],
                 "format": "mat", "size": source["bytes"], "unpack": {"archive": False, "members": []}}]}
        result = retrieve_raw({"dataset_id": "cartilage-alpha10-original", "route": route},
                              {"cache_dir": str((root/"datasets-cache").resolve()), "timeout_secs": 90,
                               "max_total_bytes": source["bytes"]})
        resource, = result["resources"]
        path = Path(resource["path"])
        if not result["ok"] or path.stat().st_size != source["bytes"] or hashlib.md5(path.read_bytes()).hexdigest() != source["md5"]:
            raise ValueError("ORIGINAL_MAT_CHECKSUM_OR_SIZE_MISMATCH")
        return {"source": source, "relative_path": path.resolve().relative_to(Path.cwd()).as_posix(),
                "sha256": digest(path), "bytes": path.stat().st_size, "provider": "Datasets 0.3.11 retrieve_raw",
                "md5_matches_official": True, "canonical_equivalence": "not yet audited", "test_target_accessed": False}

    receipt, value = store.run(contract, "P1", plan, acquire)
    atomic_json(root/"cartilage-acquisition-receipt.json", receipt)
    if value is None:
        raise RuntimeError(receipt)
    atomic_json(root/"cartilage-origin.json", value)
    print(json.dumps({"status": receipt["status"], "cache_hit": receipt["cache_hit"], **value}))


if __name__ == "__main__":
    main()
