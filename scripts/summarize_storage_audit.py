"""Sanitized audit tables; detailed inventories stay ignored."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path

from nirs4all_domains.storage import atomic_json


def main():
    parser=argparse.ArgumentParser();parser.add_argument("inventory",type=Path);args=parser.parse_args()
    r=json.loads(args.inventory.read_text());totals=r["totals"]
    def table(items):
        return ["| Path/class | Logical bytes | Unique allocated bytes | Files |", "|---|---:|---:|---:|"] + [
            f"| `{k.removeprefix('workspace/')}` | {v['bytes']:,} | {v['unique_allocated_bytes']:,} | {v['files']:,} |" for k,v in items]
    top=[(k,v) for k,v in totals.items() if k.startswith("workspace/") and k.count("/")==1]
    top.sort(key=lambda kv:-kv[1]["bytes"])
    dirs=sorted([(k,v) for k,v in totals.items() if k.startswith("workspace/")],key=lambda kv:-kv[1]["bytes"])[:25]
    pilots=sorted([(k,v) for k,v in totals.items() if k.startswith("workspace/results/") and k.count("/")==2],key=lambda kv:-kv[1]["bytes"])
    scientific=[x for x in r["files"] if x["relative"].startswith("results/")]
    phase=defaultdict(lambda:{"bytes":0,"files":0})
    for x in scientific:
        parts=Path(x["relative"]).parts
        key="/".join(parts[:min(4,len(parts)-1)])
        phase[key]["bytes"]+=x["bytes"];phase[key]["files"]+=1
    recovery=[]
    for key in ("workspace/target/debug/incremental","workspace/.tools/winlibs-x86_64-posix-seh-gcc-16.2.0-mingw-w64ucrt-14.0.0-r2.zip","workspace/.tools/llvm-mingw-20261006-ucrt-x86_64.zip"):
        match=next((x for x in r["files"] if x["root"]=="workspace" and "workspace/"+x["relative"]==key),None)
        v=totals.get(key)
        if v or match:
            recovery.append(dict(path=str(Path(r["roots"][0]["path"])/key.removeprefix("workspace/")),
                logical_bytes=v["bytes"] if v else match["bytes"],
                action="proposal_only_requires_separate_approval", risk="Rebuild/redownload required; freeze compiler versions and hashes first"))
    local=args.inventory.parent/"recovery-plan.json"
    atomic_json(local,{"proposals":recovery,"identical_result_groups":r["duplicate_scientific_bytes"],"bytes_removed":0,"phase_artifact_counts":dict(phase)})
    lines=["# Local storage audit — alpha.8", "",f"Measured on {r['measured_utc']}. Filesystem: NTFS (queried on Windows).",
           "Sizes below are bytes, not marketing GB rounded from folder names. Detailed absolute paths,",
           "file mtimes and duplicate groups are in ignored `.audit/storage-alpha8/`.","",
           f"Workspace: **{totals['workspace']['bytes']:,} logical bytes**, **{totals['workspace']['unique_allocated_bytes']:,} unique file-allocation bytes**; {totals['workspace']['files']:,} files.",
           "File allocations use Windows FileStandardInfo, and physical file IDs prevent hardlink double counting.",
           "Reparse points are not traversed. Directory/MFT overhead and unlisted external caches are excluded.",
           "The first preliminary scan used logical sizes and was superseded by this file-ID/allocation audit;",
           "its original JSON remains preserved. This corrected audit follows small source/check changes,",
           "so it includes the initial inventory file and a development check, not a historical 11-GB snapshot.", "",
           "## Volumes and external caches", "", "| Root category | Total volume bytes | Free volume bytes | Present |", "|---|---:|---:|---|"]
    lines += [f"| {x['label']} | {x['volume_total']:,} | {x['volume_free']:,} | {x['exists']} |" for x in r["roots"]]
    lines += ["", "Datasets 0.3.11 documents its Windows default under `%LOCALAPPDATA%/nirs4all-datasets/cache`;",
              "it is absent. No configured alternate Datasets cache was discovered. Historical canonical",
              "reproductions are inside results and charged there, not charged again as an external cache.",
              "The pip cache contains only 5,405 logical bytes at this measurement. This does not inventory",
              "unrelated repositories, every user Rust installation or protected private origin storage.", "", "## Top-level footprint", ""]+table(top)
    lines += ["", "Tools/Rust build/Python/upstream audits are reusable development costs; they do not scale per",
              "dataset. `target/debug/deps` and `target/debug/incremental` dominate build space; there is no",
              "release profile in this measurement. `.tools` includes Rust, GCC, LLVM and their downloaded",
              "archives. `.venv` includes native DLLs and data transport dependencies, not dataset matrices.",
              "The tracked source/docs/fixtures are small; git object bytes are separately inventoried.", "", "## Largest directories (overlapping hierarchy; do not sum)", ""]+table(dirs)
    lines += ["", "## Largest files", "", "| Relative path | Bytes | Modified UTC |", "|---|---:|---|"]
    lines += [f"| `{x['relative']}` | {x['bytes']:,} | {datetime.fromtimestamp(x['mtime_ns']/1e9,timezone.utc).date()} |" for x in r["largest_files"][:25]]
    lines += ["", "## Results by pilot", ""]+table(pilots)
    lines += ["", "The machine-local recovery report also groups every result by pilot/dataset/seed/phase path.",
              "Some bootstraps, interventions and fitted models are embedded inside JSON reports; path",
              "classification alone must not claim to measure their internal phases separately.", "", "## Artifact classes", ""]+table([(k,v) for k,v in totals.items() if k.startswith("results-class/")])
    extensions=sorted([(k,v) for k,v in totals.items() if k.startswith("extension/")],key=lambda kv:-kv[1]["bytes"])[:20]
    lines += ["", "## Formats across measured roots", ""]+table(extensions)
    dup=sum(x["possible_logical_savings"] for x in r["duplicate_scientific_bytes"])
    lines += ["", "## Reclamation proposals — no cleanup executed", "",
              f"Scientific result byte-identical groups account for **{dup:,} logical duplicate bytes**.",
              "SHA-256, size and exact paths are recorded locally. Equal summary metrics never count as duplicates.",
              "Historic repeated runs deliberately substantiate replay; byte identity alone does not authorize deletion",
              "or imply that two model protocols are interchangeable. All frozen alpha.4–alpha.7 outputs remain protected.",
              "The local plan names compiler incremental files and downloaded compiler archives as possible recovery",
              "candidates; rebuilding or obtaining exactly the same compiler archive would be necessary. These proposals",
              "overlap the top-level totals and must not be added as new costs. No scientific cache eviction is proposed.",
              "**Bytes removed or migrated: zero.** User approval is required for any future cleanup/migration.", "",
              "## Measured experiment costs and next measurement", "",
              "Frozen real alpha.7 report: 137,560,715 bytes. Its alpha.8 compact scientific payload is",
              "2,653,084 bytes before the small task/execution wrapper. The compaction preserves matched OOF",
              "predictions, scalar/vector metrics, attempt availability, confidence intervals and scoped lineage hashes.",
              "It omits full target maps/debug histories, whose reconstruction requires the preserved input and controller.",
              "Current results contain 1,051,320,067 task-JSON bytes and 62,280,821 canonical-Parquet bytes across",
              "repeated runs, plus 130,252,328 CSV bytes. These are not distinct-dataset input totals. Local per-file",
              "hashes permit provenance review; alpha.8 does not copy any of those matrices into every execution.",
              "The controlled stage measurements, peak estimates, authorized policy and post-run footprint are in",
              "`docs/audit/alpha8-bank-qualification.json` after execution. Runtime estimates remain uncalibrated",
              "for unacquired datasets; catalog dense-byte lower bounds must not be mistaken for compressed input sizes.",
              "Full-bank storage is fixed footprint + distinct provider inputs + retained per-task evidence + bounded",
              "concurrent scratch, as described in STORAGE_AND_REPRODUCIBILITY.md. Multiplying this workspace by 164 is invalid."]
    Path("docs/LOCAL_STORAGE_AUDIT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__=="__main__":main()
