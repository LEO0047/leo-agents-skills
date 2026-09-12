# 2026-09-13 本機自訂技能同步

範圍：本機 Codex、Claude Code 及共用安裝入口；同一 symlink 去重。新增 9 個 Codex 技能、更新 `openai-frontend-design`。`frontend-design`、`voice-notes` 的公開部分與倉庫一致，保留現有版本。Claude Code 的 Matt Pocock 套件屬第三方技能集合，本次未當作 Leo 獨有技能重複收錄；系統技能與外掛快取亦不收錄。

## 公開副本與原始安裝

- 本機原檔沒有改動。此次是經檢查的公開副本，不是私人目錄的完整備份。
- `Gemini-Video-Analysis` 在公開庫採 `gemini-video-analysis` 小寫目錄與 frontmatter，顯示名稱維持原名；安裝時注意同名／大小寫衝突，不自動替換原安裝。
- Instagram 私人聯絡人／thread URL 對照未上傳，改為目前任務的安全解析說明。
- 研究庫、完整教材截圖、個人絕對路徑、登入資料、聊天紀錄、缓存及 LEO overlay 不上傳。HTML 附件只包含模板和產生器。
- 保留既有授權檔案；前端設計技能包含上游內容與本機修改，不能宣稱所有內容都是 Leo 原創。
- `scripts/check-drift.sh` 既有比對只涵蓋它明列的安裝點，並未涵蓋本次九份經去識別的公開副本；不將可預期的隱私／命名差異當作安裝一致。

## 外部依賴

| 技能 | 另需準備 |
|---|---|
| gemini-video-analysis | 已配置 AGY 與登入、既有 V2 Python 環境、video_notes.py、agy_video_guard.py、模型設定與下载／切段工具；本包只是薄封裝 |
| ai-course-search | 使用者自己的 V2 工作區、Qwen 搜尋程式、資料與索引；不附私有資料 |
| ai-course-html-series | 自己的主題資料與可公開使用的圖片；模板不包含實拍素材 |
| instagram-readonly | 已登入的 Codex 內建瀏覽器及技能所列相容 DOM／捲動能力；缺能力時回報，不改用未授權路徑 |
| line-chat-advisor | 可用的 line-readonly MCP 及合法可讀的本機 LINE 環境；本包不含 MCP server 或聊天資料 |
| manage-taskboard | Codex Taskboard、taskctl 與已配置的本地服務；本包不含服務及認證 |
| taiwan-esg-research | 研究時可讀取的官方來源；寫入時另需 Notion 存取與當次授權。附離線驗證／預覽程式 |
| chatgpt-web | 已登入的 ChatGPT 與可用瀏覽器工具；模型依現場選單辨識 |
| video-date-quality | 可讀影片中繼資料的 ffprobe 或 macOS AVFoundation |
| openai-frontend-design | Codex 原生生圖，或 Claude Code 透過 Codex CLI wrapper；macOS 圖片處理工具 |

新增技能先放 codex bucket，沒有據此宣稱跨平台完整驗收。發布檢查涵蓋封裝、語法、離線測試與既有 CI；不代表本次重新操作 Instagram、LINE、Notion，或付費重跑 Gemini／生圖。
