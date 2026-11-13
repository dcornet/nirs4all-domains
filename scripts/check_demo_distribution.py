"""Audit the actual preview bytes, provenance and measured static bundle size."""

import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
dist = root / "demo/dist"
assert (dist / "index.html").is_file()
files = sorted(p for p in dist.rglob("*") if p.is_file())
assert not any(
    p.suffix in {".map", ".csv", ".parquet", ".npy", ".npz", ".zip", ".dll", ".exe"}
    for p in files
)
assert sum(p.stat().st_size for p in files) <= 20 * 1024**2, (
    "STATIC_PREVIEW_BUDGET_EXCEEDED"
)
wasm = [p for p in files if p.suffix == ".wasm"]
assert len(wasm) >= 4, "DOMAINS_METHODS_IO_FORMATS_WASM_REQUIRED"
for p in files:
    data = p.read_bytes()
    assert b"D:\\VS projects" not in data and b"C:\\Users\\cornet" not in data, p.name
    assert p.stat().st_size < 10 * 1024**2, p.name
manifest = {
    "protocol": "domains.browser_distribution.v1",
    "base_path": "/nirs4all-domains/",
    "total_bytes": sum(p.stat().st_size for p in files),
    "wasm_files": len(wasm),
    "files": [
        {
            "path": p.relative_to(dist).as_posix(),
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        for p in files
    ],
    "raw_research_data_included": False,
    "dependencies_lock_sha256": hashlib.sha256(
        (root / "demo/package-lock.json").read_bytes()
    ).hexdigest(),
}
out = root / "demo/test-results"
out.mkdir(exist_ok=True)
(out / "distribution.json").write_text(
    json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
)
print(
    json.dumps(
        {
            "static_bytes": manifest["total_bytes"],
            "files": len(files),
            "wasm_files": len(wasm),
        }
    )
)
