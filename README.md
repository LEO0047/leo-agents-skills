# leo-agents-skills

Leo 的個人精選 agent skill 倉庫，跨 Claude Code、Codex 等不同平台。

收錄的不是「全部」，而是**自己覺得有價值、會反覆用到、值得跨機器同步**的那些。

## 輸出格式規則

- 給 Leo 主要閱讀、比較、交接、長期參考的輸出，優先做成 self-contained HTML。
- 給 agent 主要讀取、接手、解析、維護的規則與操作文件，優先使用 `.md`。
- 短回覆、一般狀態更新、PR 文字、commit message、AGENTS.md、SKILL.md、README 仍維持 Markdown。
- 本機使用者向 HTML artifact 可參考桌面 `LLM模型設定.html` 目前示範出的風格，但不要依賴該檔永久存在；耐久規則是深色操作面板、section heading、卡片、表格、驗證與後續方向。
- 不為了套格式去改第三方 README、模型卡、generated transcript、reasoning log 或外部工具文件。

完整規則見 [`OUTPUT_FORMAT_POLICY.md`](OUTPUT_FORMAT_POLICY.md)。

## 倉庫結構

```
skills/
├── shared/      # 同時支援 Claude Code + Codex 的 skill
├── claude/      # Claude Code 專屬
└── codex/       # Codex 專屬
commands/
├── claude/      # Claude Code slash commands
└── codex/       # Codex slash commands
```

詳細規範見 [`docs/SKILL_SPEC.md`](docs/SKILL_SPEC.md)。

## 現有 skill 索引

### shared （跨平台）
| Skill | 一句話 |
|---|---|
| [graphify](skills/shared/graphify/) | 任意資料夾 → 知識圖譜（互動 HTML + JSON + 稽核報告） |
| [html-artifacts](skills/shared/html-artifacts/) | 判斷何時把 Agent 輸出升級成自包含 HTML artifact，而不是每次都用 HTML |
| [find-skills](skills/shared/find-skills/) | 在 skill 生態裡搜尋與安裝可重用的 skill |

### claude
| Skill | 一句話 |
|---|---|
| [codex-handoff](skills/claude/codex-handoff/) | 把 Opus 的計畫轉成簡短可貼上的 Codex rescue handoff prompt |

### codex
| Skill | 一句話 |
|---|---|
| [chronicle](skills/codex/chronicle/) | 讓 agent 看到使用者螢幕近幾小時的滾動緩衝 |
| [game-mod-management](skills/codex/game-mod-management/) | 遊戲 mod repo 與本機流程管理，特別是 BG3 存檔救援、manifest、load order 與驗證 |
| [game-modops-agent](skills/codex/game-modops-agent/) | Game ModOps v3 Windows 控制塔，協調 Nexus、Vortex、Wabbajack、MO2、LOOT 與 BG3 工具 |
| [hatch-pet](skills/codex/hatch-pet/) | 從角色概念或參考圖製作 Codex 寵物動畫 spritesheet |
| [nexus-mod-automation](skills/codex/nexus-mod-automation/) | 安全自動化 Nexus Mods / Vortex 下載佇列、監控、壓縮檔檢查與報告 |
| [playwright](skills/codex/playwright/) | 終端機驅動真實瀏覽器做自動化 |
| [windows-ui-automation](skills/codex/windows-ui-automation/) | 透過 PowerShell UI Automation 操作 Windows 桌面應用與控制項 |

### commands
| Command | 平台 |
|---|---|
| [/codex-handoff](commands/claude/codex-handoff.md) | claude |

## 安裝（暫定，未自動化）

目前**不提供 install 腳本**，倉庫只是 ground truth。如要在新機器啟用：

```bash
# 範例：手動連結到 Claude Code skills 目錄
ln -s "$(pwd)/skills/shared/graphify" ~/.claude/skills/graphify
ln -s "$(pwd)/skills/claude/codex-handoff" ~/.claude/skills/codex-handoff

# Codex 同理
ln -s "$(pwd)/skills/shared/find-skills" ~/.codex/skills/find-skills
ln -s "$(pwd)/skills/codex/chronicle" ~/.codex/skills/chronicle
```

未來會補一支 `scripts/install.sh` 自動處理（symlink 模式）。

## 貢獻自己的 skill

1. 從 [`templates/skill.template.md`](templates/skill.template.md) 起步
2. 決定歸屬：`shared/` / `claude/` / `codex/`
3. frontmatter 必填 `name / description / compat`
4. 目錄名 = `name`（小寫 + 連字號），檔案固定 `SKILL.md`

完整規範見 [`docs/SKILL_SPEC.md`](docs/SKILL_SPEC.md)。
