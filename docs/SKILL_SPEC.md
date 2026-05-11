# SKILL.md 撰寫規範

本倉庫所有 skill 必須遵守的最小規範。目的：讓同一份 `SKILL.md` 在 Claude Code 與 Codex 都能解析，且未來新增平台時不需要回頭重寫。

## 目錄與檔名

- 每個 skill 是**一個目錄**，不是單檔。目錄名 = frontmatter `name` 欄位。
- 目錄名規則：**小寫 + 連字號**。例：`find-skills`、`codex-handoff`。不要用駝峰 `findSkills`、不要用底線 `find_skills`。
- 主檔名固定 **`SKILL.md`**（全大寫副檔名小寫），兩個平台官方約定。
- 選擇性子目錄：`references/`、`scripts/`、`agents/`、`assets/`。命名沿用既有慣例。

## 歸屬（在哪個 `skills/<bucket>/` 底下）

| 條件 | 放在 |
|---|---|
| 兩個平台都能用，且實際在兩邊測試過 | `skills/shared/` |
| 只在 Claude Code 用（依賴 Claude 特有機制如 `argument-hint`、`disable-model-invocation`） | `skills/claude/` |
| 只在 Codex 用（依賴 Chronicle、Codex pet 等專屬概念） | `skills/codex/` |

**判斷不出來時優先放對應平台的專屬目錄，未來確認跨平台再升級到 `shared/`。**

## frontmatter 規範

### 必填欄位

```yaml
---
name: graphify
description: "一句話說明，會被 agent 用來決定是否觸發。語意要清楚，描述觸發場景。"
compat: [claude-code, codex]
---
```

- `name`：**必須**等於目錄名。
- `description`：一句話、聚焦觸發場景。避免行銷詞，寫清楚「什麼時候用」「處理什麼輸入」。
- `compat`：陣列，列出支援的平台。詞表見 [`COMPAT.md`](COMPAT.md)。

### 選擇性欄位（平台特定）

| 欄位 | 平台 | 用途 |
|---|---|---|
| `trigger` | Claude Code | slash command 觸發詞，如 `/graphify` |
| `argument-hint` | Claude Code | 顯示在使用者輸入欄的提示 |
| `disable-model-invocation` | Claude Code | 設 `true` 則只能透過明確指令觸發 |
| `metadata.short-description` | Codex | Codex 列表顯示用的短描述 |
| `metadata.*` | Codex | Codex 其他擴充欄位 |
| `tags` | 通用 | 用於 README 索引、未來搜尋 |

### 雙平台寫法範例

當一個 skill 在 `skills/shared/` 底下，frontmatter 同時保留兩個平台需要的欄位：

```yaml
---
name: graphify
description: "any input → knowledge graph"
compat: [claude-code, codex]
trigger: /graphify
metadata:
  short-description: "Build a knowledge graph from any folder"
tags: [knowledge-graph, viz]
---
```

兩個平台解析器都會挑自己關心的欄位，其餘忽略。

## 撰寫風格

- 第一段（H1 之後）一兩句話講清楚這個 skill 解決什麼問題。
- 之後用小標分節：`## Usage` / `## When to use` / `## Inputs` / `## Outputs` 等。
- 範例與指令用 fenced code block，明確標語言（` ```bash ` / ` ```yaml `）。
- 不要重複 frontmatter `description` 的內容。

## 變更時的注意事項

- 改 `name` 等於改目錄名，記得同步。
- 從 `claude/` 或 `codex/` 移到 `shared/` 時：更新 `compat` 陣列，補齊另一個平台需要的 frontmatter 欄位。
- 新增 `compat` 詞時先更新 [`COMPAT.md`](COMPAT.md)。
