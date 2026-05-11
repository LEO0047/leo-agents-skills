# leo-agents-skills

Leo 的個人精選 agent skill 倉庫，跨 Claude Code、Codex 等不同平台。

收錄的不是「全部」，而是**自己覺得有價值、會反覆用到、值得跨機器同步**的那些。

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
| [find-skills](skills/shared/find-skills/) | 在 skill 生態裡搜尋與安裝可重用的 skill |

### claude
| Skill | 一句話 |
|---|---|
| [codex-handoff](skills/claude/codex-handoff/) | 把 Opus 的計畫轉成簡短可貼上的 Codex rescue handoff prompt |

### codex
| Skill | 一句話 |
|---|---|
| [chronicle](skills/codex/chronicle/) | 讓 agent 看到使用者螢幕近幾小時的滾動緩衝 |
| [hatch-pet](skills/codex/hatch-pet/) | 從角色概念或參考圖製作 Codex 寵物動畫 spritesheet |
| [playwright](skills/codex/playwright/) | 終端機驅動真實瀏覽器做自動化 |

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
