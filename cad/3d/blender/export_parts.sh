#!/usr/bin/env bash
# Rebuilds parts/*.stl from the SCAD sources (needs openscad and python3 with numpy, scikit-image, pyvista). Run from the repo root.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p parts
for g in hull_l hull_r brackets beams leg th_mount thruster rudder_mount rudder_blade \
         arm_drive_l arm_drive_r arm_idler_l arm_idler_r couplers cradle box_power box_logic; do
  openscad -D "grp=\"$g\"" -o "parts/$g.stl" parts.scad 2> "parts/$g.log" || { cat "parts/$g.log"; exit 1; }
  grep -ho "KIN.*[0-9]" "parts/$g.log" > parts/kinematics.txt
  rm -f "parts/$g.log"
done
python3 stl_binary.py parts/*.stl
python3 pesho_export.py
ls -la parts
