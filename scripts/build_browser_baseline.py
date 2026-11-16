"""Build the reviewed F2 frontend using the same unchanged compiled Rust source."""
import io
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

BASE = "f4289f51fbae8cad2c460fc8ca1b1c1e0ba2ae13"

def main():
    subprocess.run(["git", "diff", "--exit-code", BASE, "--", "Cargo.toml", "Cargo.lock", "crates"], check=True)
    destination = Path(os.environ["RUNNER_TEMP"]) / "domains-f3-baseline"
    assert not destination.exists(), "Baseline destination must be new"
    destination.mkdir()
    data = subprocess.check_output(["git", "archive", BASE, "demo", "bindings/wasm", "LICENSES"])
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
    shutil.copytree("bindings/wasm/native", destination / "bindings/wasm/native")
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    node = shutil.which("node")
    assert npm and node
    npm_cli = Path(npm).parent / "node_modules/npm/bin/npm-cli.js" if os.name == "nt" else Path(npm).resolve()
    assert npm_cli.is_file()
    for directory in [destination / "bindings/wasm", destination / "demo"]:
        subprocess.run([node, str(npm_cli), "ci", "--prefix", str(directory), "--ignore-scripts", "--no-audit", "--no-fund"], check=True)
    subprocess.run([node, str(npm_cli), "run", "build", "--prefix", str(destination / "demo")], check=True)
    print(f"Built exact F2 frontend {BASE}; Rust source/lock unchanged and compiled WASM reused from this job.")

if __name__ == "__main__":
    main()
