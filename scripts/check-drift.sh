#!/bin/bash
# 比對「本機安裝的 skill」與「repo 內的 skill」是否一致。
#
# 用法：
#   scripts/check-drift.sh          # 檢查所有安裝點，列出漂移
#   scripts/check-drift.sh -q      # 只回報結果（配合排程使用）
#
# 規則：
# - repo 是 ground truth；安裝點內容應與 repo 完全相同。
# - <!-- LEO_*_OVERLAY START/END --> 標記之間是本機個人覆蓋層，
#   刻意不入公開庫，比對前會先剝除。
# - __pycache__ 與 .DS_Store 一律忽略。
# - 有漂移 exit 1，全部一致 exit 0。

set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
QUIET=0
[ "${1:-}" = "-q" ] && QUIET=1

# 安裝對照表：repo 相對路徑 → 安裝點（一行一組，冒號分隔，可多個安裝點用空白分隔）
MAP="
skills/shared/frontend-design:$HOME/.claude/skills/frontend-design $HOME/.codex/skills/frontend-design
skills/shared/openai-frontend-design:$HOME/.claude/skills/openai-frontend-design $HOME/.codex/skills/openai-frontend-design
skills/shared/voice-notes:$HOME/.claude/skills/voice-notes $HOME/.codex/skills/voice-notes
skills/codex/hatch-pet:$HOME/.codex/skills/hatch-pet
"

strip_overlay() {
  # 剝除個人覆蓋層區塊後輸出檔案內容
  sed '/<!-- LEO_.*_OVERLAY START -->/,/<!-- LEO_.*_OVERLAY END -->/d' "$1"
}

drift=0
while IFS=: read -r rel installs; do
  [ -z "$rel" ] && continue
  repo_dir="$REPO/$rel"
  for inst in $installs; do
    if [ ! -d "$inst" ]; then
      [ $QUIET -eq 0 ] && echo "MISSING  $inst（未安裝）"
      drift=1
      continue
    fi
    # 逐檔比對（以 repo 與安裝點檔案聯集為準）
    files=$( (cd "$repo_dir" && find . -type f ! -name .DS_Store ! -path '*__pycache__*'; \
              cd "$inst" && find . -type f ! -name .DS_Store ! -path '*__pycache__*') | sort -u )
    pair_drift=0
    for f in $files; do
      a="$repo_dir/$f"; b="$inst/$f"
      if [ ! -f "$a" ]; then
        [ $QUIET -eq 0 ] && echo "DRIFT    $inst/${f#./}（repo 沒有此檔）"
        pair_drift=1; continue
      fi
      if [ ! -f "$b" ]; then
        [ $QUIET -eq 0 ] && echo "DRIFT    $inst/${f#./}（安裝點缺此檔）"
        pair_drift=1; continue
      fi
      if ! cmp -s <(strip_overlay "$a") <(strip_overlay "$b"); then
        [ $QUIET -eq 0 ] && echo "DRIFT    $inst/${f#./}（內容不同）"
        pair_drift=1
      fi
    done
    if [ $pair_drift -eq 0 ]; then
      [ $QUIET -eq 0 ] && echo "OK       $inst"
    else
      drift=1
    fi
  done
done <<< "$MAP"

if [ $drift -eq 0 ]; then
  echo "PASS: 所有安裝點與 repo 一致。"
else
  echo "FAIL: 偵測到漂移。repo 是 ground truth：改了安裝點請回寫 repo，改了 repo 請重新部署安裝點。"
  exit 1
fi
