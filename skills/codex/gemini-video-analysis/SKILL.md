---
name: gemini-video-analysis
compat: [codex]
description: 用現有 agy CLI 與 Gemini 3.8 Flash 分析本機影片或先下載的公開影片，保存時間索引、原始筆記與可回查的分析。適用於「用 agy/Gemini 看影片」「影片深挖並存檔」；僅收藏連結時不啟動分析。
---

# Gemini-Video-Analysis

將影片交給 Gemini 看與記錄，再由目前的 Codex 整理分析並抽查。依使用者指定位置交付 Markdown 與附件，保留原話、來源與不確定性。不要因使用此 skill 自動擴成市場研究輪次、正式 evidence 入庫或跨平台爬取。

## 現有依賴

這是 Leo 本機既有 V2 流程的封裝，不是獨立跨機影片平台。優先使用目前工作區的 V2；找不到時請使用者指定既有 V2 根目錄。此公開包不包含研究資料庫、登入狀態、AGY runtime 或 V2 程式；不可視為獨立安裝即可執行。

必要檔案：

- `.venv.nosync/bin/python`（現有 Python 環境）
- `scripts/extract/video_notes.py`、`scripts/extract/agy_video_guard.py` 與 `config/video_analysis.yaml`
- URL 下載：`scripts/crawl/media_download.py`
- 選配字幕／抽查：`scripts/crawl/youtube_transcript.py`、`av_probe.swift`、`av_frame.swift`

讀取當前專案規則與以上程式涉及的參數，確認檔案仍存在。不要靜默重建資料庫、安裝另一套工具或改全域設定。`agy models` 確認指定模型可用；本流程預設 `gemini-3.8-flash-low`，除非使用者指定其他 effort。模型不可用就如實回報，不偷偷換模型。

## 取得與規劃

- 讀取確切目標文件，保留使用者原話。若指定「剛剛的地方」，沿用該文件與索引；附件放相鄰的專屬子資料夾。不要將所有影片堆進同一檔案，也不要在其他專案強制建立 Leo想法區。
- 先查這支影片的來源 ID、既有 metadata、筆記與雜湊。已有可用分析時讀取與整理，避免重複付費；若使用者要求重新分析，使用新附件目錄保存新版本。
- 公開 URL 先用現有下載器確認標題、頻道及格式，再下載；本機影片直接使用。agy 這條流程吃本機影片，不能把傳 URL 後得到的網頁摘要算作看完影片。
- 下載器的 `--content-id` 是必填。研究庫有正式 ID 就用它；獨立想法筆記可用本地追蹤標記，但不可冒充資料庫實體 ID。不要預先建立下載器的目標 raw 目錄。

```bash
# 下列命令在確認過的 V2 根目錄執行；替換 URL 與本地追蹤標記。
.venv.nosync/bin/python scripts/crawl/media_download.py --url 'URL' --content-id 'LOCAL_ID' --dry-run
.venv.nosync/bin/python scripts/crawl/media_download.py --url 'URL' --content-id 'LOCAL_ID'
```

影片下載完成後，必要時用現有字幕腳本取得作者字幕或原語自動字幕，供引文核對；取得失敗就記錄缺口，不把翻譯字幕當原文，不為此擅自加 ASR 依賴。長片先確認時長與影音時間軸是否一致。收到限流／登入限制時不要繞過，記錄阻礙。

只分析已要求的影片。長片或批次先看時長、已有結果與成本。單次分析的數字不是所有影片的固定成本。

### 長影片預設先切段（Leo 2026-09-07 指定）

- 長片必須先切成有影音的本機段落，再逐段交給 Gemini，不直接把整支長片一次送出。使用者指定分段時，不論片長都依此流程。
- 未指定段長時，以超過 5 分鐘視為長片、每段約 2–3 分鐘作為工作預設；可依章節、句子與實測成本調整，這不是模型上限。最後不足一段也要分析。
- 先確認原片影音起點與時長。切段採目前可用工具；macOS 可用 AVFoundation，不為切片安裝整套影音環境。切後核對每段影音、時長及最後一段，避免漏掉片尾。
- 保存分段清單：原片 SHA、每段序號、原片起訖秒數、實際時長、片段 SHA、分析輸出目錄。必要時保留小幅重疊以接續語境，合併時去重。
- 每段各自呼叫本 skill 的 analyze.py 並保存 prompt、原始回應、metadata 與筆記。先跑一段檢查品質和用量，再循序處理其餘段；失敗只處理該段，不重跑已完成片段。
- 合併筆記保留段內時間，再加原片起點換算原片時間；越界或疑似漏看的時間標記待核對，不直接當精確時間戳。
- 只有所有段落都有可追溯結果、時間覆蓋完整且完成覆核後，才報全片分析完成。部分成功需逐段列出缺口，不能用摘要或抽樣補成全片。
- 清理依原有保留規則，先保存片段 SHA 與去向；不移動使用者原有影片。


## AGY 讀片與崩潰修正（2026-09-08）

