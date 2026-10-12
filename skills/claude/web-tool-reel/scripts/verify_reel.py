#!/usr/bin/env python3
"""QA for a finished reel.

  python3 verify_reel.py master_or_final.mp4 --director harness/director.js [--audio-ref mono.wav --final IG.mp4]

1. ffprobe summary (size, fps, frame count, codecs).
2. Every planned cut (each `f0:` in the director's SHOTS) must show a frame difference
   far above the median — proves the cuts landed on the planned frames.
3. Optional: cross-correlate the final file's audio with the analysis reference;
   the offset must be 0 ms.
"""
import argparse, json, re, subprocess
import numpy as np


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-show_entries',
                          'stream=index,codec_name,profile,width,height,r_frame_rate,nb_read_frames,sample_rate,channels:format=duration,bit_rate',
                          '-of', 'json', path], capture_output=True, text=True).stdout
    return json.loads(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('--director', required=True)
    ap.add_argument('--audio-ref', default='')
    ap.add_argument('--final', default='', help='file whose audio track is checked (default: video)')
    a = ap.parse_args()

    info = probe(a.video)
    for s in info['streams']:
        print('stream', {k: s[k] for k in s if k != 'index'})
    print('format', info['format'])

    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', a.video, '-vf', 'scale=68:120,format=gray', '-f', 'rawvideo', '-'],
                         capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 120, 68).astype(float)
    d = np.abs(np.diff(fr, axis=0)).mean((1, 2)); med = np.median(d)
    cuts = sorted(set(int(x) for x in re.findall(r'f0:\s*(\d+)', open(a.director, encoding='utf-8').read())))[1:]
    weak = [c for c in cuts if c - 1 < len(d) and d[c - 1] < 4 * med]
    print(f'\nframes {len(fr)}  median diff {med:.1f}')
    print('cut:diff ' + ' '.join(f'{c}:{d[c - 1]:.0f}' for c in cuts if c - 1 < len(d)))
    print('WEAK CUTS (check visually, may be intended carry-over):', weak or 'none')

    if a.audio_ref:
        import scipy.io.wavfile as wav, scipy.signal as ss, tempfile, os
        tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a.final or a.video, '-map', '0:a', '-ac', '1', '-ar', '22050', tmp], check=True)
        _, x = wav.read(tmp); _, r = wav.read(a.audio_ref); os.unlink(tmp)
        x = x.astype(float)[:22050 * 10]; r = r.astype(float)[:22050 * 10]
        c = ss.correlate(x, r, mode='full', method='fft'); lag = c.argmax() - (len(r) - 1)
        print(f'\naudio offset vs reference: {lag} samples = {lag / 22.05:.2f} ms  ->', 'OK' if lag == 0 else 'MISALIGNED')


if __name__ == '__main__':
    main()
