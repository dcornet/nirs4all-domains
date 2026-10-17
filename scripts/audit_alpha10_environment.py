"""Read-only source/provider inventory and preservation snapshot for alpha.10."""
import argparse
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import urllib.request

from nirs4all_domains.storage import atomic_json, digest, tree_bytes


REVISION = "1aefd473a0ebeef28adc0d808c4a4b0c9c45fa9f"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("snapshot", "source"))
    args = parser.parse_args()
    root = Path(".audit/alpha10")
    root.mkdir(parents=True, exist_ok=True)
    if args.command == "snapshot":
        old = json.loads(Path("docs/audit/alpha9-frozen-output-hashes.json").read_text())
        # Preserve every previously protected output and the complete alpha.9
        # portable evidence. Never rewrite these records during alpha.10.
        for base in (Path("docs/benchmarks/alpha9"),):
            old.update({p.as_posix(): digest(p) for p in base.rglob("*") if p.is_file()})
        for p in Path("docs/audit").glob("*alpha9*.json"):
            old[p.as_posix()] = digest(p)
        for p in Path("results/alpha9-perten-keyed").rglob("*"):
            if p.is_file() and "state" not in p.parts:
                old[p.as_posix()] = digest(p)
        atomic_json("docs/audit/alpha10-frozen-output-hashes.json", old)
        versions = {}
        for name in ("nirs4all", "nirs4all-methods", "dag-ml", "nirs4all-datasets", "numpy", "scipy", "scikit-learn", "torch"):
            try:
                versions[name] = metadata.version(name)
            except metadata.PackageNotFoundError:
                versions[name] = None
        snapshot = {"baseline_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                    "workspace_unique_bytes": tree_bytes([Path.cwd()]),
                    "volumes": {v: {"free_bytes": shutil.disk_usage(v+":/").free} for v in ("C", "D")},
                    "versions": versions, "protected_files": len(old)}
        atomic_json(root/"environment.json", snapshot)
        print(json.dumps(snapshot))
    else:
        # Only public source code. Pin every fetched byte; no upstream checkout
        # is edited and no package dependency is installed by this audit.
        tree = json.loads(subprocess.check_output(["gh", "api", f"repos/GBeurier/nirs4all/git/trees/{REVISION}?recursive=1"], text=True))
        paths = [v["path"] for v in tree["tree"] if v["type"] == "blob" and (
            v["path"].startswith("nirs4all/operators/models/_aom_nirs/fast/") or v["path"] in (
                "pyproject.toml", "nirs4all/__init__.py", "nirs4all/operators/models/__init__.py",
                "nirs4all/operators/models/sklearn/aom_fast.py", "nirs4all/operators/models/_aom_nirs/__init__.py"))]
        records = {}
        for path in paths:
            destination = root/"nirs4all-source"/path
            destination.parent.mkdir(parents=True, exist_ok=True)
            content = urllib.request.urlopen(f"https://raw.githubusercontent.com/GBeurier/nirs4all/{REVISION}/{path}", timeout=45).read()
            if destination.exists() and destination.read_bytes() != content:
                raise ValueError("PINNED_SOURCE_CHANGED")
            destination.write_bytes(content)
            records[path] = {"bytes": len(content), "sha256": digest(destination)}
        atomic_json(root/"nirs4all-source.json", {"repository": "GBeurier/nirs4all", "revision": REVISION, "files": records})
        print(json.dumps({"revision": REVISION, "files": len(records), "bytes": sum(v["bytes"] for v in records.values())}))


if __name__ == "__main__":
    main()
