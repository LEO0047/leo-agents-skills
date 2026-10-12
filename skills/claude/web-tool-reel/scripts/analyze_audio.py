#!/usr/bin/env python3
"""Turn a music file into the timing data a beat-synced edit needs.

  python3 analyze_audio.py track.mp3 --out harness/audio.json [--fps 60] [--frames N]
         [--add-kicks 1.01,2.502] [--grid START:PERIOD:COUNT ...]

Prints a 0.5 s energy table (rms / low / mid / high) so you can mark sections by eye,
detects kick onsets in the 35–120 Hz band, estimates BPM from kick spacing (the
librosa beat tracker often reports HALF the real tempo — both are printed), fits a
least-squares beat grid on the steadiest run of kicks, and writes per-frame
envelopes the director reads: kick (tau 0.11 s), hit (all onsets, tau 0.07 s),
rms, low, hi.

Decode and final mux both go through ffmpeg so MP3 priming delay is identical;
verify_reel.py checks the final offset is 0 ms.
"""
import argparse, json, os, subprocess, sys, tempfile
import numpy as np
import librosa
import scipy.signal as ss


def decode(path, sr):
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-ac', '1', '-ar', str(sr), tmp], check=True)
    y, _ = librosa.load(tmp, sr=sr)
    os.unlink(tmp)
    return y


def env(times, t, tau, weights=None):
    e = np.zeros_like(t)
    for i, tk in enumerate(times):
        m = t >= tk - 1e-6
        w = 1.0 if weights is None else weights[i]
        e[m] = np.maximum(e[m], w * np.exp(-(t[m] - tk) / tau))
    return e


def steadiest_run(k, tol=0.06):
    """Longest run of kicks whose spacing stays within tol of the run's median spacing."""
    best = (0, 0)
    for i in range(len(k) - 2):
        j = i + 1
        while j + 1 < len(k):
            d = np.diff(k[i:j + 2]); med = np.median(d)
            if np.all(np.abs(d - med) <= tol * med):
                j += 1
            else:
                break
        if j - i > best[1] - best[0]:
            best = (i, j)
    return k[best[0]:best[1] + 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('audio')
    ap.add_argument('--out', default='audio.json')
    ap.add_argument('--fps', type=int, default=60)
    ap.add_argument('--frames', type=int, default=0, help='total frames (default: floor(duration * fps))')
    ap.add_argument('--sr', type=int, default=22050)
    ap.add_argument('--kick-height', type=float, default=0.35)
    ap.add_argument('--add-kicks', default='', help='comma-separated extra kick times (s)')
    ap.add_argument('--grid', action='append', default=[], help='START:PERIOD:COUNT extra kicks on a grid, e.g. 2.502:0.765:8')
    a = ap.parse_args()

    y = decode(a.audio, a.sr); sr = a.sr; dur = len(y) / sr
    hop = 128
    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=hop)); f = librosa.fft_frequencies(sr=sr, n_fft=1024)
    tt = np.arange(S.shape[1]) * hop / sr
    low = S[(f > 35) & (f < 120)].sum(0)
    d = np.maximum(0, np.diff(np.log1p(low), prepend=0))
    pk, _ = ss.find_peaks(d, height=a.kick_height, distance=int(0.18 * sr / hop))
    kicks = tt[pk]

    tempo_bt, _ = librosa.beat.beat_track(y=y, sr=sr, units='time')
    run = steadiest_run(kicks) if len(kicks) > 3 else kicks
    per = off = None
    if len(run) >= 4:
        n = np.round((run - run[0]) / np.median(np.diff(run)))
        (per, off), *_ = np.linalg.lstsq(np.vstack([n, np.ones_like(n)]).T, run, rcond=None)
    print(f'duration {dur:.3f}s   librosa beat_track {float(np.atleast_1d(tempo_bt)[0]):.2f} BPM (often half-time)')
    if per:
        print(f'kick grid on steadiest run ({len(run)} kicks, {run[0]:.3f}–{run[-1]:.3f}s): period {per:.5f}s = {60 / per:.2f} BPM, first {off:.3f}s')
    print('low-band kicks:', ' '.join(f'{x:.3f}' for x in kicks))

    # 0.5 s energy table for sectioning
    mid = S[(f > 150) & (f < 2000)].mean(0); hi = S[f > 4000].mean(0); lowm = S[(f > 30) & (f < 150)].mean(0)
    rms_fr = librosa.feature.rms(y=y, hop_length=hop, frame_length=1024)[0]
    print('\n  t(s)   rms    low     mid    high')
    for i in range(int(dur * 2)):
        m = (tt >= i * .5) & (tt < (i + 1) * .5)
        r = rms_fr[:len(tt)][m]
        print(f'{i * .5:6.1f}  {r.mean():.3f} {lowm[m].mean():7.2f} {mid[m].mean():6.2f} {hi[m].mean():6.3f}')

    extra = [float(x) for x in a.add_kicks.split(',') if x.strip()]
    for g in a.grid:
        s0, p, c = g.split(':'); extra += [float(s0) + i * float(p) for i in range(int(c))]
    allk = sorted(set(round(float(x), 3) for x in list(kicks) + extra))

    NF = a.frames or int(dur * a.fps)
    t = np.arange(NF) / a.fps
    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    ons = librosa.onset.onset_detect(onset_envelope=oenv, sr=sr, hop_length=hop, units='time')
    ostr = oenv[librosa.time_to_frames(ons, sr=sr, hop_length=hop)]; ostr = ostr / (ostr.max() or 1)
    lowf = np.convolve(np.interp(t, tt, low), np.ones(6) / 6, 'same'); lowf /= lowf.max() or 1
    rf = np.convolve(np.interp(t, tt, rms_fr[:len(tt)]), np.ones(6) / 6, 'same'); rf /= rf.max() or 1
    hif = np.convolve(np.interp(t, tt, S[f > 4000].sum(0)), np.ones(8) / 8, 'same'); hif = np.clip(hif / (np.percentile(hif, 99) or 1), 0, 1.5)
    out = {'fps': a.fps, 'frames': NF, 'duration': round(dur, 4),
           'bpm': round(60 / per, 2) if per else None, 'beat': round(float(per), 6) if per else None,
           'sections': {}, 'kicks': allk, 'onsets': [round(float(x), 3) for x in ons],
           'kick': np.round(env(allk, t, .11), 3).tolist(), 'hit': np.round(env(list(ons), t, .07, list(ostr)), 3).tolist(),
           'rms': np.round(rf, 3).tolist(), 'low': np.round(lowf, 3).tolist(), 'hi': np.round(hif, 3).tolist()}
    json.dump(out, open(a.out, 'w'))
    print(f'\nwrote {a.out}: {NF} frames, {len(allk)} kicks. Fill "sections" by hand from the table above.')


if __name__ == '__main__':
    main()
