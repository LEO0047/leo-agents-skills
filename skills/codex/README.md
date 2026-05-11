# skills/codex

**Codex 專屬** skill。

## 收錄條件

- 依賴 Codex 特有機制（例如 Chronicle 螢幕緩衝、Codex pet 概念、Codex 系統 skill 如 `$imagegen`）
- `SKILL.md` 的 `compat` 應只包含 `codex`
- 安裝位置：`~/.codex/skills/<name>/`

## 何時升級到 `skills/shared/`

若實測在 Claude Code 也能跑（補上 `trigger` 等 frontmatter 後仍正確觸發），把 `compat` 加上 `claude-code` 並把目錄搬到 `skills/shared/`。

詳見根目錄 [`docs/SKILL_SPEC.md`](../../docs/SKILL_SPEC.md)。
