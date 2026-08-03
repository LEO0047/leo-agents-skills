#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: inspect-image-asset.sh [--require-alpha] <image> [<image> ...]

Reports format, dimensions, alpha-channel presence, and byte size using macOS
sips and stat. With --require-alpha, exits 2 if any image has no alpha channel.
EOF
}

require_alpha="false"
case "${1:-}" in
  -h|--help)
    usage
    exit 0
    ;;
  --require-alpha)
    require_alpha="true"
    shift
    ;;
esac

if [[ "$#" -eq 0 ]]; then
  usage >&2
  exit 64
fi

if ! command -v sips >/dev/null 2>&1; then
  echo "Error: macOS sips is required but was not found on PATH." >&2
  exit 69
fi

status=0
for image_path in "$@"; do
  if [[ ! -f "$image_path" ]]; then
    echo "Error: file not found: $image_path" >&2
    status=66
    continue
  fi

  if ! metadata="$(sips -g format -g pixelWidth -g pixelHeight -g hasAlpha "$image_path" 2>/dev/null)"; then
    echo "Error: sips could not inspect: $image_path" >&2
    status=65
    continue
  fi

  format="$(awk -F': ' '/^[[:space:]]*format:/{print $2; exit}' <<<"$metadata")"
  width="$(awk -F': ' '/^[[:space:]]*pixelWidth:/{print $2; exit}' <<<"$metadata")"
  height="$(awk -F': ' '/^[[:space:]]*pixelHeight:/{print $2; exit}' <<<"$metadata")"
  has_alpha="$(awk -F': ' '/^[[:space:]]*hasAlpha:/{print $2; exit}' <<<"$metadata")"
  byte_size="$(stat -f '%z' "$image_path")"

  printf 'asset=%s\n' "$image_path"
  printf 'format=%s\n' "${format:-unknown}"
  printf 'width=%s\n' "${width:-unknown}"
  printf 'height=%s\n' "${height:-unknown}"
  printf 'has_alpha=%s\n' "${has_alpha:-unknown}"
  printf 'bytes=%s\n' "$byte_size"

  if [[ "$require_alpha" == "true" && "$has_alpha" != "yes" ]]; then
    echo "Error: alpha channel required but not present: $image_path" >&2
    status=2
  fi
done

exit "$status"
