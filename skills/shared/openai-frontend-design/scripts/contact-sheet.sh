#!/usr/bin/env bash
# Build a contact sheet: every PNG/JPG/WebP in a folder, shown at its rendered
# CSS size on near-white, near-black, and checkerboard, with sips metadata.
#
# Usage: contact-sheet.sh <asset-dir> [sizes.tsv] [out.html]
#   sizes.tsv  optional. Lines of "<filename or id><TAB><css width>", e.g.
#              "hero-scene.png<TAB>720px" or "feature-spot-1<TAB>480px".
#              An id matches the filename without extension. Default 320px.
#   out.html   default: <asset-dir>/contact-sheet.html
#
# Pure HTML+CSS output; open it in a browser or screenshot it with a browser tool.
set -euo pipefail

DIR="${1:-}"; SIZES="${2:-}"; OUT="${3:-}"
if [ -z "$DIR" ] || [ ! -d "$DIR" ]; then
  echo "usage: contact-sheet.sh <asset-dir> [sizes.tsv] [out.html]" >&2; exit 64
fi
command -v sips >/dev/null 2>&1 || { echo "Error: macOS sips is required." >&2; exit 69; }
DIR="$(cd "$DIR" && pwd)"
[ -n "$OUT" ] || OUT="$DIR/contact-sheet.html"

width_for() {
  local name="$1" base="${1%.*}"
  if [ -n "$SIZES" ] && [ -f "$SIZES" ]; then
    awk -F'\t' -v f="$name" -v b="$base" '
      $1==f || $1==b { print $2; found=1; exit }
      END { if (!found) print "320px" }' "$SIZES"
  else
    echo "320px"
  fi
}

count=0
{
cat <<'HTML'
<!doctype html><meta charset="utf-8"><title>Contact sheet</title>
<style>
body{margin:0;padding:24px;font:13px/1.45 -apple-system,system-ui,sans-serif;background:#8a8a8a;color:#111}
h1{font-size:15px;font-weight:600;color:#fff;margin:0 0 20px}
.row{display:grid;grid-template-columns:220px repeat(3,max-content);gap:16px;align-items:start;margin-bottom:28px}
.meta{background:#fff;padding:10px 12px;border-radius:6px;word-break:break-all}
.cell{padding:16px;border-radius:6px}
.light{background:#f5f5f3}.dark{background:#141414}
.check{background-color:#e9e9e9;background-image:
 linear-gradient(45deg,#bdbdbd 25%,transparent 25%,transparent 75%,#bdbdbd 75%),
 linear-gradient(45deg,#bdbdbd 25%,transparent 25%,transparent 75%,#bdbdbd 75%);
 background-size:16px 16px;background-position:0 0,8px 8px}
img{display:block;height:auto}
</style>
HTML
printf '<h1>%s</h1>\n' "$DIR"
for f in "$DIR"/*.png "$DIR"/*.jpg "$DIR"/*.jpeg "$DIR"/*.webp; do
  [ -f "$f" ] || continue
  name="$(basename "$f")"
  w="$(width_for "$name")"
  meta="$(sips -g pixelWidth -g pixelHeight -g hasAlpha "$f" 2>/dev/null \
         | awk -F': ' 'NR>1 { gsub(/^[ \t]+/, "", $1); printf "%s %s<br>", $1, $2 }')"
  printf '<div class="row"><div class="meta"><b>%s</b><br>%srendered width %s</div>' "$name" "$meta" "$w"
  for bg in light dark check; do
    printf '<div class="cell %s"><img src="file://%s" style="width:%s" alt=""></div>' "$bg" "$f" "$w"
  done
  printf '</div>\n'
  count=$((count + 1))
done
} > "$OUT"

echo "output=$OUT"
echo "assets=$count"
