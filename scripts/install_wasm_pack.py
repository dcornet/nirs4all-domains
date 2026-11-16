"""Install only the reviewed official wasm-pack executable after SHA-256 verification."""
import hashlib
import io
import os
import platform
import tarfile
import urllib.request
from pathlib import Path

VERSION = "0.13.1"
ASSETS = {
    "Windows": ("x86_64-pc-windows-msvc", "4fd5375c2f85bae92c3e8fb14ad0d27b8fb92e85f4397064d9e66a94a79d6fae"),
    "Linux": ("x86_64-unknown-linux-musl", "c539d91ccab2591a7e975bcf82c82e1911b03335c80aa83d67ad25ed2ad06539"),
}

def main():
    target, digest = ASSETS[platform.system()]
    assert platform.machine().lower() in {"amd64", "x86_64"}, "Unsupported reviewed wasm-pack architecture"
    name = f"wasm-pack-v{VERSION}-{target}"
    url = f"https://github.com/wasm-bindgen/wasm-pack/releases/download/v{VERSION}/{name}.tar.gz"
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read(8 * 1024**2 + 1)
    assert len(data) <= 8 * 1024**2 and hashlib.sha256(data).hexdigest() == digest, "Unverified wasm-pack archive"
    executable = "wasm-pack.exe" if platform.system() == "Windows" else "wasm-pack"
    destination = Path(os.environ["RUNNER_TEMP"]) / name
    destination.mkdir(exist_ok=True)
    # Extract one regular, explicitly named member; never trust archive paths/links.
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        member = archive.getmember(f"{name}/{executable}")
        assert member.isfile() and member.size <= 32 * 1024**2
        content = archive.extractfile(member).read()
    binary = destination / executable
    binary.write_bytes(content)
    binary.chmod(0o755)
    with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as path_file:
        path_file.write(str(destination) + "\n")
    print(f"Verified wasm-pack {VERSION} {target}: SHA256 {digest}")

if __name__ == "__main__":
    main()
