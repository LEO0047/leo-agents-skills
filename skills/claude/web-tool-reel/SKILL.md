---
name: web-tool-reel
description: "把自己做的瀏覽器視覺工具（WebGL／Canvas 網站，例如 Thermal Tracking）逐格驅動成跟音樂節拍對齊的 9:16 Reel；要用網站做作品短片、宣傳片或音樂同步剪輯時使用。"
compat: [claude-code]
tags: [video, motion-design, webgl, reel, instagram, ffmpeg, playwright]
---

# web-tool-reel

把一個在瀏覽器裡即時算畫面的網站，做成一支跟指定音樂逐格對齊的直式短片。片中畫面的效果全部來自網站自己的引擎，不是錄螢幕。第一次實作是 Thermal Tracking 的 24 秒 Reel，完整紀錄見 [references/thermal-tracking-case.md](references/thermal-tracking-case.md)。

三條核心原則，後面每一步都是為了守住它們：

1. **不錄螢幕。** 在網站副本加一個掛鉤，讓程式一格一格驅動網站自己的引擎，畫面直接是原生 1080×1920。
2. **確定性。** 時間、亂數、引擎時鐘全部由腳本控制，任何一格都能單獨重算；壞了哪一段就只重算那一段。
3. **音樂決定分鏡。** 先把歌拆成段落和大鼓時間，再排畫面，不是剪完再去對拍。

## When to use

- 使用者要用自己做的網站或互動工具做作品短片、宣傳片、IG Reel
- 要求畫面跟指定音樂的節拍、drop 對齊
- 要再做一支 Thermal Tracking Reel，或延續這套做法到別的網站

使用者通常會說「自主完成，不要逐步問我」。照做：**只有拿不到指定音樂時停下來問**，其餘創意決策自己做，做完一次交代。

## Inputs

| 項目 | 處理方式 |
| --- | --- |
| 網站原始碼 | 雲端常擋 `*.github.io`，但 `github.com` 可以 clone |
| 指定音樂 | YouTube 在雲端和使用者 VM 都連不到。直接請使用者把音檔放進 Downloads，**不准換歌**。等音檔的同時先做環境與引擎 |
| 素材資料夾 | 用 `device_request_folder_access` 一次要齊。先做縮圖總表看內容；別人的作品、含私人通知的螢幕錄影、轉向錯誤的翻拍都不要用。跟任務無關的資料夾不要碰 |
| 規格 | 預設 9:16、1080×1920、60 fps、20–30 秒、極少文字、片尾「Made with ＋ 網址」 |

## Usage

### 1. 環境

```bash
mkdir -p ~/reel/project && cd ~/reel/project && npm init -y
npm i three@<網站用的版本> @fontsource/ibm-plex-mono @fontsource/unbounded   # CDN 與 Google Fonts 會被擋
pip install librosa --break-system-packages
```

速度關鍵是繪圖後端。雲端 Linux 用 headless 只會拿到 SwiftShader，約 1.6 秒一格。改用 Xvfb 加 Mesa llvmpipe 約 0.55 秒一格，快三倍：

```bash
GALLIUM_DRIVER=llvmpipe xvfb-run -a -s "-screen 0 1280x1024x24" python3 scripts/render.py --root ~/reel/project ...
```

`render.py` 啟動時會印出 renderer，要看到 `llvmpipe` 才對。在有 GPU 的 Mac 上執行時不需要 Xvfb。

### 2. 拆網站引擎

先讀完主程式，找出 render loop、時間變數、參數物件和素材物件，再在網站副本加上 `window.__HARNESS` 掛鉤。正式網站不會設這個旗標，所以不受影響。完整補丁、注入碼和套風格時的陷阱都在 [references/engine-hook.md](references/engine-hook.md)。

### 3. 音樂分析

```bash
python3 scripts/analyze_audio.py track.mp3 --out harness/audio.json --frames <總格數> [--grid 2.502:0.765:8]
```

- librosa 的 beat tracker 常把 156 BPM 抓成一半的 78。腳本會同時印出用低頻 onset 擬合的拍長，以那個為準。
- 偵測到的「大鼓」裡也會混進切分音和 bass。對照擬合出的拍格手動清掉不在拍上的，缺的用 `--add-kicks`、`--grid` 補。
- 段落請看腳本印出的 0.5 秒能量表自己判斷：低頻突然消失是 break 或 build，低頻暴增是 drop。
- 分析和最後混音都用 ffmpeg 解碼，MP3 的編碼延遲才會一致。

### 4. 導演檔

所有創意決策集中在 `harness/director.js`，之後改片只改這個檔。完整範例見 [references/director.example.js](references/director.example.js)，結構如下：

