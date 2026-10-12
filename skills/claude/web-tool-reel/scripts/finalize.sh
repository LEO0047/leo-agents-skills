#!/usr/bin/env bash
# Mux + encode the deliverables from the rendered master.
#   FRAMES=1443 FPS=60 CRF=20 ./finalize.sh <master_video.mp4> <music> <out_dir> [name_prefix]
# Outputs <prefix>_IG_1080x1920_60fps.mp4 (H.264 High@4.2 + AAC 48 kHz, faststart)
# and <prefix>_noMusic_1080x1920_60fps.mp4 (same video stream, copied bit-for-bit).
set -euo pipefail
MASTER="$1"; MUSIC="$2"; OUT="$3"; NAME="${4:-Reel}"
CRF="${CRF:-20}"; FRAMES="${FRAMES:-1443}"; FPS="${FPS:-60}"
mkdir -p "$OUT"
DUR=$(python3 -c "print($FRAMES/$FPS)")
FADE=$(python3 -c "print($FRAMES/$FPS-0.06)")
ffmpeg -v error -y -i "$MASTER" -i "$MUSIC" -map 0:v:0 -map 1:a:0 \
  -c:v libx264 -preset slow -crf "$CRF" -profile:v high -level:v 4.2 -pix_fmt yuv420p -r "$FPS" \
  -x264-params "keyint=$FPS:min-keyint=$FPS" -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -af "afade=t=out:st=$FADE:d=0.06" -c:a aac -b:a 256k -ar 48000 \
  -t "$DUR" -movflags +faststart "$OUT/${NAME}_IG_1080x1920_${FPS}fps.mp4"
ffmpeg -v error -y -i "$OUT/${NAME}_IG_1080x1920_${FPS}fps.mp4" -map 0:v:0 -c copy -movflags +faststart \
  "$OUT/${NAME}_noMusic_1080x1920_${FPS}fps.mp4"
ls -la "$OUT"
