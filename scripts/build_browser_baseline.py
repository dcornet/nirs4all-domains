"""Build the exact reviewed F2 frontend and its own Rust WASM on the hosted runner."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

BASE = "f4289f51fbae8cad2c460fc8ca1b1c1e0ba2ae13"

def main():
    assert subprocess.check_output(["git", "rev-parse", f"{BASE}^{{commit}}"], text=True).strip() == BASE
    destination = Path(os.environ["RUNNER_TEMP"]) / "domains-f3-baseline"
    assert not destination.exists(), "Baseline destination must be new"
    destination.mkdir()
    data = subprocess.check_output(["git", "archive", BASE, "Cargo.toml", "Cargo.lock", "crates", "demo", "bindings/wasm", "LICENSES", "schemas"])
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as archive:
        for member in archive:
            target = (destination / member.name).resolve()
            assert target.is_relative_to(destination.resolve()) and not member.issym() and not member.islnk()
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                assert member.isfile()
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    node = shutil.which("node")
    assert npm and node
    npm_cli = Path(npm).parent / "node_modules/npm/bin/npm-cli.js" if os.name == "nt" else Path(npm).resolve()
    assert npm_cli.is_file()
    for directory in [destination / "bindings/wasm", destination / "demo"]:
        subprocess.run([node, str(npm_cli), "ci", "--prefix", str(directory), "--ignore-scripts", "--no-audit", "--no-fund"], check=True)
    # F4 has additive Rust changes. Reusing candidate WASM would no longer be an
    # exact F2 baseline. Compile the archived F2 crate/lock in a separate target
    # directory using the already verified hosted wasm-pack and observer.
    environment = {**os.environ, "CARGO_TARGET_DIR": str(destination / "target")}
    observer = Path(__file__).with_name("observe_wasm_build.py").resolve()
    subprocess.run([sys.executable, str(observer)], cwd=destination, env=environment, check=True)
    assert (destination / "Cargo.lock").read_bytes() == subprocess.check_output(["git", "show", f"{BASE}:Cargo.lock"]), "Baseline build changed the frozen lock"
    subprocess.run([node, str(npm_cli), "run", "build", "--prefix", str(destination / "demo")], check=True)
    proof = Path("demo/test-results")
    proof.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(destination / "demo/test-results/wasm-build.resources.json", proof / "baseline-wasm-build.resources.json")
    binary = destination / "bindings/wasm/native/nirs4all_domains_bg.wasm"
    receipt = {"protocol": "domains.technical_baseline_build.v2", "base_commit": BASE,
               "frontend_source_commit": BASE, "rust_source_commit": BASE,
               "cargo_lock_sha256": hashlib.sha256((destination / "Cargo.lock").read_bytes()).hexdigest(),
               "compiled_wasm_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
               "candidate_wasm_reused": False, "separate_target_directory": True,
               "scope": "Archived F2 source and locked dependencies compiled on this hosted runner. Compiler resources observed separately; no science campaign or real-source fit."}
    (proof / "technical-baseline-build.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))

if __name__ == "__main__":
    main()
