import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = "{http://www.xilinx.com/XMLSchema}"


class ProjectTests(unittest.TestCase):
    def test_prepared_project_selects_zhulong_and_has_all_sources(self):
        subprocess.run([sys.executable, str(ROOT / "firmware/prepare.py")], check=True, capture_output=True)
        out = ROOT / ".build/firmware"
        project = ET.parse(out / "zhulong-v2.xise")
        for f in project.findall(f"{NS}files/{NS}file"):
            self.assertTrue((out / f.attrib[NS + "name"]).is_file())
        top = (out / "TopEthernet16HostMot2.vhd").read_text()
        selections = re.findall(r"(?im)^use work\.(\w+)\.all;", top)
        self.assertEqual(selections, ["FixICap", "IDROMConst", "i92_x9card", "PIN_ZHULONG_V2_34"])
        props = {p.attrib[NS + "name"]: p.attrib[NS + "value"] for p in project.findall(f"{NS}properties/{NS}property")}
        self.assertEqual(props["Device"], "xc6slx9")
        self.assertEqual(props["Package"], "tqg144")
        self.assertEqual(props["UserID Code (8 Digit Hexadecimal)"], "0x00007192")

    def test_pin_map_agrees_with_vendor_document(self):
        table = (ROOT / "mesa/board/引脚定义.txt").read_text()
        source = (ROOT / "firmware/zhulong-v2/PIN_ZHULONG_V2_34.vhd").read_text()
        rows = re.findall(r"(?m)^\s*\d+\s+(\d+)\s+IOPort\s+(\w+)(.*)$", table)
        self.assertEqual(len(rows), 34)
        roles = {"None": "NullTag", "StepGen": "StepGenTag", "PWM": "PWMTag", "SSerial": "SSerialTag", "QCount": "QCountTag"}
        for gpio, function, detail in rows:
            line = re.search(rf'^\s*{gpio} => (IOPortTag.*)$', source, re.M).group(1)
            self.assertIn(roles[function], line)
        profile = json.loads((ROOT / "mesa/board/zhulong-v2.json").read_text())
        self.assertEqual(profile["homing"]["axes"], {"X": {"gpio": 20, "direction": -1}, "Y": {"gpio": 21, "direction": 1}, "Z": {"gpio": 22, "direction": -1}})
