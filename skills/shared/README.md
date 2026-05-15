# skills/shared

同時支援 **Claude Code** 與 **Codex** 的 skill。

## 輸出格式規則

- 給使用者主要閱讀的長篇說明、比較表、儀表板、交接文件、模型狀態頁，優先輸出 self-contained HTML。
- 給 agent 主要讀取的規則、skill、command、memory note、handoff prompt，優先保留 `.md`。
- 若要做本機 HTML 參考頁，可參考桌面 `LLM模型設定.html` 目前示範出的風格，但不要依賴該檔永久存在；耐久規則是深色操作面板、section heading、卡片、表格、驗證與後續方向。
- 不更新第三方 README、模型卡、generated transcript、reasoning log 或外部工具文件來套這條規則。

## 收錄條件

- 在兩個平台都實際測試過、能正常觸發
- `SKILL.md` 的 `compat` 欄位**必須**包含 `claude-code` 與 `codex`
- frontmatter 同時保留兩個平台需要的欄位（例如 `trigger` + `metadata`）

## 升降級規則

- 從 `skills/claude/` 或 `skills/codex/` 升上來時：補齊另一平台的 frontmatter 欄位、更新 `compat` 陣列
- 若某 skill 後來只在單一平台維護：降回對應的 `claude/` 或 `codex/`

詳見根目錄 [`docs/SKILL_SPEC.md`](../../docs/SKILL_SPEC.md)。
