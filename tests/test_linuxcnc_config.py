import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("machine_config", ROOT / "linuxcnc/prepare.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class ConfigTests(unittest.TestCase):
    def settings(self):
        return json.loads((ROOT / "linuxcnc/homing.json").read_text())

    def test_unknown_or_insufficient_travel_does_not_emit_runtime_config(self):
        for value in (None, 5, 10, float("nan")):
            with tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "config"
                settings = self.settings()
                settings["usable_travel_from_switch_mm"] = dict.fromkeys("XYZ", value)
                with self.assertRaises(ValueError):
                    builder.prepare(settings, target)
                self.assertFalse(target.exists())

    def test_complete_profile_wires_active_low_inputs_and_signed_offsets(self):
        settings = self.settings()
        settings["usable_travel_from_switch_mm"] = dict.fromkeys("XYZ", 200)
        with tempfile.TemporaryDirectory() as directory:
            path = builder.prepare(settings, Path(directory))
            ini = path.read_text()
            hal = (path.parent / "烛龙V2.hal").read_text()
            self.assertIn("HOMEMOD = zhulong_homing", ini)
            for j, axis in enumerate("XYZ"):
                section = ini.split(f"[JOINT_{j}]")[1].split("[")[0]
                direction = 1 if axis == "Y" else -1
                self.assertIn(f"HOME_OFFSET = {direction * 5}", section)
                self.assertIn(f"HOME_SEARCH_VEL = {direction * 2.0}", section)
                self.assertIn(f"HOME_LATCH_VEL = {direction * 0.5}", section)
                self.assertIn(f"gpio.{20+j:03}.in_not => debounce.0.{j}.in", hal)
            self.assertLess(hal.index("addf hm2_7i92.0.read"), hal.index("addf debounce.0"))
            self.assertLess(hal.index("addf debounce.0"), hal.index("addf motion-controller"))
