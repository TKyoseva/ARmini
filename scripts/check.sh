#!/usr/bin/env bash
# Run before every commit (Cursor agent, pre-commit hook and GitHub Actions use the same script).
set -euo pipefail
cd "$(dirname "$0")/.."
fail=0

# 1. secrets never committed
if git diff --cached --name-only 2>/dev/null | grep -E '(secrets\.h|\.env|^private/)' ; then
  echo "BLOCKED: secret or private file staged"; exit 1
fi

# 2. interfaces in sync
python3 scripts/sync_interfaces.py >/dev/null
if ! git diff --quiet -- cad/openscad/interfaces.scad 2>/dev/null; then
  echo "note: cad/openscad/interfaces.scad regenerated, stage it"; git add cad/openscad/interfaces.scad || true
fi

# 3. CAD renders
if command -v openscad >/dev/null; then
  mkdir -p build
  openscad -o build/AR-Mini_v1.stl cad/openscad/AR-Mini_v1.scad 2> build/openscad.log || { echo "OpenSCAD FAILED (build/openscad.log)"; fail=1; }
else echo "skip: openscad not installed"; fi

# 4. PCB rules (KiCad 10: kicad-cli from PATH, or the macOS app bundle)
#    --severity-error: library warnings ("footprint library 'AR-Mini' not configured") are cosmetic,
#    the footprints are embedded in the board. --refill-zones: DRC on the filled GND pour even if
#    the board was saved unfilled (otherwise every GND pad reports "unconnected").
KICAD_CLI="$(command -v kicad-cli || true)"
[ -z "$KICAD_CLI" ] && [ -x /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli ] && KICAD_CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
if [ -n "$KICAD_CLI" ]; then
  mkdir -p build
  for sch in pcb/*/*.kicad_sch; do [ -e "$sch" ] || continue
    "$KICAD_CLI" sch erc --severity-error --exit-code-violations -o "build/$(basename "$sch" .kicad_sch)_erc.rpt" "$sch" || { echo "ERC FAILED: $sch"; fail=1; }
  done
  for pcb in pcb/*/*.kicad_pcb; do [ -e "$pcb" ] || continue
    "$KICAD_CLI" pcb drc --refill-zones --severity-error --exit-code-violations -o "build/$(basename "$pcb" .kicad_pcb)_drc.rpt" "$pcb" || { echo "DRC FAILED: $pcb"; fail=1; }
  done
else echo "skip: kicad-cli not installed"; fi

# 5. firmware builds (every PlatformIO project under firmware/)
#    firmware/armini: target build + host unit tests (native env, Unity).
#    firmware/bench:  all module envs (default_envs) + host unit tests of lib/benchcore.
if command -v pio >/dev/null; then
  for ini in firmware/*/platformio.ini; do [ -e "$ini" ] || continue
    dir="$(dirname "$ini")"
    if [ "$dir" = "firmware/armini" ]; then
      (cd "$dir" && pio run -e devkit_lipo) || { echo "FIRMWARE BUILD FAILED: $ini (devkit_lipo)"; fail=1; }
      (cd "$dir" && pio test -e native)     || { echo "FIRMWARE TESTS FAILED: $ini (native)"; fail=1; }
    elif [ "$dir" = "firmware/bench" ]; then
      (cd "$dir" && pio run)            || { echo "FIRMWARE BUILD FAILED: $ini (all module envs)"; fail=1; }
      (cd "$dir" && pio test -e native) || { echo "FIRMWARE TESTS FAILED: $ini (native)"; fail=1; }
    else
      (cd "$dir" && pio run) || { echo "FIRMWARE BUILD FAILED: $ini"; fail=1; }
    fi
  done
else echo "skip: platformio not installed"; fi

[ $fail -eq 0 ] && echo "check: OK" || { echo "check: FAILED"; exit 1; }
