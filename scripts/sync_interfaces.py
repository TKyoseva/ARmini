#!/usr/bin/env python3
"""interfaces/interfaces.json -> cad/openscad/interfaces.scad (OpenSCAD variables).
KiCad side: the agent reads the same JSON and places holes/outline; check.sh compares them."""
import json, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((root / "interfaces/interfaces.json").read_text())

def scad(v):
    if v is None:
        return "undef"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return '"' + v.replace('"', '\\"') + '"'
    if isinstance(v, list):
        return "[" + ", ".join(scad(x) for x in v) + "]"
    raise TypeError(v)

out = ["// GENERATED from interfaces/interfaces.json by scripts/sync_interfaces.py. Do not edit."]
for group, vals in data.items():
    if group.startswith("_"):
        continue
    for k, v in vals.items():
        out.append(f"if_{group}_{k} = {scad(v)};")
(root / "cad/openscad/interfaces.scad").write_text("\n".join(out) + "\n")
print(f"wrote cad/openscad/interfaces.scad ({len(out) - 1} values)")
