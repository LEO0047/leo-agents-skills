# skills/claude

**Claude Code 專屬** skill。

## 收錄條件

- 依賴 Claude Code 特有機制（例如 `argument-hint`、`disable-model-invocation`、Claude Code skill loader）
- `SKILL.md` 的 `compat` 應只包含 `claude-code`
- 安裝位置：`~/.claude/skills/<name>/`

## 何時升級到 `skills/shared/`

若實測在 Codex 也能跑（補上 `metadata` frontmatter 後仍正確觸發），把 `compat` 加上 `codex` 並把目錄搬到 `skills/shared/`。

詳見根目錄 [`docs/SKILL_SPEC.md`](../../docs/SKILL_SPEC.md)。
