#!/usr/bin/env python3
"""Make a still "heat-ready": thermal-style tools read brightness as temperature,
so a dark photo turns into a black frame and a hazy one into a white wall.

  python3 prep_still.py in.png out_hot.png [--clip 2.5] [--lo 0.03] [--hi 0.62] [--gamma 0.9]

CLAHE on the L channel (local contrast, keeps skin/tattoos/lights separable),
then a levels stretch. Prints luminance percentiles before/after so you can tune:
aim for a median around 0.3–0.45 with real highlights near 1.0.
"""
import argparse
import cv2
import numpy as np


def stats(img):
    l = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(float) / 255
    return ' '.join(f'p{p}={v:.2f}' for p, v in zip((5, 25, 50, 75, 95, 99), np.percentile(l, (5, 25, 50, 75, 95, 99))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--clip', type=float, default=2.5)
    ap.add_argument('--lo', type=float, default=0.03)
    ap.add_argument('--hi', type=float, default=0.62)
    ap.add_argument('--gamma', type=float, default=0.9)
    a = ap.parse_args()
    im = cv2.imread(a.src)
    print('before', stats(im))
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB)
    lab[:, :, 0] = cv2.createCLAHE(clipLimit=a.clip, tileGridSize=(8, 8)).apply(lab[:, :, 0])
    out = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR).astype(np.float32) / 255
    out = np.clip((out - a.lo) / (a.hi - a.lo), 0, 1) ** a.gamma
    out = (out * 255).astype(np.uint8)
    cv2.imwrite(a.dst, out)
    print('after ', stats(out))


if __name__ == '__main__':
    main()
