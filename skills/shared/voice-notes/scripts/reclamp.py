#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修正既有逐字稿過長的 word 跨度，重新輸出 TXT/SRT/VTT/JSON。

這是時間長度限制，不是重新辨識或精確重對齊；不據此推斷講者身分。
來源優先使用 _asr_original/。預設寫到 _reclamped/；--report 只顯示統計。
--in-place 會先備份到 _before_reclamp/，再覆蓋四種格式並移除舊 speaker_id。

用法：reclamp.py --session <逐字稿資料夾> [--report | --in-place]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from fusion import Word, build_segments, render_srt, render_txt, render_vtt

MAX_WORD_SECONDS = 2.0   # 與 transcribe.py 同值


def log(message: str) -> None:
    print(message, flush=True)


def transcript_jsons(session: Path, *, pristine: bool = True) -> list[tuple[Path, Path]]:
    """回傳 [(讀取來源, 對應的現行檔), …]。來源優先用 _asr_original/。"""
    out = []
    for current in sorted(session.glob("*.json")):
        if current.name.endswith((".capture.json", ".addressed.json",
                                  ".speaker_id.json", ".content_id.json")):
            continue
        backup = session / "_asr_original" / current.name
        out.append((backup if pristine and backup.is_file() else current, current))
    return out


def clamp_words(raw_words: list[dict]) -> tuple[list[Word], int, float]:
    """回傳(夾過的 Word 串, 夾了幾個, 夾掉多少秒)。"""
    words, clamped, saved = [], 0, 0.0
    for item in raw_words:
        start, end = float(item["start"]), float(item["end"])
        end = max(start, end)
        if end - start > MAX_WORD_SECONDS:
            saved += end - start - MAX_WORD_SECONDS
            end = start + MAX_WORD_SECONDS
            clamped += 1
        words.append(Word(text=item["text"], start=start, end=end,
                          speaker=item.get("speaker", "UNKNOWN"),
                          display_speaker=item.get("display_speaker", "UNKNOWN"),
                          overlap=bool(item.get("overlap")),
                          assignment=item.get("assignment", "unknown")))
    return words, clamped, saved


def degenerate_segments(segments) -> tuple[int, float]:
    """≥10 秒但字數 ≤3 的片段——就是被靜音撐出來的那種。"""
    count, seconds = 0, 0.0
    for s in segments:
        duration = (s.end - s.start) if hasattr(s, "end") else (s["end"] - s["start"])
        text = (s.text if hasattr(s, "text") else s.get("text") or "").strip()
        if duration >= 10 and len(text) <= 3:
            count += 1
            seconds += duration
    return count, seconds


def rebuild(source: Path):
    data = json.loads(source.read_text(encoding="utf-8"))
    words, clamped, saved = clamp_words(data.get("words") or [])
    segments = build_segments(words)
    return data, words, segments, clamped, saved


def main() -> None:
    ap = argparse.ArgumentParser(description="夾住對齊器撐過靜音的 word 跨度並重新 fuse")
    ap.add_argument("--session", required=True)
    ap.add_argument("--in-place", action="store_true",
                    help="覆蓋現行檔(先備份到 _before_reclamp/);預設只寫 _reclamped/")
    ap.add_argument("--report", action="store_true", help="只印統計,不寫任何檔")
    args = ap.parse_args()

    session = Path(args.session)
    parts = transcript_jsons(session)
    if not parts:
        log("此場次沒有逐字稿 json"); sys.exit(1)

    for source, current in parts:
        data, words, segments, clamped, saved = rebuild(source)
        old_bad, old_secs = degenerate_segments(data.get("segments") or [])
        new_bad, new_secs = degenerate_segments(segments)
        log(f"{current.name}(來源 {'_asr_original' if source != current else '現行檔'})")
        log(f"  word 夾住 {clamped} 個,共收回 {saved / 60:.1f} 分鐘假時間")
        log(f"  ≥10 秒卻 ≤3 字的片段:{old_bad} 個 / {old_secs / 60:.1f} 分 "
            f"→ {new_bad} 個 / {new_secs / 60:.1f} 分")
        log(f"  片段數 {len(data.get('segments') or [])} → {len(segments)}")
        if args.report:
            continue
        payload = dict(data)
        payload["segments"] = [vars(s) for s in segments]
        payload["words"] = [vars(w) for w in words]
        payload.pop("speaker_id", None)     # 姓名要重跑 speaker_id 才算數
        meta = dict(payload.get("metadata") or {})
        meta["reclamped_word_spans"] = clamped
        meta["max_word_seconds"] = MAX_WORD_SECONDS
        payload["metadata"] = meta

        if args.in_place:
            before = session / "_before_reclamp"
            before.mkdir(exist_ok=True)
            for suffix in (".json", ".txt", ".srt", ".vtt"):
                live = current.with_suffix(suffix)
                if live.is_file() and not (before / live.name).exists():
                    shutil.copy2(live, before / live.name)
            out_dir, stem = session, current.stem
        else:
            out_dir = session / "_reclamped"
            out_dir.mkdir(exist_ok=True)
            stem = current.stem
        (out_dir / f"{stem}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        (out_dir / f"{stem}.txt").write_text(render_txt(segments), encoding="utf-8")
        (out_dir / f"{stem}.srt").write_text(render_srt(segments), encoding="utf-8")
        (out_dir / f"{stem}.vtt").write_text(render_vtt(segments), encoding="utf-8")
        log(f"  寫入 {out_dir}/{stem}.{{json,txt,srt,vtt}}")
    if not args.report and not args.in_place:
        log("這是預覽。確認後加 --in-place,然後重跑 speaker_id identify --apply 把姓名補回來。")


if __name__ == "__main__":
    main()
