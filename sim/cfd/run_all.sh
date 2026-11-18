#!/usr/bin/env bash
# AR-Mini C085 · the whole matrix: 5 speeds × (single hull, catamaran) + mesh check at 0.6 m/s. About 1 h on 4 cores.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; out="$here/out"; mkdir -p "$out"; res="$out/results.jsonl"; : > "$res"
run() {  # name mode base speed keep
  "$here/run_case.sh" "$out/$1" "$2" "$3" "$4" 2000 > "$out/$1.log" 2>&1 || { echo "FAILED $1" | tee -a "$out/failed.txt"; return; }
  python3 "$here/forces.py" "$out/$1" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); d.update(mode='$2', base_m=$3, speed=$4, cells=int(open('$out/$1/log.checkMesh').read().split('cells:')[1].split()[0])); print(json.dumps(d))" >> "$res"
  [ "$5" = keep ] || rm -rf "$out/$1"/[1-9]* "$out/$1/constant/polyMesh"
  tail -1 "$res"
}
for U in 0.2 0.4 0.6 0.8 1.0; do
  keep=no; [ "$U" = 0.6 ] && keep=keep
  run "single_U$U" single 0.025 "$U" $keep
  run "pair_U$U" pair 0.025 "$U" $keep
done
run mesh_coarse single 0.035 0.6 no
run mesh_fine single 0.018 0.6 no
echo ALL DONE
