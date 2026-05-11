# compat 欄位詞表

`SKILL.md` 的 `compat` 陣列只能用這份文件登記過的詞。新增平台 = 先更新本檔。

## 目前支援

| 詞 | 對應平台 | 解析的 frontmatter |
|---|---|---|
| `claude-code` | Anthropic Claude Code CLI | `name`, `description`, `trigger`, `argument-hint`, `disable-model-invocation` |
| `codex` | OpenAI Codex CLI | `name`, `description`, `metadata.*` |

## 未來可能加入（暫未支援）

加入時：在此表登記、補一段「Notes for `<platform>`」說明它解析哪些欄位、有什麼坑。

- `cursor`：Cursor IDE 的 project rules
- `gemini-cli`：Google Gemini CLI 的 `activate_skill` 機制
- `copilot-cli`：GitHub Copilot CLI

## 使用範例

```yaml
compat: [claude-code]                # 只支援 Claude Code
compat: [codex]                      # 只支援 Codex
compat: [claude-code, codex]         # 兩個都支援（放在 skills/shared/）
```

## 與目錄歸屬的關係

`compat` 是真實宣告；目錄是分類索引。兩者應該一致：
- `skills/shared/<name>/` 的 `compat` **必須**包含 `claude-code` 和 `codex` 兩項。
- `skills/claude/<name>/` 的 `compat` **應該**只有 `claude-code`。
- `skills/codex/<name>/` 的 `compat` **應該**只有 `codex`。

若實測發現某 skill 跨平台可用，**先升級 `compat` 並把目錄搬到 `shared/`**，兩者同步。