```js
const SHOTS = [
  { id: 'S01', name: 'EMERGE', f0: 0, src: f0 => demoSrc(f0, { tOff: 1.2 }), clear: true,
    look: L('sonar', { decay: .965 }),              // 網站的 mood ＋ 覆寫參數
    auto(b) { P.glow = b.glow + .5 * G.kick; },      // 每格跟音樂動
    pre(src, f0) { /* 3D 鏡頭運動 */ },
    post: () => ({ black: 1 - easeOut(G.f / 40) }) },
];
```

- 切點放在大鼓前 1 格：`round(t × 60) - 1`。
- `clear: false` 不清拖尾，讓上一個鏡頭的殘影拖進下一個。這是這類工具最好看的轉場，大部分切點都用它。
- 後製是一張獨立的 WebGL2 canvas，參數有 `punch`、`rgb`、`flash`、`glitch`、`black`、`heat`、`vig`，上面再疊一張 2D 文字層。shader 取樣時不翻 y，`readPixels` 就會是由上而下的順序，可以直接餵給 ffmpeg。
- 擷取畫面不要用 `toDataURL`。用 `readPixels` 取 RGBA，POST 給同源伺服器再寫進 ffmpeg。`render.py` 已經實作好，director 只要提供 `__DIR.frame(f)` 和 `__DIR.send(f, path)`。

### 5. 素材準備

這類工具把亮度當溫度，素材的亮度分布決定成敗。

```bash
python3 scripts/prep_still.py dark_photo.png dark_photo_hot.png --lo 0.03 --hi 0.62 --gamma 0.9
```

- 太暗的圖在熱感裡會整片黑，先做 CLAHE 加色階，中位亮度拉到 0.3–0.45。
- 有煙霧、光柱的現場照背景會整片燙、主體反而冷。裁切避開亮部，或用 canvas 的 `brightness(.85)` 壓下來。
- 靜態圖要做成 canvas 素材，每格依鏡頭函式推鏡，大鼓時加震動，拖尾才有東西可以拉。
- 3D 模型改成原生 1080×1920 渲染。打光太亮的模型把 `toneMappingExposure` 降到 0.55–0.75；長條形的模型用 bbox 算出軸向，讓鏡頭沿著機身移動。
- 素材不夠動就自己寫一個 three.js 場景，例如這次為 build-up 寫了光環隧道。

### 6. 預覽，然後全片渲染

```bash
# 每個鏡頭中段各取一格，preroll 讓拖尾長出來
python3 scripts/render.py --root ~/reel/project --stills 60,125,215,... --preroll 20 --outdir previews/v1
# 全片
python3 scripts/render.py --root ~/reel/project --video ~/reel/out/master.mp4 --png-every 60
```

- 預覽格拼成縮圖總表後，要**真的用 Read 打開看**：主體看得出來嗎？有沒有整片過曝或全黑？構圖有沒有偏？字有沒有落在安全區？
- 全片 1443 格在 2 vCPU 上約 27 分鐘。用 `setsid nohup ... < /dev/null & disown` 背景執行，每次輪詢的 `sleep` 不超過 115 秒，因為工具逾時會殺掉整個 process group。
- 只有一段要修時不用重跑。從一個 `clear: true` 的鏡頭開始，用 `--from A --to B --preroll 0` 重算那一段，再拼回母帶：

```bash
ffmpeg -i master.mp4 -i seg.mp4 -filter_complex \
 "[0:v]trim=start_frame=0:end_frame=A,setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];\
  [0:v]trim=start_frame=B:end_frame=N,setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0[v]" \
 -map "[v]" -r 60 -c:v libx264 -preset veryfast -crf 8 -pix_fmt yuv420p master_v2.mp4
```

### 7. 輸出與專案檔

```bash
FRAMES=1443 CRF=20 scripts/finalize.sh master.mp4 track.mp3 deliver/ ThermalReel
python3 scripts/make_fcpxml.py --director harness/director.js --frames 1443 \
  "/Users/<me>/Downloads/<資料夾>/ThermalReel_noMusic_1080x1920_60fps.mp4" "/Users/<me>/Downloads/track.mp3" timeline.fcpxml
```

- 熱感的顆粒很吃位元率：CRF 20 大約 17 Mbps，24 秒約 50 MB。
- 專案打包內容：網站副本（含掛鉤與模型）、`harness/`（導演檔、`audio.json`、字體、處理過的素材、音檔）、這裡的腳本、中文 README（分鏡表與「怎麼改」）、分鏡總表圖。`node_modules` 只要放 three 的 `build/three.module.js`、`GLTFLoader.js`、`BufferGeometryUtils.js`。
- FCPXML 1.10 時間軸每個鏡頭一段，音樂掛成連接音訊，Final Cut 10.6 以上和 Resolve 18 以上都能匯入。

### 8. 驗收（不准跳過）

```bash
python3 scripts/verify_reel.py master.mp4 --director harness/director.js \
  --audio-ref mono.wav --final deliver/ThermalReel_IG_1080x1920_60fps.mp4
```

