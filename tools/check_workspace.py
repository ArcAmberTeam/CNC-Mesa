"""Check provenance and declared dependency boundaries without hardware access."""

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = json.loads((ROOT / "workspace.json").read_text())["modules"]


def visit(name: str, path: tuple = ()) -> None:
    if name in path:
        raise SystemExit(f"Dependency cycle: {path + (name,)}")
    module = MODULES[name]
    for entry in module["entrypoints"]:
        if not (ROOT / name / entry).is_file():
            raise SystemExit(f"Missing module entry point: {name}/{entry}")
    for dependency in module["dependencies"]:
        if module["kind"] == "library" and MODULES[dependency]["kind"] == "app":
            raise SystemExit(f"Library {name} depends on application {dependency}")
        visit(dependency, path + (name,))


for name in MODULES:
    visit(name)


def verify_files(base: Path, entries: dict) -> None:
    for name, entry in entries.items():
        expected = entry["sha256"] if isinstance(entry, dict) else entry
        actual = hashlib.sha256((base / name).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"Original file changed: {base / name}")


verify_files(ROOT, json.loads((ROOT / "docs/provenance/vendor.json").read_text())["files"])
snapshot = ROOT / "hostmot2"
manifest = json.loads((snapshot / "manifest.json").read_text())
verify_files(snapshot / "upstream", manifest["files"])
homing = ROOT / "homing"
verify_files(homing / "upstream", json.loads((homing / "provenance.json").read_text())["test_planner_files"])
actual = {str(p.relative_to(snapshot / "upstream")) for p in (snapshot / "upstream").rglob("*") if p.is_file()}
if actual != set(manifest["files"]):
    raise SystemExit("Unexpected additions/removals in the immutable upstream snapshot")
for source in ROOT.rglob("*.py"):
    if ".build" in source.parts or "upstream" in source.parts:
        continue
    for node in ast.walk(ast.parse(source.read_text())):
        modules = [node.module or ""] if isinstance(node, ast.ImportFrom) else [n.name for n in node.names] if isinstance(node, ast.Import) else []
        for module in modules:
            owner = source.relative_to(ROOT).parts[0]
            target = module.split(".")[0]
            apps = {n for n, m in MODULES.items() if m["kind"] == "app"}
            if owner in MODULES and MODULES[owner]["kind"] == "library" and target in apps | {"tests", "tools"}:
                raise SystemExit(f"Package depends on application/tooling: {source}:{node.lineno}")
            if not source.is_relative_to(ROOT / "mesa/mesa_firmware") and module.startswith("mesa_firmware."):
                raise SystemExit(f"Use the public mesa_firmware entry point: {source}:{node.lineno}")
print(f"Provenance and dependency checks passed ({len(manifest['files'])} upstream files).")
