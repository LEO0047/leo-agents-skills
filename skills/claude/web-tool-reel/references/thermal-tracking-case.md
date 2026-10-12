# 案例：Thermal Tracking Reel（2026-10-12）

這是這個技能的第一次實作。導演檔全文在 [`director.example.js`](director.example.js)。

## Brief（Leo 的原始指令重點）

- 作品工具：leo0047.github.io/thermal-tracking
- 20–30 秒、9:16、1080×1920、60 fps
- 不是網站教學，而是「用網站真正製作出令人驚豔的視覺藝術短片」
- Experimental／Techno／Cyberpunk、極少文字、不需要旁白、不展示操作流程
- 最後簡短顯示「Made with Thermal Tracking」與網站連結
- 指定音樂拿不到就請他提供，不准換歌；其餘自主決定，不要逐步詢問
- 交付：可直接上傳 IG 的 MP4、無配樂版、可修改的專案檔

## 音樂

Best place（novah），24.06 秒。librosa 給 78.3 BPM，用低頻 onset 校正後是 **156.93 BPM**（拍長 0.38234 秒）。

| 段落 | 秒 | 特徵 |
| --- | --- | --- |
| INTRO | 0–2.50 | 1.5–2.4 秒低頻空掉 |
| GROOVE | 2.50–8.62 | 四小節，半拍大鼓，hi-hat 漸強 |
| BREAKDOWN | 8.62–11.68 | 只剩 bass 與氛圍 |
| BUILD | 11.68–14.75 | 沒有大鼓，小鼓滾奏加速 |
| DROP | 14.75–24.06 | 低頻能量是前段的 7 倍，六小節 |

drop 第一記大鼓在 14.78 秒，切點放在第 885 格（14.75 秒）。

## 分鏡（27 個鏡頭）

| 段落 | 格數 | 鏡頭 | 素材 × 心情 |
| --- | --- | --- | --- |
| INTRO | 0–91 | S01 EMERGE | 蝴蝶 × SONAR，從全黑浮現 |
| | 92–148 | S02 SCAN | 蝴蝶 × SPECIMEN，放大鏡左掃到右 |
| GROOVE | 149–240 | S03 SKIN | 刺青背影 × 鐵虹，推到蝴蝶刺青 |
| | 241–332 | S04 TOWER | 城塞 × NIGHT WATCH |
| | 333–424 | S05 BOOTH | DJ × GLITCH |
| | 425–469 | S06 GARAGE | 工坊 × CRT |
| | 470–515 | S07 TEASE | 星艦 × NEGATIVE |
| BREAKDOWN | 516–607 | S08 LIQUID CROWD | 舞池 × LAVA |
| | 608–699 | S09 DREAM | 刺青背影 × MELTDOWN |
| BUILD | 700–791 | S10 TUNNEL | 自製光環隧道 × SONAR |
| | 792–884 | S11a–h | 每拍到每 6 格換素材與心情，過熱成白，3 格黑 |
| DROP | 885–977 | D1 LIFTOFF | 星艦 × TYPHOON，沿船身從尾焰往上掃 |
| | 978–1069 | D1b ORBIT | 星艦全景（與 D1 同一條斜線，形成拉遠的 match cut） |
| | 1070–1160 | D2 BEACON | 城塞 × NEON BLOOM |
| | 1161–1252 | D3a–d ROLL | 每記大鼓換：GLITCH／NEWSPRINT／BLUEPRINT／CRT |
| | 1253–1298 | D4 SLAM | 星艦尾焰特寫 × 切片 |
| END | 1299–1442 | END | 蝴蝶 × SONAR ＋ 字卡 ＋ 網址打字 |

## 迭代紀錄（預覽格抓到的問題）

| 版本 | 問題 | 修法 |
| --- | --- | --- |
| v1 | 刺青背影整片黑（中位亮度 0.12） | CLAHE ＋ 色階 → 中位 0.35 |
| v1 | DJ 照片上半部煙霧整片燙，人反而冷 | 裁切往下移到人與混音台，`brightness(.9)` |
| v1 | LAVA 整片過曝 | `black .2`、`glow .8`、`gamma 1.6` |
| v1 | 片尾網址落在 IG 底部 UI 下 | 蝴蝶改用自訂 canvas 畫小、畫高，字卡整組上移到 y 1062–1500 |
| v1–v4 | 星艦只剩一條白棒 | 曝光降到 0.55–0.75，鏡頭改沿船身軸線移動 |
| full1 | D1 後半段船頭黑色隔熱瓦對著鏡頭，畫面變暗 | 拆成 D1（貼近掃描）＋ D1b（全景），只重算 885–1069 再拼回母帶 |

## 效能與交付數字

- Xvfb ＋ llvmpipe：約 0.55 秒／格；加上 x264 約 1.1 秒／格，全片約 27 分鐘（2 vCPU）
- 母帶 CRF 10 約 400 MB；IG 版 CRF 20 約 49 MB（17 Mbps）
- 所有預定切點的畫面差異都遠高於中位數；D1→D1b 是刻意的 match cut，差異較低屬於正常
- 成品音軌與分析音源互相關偏移 0 ms
- 交付到 Downloads：50 MB 檔案切成 26 MB 兩段傳輸再 `cat` 接回；橋接會在檔頭插入約 5.8 KB 的 `uuid` box，以封包 md5 驗證影音資料逐位元一致

## 文案（seven_dept）

英文極簡版：

```
A website that fakes a thermal camera: the brighter it is, the hotter it reads, and every heat source gets numbered and tracked.
Every frame of these 24 seconds was rendered by it.

Thermal Tracking | link in bio
Music: Best place — novah
Order after chaos.
```
