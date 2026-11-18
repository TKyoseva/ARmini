#!/usr/bin/env bash
# AR-Mini C085 · mesh and solve one case: run_case.sh <case dir> <single|pair> <base cell m> <speed m/s> [iterations]
# Ubuntu's openfoam 1912 package: function objects crash ("sha1" stream error), so forces are integrated
# afterwards by forces.py from the written fields.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
export WM_PROJECT_DIR="${WM_PROJECT_DIR:-/usr/share/openfoam}"
case="$1"; mode="$2"; h="$3"; U="$4"; iters="${5:-1200}"
python3 "$here/make_case.py" "$case" "$mode" "$h" "$U"
cd "$case"
sed -i "s/endTime 1200; deltaT 1;/endTime $iters; deltaT 1;/; s/writeInterval 1200;/writeInterval $iters;/" system/controlDict
blockMesh > log.blockMesh 2>&1
surfaceFeatureExtract > log.surfaceFeatureExtract 2>&1
snappyHexMesh -overwrite > log.snappyHexMesh 2>&1
checkMesh > log.checkMesh 2>&1
decomposePar > log.decomposePar 2>&1
mpirun --allow-run-as-root --oversubscribe -np 4 simpleFoam -parallel > log.simpleFoam 2>&1
reconstructPar -latestTime > log.reconstructPar 2>&1
rm -rf processor*
grep "cells:" log.checkMesh | head -1
grep -c "^Time =" log.simpleFoam
