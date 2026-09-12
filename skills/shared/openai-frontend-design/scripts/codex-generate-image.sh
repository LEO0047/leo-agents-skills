#!/bin/bash
# Bridge to OpenAI native image generation via a non-interactive Codex subagent.
#
# Claude Code has no built-in image generation tool. The bundled Codex CLI does
# (the built-in `image_gen` tool) and reuses the existing ChatGPT login, so no
# API key is needed. This script runs one Codex turn whose only job is to
# generate (or edit) one image and copy it to a path you choose.
#
# Usage:
#   codex-generate-image.sh --out <path.png> --prompt-file <prompt.txt> [options]
#   codex-generate-image.sh --out <path.png> --prompt "<text>"          [options]
#
# Options:
#   --edit <path>     Local source image to edit. Attached to the turn (-i) so the
#                     built-in tool can see it. Repeatable; order is preserved.
#   --model <id>      Codex model for the driving turn (NOT the image model).
#   --timeout <sec>   Hard limit on the Codex turn. Default 600. Enforced here;
#                     no coreutils `timeout` required.
#   --dry-run         Print the composed Codex invocation and exit.
#
# Refuses to overwrite an existing --out path: every derived asset gets a new
# path. The Codex original stays under ~/.codex/generated_images/.
#
# Output on success (stdout):
#   SAVED= ORIGINAL= METADATA= ASSUMPTIONS=   the subagent's own report
#   VERIFIED_ON_DISK=<path>                    checked by this script
#   sips metadata (size, alpha, format)        checked by this script
# Exit: 0 verified on disk | 1 usage or no file | 124 timed out

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
    -h|--help)     sed -n '2,29p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)             die "unknown argument: $1" ;;
  esac
done

[ -n "$OUT" ] || die "--out is required"
if [ ! -x "$CODEX_BIN" ]; then
  if command -v codex >/dev/null 2>&1; then
    CODEX_BIN="$(command -v codex)"
  else
    die "Codex CLI not executable at $CODEX_BIN and no 'codex' on PATH (override with CODEX_BIN)"
  fi
fi
case "$TIMEOUT" in
  ''|*[!0-9]*) die "--timeout must be a positive integer (seconds)" ;;
esac

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

# Edit sources are attached to the turn with -i, which is how the built-in tool
# sees an image: it edits images visible in the conversation, not arbitrary
# filesystem paths. No extra writable directories are granted for this.
ATTACH_ARGS=()
EDIT_INSTRUCTION=""
if [ ${#EDIT_PATHS[@]} -gt 0 ]; then
  EDIT_LIST=""
  for p in "${EDIT_PATHS[@]}"; do
    [ -f "$p" ] || die "edit source not found: $p"
    abs="$(cd "$(dirname "$p")" && pwd)/$(basename "$p")"
    EDIT_LIST="${EDIT_LIST}
- ${abs}"
    ATTACH_ARGS+=(-i "$abs")
  done
  EDIT_INSTRUCTION="
This is an EDIT, not a fresh generation. The image(s) attached to this message
are the edit sources, in this order:${EDIT_LIST}
Use the attached image(s) with your built-in image generation tool's edit flow.
Preserve every stated invariant. The source files on disk stay untouched."
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
- Use the prompt as written: same subject, palette, background, and composition.
  No augmentation, editorializing, or "improvement".
- Copy the generated file to ./${OUT_NAME}. Leave the original under
  ~/.codex/generated_images in place as the preserved source.
- Touch no other file in the working directory.
- Do not install anything, run git, or reach the network beyond generation.

Finally print exactly these four lines and nothing else after them:
SAVED=<absolute path of ./${OUT_NAME}>
ORIGINAL=<absolute path of the preserved generated original>
METADATA=<one-line output of: sips -g pixelWidth -g pixelHeight -g hasAlpha ./${OUT_NAME}>
ASSUMPTIONS=<one line, or "none">
EOF

CMD=("$CODEX_BIN" exec -C "$OUT_DIR" -s workspace-write --skip-git-repo-check)
[ -n "$MODEL" ] && CMD+=(-m "$MODEL")
[ ${#ATTACH_ARGS[@]} -gt 0 ] && CMD+=("${ATTACH_ARGS[@]}")
CMD+=(--)   # end of options: the prompt can never be parsed as an -i file

if [ "$DRY_RUN" -eq 1 ]; then
  printf 'would run: %s <TASK>\n' "${CMD[*]}"
  printf -- '--- turn instructions ---\n%s\n' "$TASK"
  exit 0
fi

printf 'generating via Codex subagent -> %s/%s (timeout %ss)\n' "$OUT_DIR" "$OUT_NAME" "$TIMEOUT" >&2

LOG="$(mktemp -t codex-imagegen)"
trap 'rm -f "$LOG"' EXIT

# Portable watchdog: macOS ships no coreutils `timeout`.
"${CMD[@]}" "$TASK" >"$LOG" 2>&1 &
CODEX_PID=$!
( sleep "$TIMEOUT"; kill -TERM "$CODEX_PID" 2>/dev/null ) 2>/dev/null &
WATCHDOG_PID=$!
CODEX_STATUS=0
{ wait "$CODEX_PID" || CODEX_STATUS=$?; } 2>/dev/null
{ pkill -P "$WATCHDOG_PID"; kill "$WATCHDOG_PID"; wait "$WATCHDOG_PID"; } >/dev/null 2>&1 || true

if [ "$CODEX_STATUS" -eq 143 ] || [ "$CODEX_STATUS" -eq 124 ]; then
  printf 'TIMEOUT: Codex turn exceeded %ss; no file accepted\n' "$TIMEOUT" >&2
  tail -20 "$LOG" >&2
  exit 124
fi

# Truth comes from the filesystem, never from the agent's own claim.
if [ ! -f "$OUT_DIR/$OUT_NAME" ]; then
  printf 'FAILED: no file at %s/%s (codex exit %s)\n' "$OUT_DIR" "$OUT_NAME" "$CODEX_STATUS" >&2
  printf -- '--- last 30 lines of Codex output ---\n' >&2
  tail -30 "$LOG" >&2
  exit 1
fi

grep -E '^(SAVED|ORIGINAL|METADATA|ASSUMPTIONS)=' "$LOG" | tail -4 || true
printf 'VERIFIED_ON_DISK=%s/%s\n' "$OUT_DIR" "$OUT_NAME"
sips -g pixelWidth -g pixelHeight -g hasAlpha -g format "$OUT_DIR/$OUT_NAME" 2>/dev/null | tail -4
