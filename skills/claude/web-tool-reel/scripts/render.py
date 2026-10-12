#!/usr/bin/env python3
"""Drive a hooked web engine frame by frame and capture every frame losslessly.

The project directory (--root) is served over HTTP; the page (--page) must expose
window.__TT after the harness hook, and the director script (--director) must expose
window.__DIR = { frame(f), send(f, path), NF }.  See ../SKILL.md.

  # review frames (PNG), each with a short pre-roll so trails exist
  xvfb-run -a -s "-screen 0 1280x1024x24" python3 render.py --root ~/reel/project --stills 60,215,960
  # full render (video only, near-lossless master)
  xvfb-run -a -s "-screen 0 1280x1024x24" python3 render.py --root ~/reel/project --video master.mp4
  # re-render one segment that starts on a clear:true shot, then splice it into the master
  ... --video seg.mp4 --from 885 --to 1070 --preroll 0

On a Mac with a real GPU, drop xvfb-run; Chromium will use Metal/ANGLE directly.
"""
import argparse, http.server, os, subprocess, sys, threading, time
from functools import partial
from playwright.sync_api import sync_playwright

W, H, FPS = 1080, 1920, 60

INIT = """
window.__HARNESS = true; window.__TT_L = %(long_edge)d; window.__vt = 0;
performance.now = () => window.__vt;
let __s = %(seed)d; Math.random = () => { __s = (__s * 1664525 + 1013904223) >>> 0; return __s / 4294967296; };
"""


class Sink:
    """Receives raw RGBA frames POSTed by the page and pipes them to ffmpeg."""
    def __init__(self):
        self.ff = None; self.png_for = None; self.outdir = None; self.count = 0; self.err = None

    def handle(self, f, data):
        if len(data) != W * H * 4:
            self.err = f'bad frame size {len(data)} (expected {W * H * 4})'; return
        if self.ff:
            self.ff.stdin.write(data)
        if self.png_for is not None and f in self.png_for:
            from PIL import Image
            Image.frombytes('RGBA', (W, H), data).convert('RGB').save(os.path.join(self.outdir, f'f{f:04d}.png'))
        self.count += 1


SINK = Sink()


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(n)
        f = int(self.path.split('f=')[1]) if 'f=' in self.path else -1
        SINK.handle(f, data)
        self.send_response(200 if not SINK.err else 500)
        self.send_header('Content-Length', '0'); self.end_headers()


def main():
    global W, H, FPS
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.getcwd(), help='project directory served as /')
    ap.add_argument('--page', default='/engine/index.html')
    ap.add_argument('--director', default='/harness/director.js')
    ap.add_argument('--port', type=int, default=8130)
    ap.add_argument('--size', default='1080x1920')
    ap.add_argument('--fps', type=int, default=60)
    ap.add_argument('--seed', type=int, default=20261012)
    ap.add_argument('--stills', default='', help='comma-separated frame numbers to save as PNG')
    ap.add_argument('--preroll', type=int, default=30)
    ap.add_argument('--outdir', default='previews')
    ap.add_argument('--video', default='', help='output master video path')
    ap.add_argument('--crf', type=int, default=10)
    ap.add_argument('--from', dest='f0', type=int, default=0)
    ap.add_argument('--to', dest='f1', type=int, default=-1)
    ap.add_argument('--png-every', type=int, default=0)
    ap.add_argument('--headless', action='store_true', help='use headless (SwiftShader, ~3x slower than llvmpipe under Xvfb)')
    a = ap.parse_args()
    W, H = (int(x) for x in a.size.split('x')); FPS = a.fps
    root = os.path.abspath(os.path.expanduser(a.root))
    outdir = a.outdir if os.path.isabs(a.outdir) else os.path.join(root, a.outdir)

    srv = http.server.ThreadingHTTPServer(('127.0.0.1', a.port), partial(Handler, directory=root))
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    args = ['--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows', '--ignore-gpu-blocklist']
    if sys.platform.startswith('linux') and not a.headless:
        args += ['--use-angle=gl', '--use-gl=angle']   # Mesa llvmpipe through Xvfb
    with sync_playwright() as p:
        b = p.chromium.launch(headless=a.headless, args=args)
        pg = b.new_page(viewport={'width': 1200, 'height': 900})
        pg.on('pageerror', lambda e: print('PAGEERR', e, flush=True))
        pg.on('console', lambda m: m.type == 'error' and print('CONSOLE', m.text, flush=True))
        pg.add_init_script(INIT % {'long_edge': max(W, H), 'seed': a.seed})
        pg.goto(f'http://127.0.0.1:{a.port}{a.page}')
        pg.wait_for_function('window.__TT', timeout=60000)
        print('renderer:', pg.evaluate("(() => { const g = __TT.gl, e = g.getExtension('WEBGL_debug_renderer_info'); return e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : '?'; })()"), flush=True)
        pg.add_script_tag(url=a.director)
        pg.wait_for_function('window.__DIR || window.__DIR_ERR', timeout=180000)
        err = pg.evaluate('window.__DIR_ERR || null')
        if err:
            print('DIRECTOR ERROR', err); sys.exit(1)
        NF = pg.evaluate('__DIR.NF')
        f1 = NF if a.f1 < 0 else a.f1
        os.makedirs(outdir, exist_ok=True)
        SINK.outdir = outdir

        if a.stills:
            targets = sorted(int(x) for x in a.stills.split(','))
            SINK.png_for = set(targets)
            done, t0 = -10, time.time()
            for tf in targets:
                for f in range(max(0, tf - a.preroll, done + 1), tf + 1):
                    sid = pg.evaluate(f'__DIR.frame({f})')
                    if f == tf:
                        pg.evaluate(f'__DIR.send({f}, "/frame")')
                done = tf
                print(f'still {tf} [{sid}] {time.time() - t0:.1f}s', flush=True)
        else:
            if not a.video:
                print('need --video or --stills'); sys.exit(2)
            SINK.png_for = set(range(a.f0, f1, a.png_every)) if a.png_every else None
            SINK.ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS),
                                        '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', str(a.crf), '-pix_fmt', 'yuv420p',
                                        '-x264-params', f'keyint={FPS}', a.video], stdin=subprocess.PIPE)
            for f in range(max(0, a.f0 - a.preroll) if a.f0 > 0 else 0, a.f0):
                pg.evaluate(f'__DIR.frame({f})')
            t0 = time.time()
            for f in range(a.f0, f1):
                sid = pg.evaluate(f'(async () => {{ const s = await __DIR.frame({f}); await __DIR.send({f}, "/frame"); return s; }})()')
                if SINK.err:
                    print('ERR', SINK.err); break
                if f % 30 == 0:
                    el = time.time() - t0; n = f - a.f0 + 1
                    print(f'frame {f}/{f1} [{sid}] {el / n:.2f}s/f eta {el / n * (f1 - f):.0f}s', flush=True)
            SINK.ff.stdin.close(); SINK.ff.wait()
            print('frames written', SINK.count)
        b.close()
    srv.shutdown()


if __name__ == '__main__':
    main()
