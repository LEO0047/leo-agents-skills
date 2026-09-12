---
name: ai-course-search
compat: [codex]
description: 搜尋 Leo 的「Ai課程設計」V2 本機研究庫與 Leo 想法。當其他 Codex 對話需要既有研究、證據、課程對照、影片字幕或 Leo 原話時使用；不適用一般網路搜尋。
---

# AI 課程資料庫搜尋

先由使用者指定既有「Ai課程設計」工作區，或使用當前已確認的工作區。公開包只包含搜尋流程，不包含 V2 資料、索引、模型權重或搜尋程式。

先讀該工作區的 `AGENTS.md`，接著讀 `V2資料庫/AGENTS.md`。詳細操作以 `V2資料庫/scripts/embed/README.md` 為單一來源，不要另造搜尋系統。

在 `V2資料庫` 使用 `.venv.nosync/bin/python scripts/embed/search.py query "問題"`。這是本機 Qwen3 混合搜尋，回傳有來源的段落，不產生答案。判斷研究依據時加 `--source-kind evidence`；找 Leo 原話時加 `--source-kind idea --authorship leo_original`。精確參數與錯誤處理見工作區指引。

需要既有研究時先檢索，再回查引用段落。任務狀態去讀 `Handoff/待辦接力.md`，不要從研究搜尋推算。這個技能不授權新增研究、修改 Notion、下載模型或安排其他任務。BGE-M3 已移至垃圾桶，不要自動下載回來。

如果本機路徑或模型不存在，說明缺少的資源；不可假裝已搜尋。此技能依賴這台 Mac 的本機資料，不是跨電腦或雲端資料服務。
