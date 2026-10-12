// =====================================================================
//  THERMAL TRACKING — REEL DIRECTOR
//  Drives the site's own WebGL engine (engine/index.html, exposed as
//  window.__TT) frame by frame at 60 fps, 1080×1920, synced to audio.json.
//  Edit SHOTS below to re-cut; run render.py to re-render.
// =====================================================================
(async () => {
'use strict';
const TT = window.__TT;
const A = await (await fetch('/harness/audio.json')).json();
const FPS = 60, NF = A.frames, W = 1080, H = 1920;
const P = TT.P, M = TT.MOODS;

await Promise.all([
  document.fonts.load('500 20px "IBM Plex Mono"'), document.fonts.load('400 20px "IBM Plex Mono"'),
  document.fonts.load('600 20px "IBM Plex Mono"'), document.fonts.load('600 40px "Unbounded"'),
  document.fonts.load('300 40px "Unbounded"'), document.fonts.load('800 40px "Unbounded"')
]);

P.aspect = '9:16'; TT.setSize();
if (TT.W !== W || TT.H !== H) throw new Error('engine size ' + TT.W + 'x' + TT.H);

// ---------------------------------------------------------------- utils
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, k) => a + (b - a) * k;
const ease = x => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const easeOut = x => 1 - Math.pow(1 - clamp(x), 3);
const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
const fr = t => Math.round(t * FPS);
const L = (mood, o = {}) => Object.assign({}, mood ? M[mood] : {}, o);
// pulse that fires at frame f0 and decays over n frames
const spike = (f, f0, n, p = 2) => (f < f0 || f >= f0 + n) ? 0 : Math.pow(1 - (f - f0) / n, p);

// ---------------------------------------------------------------- looks
const VK = ['palette', 'trailMode', 'centerMode', 'labelMode', 'bg', 'black', 'gamma', 'edge', 'grain', 'decay', 'zoom', 'amp', 'rays',
  'angle', 'speed', 'warp', 'glow', 'thr', 'minA', 'hold', 'on1', 'on2', 'on3', 'boxes', 'lines', 'thumbs', 'hud', 'pulse'];
function look(v, rampFx) {
  const full = {};
  for (const k of VK) full[k] = TT.DEFAULTS[k];
  Object.assign(full, v);
  if (!('edge' in v)) full.edge = TT.PALETTES[full.palette].edge;
  if (!('bg' in v)) full.bg = 'dark';
  for (const k of VK) P[k] = full[k];
  TT.applyPalette(full.palette);
  setFx(v.fx || [], rampFx);
}
function setFx(list, ramp) {
  const now = performance.now();
  TT.stack.length = 0;
  for (const [key, opt, ctrl] of list) {
    const f = TT.FX[key];
    TT.stack.push({ key, amt: opt && opt.amt != null ? opt.amt : f.amt, size: opt && opt.size != null ? opt.size : f.size,
      ctrl: { x: ctrl ? ctrl.x : .5, y: ctrl ? ctrl.y : .5 }, t0: ramp ? now : now - 1e7, dir: 1 });
  }
}
const fxItem = key => TT.stack.find(it => it.key === key);

// ---------------------------------------------------------------- sources
const loadImg = url => new Promise((ok, bad) => { const im = new Image(); im.onload = () => ok(im); im.onerror = bad; im.src = url; });
const IMG = { dj: await loadImg('/harness/dj_hot.png'), rave: await loadImg('/harness/rave_hot.png') };

// 3D bases from the site, rendered natively at 1080×1920
const BASE_TUNE = { starship: { zoom: 1.0 }, citadel: { zoom: .8, elev: .3 }, workshop: { zoom: .66, elev: .42 } };
for (const [k, o] of Object.entries(BASE_TUNE)) Object.assign(TT.BASES[k], { w: W, h: H }, o);
const STAGE = {};
for (const k of ['starship', 'citadel', 'workshop']) {
  STAGE[k] = await (TT.stages[k] = TT.buildStage(k));
  STAGE[k].cam0 = STAGE[k].cam.position.clone();
}
TT.mr.setSize(W, H, false);
const { T: THREE } = await TT.loadThree();

// custom stage: a light tunnel for the build-up (white = hot)
function buildTunnel() {
  const T = THREE, scene = new T.Scene(); scene.background = new T.Color(0);
  const cam = new T.PerspectiveCamera(64, W / H, .1, 600); cam.position.set(0, 0, 0); cam.lookAt(0, 0, -1);
  const spin = new T.Group(); scene.add(spin);
  const N = 40, gap = 7, Lz = N * gap, rings = [];
  for (let i = 0; i < N; i++) {
    const sq = i % 3 === 0, r = sq ? 4.6 : 3.3 + (i % 2) * .7;
    const geo = sq ? new T.RingGeometry(r - .09, r, 4, 1) : new T.RingGeometry(r - .055, r, 96, 1);
    const k = [1, .45, .8, .3, .65][i % 5];
    const mat = new T.MeshBasicMaterial({ color: new T.Color(k, k, k), side: T.DoubleSide, transparent: true });
    const m = new T.Mesh(geo, mat); m.userData = { z0: -i * gap, rot: (i % 2 ? 1 : -1) * (.2 + (i % 4) * .12), k };
    spin.add(m); rings.push(m);
  }
  // dashes along the walls
  const NS = 160, pos = new Float32Array(NS * 6), col = new Float32Array(NS * 6), st = [];
  for (let i = 0; i < NS; i++) {
    const a = hash(i * 3.1) * Math.PI * 2, r = 2.2 + hash(i * 7.7) * 3.2, k = .3 + .7 * hash(i * 1.3);
    st.push({ x: Math.cos(a) * r, y: Math.sin(a) * r, z0: -hash(i * 5.3) * Lz, len: 1 + 4 * hash(i * 9.1), k });
    col.set([k, k, k, k * .1, k * .1, k * .1], i * 6);
  }
  const g = new T.BufferGeometry();
  g.setAttribute('position', new T.BufferAttribute(pos, 3)); g.setAttribute('color', new T.BufferAttribute(col, 3));
  const dashes = new T.LineSegments(g, new T.LineBasicMaterial({ vertexColors: true, transparent: true, blending: T.AdditiveBlending }));
  dashes.frustumCulled = false; spin.add(dashes);
  // hot core at the vanishing point
  const cv = document.createElement('canvas'); cv.width = cv.height = 256;
  const cc = cv.getContext('2d'), gr = cc.createRadialGradient(128, 128, 0, 128, 128, 128);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(.18, 'rgba(255,255,255,.85)'); gr.addColorStop(.5, 'rgba(120,120,120,.25)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
  cc.fillStyle = gr; cc.fillRect(0, 0, 256, 256);
  const core = new T.Sprite(new T.SpriteMaterial({ map: new T.CanvasTexture(cv), blending: T.AdditiveBlending, transparent: true, depthWrite: false }));
  core.position.set(0, 0, -Lz * .9); core.scale.set(60, 60, 1); scene.add(core);
  const stage = { b: { spin: 0 }, scene, cam, spin, dist: 0, flick: 0, core };
  stage.update = t => {
    const d = stage.dist;
    for (const m of rings) {
      let z = ((m.userData.z0 + d) % Lz + Lz) % Lz - Lz; // [-Lz, 0)
      m.position.z = z; m.rotation.z = t * m.userData.rot;
      const near = clamp(-z / 10), far = 1 - clamp((-z - Lz * .55) / (Lz * .45));
      m.material.opacity = near * far * (1 - stage.flick * .6 * (m.userData.k < .5 ? 1 : 0));
    }
    for (let i = 0; i < NS; i++) {
      const s = st[i]; const z = ((s.z0 + d * 1.6) % Lz + Lz) % Lz - Lz;
      pos.set([s.x, s.y, z, s.x, s.y, z - s.len], i * 6);
    }
    g.attributes.position.needsUpdate = true;
    spin.rotation.z = Math.sin(t * .7) * .25 + t * .15;
    core.scale.setScalar(55 + stage.flick * 40);
  };
  return stage;
}
STAGE.tunnel = buildTunnel();
// starship: camera that travels along the hull (axis is tilted by the site's -0.3 rad)
const shipBox = new THREE.Box3().setFromObject(STAGE.starship.spin);
const shipHL = (shipBox.max.y - shipBox.min.y) / 2 / Math.cos(.3);
const SHIP_AX = new THREE.Vector3(Math.sin(.3), Math.cos(.3), 0);
function shipCam(stage, s, dist) {   // s ∈ [-.5, .5] from engines to nose; dist × the site's own camera distance
  const tgt = SHIP_AX.clone().multiplyScalar(2 * s * shipHL);
  stage.cam.position.copy(stage.cam0).multiplyScalar(dist).add(tgt); stage.cam.lookAt(tgt);
}

function modelSrc(key, f0, opt = {}) {
  return { kind: 'model', el: TT.mr.domElement, stage: STAGE[key], base: key, name: key, t0: f0 / FPS, speed: opt.speed || 1, tOff: opt.tOff || 0 };
}
function demoSrc(f0, opt = {}) {
  return { kind: 'demo', el: TT.demo, base: 'butterfly', name: 'butterfly', t0: f0 / FPS, speed: opt.speed || 1, tOff: opt.tOff || 0 };
}
// a still photo with a camera move: cam(lt) → { cx, cy, h (visible fraction of image height), rot, sx, sy }
function stillSrc(img, f0, cam, filter) {
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  const c = cv.getContext('2d');
  return { kind: 'image', el: cv, dirty: true, name: 'still', t0: f0 / FPS, speed: 1, tOff: 0,
    draw(lt) {
      const k = cam(lt), iw = img.naturalWidth, ih = img.naturalHeight, s = H / (k.h * ih);
      c.setTransform(1, 0, 0, 1, 0, 0); c.fillStyle = '#000'; c.fillRect(0, 0, W, H);
      c.filter = filter || 'none';
      c.translate(W / 2 + (k.sx || 0), H / 2 + (k.sy || 0)); c.rotate(k.rot || 0); c.scale(s, s);
      c.translate(-k.cx * iw, -k.cy * ih); c.drawImage(img, 0, 0);
      c.filter = 'none';
    } };
}

// ---------------------------------------------------------------- global clock
const G = { f: 0, t: 0, kick: 0, hit: 0, rms: 0, low: 0, hi: 0 };
const shakeXY = (amp, f) => [(hash(f * 1.7) - .5) * 2 * amp, (hash(f * 2.3 + 5) - .5) * 2 * amp];

// ---------------------------------------------------------------- post (separate WebGL2 canvas)
const post = document.createElement('canvas'); post.width = W; post.height = H;
const pg = post.getContext('webgl2', { antialias: false, alpha: false, preserveDrawingBuffer: true });
const VS = '#version 300 es\nlayout(location=0) in vec2 p;out vec2 uv;void main(){uv=p*.5+.5;gl_Position=vec4(p,0.,1.);}';
const FS = `#version 300 es
precision highp float;in vec2 uv;out vec4 o;
uniform sampler2D img,txt;uniform float punch,rgb,flash,black,glitch,inv,seed,txtA,heat,vig;uniform vec2 shake;
float h(float n){return fract(sin(n*91.7+seed*13.13)*43758.5453);}
void main(){
  vec2 p=uv; // p.y = 0 is the TOP of the frame (readPixels comes out top-down)
  if(glitch>0.){
    float band=floor(p.y*54.);float r=h(band);
    if(r<glitch*.7)p.x+=(h(band+7.)-.5)*glitch*.22;
    float big=floor(p.y*7.);if(h(big+31.)<glitch*.35)p.x+=(h(big+3.)-.5)*glitch*.08;
  }
  p=(p-.5)/punch+.5+shake;
  vec2 d=p-.5;
  vec3 c;
  c.r=texture(img,clamp(.5+d*(1.+rgb),0.,1.)).r;
  c.g=texture(img,clamp(p,0.,1.)).g;
  c.b=texture(img,clamp(.5+d*(1.-rgb),0.,1.)).b;
  c=mix(c,1.-c,inv);
  c=mix(c,vec3(1.,.97,.9),heat*smoothstep(.15,.9,dot(c,vec3(.3,.5,.2))));
  float v=smoothstep(1.2,.3,length((uv-.5)*vec2(.5625,1.))*1.35);c*=mix(1.,v,vig);
  vec4 t=texture(txt,uv);
  c=mix(c,t.rgb,t.a*txtA);
  c+=flash;
  c=mix(c,vec3(0.),black);
  o=vec4(c,1.);
}`;
function sh(type, src) { const s = pg.createShader(type); pg.shaderSource(s, src); pg.compileShader(s); if (!pg.getShaderParameter(s, pg.COMPILE_STATUS)) throw new Error(pg.getShaderInfoLog(s)); return s; }
const prog = pg.createProgram(); pg.attachShader(prog, sh(pg.VERTEX_SHADER, VS)); pg.attachShader(prog, sh(pg.FRAGMENT_SHADER, FS)); pg.linkProgram(prog);
const U = {}; for (const n of ['img', 'txt', 'punch', 'rgb', 'flash', 'black', 'glitch', 'inv', 'seed', 'txtA', 'heat', 'vig', 'shake']) U[n] = pg.getUniformLocation(prog, n);
const vao = pg.createVertexArray(); pg.bindVertexArray(vao);
pg.bindBuffer(pg.ARRAY_BUFFER, pg.createBuffer()); pg.bufferData(pg.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), pg.STATIC_DRAW);
pg.enableVertexAttribArray(0); pg.vertexAttribPointer(0, 2, pg.FLOAT, false, 0, 0);
function mkTex() { const t = pg.createTexture(); pg.bindTexture(pg.TEXTURE_2D, t);
  for (const [k, v] of [[pg.TEXTURE_MIN_FILTER, pg.LINEAR], [pg.TEXTURE_MAG_FILTER, pg.LINEAR], [pg.TEXTURE_WRAP_S, pg.CLAMP_TO_EDGE], [pg.TEXTURE_WRAP_T, pg.CLAMP_TO_EDGE]]) pg.texParameteri(pg.TEXTURE_2D, k, v);
  return t; }
const imgTex = mkTex(), txtTex = mkTex();
const txt = document.createElement('canvas'); txt.width = W; txt.height = H; const tc = txt.getContext('2d');
const pixels = new Uint8Array(W * H * 4);

function runPost(pp) {
  pg.viewport(0, 0, W, H); pg.useProgram(prog);
  pg.activeTexture(pg.TEXTURE0); pg.bindTexture(pg.TEXTURE_2D, imgTex);
  pg.texImage2D(pg.TEXTURE_2D, 0, pg.RGBA, pg.RGBA, pg.UNSIGNED_BYTE, TT.out); pg.uniform1i(U.img, 0);
  pg.activeTexture(pg.TEXTURE1); pg.bindTexture(pg.TEXTURE_2D, txtTex);
  if (pp.txtDirty) pg.texImage2D(pg.TEXTURE_2D, 0, pg.RGBA, pg.RGBA, pg.UNSIGNED_BYTE, txt);
  pg.uniform1i(U.txt, 1);
  pg.uniform1f(U.punch, pp.punch); pg.uniform1f(U.rgb, pp.rgb); pg.uniform1f(U.flash, pp.flash); pg.uniform1f(U.black, pp.black);
  pg.uniform1f(U.glitch, pp.glitch); pg.uniform1f(U.inv, pp.inv); pg.uniform1f(U.seed, pp.seed); pg.uniform1f(U.txtA, pp.txtA);
  pg.uniform1f(U.heat, pp.heat); pg.uniform1f(U.vig, pp.vig); pg.uniform2f(U.shake, pp.shake[0], pp.shake[1]);
  pg.drawArrays(pg.TRIANGLES, 0, 3);
  pg.readPixels(0, 0, W, H, pg.RGBA, pg.UNSIGNED_BYTE, pixels);
}

// ---------------------------------------------------------------- end card (drawn on the text layer)
const URL_TXT = 'leo0047.github.io/thermal-tracking';
function drawEndCard(f, f0) {
  const k = f - f0;                     // frames since the card started
  tc.setTransform(1, 0, 0, 1, 0, 0); tc.clearRect(0, 0, W, H);
  if (k < 0) return;
  const cx = W / 2;
  // layout (inside the Reels safe zone: nothing below y≈1500, nothing in the right-hand button column)
  const Y = { made: 1118, l1: 1250, l2: 1372, box0: 1062, box1: 1408, url: 1492 };
  const band = tc.createLinearGradient(0, 960, 0, 1620);
  band.addColorStop(0, 'rgba(0,0,0,0)'); band.addColorStop(.22, 'rgba(0,0,0,.6)'); band.addColorStop(.8, 'rgba(0,0,0,.6)'); band.addColorStop(1, 'rgba(0,0,0,0)');
  tc.globalAlpha = easeOut(k / 8); tc.fillStyle = band; tc.fillRect(0, 960, W, 660); tc.globalAlpha = 1;
  tc.textAlign = 'center'; tc.textBaseline = 'alphabetic';
  // MADE WITH
  const a1 = easeOut((k - 2) / 6);
  tc.font = '500 30px "IBM Plex Mono"'; tc.fillStyle = `rgba(242,244,248,${.85 * a1})`;
  spaced('MADE WITH', cx, Y.made, 9);
  // THERMAL / TRACKING — glitch-in: horizontal jitter that settles
  tc.font = '600 112px "Unbounded"';
  [['THERMAL', Y.l1], ['TRACKING', Y.l2]].forEach(([str, y], i) => {
    const kk = k - 3 - i * 3; if (kk < 0) return;
    const j = kk < 10 ? (1 - kk / 10) : 0;
    const dx = (hash(f * 3.1 + i) - .5) * 140 * j * j, a = clamp(kk / 3);
    if (j > 0) { // RGB ghosts while it settles
      tc.fillStyle = `rgba(255,61,143,${.7 * j})`; fitText(str, cx + dx - 10 * j, y, 840);
      tc.fillStyle = `rgba(92,225,255,${.7 * j})`; fitText(str, cx + dx + 10 * j, y, 840);
    }
    tc.fillStyle = `rgba(255,255,255,${a})`; fitText(str, cx + dx, y, 840);
  });
  // tracking box around the title, in the site's own label style
  const bk = easeOut((k - 1) / 7);
  if (bk > 0) {
    const sc = lerp(1.12, 1, bk), bw = 900 * sc, bh = (Y.box1 - Y.box0) * sc, bx = cx - bw / 2, by = (Y.box0 + Y.box1) / 2 - bh / 2;
    tc.lineWidth = 2; tc.strokeStyle = `rgba(242,244,248,${.9 * bk})`; tc.strokeRect(bx, by, bw, bh);
    tc.lineWidth = 5; const c = 26;
    for (const [x, y, sx, sy] of [[bx, by, 1, 1], [bx + bw, by, -1, 1], [bx, by + bh, 1, -1], [bx + bw, by + bh, -1, -1]]) {
      tc.beginPath(); tc.moveTo(x, y + sy * c); tc.lineTo(x, y); tc.lineTo(x + sx * c, y); tc.stroke();
    }
    tc.font = '500 22px "IBM Plex Mono"'; tc.textAlign = 'left';
    const lab = 'SECTION 00', lw = tc.measureText(lab).width;
    tc.fillStyle = `rgba(0,0,0,${.82 * bk})`; tc.fillRect(bx + 1, by + 1, lw + 20, 32);
    tc.fillStyle = `rgba(242,244,248,${bk})`; tc.fillText(lab, bx + 10, by + 24);
    tc.textAlign = 'center';
  }
  // URL types in like a terminal
  const n = clamp(Math.floor((k - 12) * 1.6), 0, URL_TXT.length);
  if (k >= 10) {
    tc.font = '400 36px "IBM Plex Mono"'; tc.textAlign = 'left';
    const full = tc.measureText(URL_TXT).width, x0 = cx - full / 2, y = Y.url;
    const s = URL_TXT.slice(0, n); tc.fillStyle = 'rgba(242,244,248,.95)'; tc.fillText(s, x0, y);
    const cw = tc.measureText(s).width;
    if (n < URL_TXT.length || Math.floor(k / 12) % 2 === 0) { tc.fillStyle = 'rgba(255,61,143,.95)'; tc.fillRect(x0 + cw + 4, y - 30, 18, 38); }
    tc.textAlign = 'center';
  }
}
// end-card base: the site's butterfly, drawn smaller and higher so the type has room
function endSrc(f0) {
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H; const c = cv.getContext('2d');
  return { kind: 'image', el: cv, dirty: true, name: 'butterfly', t0: f0 / FPS, speed: 1.2, tOff: 4,
    draw(lt) {
      TT.drawDemo(lt);
      const s = 1.3, dw = 720 * s, dh = 960 * s;
      c.setTransform(1, 0, 0, 1, 0, 0); c.fillStyle = '#000'; c.fillRect(0, 0, W, H);
      c.drawImage(TT.demo, (W - dw) / 2, 650 - 444 * s, dw, dh);
    } };
}
function spaced(s, cx, y, sp) {
  const w = [...s].reduce((a, ch) => a + tc.measureText(ch).width + sp, -sp);
  let x = cx - w / 2; tc.textAlign = 'left';
  for (const ch of s) { tc.fillText(ch, x, y); x += tc.measureText(ch).width + sp; }
  tc.textAlign = 'center';
}
function fitText(s, x, y, maxW) {
  const w = tc.measureText(s).width;
  if (w <= maxW) tc.fillText(s, x, y); else { tc.save(); tc.translate(x, y); tc.scale(maxW / w, 1); tc.fillText(s, 0, 0); tc.restore(); }
}

// ======================================================================
//  SHOTS — frame-accurate cut list (60 fps). Cuts sit 1 frame before the kick.
// ======================================================================
const DJ_WIDE = lt => ({ cx: .5, cy: .5, h: 1 });
const SHOTS = [
  // ---------------- INTRO 0.00–2.50 ----------------
  { id: 'S01', name: 'EMERGE', f0: 0, src: f0 => demoSrc(f0, { speed: 1, tOff: 1.2 }), clear: true,
    look: L('sonar', { decay: .965, zoom: .3, rays: .9, glow: .9, hold: 14 }),
    auto(b) { P.glow = b.glow + .5 * G.kick + .25 * G.hit; P.zoom = b.zoom + .25 * G.hit; },
    post: () => ({ black: 1 - easeOut(G.f / 40), vig: .3 }) },
  { id: 'S02', name: 'SCAN', f0: 92, src: 'keep', clear: false,
    look: L('spec', { decay: .8, glow: .35, hold: 20, fx: [['lens', { amt: .55, size: .32 }, { x: .2, y: .55 }]] }),
    auto(b, f0) { const it = fxItem('lens'); const k = (G.f - f0) / 57; if (it) { it.ctrl.x = lerp(.18, .82, ease(k)); it.ctrl.y = .52 + .06 * Math.sin(k * 5); } },
    post: () => ({ glitch: spike(G.f, 92, 4) * .5 }) },
  // ---------------- GROOVE 2.50–8.62 ----------------
  { id: 'S03', name: 'SKIN', f0: 149, clear: true,
    src: f0 => stillSrc(IMG.rave, f0, lt => {
      const k = ease(lt / 1.55), [sx, sy] = shakeXY(14 * G.kick, G.f);
      return { cx: lerp(.5, .37, k), cy: lerp(.56, .56, k), h: lerp(.82, .4, k), rot: lerp(-.02, .015, k), sx, sy };
    }),
    look: L('typhoon', { decay: .95, zoom: .32, amp: .45, rays: .25, glow: .85, pulse: false, grain: .45, thr: .5, minA: .25, hold: 8, fx: [] }),
    auto(b) { P.glow = b.glow + .45 * G.kick; P.zoom = b.zoom + .2 * G.kick; },
    post: () => ({ flash: .55 * spike(G.f, 149, 7), punch: 1 + .02 * G.kick }) },
  { id: 'S04', name: 'TOWER', f0: 241, clear: true, src: f0 => modelSrc('citadel', f0, { speed: 1.6, tOff: 2.0 }),
    look: L('watch', { decay: .94, glow: .75, hold: 10 }),
    pre(src, f0) { const lt = (G.f - f0) / FPS, c = src.stage.cam; c.position.copy(src.stage.cam0).multiplyScalar(lerp(.86, .72, ease(lt / 1.55))); c.lookAt(0, 0, 0); },
    auto(b) { P.glow = b.glow + .4 * G.kick; },
    post: () => ({ punch: 1 + .018 * G.kick, glitch: spike(G.f, 241, 3) * .4 }) },
  { id: 'S05', name: 'BOOTH', f0: 333, clear: true,
    src: f0 => stillSrc(IMG.dj, f0, lt => {
      const k = ease(lt / 1.55), [sx, sy] = shakeXY(18 * G.kick, G.f);
      return { cx: lerp(.44, .38, k), cy: lerp(.66, .62, k), h: lerp(.6, .42, k), rot: lerp(.02, -.01, k), sx, sy };
    }, 'brightness(.9) contrast(1.15)'),
    look: L('glitch', { decay: .88, glow: .5, gamma: 1.35, fx: [['slice', { amt: .32, size: .2 }, { x: .5, y: .5 }], ['pixel', { amt: .25, size: .14 }, { x: .8, y: .85 }]] }),
    auto(b) { const it = fxItem('slice'); if (it) it.amt = .25 + .35 * G.kick; P.glow = b.glow + .4 * G.kick; },
    post: () => ({ punch: 1 + .025 * G.kick, rgb: .004 * G.kick }) },
  { id: 'S06', name: 'GARAGE', f0: 425, clear: true, src: f0 => modelSrc('workshop', f0, { speed: 2.2, tOff: 4.0 }),
    look: L('tv', { decay: .9, speed: .55, glow: .55 }),
    pre(src, f0) { const lt = (G.f - f0) / FPS, c = src.stage.cam; c.position.copy(src.stage.cam0).multiplyScalar(lerp(.95, .82, ease(lt / .78))); c.lookAt(0, 0, 0); },
    auto(b) { P.glow = b.glow + .35 * G.kick + .3 * G.hi; },
    post: () => ({ punch: 1 + .02 * G.kick }) },
  { id: 'S07', name: 'TEASE', f0: 470, clear: true, src: f0 => modelSrc('starship', f0, { speed: 1, tOff: 3 }),
    look: L('neg', { grain: .35 }),
    post: () => ({ glitch: spike(G.f, 470, 4) * .6, punch: 1.04 - .04 * easeOut((G.f - 470) / 46) }) },
  // ---------------- BREAKDOWN 8.62–11.68 ----------------
  { id: 'S08', name: 'LIQUID CROWD', f0: 516, clear: true,
    src: f0 => stillSrc(IMG.dj, f0, lt => {
      const k = ease(lt / 1.55);
      return { cx: lerp(.6, .55, k), cy: lerp(.5, .44, k), h: lerp(.6, .7, k), rot: lerp(-.01, .01, k) };
    }, 'brightness(.85)'),
    look: L('lava', { decay: .972, glow: .8, black: .2, gamma: 1.6, fx: [['blobs', { amt: .8, size: .7 }], ['warp', { amt: .3, size: .9 }, { x: .5, y: .5 }]] }),
    auto(b) { P.glow = b.glow + .25 * G.low; },
    post: () => ({ flash: .35 * spike(G.f, 516, 8), vig: .25 }) },
  { id: 'S09', name: 'DREAM', f0: 608, clear: false,
    src: f0 => stillSrc(IMG.rave, f0, lt => {
      const k = ease(lt / 1.55);
      return { cx: lerp(.5, .47, k), cy: lerp(.36, .44, k), h: lerp(.55, .68, k), rot: lerp(.03, -.02, k) };
    }),
    look: L('melt', { decay: .965, glow: 1.0, fx: [['blobs', { amt: .75, size: .5 }], ['warp', { amt: .45, size: .7 }, { x: .5, y: .3 }], ['pixel', { amt: 0, size: .3 }, { x: .5, y: .55 }]] }),
    auto(b) { const it = fxItem('pixel'); if (it) it.amt = .55 * G.hit; P.glow = b.glow + .4 * G.hit; },
    post: () => ({ vig: .25 }) },
  // ---------------- BUILD 11.68–14.75 ----------------
  { id: 'S10', name: 'TUNNEL', f0: 700, clear: true, src: f0 => modelSrc('tunnel', f0),
    look: L('sonar', { decay: .95, zoom: .25, rays: .55, glow: .8, pulse: false, hold: 6, boxes: true, labelMode: 'section' }),
    pre(src, f0) { const lt = (G.f - f0) / FPS; src.stage.dist = 12 * lt + 6 * lt * lt; src.stage.flick = G.hit; },
    auto(b, f0) { const k = (G.f - f0) / 184; P.zoom = lerp(.22, .55, k) + .25 * G.hit; P.glow = b.glow + .5 * G.hit; },
    post: () => ({ flash: .3 * spike(G.f, 700, 6), punch: 1 + .015 * G.hit }) },
  { id: 'S11a', f0: 792, clear: false, src: f0 => modelSrc('tunnel', f0, { tOff: 2 }), look: L('neon', { fx: [], zoom: .6, decay: .955 }), build: true },
  { id: 'S11b', f0: 815, clear: false, src: f0 => modelSrc('citadel', f0, { speed: 3, tOff: 6 }), look: L('typhoon', { fx: [], zoom: .65 }), build: true },
  { id: 'S11c', f0: 838, clear: false, src: f0 => stillSrc(IMG.dj, f0, lt => ({ cx: .38, cy: .6, h: .42 - lt * .1 })), look: L('spec', { fx: [], decay: .9, trailMode: 'burst', zoom: .7 }), build: true },
  { id: 'S11d', f0: 850, clear: false, src: f0 => stillSrc(IMG.rave, f0, lt => ({ cx: .5, cy: .45, h: .5 - lt * .12 })), look: L('sonar', { zoom: .75, rays: .3 }), build: true },
  { id: 'S11e', f0: 861, clear: false, src: f0 => modelSrc('tunnel', f0, { tOff: 4 }), look: L('typhoon', { fx: [], zoom: .85 }), build: true },
  { id: 'S11f', f0: 867, clear: false, src: f0 => modelSrc('starship', f0, { tOff: 7 }), look: L('neon', { fx: [], zoom: .85 }), build: true },
  { id: 'S11g', f0: 873, clear: false, src: f0 => modelSrc('citadel', f0, { tOff: 9 }), look: L('spec', { fx: [], trailMode: 'burst', zoom: .9, decay: .95 }), build: true },
  { id: 'S11h', f0: 879, clear: false, src: f0 => modelSrc('tunnel', f0, { tOff: 5 }), look: L('typhoon', { fx: [], zoom: 1, gamma: .7, glow: 1.5 }), build: true },
  // ---------------- DROP 14.75–24.06 ----------------
  { id: 'D1', name: 'LIFTOFF', f0: 885, clear: true, src: f0 => modelSrc('starship', f0, { speed: 1.25, tOff: 8 }),
    look: L('typhoon', { decay: .955, zoom: .35, glow: .6, gamma: 1.5, pulse: false, fx: [['pixel', { amt: .3, size: .3 }, { x: .16, y: .62 }]] }),
    pre(src, f0) { TT.mr.toneMappingExposure = .62; const k = ease((G.f - f0) / 93); shipCam(src.stage, lerp(-.32, -.02, k), lerp(.44, .56, k) - .03 * G.kick); },
    auto(b) { P.glow = b.glow + .6 * G.kick; P.zoom = b.zoom + .4 * G.kick; const it = fxItem('pixel'); if (it) it.amt = .2 + .35 * G.kick; },
    post: () => ({ flash: spike(G.f, 885, 12, 1.5), punch: 1 + .035 * G.kick, rgb: .006 * G.kick, glitch: spike(G.f, 885, 6) * .5 }) },
  { id: 'D1b', name: 'ORBIT', f0: 978, clear: false, src: f0 => modelSrc('starship', f0, { speed: 1.25, tOff: 8.2 }),
    look: L('typhoon', { decay: .95, zoom: .3, glow: .55, gamma: 1.35, pulse: false, fx: [] }),
    pre(src, f0) { TT.mr.toneMappingExposure = .75; const k = ease((G.f - f0) / 92); shipCam(src.stage, .02, lerp(1.08, .9, k) - .04 * G.kick); },
    auto(b) { P.glow = b.glow + .6 * G.kick; P.zoom = b.zoom + .45 * G.kick; },
    post: () => ({ punch: 1 + .035 * G.kick, rgb: .006 * G.kick, glitch: spike(G.f, 978, 3) * .4 }) },
  { id: 'D2', name: 'BEACON', f0: 1070, clear: true, src: f0 => modelSrc('citadel', f0, { speed: 2.2, tOff: 11 }),
    look: L('neon', { decay: .96, glow: .85, zoom: .45, fx: [['lens', { amt: .5, size: .45 }, { x: .5, y: .5 }]] }),
    pre(src, f0) { const lt = (G.f - f0) / FPS, c = src.stage.cam; c.position.copy(src.stage.cam0).multiplyScalar(lerp(.8, .92, ease(lt / 1.55))); c.lookAt(0, 0, 0); },
    auto(b) { const it = fxItem('lens'); if (it) it.amt = .35 + .55 * G.kick; P.zoom = b.zoom + .3 * G.kick; P.glow = b.glow + .4 * G.kick; },
    post: () => ({ punch: 1 + .03 * G.kick, rgb: .005 * G.kick, glitch: spike(G.f, 1070, 3) * .5 }) },
  // roulette — one look per beat, like hitting ROLL on every kick
  { id: 'D3a', name: 'ROLL 1', f0: 1161, clear: false,
    src: f0 => stillSrc(IMG.dj, f0, lt => { const [sx, sy] = shakeXY(22 * G.kick, G.f); return { cx: .4, cy: .64, h: .48 - lt * .1, sx, sy }; }, 'brightness(.9)'),
    look: L('glitch', { decay: .9, fx: [['slice', { amt: .45, size: .25 }, { x: .5, y: .5 }]] }), roll: true },
  { id: 'D3b', name: 'ROLL 2', f0: 1184, clear: false,
    src: f0 => stillSrc(IMG.rave, f0, lt => { const [sx, sy] = shakeXY(22 * G.kick, G.f); return { cx: .45, cy: .52, h: .55 - lt * .12, sx, sy }; }),
    look: L('print', { decay: .85, fx: [['halftone', { amt: 1, size: .32 }]] }), roll: true },
  { id: 'D3c', name: 'ROLL 3', f0: 1207, clear: false, src: f0 => modelSrc('workshop', f0, { speed: 3, tOff: 8 }),
    look: L('blue', { fx: [['halftone', { amt: .5, size: .12 }]] }), roll: true },
  { id: 'D3d', name: 'ROLL 4', f0: 1230, clear: false, src: f0 => modelSrc('tunnel', f0, { tOff: 3 }),
    pre(src, f0) { const lt = (G.f - f0) / FPS; src.stage.dist = 80 + 40 * lt; src.stage.flick = G.kick; },
    look: L('tv', { decay: .9, glow: .8 }), roll: true },
  { id: 'D4', name: 'SLAM', f0: 1253, clear: false, src: f0 => modelSrc('starship', f0, { speed: 1.4, tOff: 5 }),
    look: L('typhoon', { decay: .955, zoom: .45, glow: .7, gamma: 1.5, pulse: false, fx: [['slice', { amt: .2, size: .3 }, { x: .5, y: .5 }]] }),
    pre(src, f0) { TT.mr.toneMappingExposure = .6; const k = (G.f - f0) / 46; shipCam(src.stage, lerp(-.36, -.26, k), lerp(.55, .45, k) - .04 * G.kick); },
    auto(b) { const it = fxItem('slice'); if (it) it.amt = .1 + .6 * G.kick; P.glow = b.glow + .6 * G.kick; P.zoom = b.zoom + .3 * G.kick; },
    post: () => ({ punch: 1 + .04 * G.kick, rgb: .008 * G.kick, flash: .4 * spike(G.f, 1253, 5) }) },
  // ---------------- END CARD 21.65–24.06 ----------------
  { id: 'END', name: 'MADE WITH', f0: 1299, clear: true, src: f0 => endSrc(f0),
    look: L('sonar', { decay: .96, zoom: .3, rays: .85, glow: .9, boxes: false, lines: true, thumbs: false, hud: true }),
    auto(b) { P.glow = b.glow + .5 * G.kick; P.zoom = b.zoom + .2 * G.kick; },
    text: true,
    post: () => ({ flash: .5 * spike(G.f, 1299, 6) + .35 * spike(G.f, 1437, 4), punch: 1 + .012 * G.kick, black: G.f >= 1440 ? 1 : 0, vig: .2 }) }
];
// build segment: accelerating cuts, overheating toward the drop
const BUILD_POST = () => {
  const k = clamp((G.f - 792) / 90);
  return { punch: 1 + .02 * G.hit + .03 * k, rgb: .002 + .01 * k * k, glitch: .08 + .5 * k * k * (hash(G.f) > .5 ? 1 : .3),
    heat: G.f >= 876 ? (G.f - 876) / 6 : 0, black: G.f >= 882 ? 1 : 0, flash: .25 * G.hit };
};
const ROLL_POST = sh => ({ punch: 1 + .03 * G.kick, rgb: .006 * G.kick, glitch: spike(G.f, sh.f0, 3) * .7, flash: .2 * spike(G.f, sh.f0, 3) });
SHOTS.forEach((s, i) => { s.f1 = i + 1 < SHOTS.length ? SHOTS[i + 1].f0 : NF; });

// ---------------------------------------------------------------- runtime
let cur = null, base = null;
function enter(sh) {
  const prev = cur; cur = sh;
  TT.mr.toneMappingExposure = 1.35;
  if (sh.src !== 'keep') TT.setSrc(sh.src(sh.f0));
  else if (prev) { /* same source keeps running */ }
  if (sh.clear) { TT.clearTrails(); TT.resetTracking(); }
  look(sh.look, !!sh.rampFx);
  base = {}; for (const k of VK) base[k] = P[k];
}
let lastTxt = -1;
async function frame(f) {
  G.f = f; G.t = f / FPS;
  G.kick = A.kick[f] || 0; G.hit = A.hit[f] || 0; G.rms = A.rms[f] || 0; G.low = A.low[f] || 0; G.hi = A.hi[f] || 0;
  const sh = SHOTS.find(s => f >= s.f0 && f < s.f1);
  if (sh !== cur) enter(sh);
  // reset per-frame automated values to the shot's base, then automate
  for (const k of VK) P[k] = base[k];
  if (sh.auto) sh.auto(base, sh.f0);
  if (sh.build) { P.glow = base.glow + .5 * G.hit; P.zoom = base.zoom + .2 * G.hit; }
  if (sh.roll) { P.glow = base.glow + .5 * G.kick; P.zoom = base.zoom + .25 * G.kick; }
  if (sh.pre) sh.pre(TT.src, sh.f0);
  window.__vt = f * 1000 / FPS;
  TT.T = f / FPS - 1 / FPS;   // engine clock = timeline clock (deterministic for any start frame)
  TT.step(1 / FPS);
  const pp = Object.assign({ punch: 1, rgb: 0, flash: 0, black: 0, glitch: 0, inv: 0, seed: f % 97, txtA: 0, heat: 0, vig: 0, shake: [0, 0], txtDirty: false },
    sh.build ? BUILD_POST() : sh.roll ? ROLL_POST(sh) : (sh.post ? sh.post() : {}));
  if (sh.text) { drawEndCard(f, sh.f0); pp.txtA = 1; pp.txtDirty = true; lastTxt = f; }
  runPost(pp);
  return sh.id;
}
async function send(f, path) {
  const r = await fetch(path + '?f=' + f, { method: 'POST', body: pixels });
  if (!r.ok) throw new Error('post ' + r.status);
}
window.__DIR = { frame, send, SHOTS, NF, ready: true, G, dbg: { STAGE, shipCam, TT, THREE } };
})().catch(e => { window.__DIR_ERR = String(e && e.stack || e); console.error(e); });
