# 拆網站引擎：掛鉤寫法

每個網站的結構都不一樣，所以這份不是通用程式，而是 Thermal Tracking 實際用過、可以照抄改名的做法。動手前先把主程式整個讀完，找出四樣東西：

| 要找的 | Thermal Tracking 裡叫什麼 |
| --- | --- |
| render loop | `loop(now)` → `render(true)` |
| 時間變數 | `T`（秒）、`frame` |
| 參數物件 | `P`（所有滑桿、開關、配色）與 `DEFAULTS` |
| 素材物件 | `src`（`kind: demo / image / video / model`） |

## 1. 複製網站並改成本機資源

```bash
git clone https://github.com/<user>/<repo>.git site     # *.github.io 常被雲端擋，github.com 可以 clone
mkdir -p project/engine && cp -r site/index.html site/models project/engine/
cd project && npm i three@0.160.0 @fontsource/ibm-plex-mono @fontsource/unbounded
```

## 2. 用一段 Python 打補丁（每一處都 assert，網站改版時會立刻失敗而不是默默壞掉）

```python
import re
p = 'engine/index.html'; s = open(p, encoding='utf-8').read()

# three.js 與字體改讀本機
s = s.replace('https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js', '/node_modules/three/build/three.module.js')
s = s.replace('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/', '/node_modules/three/examples/jsm/')
gf = re.search(r'<link rel="stylesheet" href="https://fonts.googleapis.com[^>]+>', s).group(0)
s = s.replace(gf, '<link rel="stylesheet" href="/harness/fonts.css">')

# 輸出長邊可注入：9:16 時注入 1920 → 原生 1080×1920
assert 'const L = 1080, m = Math.max(a, b);' in s
s = s.replace('const L = 1080, m = Math.max(a, b);', 'const L = window.__TT_L || 1080, m = Math.max(a, b);')

# 在啟動 rAF loop 之前插入掛鉤；正式網站不會設 __HARNESS，所以不受影響
tail = 'requestAnimationFrame(loop);\n})();\n</script>'
assert s.count(tail) == 1
hook = '''if (window.__HARNESS) {
  window.__TT = {
    P, DEFAULTS, MOODS, BASES, FX, PALETTES, stack, tracks, ctr, out, glc, gl, demo, thumbSt,
    applyValues, resetAll, applyPalette, setSize, clearTrails, addFx, clearFx, selectItem, live, setMood,
    loadThree, buildStage, stages, drawDemo, syncBg,
    get mr() { return mr; },
    get src() { return src; }, setSrc(s) { src = s; },
    setSourceFull: setSource,
    get T() { return T; }, set T(v) { T = v; },
    get W() { return W; }, get H() { return H; },
    step(dt) {
      T += dt; frame++; fps = 60;
      const lt = (src.t0 !== undefined ? (T - src.t0) * (src.speed || 1) + (src.tOff || 0) : T);
      if (src.kind === 'demo') drawDemo(lt);
      else if (src.kind === 'model') drawModel(lt);
      else if (src.draw) { src.draw(lt); src.dirty = true; }
      uploadSource(); render(true);
    },
    resetTracking() { tracks.length = 0; thumbSt.clear(); thumbIds = []; move = 0; }
  };
  return;
}
'''
s = s.replace(tail, hook + tail)
open(p, 'w', encoding='utf-8').write(s)
```

## 3. 頁面載入前注入

[`render.py`](../scripts/render.py) 會自動注入下面這段：

```js
window.__HARNESS = true; window.__TT_L = 1920; window.__vt = 0;
performance.now = () => window.__vt;          // 漸入漸出、計時器都改吃虛擬時鐘
let __s = 20261012; Math.random = () => { __s = (__s * 1664525 + 1013904223) >>> 0; return __s / 4294967296; };
```

## 4. 套風格時避開的陷阱

- 網站的 `resetAll()` 會順手 `clearTrails()`。換鏡頭要保留殘影時，直接把 `DEFAULTS ＋ mood ＋ 覆寫` 寫進 `P`，再呼叫 `applyPalette`。
- 換底色的 chip handler 也會清拖尾；不要透過 UI 點選，直接寫 `P.bg`。
- UI 的「移除效果」用真實時間的 `setTimeout`。改成直接操作 `stack` 陣列，`t0` 設成 `performance.now() - 1e7`，效果就是完全淡入的狀態。
- 網站內建的 3D 底座尺寸寫死在設定裡（例如 `BASES.starship.w/h`），要在 `buildStage` 之前改成 1080×1920，鏡頭才會照 9:16 重新取景。