- [ ] 規格正確：1080×1920、60/1、幀數符合、H.264 High@4.2、AAC 48 kHz、`start_time = 0`
- [ ] 每個預定切點的畫面差異都遠高於中位數。被標成 weak 的切點要逐格看，確認是刻意的 match cut 或殘影轉場
- [ ] 音軌偏移 0 ms
- [ ] 用成品重新抽格做分鏡總表，每個鏡頭一格，全部看過一次
- [ ] 片尾字卡在 Reels 安全區：y 約 250–1500，避開右側按鈕欄。主頁格子會裁成 3:4 置中，標題要落在 y 240–1680 之內

### 9. 交付到使用者電腦（Cowork 遠端裝置）

- `device_commit_files` 每個檔上限 30 MB，大檔要先切再接：

```bash
split -b 26000000 -d -a 2 IG.mp4 /mnt/user-data/outputs/.parts/IG.part     # 雲端
# commit 到 ~/Downloads/<交付資料夾>/.parts/ 之後，在使用者 VM 上：
cat .parts/IG.part00 .parts/IG.part01 > IG.mp4 && truncate -s 0 .parts/IG.part0*
```

- 使用者 VM 不能 `rm`，`.parts` 裡會留下 0 byte 的檔案，要告訴使用者自己刪。
- 傳輸橋接會在 MP4 和 PNG 的檔頭插入約 5.8 KB 的 `uuid` 中繼資料，所以整個檔案的 md5 一定對不上。改成兩邊都跑 `ffmpeg -v error -i f -map 0:v -c copy -f md5 -`（音訊同理）比對封包，一致就代表影音資料逐位元相同。
- 對話裡的 SendUserFile 上限也是 30 MB，另外壓一支 720p 預覽版（CRF 25，約 13 MB）放進對話。

## Outputs

1. `<名稱>_IG_1080x1920_60fps.mp4`（含音樂）
2. `<名稱>_noMusic_1080x1920_60fps.mp4`
3. `<名稱>_project.zip`（可重新渲染的專案、FCPXML 時間軸、README）
4. `<名稱>_storyboard.png`
5. 對話裡的 720p 預覽

最後回報的結構：一段結論、交付表、段落與音樂的對位表、素材怎麼取捨，以及自己挑出的弱點與注意事項。弱點要誠實講，例如哪幾個鏡頭主體看不清楚、哪一段可以只重算來改。

## 可以沿用的分鏡骨架

| 段落 | 做法 |
| --- | --- |
| INTRO | 工具的招牌素材從全黑浮現；低頻空掉的那段換一個「掃描」效果 |
| GROOVE | 一小節一個鏡頭，每個鏡頭換素材和心情；最後半小節預告 drop 的主角 |
| BREAKDOWN | 液化類的心情，bass 打點時觸發小爆點 |
| BUILD | 切點從每拍一刀加速到每 6 格一刀，拖尾不清空；最後幾格過熱成白，再接 3 格全黑 |
| DROP | 第 1 格閃白；主角兩個角度（貼近掃描、全景），每記大鼓 punch 加 glow；中段每拍換一組心情，把工具的隨機功能（例如 ROLL）變成剪輯節奏 |
| END | 回到招牌素材；標題用工具自己的視覺語言框起來（例如追蹤框加「SECTION 00」），網址用打字效果出現，最後一記大鼓後切黑 |

## Notes

| 地雷 | 解法 |
| --- | --- |
| `pkill -f <pattern>` 的 pattern 也出現在自己的指令列裡 | 會把自己的 shell 一起殺掉（exit 144）。先用 `pgrep` 拿 PID，再 `kill <PID>` |
| `cd` 之後 `rm -f *` | 會被安全檢查擋下。新資料夾本來就是空的，或寫完整路徑 |
| 工具逾時殺掉背景渲染 | 一律 `setsid nohup ... & disown`，輪詢間隔小於 120 秒 |
| 換鏡頭時拖尾不見 | 某個函式裡藏了 `clearTrails`，見 [references/engine-hook.md](references/engine-hook.md) |
| 3D 主體整片白、看不出形狀 | 降 `toneMappingExposure`、降 glow、提高 gamma |
| 黑色材質那一面在熱感裡變透明 | 用 `tOff` 調自轉相位讓亮面對鏡頭，或讓鏡頭停在亮的那一段 |
| 字卡被 IG 介面蓋住 | 守住第 8 步的安全區 |

發文時：caption 裡的網址點不了，網址放主頁 bio，內文寫「link in bio」。音樂署名常常是從檔名或標籤推出來的，發之前請使用者確認藝人名稱；IG 如果因為版權把聲音靜音，改傳無配樂版，再從 IG 音樂庫加同一首。素材如果是 AI 生成的逼真照片，提醒使用者考慮打開「AI 標籤」。發在 seven_dept 帳號時，文案語氣照 `seventh-dept-post` 技能。
