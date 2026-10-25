import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_builder", ROOT / "tools/prepare_release.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class ReleaseTests(unittest.TestCase):
    def test_unbuilt_firmware_cannot_be_advertised_as_an_update(self):
        version = json.loads((ROOT / "release.json").read_text())["version"]
        with tempfile.TemporaryDirectory() as directory:
            path = builder.prepare(version, Path(directory))
            manifest = json.loads(path.read_text())
            self.assertEqual(path.name, "mesa-release.json")
            self.assertIs(manifest["firmware"]["available"], False)
            self.assertIsNone(manifest["firmware"]["asset"])
            self.assertIsNone(manifest["firmware"]["sha256"])
            self.assertIsNone(manifest["firmware"]["size"])
            self.assertEqual(manifest["firmware"]["origin"], "unavailable")
            self.assertEqual(manifest["firmware"]["verification"],
                             {"implementation": False, "timing": False, "board_approved": False})
            self.assertIs(manifest["physical_constraints_verified"], False)
            self.assertEqual(manifest["tag_name"], f"v{version}")
            self.assertEqual(manifest["compatible_app_version"], version)
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
            self.assertEqual(manifest["source_commit"], commit)
            for artifact in manifest["artifacts"].values():
                data = (path.parent / artifact["asset"]).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), artifact["sha256"])
                self.assertEqual(len(data), artifact["size_bytes"])
            with tarfile.open(path.parent / manifest["artifacts"]["integration"]["asset"]) as archive:
                names = archive.getnames()
                self.assertIn("homing/src/homing.c", names)
                self.assertIn("tests/hdl/nc_inputs_tb.vhd", names)
                self.assertFalse(any(name.endswith((".bit", ".bin", ".so")) for name in names))

    def test_invalid_or_unpaired_version_does_not_emit_artifacts(self):
        for version in ("../bad", "v26.10.26.1", "26.10.26.999"):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "release"
                with self.assertRaises(ValueError):
                    builder.prepare(version, target)
                self.assertFalse(target.exists())
