#!/usr/bin/env bash
# Turn one XIAO cam recording folder (C049_<n>/frame_00001.jpg … + index.csv) into an mp4 on the Mac.
#
#   bash scripts/frames_to_mp4.sh /Volumes/SDCARD/C049_3            -> C049_3.mp4 next to the folder
#   bash scripts/frames_to_mp4.sh /Volumes/SDCARD/C049_3 out.mp4    -> given file
#
# The frame rate is the real one from index.csv: (frames − 1) / (t_last − t_first). Needs ffmpeg (brew install ffmpeg).
set -euo pipefail

dir="${1:?usage: frames_to_mp4.sh <folder> [out.mp4]}"
dir="${dir%/}"
out="${2:-${dir}.mp4}"
idx="$dir/index.csv"

command -v ffmpeg >/dev/null || { echo "ffmpeg not found (brew install ffmpeg)"; exit 1; }
[ -f "$idx" ] || { echo "no $idx"; exit 1; }

# Frame rate from the index (header line skipped). Falls back to 10 fps with a single frame.
fps="$(awk -F, 'NR>1 && NF>=2 { if (n==0) t0=$2; t1=$2; n++ }
  END { if (n>1 && t1>t0) printf "%.3f", (n-1)*1000/(t1-t0); else print "10" }' "$idx")"
frames="$(awk -F, 'NR>1 && NF>=2 {n++} END {print n+0}' "$idx")"

echo "$dir: $frames frames, $fps fps -> $out"
ffmpeg -hide_banner -loglevel warning -y \
  -framerate "$fps" -start_number 1 -i "$dir/frame_%05d.jpg" \
  -c:v libx264 -pix_fmt yuv420p -movflags +faststart "$out"
echo "done: $out"
