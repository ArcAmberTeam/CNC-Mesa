"""Analyze and elaborate the board IDROM, using real Mesa package definitions."""

from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if not shutil.which("ghdl"):
    raise SystemExit("GHDL is required (Debian: apt-get install ghdl).")
sources = [
    "hostmot2/upstream/IDROMConst.vhd",
    "hostmot2/upstream/i92_x9card.vhd",
    "firmware/zhulong-v2/PIN_ZHULONG_V2_34.vhd",
    "tests/hdl/board_profile_tb.vhd",
]
with tempfile.TemporaryDirectory(prefix="cnc-mesa-ghdl-") as work:
    for source in sources:
        subprocess.run(["ghdl", "-a", "--std=08", "-fsynopsys", str(ROOT / source)], cwd=work, check=True)
    subprocess.run(["ghdl", "-r", "--std=08", "-fsynopsys", "board_profile_tb", "--assert-level=error"], cwd=work, check=True)
