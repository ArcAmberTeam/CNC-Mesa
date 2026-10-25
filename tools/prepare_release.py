"""Package a fixed source revision; no reconstructed FPGA bitstream is available."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_PATHS = (
    "Makefile", "homing", "linuxcnc", "mesa/board/zhulong-v2.json",
    "docs/homing.md", "docs/linuxcnc-integration-handoff.md",
    "tests/test_linuxcnc_config.py", "tests/homing", "tests/hdl",
    "tools/test_homing.py", "tools/test_hdl.py",
    "firmware/zhulong-v2/PIN_ZHULONG_V2_34.vhd",
    "hostmot2/upstream/IDROMConst.vhd", "hostmot2/upstream/i92_x9card.vhd",
    "hostmot2/upstream/wordpr.vhd", "hostmot2/upstream/wordrb.vhd",
)


def prepare(version: str, destination: Path) -> Path:
    """Emit archives, hashes and an explicit unavailable-firmware manifest."""
    if not re.fullmatch(r"\d{2}\.\d{2}\.\d{2}\.\d+", version):
        raise ValueError("Version must use YY.MM.DD.N (without a v prefix)")
    release = json.loads((ROOT / "release.json").read_text())
    if version != release["version"] or version != release["compatible_app_version"]:
        raise ValueError("Release tag, source version and application version must match")
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError("Release output must be an empty directory")
    subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=ROOT, check=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    board = json.loads((ROOT / "mesa/board/zhulong-v2.json").read_text())
    destination.mkdir(parents=True, exist_ok=True)
    artifacts = {}
    for kind, paths in (("source", ()), ("integration", INTEGRATION_PATHS)):
        archive = destination / f"cnc-mesa-{kind}-{version}.tar.gz"
        subprocess.run(["git", "archive", "--format=tar.gz", "-o", str(archive.resolve()), commit, *paths], cwd=ROOT, check=True)
        artifacts[kind] = {"asset": archive.name, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                           "size_bytes": archive.stat().st_size}
    manifest = {
        "schema_version": 1, "version": version, "tag_name": f"v{version}",
        "board": board["name"], "variant": board["pin_package"],
        "fpga": board["fpga"], "package": board["package"],
        "physical_constraints_verified": board["physical_constraints_verified"],
        "source_commit": commit, "compatible_app_version": release["compatible_app_version"],
        "firmware": {"available": False, "asset": None, "sha256": None, "size_bytes": None,
                     "reason": "No ISE-built and board-verified bitstream is available for this revision"},
        "artifacts": artifacts,
    }
    manifest_path = destination / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    hashes = [f"{entry['sha256']}  {entry['asset']}" for entry in artifacts.values()]
    hashes.append(f"{hashlib.sha256(manifest_path.read_bytes()).hexdigest()}  manifest.json")
    (destination / "SHA256SUMS").write_text("\n".join(hashes) + "\n")
    (destination / "release-notes.md").write_text(
        f"CNC-Mesa {version}; paired application version {release['compatible_app_version']}.\n\n"
        f"Source revision: `{commit}`. Includes NC input configuration, double-touch HOMEMOD, "
        "GPIO VHDL simulations, integration sources and checksums.\n\n"
        "This release contains source artifacts only. No new flashable FPGA bitstream was built. "
        "The original vendor bitstream inside the full reference source archive is not an update payload. "
        "Updaters must honor `firmware.available=false`; do not flash files from the source archive.\n"
    )
    return manifest_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(prepare(args.version, args.output))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error
