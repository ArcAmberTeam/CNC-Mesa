"""Generate a commissioning configuration only after travel is specified."""
import json
import math
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]


def prepare(settings: dict, destination: Path) -> Path:
    board = json.loads((ROOT / "mesa/board/zhulong-v2.json").read_text())
    distance = board["homing"]["distance_mm"]
    if not isinstance(distance, (int, float)) or not math.isfinite(distance) or distance <= 0:
        raise ValueError("Retreat distance must be a finite positive distance in mm")
    lengths = settings["usable_travel_from_switch_mm"]
    for axis in "XYZ":
        if not isinstance(lengths[axis], (float, int)) or not math.isfinite(lengths[axis]) or lengths[axis] <= 3 * distance:
            raise ValueError(f"{axis}: set measured usable travel from switch (> {3 * distance} mm)")
    search, latch, final = (settings[k] for k in ("search_speed_mm_s", "latch_speed_mm_s", "return_speed_mm_s"))
    if not all(isinstance(v, (float, int)) and math.isfinite(v) for v in (search, latch, final)) or not 0 < latch < search <= 5 or not 0 < final <= 5:
        raise ValueError("Require 0 < latch < search <= 5 and 0 < return <= 5 mm/s")
    source = ROOT / "linuxcnc/vendor-reference"
    destination.mkdir(parents=True, exist_ok=True)
    for file in source.iterdir():
        if file.is_file():
            shutil.copyfile(file, destination / file.name)
    ini = (destination / "烛龙V2.ini").read_text()
    ini = ini.replace("[EMCMOT]", "[EMCMOT]\nHOMEMOD = zhulong_homing", 1)

    def update_section(text: str, section: str, values: dict) -> str:
        pattern = rf"(?ms)^\[{section}\]\s*\n(.*?)(?=^\[|\Z)"
        match = re.search(pattern, text)
        if not match:
            raise ValueError(f"Missing INI section {section}")
        body = match.group(1)
        for key, value in values.items():
            body = re.sub(rf"(?m)^{key}\s*=.*\n?", "", body)
            body += f"{key} = {value}\n"
        return text[:match.start()] + f"[{section}]\n" + body + "\n" + text[match.end():]

    for joint, axis in enumerate("XYZ"):
        direction = board["homing"]["axes"][axis]["direction"]
        # Reserve one retreat distance at each physical end.
        span = lengths[axis] - 2 * distance
        limits = {"MIN_LIMIT": -span if direction > 0 else 0.0,
                  "MAX_LIMIT": 0.0 if direction > 0 else span}
        ini = update_section(ini, f"AXIS_{axis}", limits)
        ini = update_section(ini, f"JOINT_{joint}", {
            **limits, "HOME": 0.0, "HOME_OFFSET": direction * distance,
            "HOME_SEARCH_VEL": direction * search, "HOME_LATCH_VEL": direction * latch,
            "HOME_FINAL_VEL": final, "HOME_IGNORE_LIMITS": "YES", "HOME_USE_INDEX": "NO",
            "HOME_SEQUENCE": joint + 1,
        })
    # Rotary joints have no specified homing method; exclude from HOME ALL.
    for joint in range(3, 6):
        ini = update_section(ini, f"JOINT_{joint}", {"HOME_SEQUENCE": 101})
    (destination / "烛龙V2.ini").write_text(ini)
    hal = (destination / "烛龙V2.hal").read_text()
    hal = hal.replace("loadrt hostmot2", "loadrt debounce cfg=3\nloadrt hostmot2", 1)
    hal = hal.replace("addf motion-command-handler", "addf debounce.0 servo-thread\naddf motion-command-handler", 1)
    extra = ["setp debounce.0.delay 5"]
    for joint, axis in enumerate("XYZ"):
        a = axis.lower()
        gpio = board["homing"]["axes"][axis]["gpio"]
        side = "pos" if axis == "Y" else "neg"
        hal = re.sub(rf"(?m)^net {a}-{side}-limit\s+=>\s+joint\.{joint}\.{side}-lim-sw-in.*$", "", hal)
        extra.extend([
            f"net {a}-home-raw hm2_7i92.0.gpio.{gpio:03}.in_not => debounce.0.{joint}.in",
            f"net {a}-home-sw debounce.0.{joint}.out => joint.{joint}.{side}-lim-sw-in",
        ])
    (destination / "烛龙V2.hal").write_text(hal + "\n" + "\n".join(extra) + "\n")
    return destination / "烛龙V2.ini"


if __name__ == "__main__":
    try:
        print(prepare(json.loads((ROOT / "linuxcnc/homing.json").read_text()), ROOT / ".build/linuxcnc"))
    except ValueError as error:
        raise SystemExit(str(error)) from error
