# skills/shared

同時支援 **Claude Code** 與 **Codex** 的 skill。

## 收錄條件

- 在兩個平台都實際測試過、能正常觸發
- `SKILL.md` 的 `compat` 欄位**必須**包含 `claude-code` 與 `codex`
- frontmatter 同時保留兩個平台需要的欄位（例如 `trigger` + `metadata`）

## 升降級規則

- 從 `skills/claude/` 或 `skills/codex/` 升上來時：補齊另一平台的 frontmatter 欄位、更新 `compat` 陣列
- 若某 skill 後來只在單一平台維護：降回對應的 `claude/` 或 `codex/`

詳見根目錄 [`docs/SKILL_SPEC.md`](../../docs/SKILL_SPEC.md)。