- 使用下列 analyze.py 或 V2 video_notes.py；兩者共用 `native-video-guard/1`。每次呼叫的 PreToolUse hook 只准 `view_file` 讀指定影片，禁止 AGY 執行指令、寫程式、安裝依賴或讀其他檔案。不使用 `--dangerously-skip-permissions`。
- AGY 直接讀 MP4；讀不到就保留失敗，不讓它自行改用 Python ctypes、Objective-C、Swift、抽幀、OCR 或 ASR。切段和事後畫面核對由目前 Agent 使用既有工具另做。
- 成功結果須有 `native_media_step_indices` 與 `tool_audit_path`，證明指定影片以 `video/mp4` 傳入。JSON 合格仍需內容抽查。舊分析／恢復回應若缺讀片證明，標「讀片方式待核對」，不自動算完整影片，也不自動重付費。
- 逾時會終止這次 AGY 的程序群組，原始輸出與工具紀錄留在 `logs.nosync/extract/agy-workspaces/`。失敗先查紀錄；不要原樣循環重跑，也不要用隱藏 macOS 崩潰通知代替修正。

## 執行 Gemini

`SKILL_DIR` 設為本 SKILL.md 所在的絕對目錄。公開資料夾名稱為 `gemini-video-analysis`，顯示名稱保留 Gemini-Video-Analysis；不改本機既有安裝名稱。

獨立筆記使用本 skill 的薄封裝，重用 V2 的 prompt、schema、agy runtime 與解析函式，不写 normalized 或 DuckDB：

```bash
.venv.nosync/bin/python "$SKILL_DIR/scripts/analyze.py" \
  --v2-root "$PWD" --video '/absolute/video.mp4' \
  --source-url 'https://www.youtube.com/watch?v=VIDEO_ID' \
  --output '/absolute/target/分析附件' --timeout 900
```

- `--dry-run` 只確認依賴、計算指紋與顯示執行計畫，不呼叫模型、不建立附件。
- 輸出目錄須專用；相同影片、模型、prompt、來源的完整結果會 cache hit；不同請求或失敗未完成會停止，避免覆寫或不明重跑。執行期間不並行操作同一輸出目錄。
- 現有 runtime 預設低 effort、prompt 內 schema 加本地驗證，不加 `--json-schema`。後者曾明顯增加 token 消耗；不要為了格式問題立即重跑模型。
- 原 runtime 保存完整 agy 回應至 V2 `logs.nosync/extract/agy/`。若解析或格式驗證失敗，先找這次來源與呼叫的原始輸出。外層 ERROR 但有完整 response 時可以恢復，仍需記錄錯誤並檢查內容，不能直接當成功。
- 恢復時加 `--recover-agy-output '/absolute/saved-response.txt'`，使用新的附件目錄，且由目前 Agent 確認回應確實屬於同一影片、prompt 與模型。此路徑不再呼叫模型。
- 執行中以短等待讀取狀態並持續更新使用者；不因尚未回傳而再送一次。逾時保留失敗紀錄；先查現有回應能否恢復，再決定是否有理由重試。

若使用者明確要求正式 V2 入庫，改用現有 `video_notes.py --video ... --run-id ...` 的持久化與 cache 路線，之後依當前專案規則使用 `video_to_evidence.py prepare → 目前 Agent 判讀 → ingest`。不要先跑獨立筆記再付費重跑一次入庫。

## 整理與抽查

讀取完整 `gemini-notes.json`，由目前 Agent 寫分析，不將 Gemini 描述偽裝成 Leo 主張或逐字引文。重點包括：

- 影片 metadata、來源連結、分析模型、實際分析範圍與時間索引。
- 各段任務、輸入／限制、工具、可见成果、失敗與修正。講者評價另外標示。
- 回應使用者的用途；例如課程研究才加候選練習、學員負擔與待驗證項目。不強制所有影片都是課程案例。
- 對重要或可疑畫面做適量抽查（可用現有 `av_frame.swift` 取得、`view_image` 閱讀），記錄時間戳與圖檔。抽幀是驗證 Gemini 筆記，不取代 Gemini 分析全片。
- 核對時間界線、前後矛盾、數量與名稱。`quality_flags=[]`、JSON 合格、agy SUCCESS 都不是全片內容正確的證明。沒有明確來源就 null／待確認。
- `spoken_text`、`on_screen_text` 仍是模型辨讀；未與字幕或畫面比對不能標成已核實引文。`summary`、`what_happens` 是描述，不能當逐字引用。
- 成品或過程紀錄頁不證明整段操作完全自主；列印中不等於實物完成；對比示範不等於全面評測勝出。影片中的價格、會員權益等只作講者內容；若要當現行事實，另查第一方資料。

保存主分析文件、原始筆記、prompt、分析 metadata、必要核對畫面及限制；更新既有索引。檢查附件連結與 JSON 可讀性。報告 token／耗時取自實際回應，未知金額不要推算。

## 影片保留與完成條件

保留方式依當前專案和使用者指示，不把 V2 的清理習慣當全域預設。V2 既有規則是分析完成後將下載影音移到垃圾桶，保留來源 metadata、筆記、字幕、核對畫面、SHA 與去向紀錄；執行前確認規則仍適用。不要移動使用者原有影片、未分析完的檔案或清空垃圾桶。

交付前確認：真實 Gemini 呼叫／可追溯恢復結果、覆蓋範圍明確、重要疑點揭露、主文與附件已落地且連結可用。最終簡述結果並給主文件連結；筆記完成不代表課程驗證或研究輪次 PASS。
