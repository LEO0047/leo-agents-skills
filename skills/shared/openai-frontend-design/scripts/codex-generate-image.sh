#!/bin/bash
# Bridge to OpenAI native image generation via a non-interactive Codex subagent.
#
# Claude Code has no built-in image generation tool. The bundled Codex CLI does
# (`image_gen__imagegen`) and reuses the existing ChatGPT login, so no API key is
# needed. This script runs one Codex turn whose only job is to generate an image
# and copy it to a path you choose.
#
# Usage:
#   codex-generate-image.sh --out <path.png> --prompt-file <prompt.txt> [options]
#   codex-generate-image.sh --out <path.png> --prompt "<text>"          [options]
#
# Options:
#   --edit <path>     Local source image to edit instead of generating fresh.
#                     Repeatable for multiple references.
#   --model <id>      Codex model for the driving turn (not the image model).
#   --timeout <sec>   Hard limit on the Codex turn. Default 600.
#   --dry-run         Print the composed Codex invocation and exit.
#
# Refuses to overwrite an existing --out path: the skill requires new paths for
# every derived asset.

set -euo pipefail

CODEX_BIN="${CODEX_BIN:-/Applications/ChatGPT.app/Contents/Resources/codex}"
OUT=""
PROMPT=""
PROMPT_FILE=""
MODEL=""
TIMEOUT=600
DRY_RUN=0
EDIT_PATHS=()

die() { printf 'error: %s\n' "$1" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --out)         OUT="${2:-}"; shift 2 ;;
    --prompt)      PROMPT="${2:-}"; shift 2 ;;
    --prompt-file) PROMPT_FILE="${2:-}"; shift 2 ;;
    --edit)        EDIT_PATHS+=("${2:-}"); shift 2 ;;
    --model)       MODEL="${2:-}"; shift 2 ;;
    --timeout)     TIMEOUT="${2:-}"; shift 2 ;;
    --dry-run)     DRY_RUN=1; shift ;;
    -h|--help)     sed -n '2,28p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)             die "unknown argument: $1" ;;
  esac
done

[ -n "$OUT" ] || die "--out is required"
[ -x "$CODEX_BIN" ] || die "Codex CLI not executable at $CODEX_BIN (override with CODEX_BIN)"

if [ -n "$PROMPT_FILE" ]; then
  [ -f "$PROMPT_FILE" ] || die "prompt file not found: $PROMPT_FILE"
  PROMPT="$(cat "$PROMPT_FILE")"
fi
[ -n "$PROMPT" ] || die "provide --prompt or --prompt-file"

[ -e "$OUT" ] && die "refusing to overwrite existing path: $OUT (choose a new output path)"

OUT_DIR="$(cd "$(dirname "$OUT")" 2>/dev/null && pwd)" \
  || die "output directory does not exist: $(dirname "$OUT")"
OUT_NAME="$(basename "$OUT")"
case "$OUT_NAME" in
  *.png|*.jpg|*.jpeg|*.webp) ;;
  *) die "--out must end in .png, .jpg, .jpeg, or .webp" ;;
esac

# Edit mode needs the source readable by the Codex sandbox.
EXTRA_DIRS=()
EDIT_INSTRUCTION=""
if [ ${#EDIT_PATHS[@]} -gt 0 ]; then
  EDIT_LIST=""
  for p in "${EDIT_PATHS[@]}"; do
    [ -f "$p" ] || die "edit source not found: $p"
    abs="$(cd "$(dirname "$p")" && pwd)/$(basename "$p")"
    EDIT_LIST="${EDIT_LIST}
- ${abs}"
    EXTRA_DIRS+=(--add-dir "$(dirname "$abs")")
  done
  EDIT_INSTRUCTION="
This is an EDIT, not a fresh generation. First inspect each local source with
your view_image tool, then pass exactly these local paths as
referenced_image_paths (never mix local paths with conversation-image
references):${EDIT_LIST}
Preserve every stated invariant. Do not modify the source files."
fi

# The turn is deliberately over-constrained: exec mode cannot answer questions,
# and a chatty agent wastes tokens without producing a file.
read -r -d '' TASK <<EOF || true
Generate one image with your built-in image generation tool, then save it into
your working directory as exactly \`${OUT_NAME}\`.
${EDIT_INSTRUCTION}

Image prompt, to be used as written:
---
${PROMPT}
---

Hard rules for this turn:
- Never ask a question. If a detail is missing, choose the reading that best
  serves the prompt as written and state the assumption in one line.
- Do not augment, editorialize, or "improve" the subject, palette, background,
  or composition beyond what the prompt states.
- Copy the generated file to ./${OUT_NAME}. Do not move or delete the original
  under ~/.codex/generated_images — it must stay as the preserved source.
- Do not touch, overwrite, or delete any other file in the working directory.
- Do not install anything, run git, or reach the network beyond generation.

Finally print exactly these four lines and nothing else after them:
SAVED=<absolute path of ./${OUT_NAME}>
ORIGINAL=<absolute path of the preserved generated original>
METADATA=<one-line output of: sips -g pixelWidth -g pixelHeight -g hasAlpha ./${OUT_NAME}>
ASSUMPTIONS=<one line, or "none">
EOF

CMD=("$CODEX_BIN" exec -C "$OUT_DIR" -s workspace-write --skip-git-repo-check)
[ -n "$MODEL" ] && CMD+=(-m "$MODEL")
[ ${#EXTRA_DIRS[@]} -gt 0 ] && CMD+=("${EXTRA_DIRS[@]}")

if [ "$DRY_RUN" -eq 1 ]; then
  printf 'would run: %s\n' "${CMD[*]}"
  printf -- '--- turn instructions ---\n%s\n' "$TASK"
  exit 0
fi

printf 'generating via Codex subagent -> %s/%s\n' "$OUT_DIR" "$OUT_NAME" >&2

LOG="$(mktemp -t codex-imagegen)"
trap 'rm -f "$LOG"' EXIT

# macOS ships no `timeout`; use it only when coreutils provides one.
TIMEOUT_BIN=""
for c in timeout gtimeout; do
  command -v "$c" >/dev/null 2>&1 && { TIMEOUT_BIN="$c"; break; }
done

if [ -n "$TIMEOUT_BIN" ]; then
  "$TIMEOUT_BIN" "$TIMEOUT" "${CMD[@]}" "$TASK" >"$LOG" 2>&1 || true
else
  "${CMD[@]}" "$TASK" >"$LOG" 2>&1 || true
fi

# Truth comes from the filesystem, never from the agent's own claim.
if [ ! -f "$OUT_DIR/$OUT_NAME" ]; then
  printf 'FAILED: no file at %s/%s\n' "$OUT_DIR" "$OUT_NAME" >&2
  printf -- '--- last 30 lines of Codex output ---\n' >&2
  tail -30 "$LOG" >&2
  exit 1
fi

grep -E '^(SAVED|ORIGINAL|METADATA|ASSUMPTIONS)=' "$LOG" | tail -4 || true
printf 'VERIFIED_ON_DISK=%s/%s\n' "$OUT_DIR" "$OUT_NAME"
sips -g pixelWidth -g pixelHeight -g hasAlpha -g format "$OUT_DIR/$OUT_NAME" 2>/dev/null | tail -5
