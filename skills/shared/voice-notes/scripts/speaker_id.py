#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""聲紋註冊與命名閘門(點點禪膠囊・後置版)

在 voice-notes 轉錄完成後,把 diarization 的 Speaker A/B/C 對到真人姓名。
模型:sherpa-onnx CAM++ 中英語者驗證(192 維),與轉錄共用 venv。

用法(一律用 voice-notes venv 的 python 跑):
  speaker_id.py enroll   --session <場次資料夾> --map "Speaker A=Leo,Speaker B=孫佑侖"
  speaker_id.py identify --session <場次資料夾> [--apply]
  speaker_id.py profiles

決策規則(identify):
  cosine ≥ NAME_T 且領先第二名 ≥ MARGIN → 寫入姓名
  cosine < NONMEMBER_T                  → 疑似非成員(僅標記,由 ingest 決定隔離)
  其餘                                   → UNKNOWN,留原標籤待人工複核

硬規則(2026-08-03 加,起因:全日 8 場聲紋多對一塌陷):
  1. UNKNOWN 剩餘桶永不命名——它不是 cluster,是沒對到人的殘餘音訊。
  2. cluster 有效語音 < MIN_NAME_SECONDS 不命名。
  3. 一名一 cluster:同名衝突只留分數最高者,其餘降回 unknown 待人工。
  4. 熱詞回聲片段(覆蓋率判定,非 startswith)不入聲紋計算。
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
import sherpa_onnx

MODEL = Path.home() / "Library/Caches/local-speaker-transcriber/models/speaker-embedding/campplus_zh_en.onnx"
PROFILES = Path.home() / ("Library/Mobile Documents/com~apple~CloudDocs/Coding/Experiments/Claude/"
                          "點點禪膠囊/tools/voiceprints/profiles.json")
HOTWORDS = PROFILES.parent.parent / "asr_hotwords.txt"  # 膠囊 tools/asr_hotwords.txt
NAME_T = 0.45        # 命名門檻
MARGIN = 0.06        # 與第二名的最小差距
NONMEMBER_T = 0.25   # 低於此值 → 疑似非成員
MAX_SPK_SECONDS = 90 # 每位講者最多取用的語音量
MIN_SEG = 1.0        # 太短的片段不取
MIN_NAME_SECONDS = 10.0  # 桶內有效語音低於此秒數不命名(幾秒的底噪也能擠出 embedding,但不可信)

# 熱詞回聲片段不入聲紋:那些「文字」底下的音訊是靜音/底噪,拿去算 embedding
# 會產生「看起來很確定的錯誤歸屬」(2026-08-03 全日 8 場 UNKNOWN 被簽成真名)。
# startswith 擋不住無頭回聲,改用與 transcribe.py 同款的覆蓋率判定。
ECHO_HEADER_RE = re.compile(r"本[录錄]音可能包含以下[词詞][汇匯彙][::]?")
ECHO_STRIP_RE = re.compile(r"[\s、,,。..::;;!!??()()「」『』…-]+")
ECHO_COVERAGE = 0.85
ECHO_MIN_RUN = 6     # 片段級判定,比 transcribe.py 的 run 級門檻嚴一點

_echo_tokens_cache = None


def echo_tokens():
    global _echo_tokens_cache
    if _echo_tokens_cache is None:
        tokens = set()
        try:
            for ln in HOTWORDS.read_text(encoding="utf-8").splitlines():
                term = ln.strip()
                if term and not term.startswith("#"):
                    tokens.add(ECHO_STRIP_RE.sub("", term).lower())
        except OSError:
            pass
        _echo_tokens_cache = sorted((t for t in tokens if t), key=len, reverse=True)
    return _echo_tokens_cache


def is_pollution(text):
    """這段文字是熱詞回聲(而非真人講話)嗎?片段文字已是 zh-tw,直接比。"""
    if ECHO_HEADER_RE.search(text):
        return True
    folded = ECHO_STRIP_RE.sub("", text).lower()
    if len(folded) < ECHO_MIN_RUN:
        return False
    residual = folded
    for token in echo_tokens():
        residual = residual.replace(token, "")
    if 1.0 - len(residual) / len(folded) >= ECHO_COVERAGE:
        return True
    # fusion 切行會切在 token 中間(「團媽、…、馬」),殘片壓低覆蓋率。
    # 補一條頓號清單判定:≥5 節、中段全是完整 token、首尾是 token 或其斷片。
    parts = [ECHO_STRIP_RE.sub("", p).lower() for p in text.split("、")]
    parts = [p for p in parts if p]
    if len(parts) < 5:
        return False
    tokens = set(echo_tokens())
    if not all(p in tokens for p in parts[1:-1]):
        return False
    edge_ok = lambda p: p in tokens or any(
        t.startswith(p) or t.endswith(p) for t in tokens)
    return edge_ok(parts[0]) and edge_ok(parts[-1])


def log(msg):
    print(msg, flush=True)


def load_extractor():
    cfg = sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=str(MODEL), num_threads=4)
    return sherpa_onnx.SpeakerEmbeddingExtractor(cfg)


def to_wav16k(audio_path, tmpdir):
    out = Path(tmpdir) / "audio16k.wav"
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", "-c", "1",
                    str(audio_path), str(out)], check=True, capture_output=True)
    with wave.open(str(out), "rb") as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1
        samples = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return samples.astype(np.float32) / 32768.0


def session_parts(session):
    """回傳 [(json_path, audio_path), …];_asr_original 不算。"""
    parts = []
    for j in sorted(Path(session).glob("*.json")):
        if j.name.endswith(".capture.json") or "_asr_original" in str(j):
            continue
        audio = None
        for ext in (".m4a", ".wav", ".mp3", ".flac"):
            cand = j.with_suffix(ext)
            if cand.exists():
                audio = cand
                break
        if audio is None:
            m4as = [a for a in Path(session).glob("*.m4a")]
            audio = m4as[0] if len(m4as) == 1 else None
        if audio:
            parts.append((j, audio))
    return parts


def speaker_embedding(extractor, samples, segments):
    """給一位講者的片段列表,回傳(embedding, 使用秒數)。"""
    segs = [s for s in segments
            if not s.get("overlap")
            and (s["end"] - s["start"]) >= MIN_SEG
            and not is_pollution(s.get("text", ""))]
    segs.sort(key=lambda s: s["end"] - s["start"], reverse=True)
    embs, weights, used = [], [], 0.0
    for s in segs:
        if used >= MAX_SPK_SECONDS:
            break
        a, b = int(s["start"] * 16000), int(s["end"] * 16000)
        chunk = samples[a:b]
        if len(chunk) < 16000 * MIN_SEG:
            continue
        st = extractor.create_stream()
        st.accept_waveform(16000, chunk)
        st.input_finished()
        e = np.array(extractor.compute(st), dtype=np.float32)
        n = np.linalg.norm(e)
        if n == 0:
            continue
        embs.append(e / n)
        weights.append(s["end"] - s["start"])
        used += s["end"] - s["start"]
    if not embs:
        return None, 0.0
    m = np.average(np.stack(embs), axis=0, weights=weights)
    return m / np.linalg.norm(m), used


def collect_session_embeddings(session):
    """回傳 {speaker_label: (embedding, seconds)}(跨上/下多檔合併)。"""
    extractor = load_extractor()
    pooled = {}
    for jpath, apath in session_parts(session):
        data = json.loads(jpath.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as td:
            samples = to_wav16k(apath, td)
            by_spk = {}
            for s in data.get("segments", []):
                by_spk.setdefault(s.get("speaker", "?"), []).append(s)
            for spk, segs in by_spk.items():
                emb, secs = speaker_embedding(extractor, samples, segs)
                if emb is None:
                    continue
                if spk in pooled:
                    e0, s0 = pooled[spk]
                    m = (e0 * s0 + emb * secs) / (s0 + secs)
                    pooled[spk] = (m / np.linalg.norm(m), s0 + secs)
                else:
                    pooled[spk] = (emb, secs)
        log(f"  讀取 {jpath.name}(音檔 {apath.name})")
    return pooled


def load_profiles():
    if PROFILES.exists():
        raw = json.loads(PROFILES.read_text(encoding="utf-8"))
        return {k: {"embedding": np.array(v["embedding"], dtype=np.float32),
                    "seconds": v["seconds"], "sessions": v["sessions"]}
                for k, v in raw.items()}
    return {}


def save_profiles(profiles):
    PROFILES.parent.mkdir(parents=True, exist_ok=True)
    out = {k: {"embedding": [round(float(x), 6) for x in v["embedding"]],
               "seconds": round(v["seconds"], 1),
               "sessions": v["sessions"],
               "model": MODEL.name,
               "updated": datetime.now().isoformat(timespec="seconds")}
           for k, v in profiles.items()}
    PROFILES.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_enroll(args):
    mapping = {}
    for pair in args.map.split(","):
        label, name = pair.split("=", 1)
        mapping[label.strip()] = name.strip()
    pooled = collect_session_embeddings(args.session)
    profiles = load_profiles()
    session_name = Path(args.session).name
    for label, name in mapping.items():
        if label not in pooled:
            log(f"⚠ {label} 在此場次沒有足夠語音,跳過")
            continue
        emb, secs = pooled[label]
        if name in profiles:
            p = profiles[name]
            m = (p["embedding"] * p["seconds"] + emb * secs) / (p["seconds"] + secs)
            profiles[name] = {"embedding": m / np.linalg.norm(m),
                              "seconds": p["seconds"] + secs,
                              "sessions": sorted(set(p["sessions"] + [session_name]))}
        else:
            profiles[name] = {"embedding": emb, "seconds": secs, "sessions": [session_name]}
        log(f"✓ 註冊 {name} ← {label}({secs:.0f}s 語音)")
    save_profiles(profiles)
    log(f"聲紋檔:{PROFILES}")


def decide(scores):
    """scores: {name: cosine} → (decision, best_name, best, runnerup)"""
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    best_name, best = ranked[0]
    runner = ranked[1][1] if len(ranked) > 1 else -1.0
    if best >= NAME_T and (best - runner) >= MARGIN:
        return "named", best_name, best, runner
    if best < NONMEMBER_T:
        return "nonmember?", best_name, best, runner
    return "unknown", best_name, best, runner


def cmd_identify(args):
    profiles = load_profiles()
    if not profiles:
        log("沒有聲紋檔,先 enroll"); sys.exit(2)
    pooled = collect_session_embeddings(args.session)
    if not pooled:
        log("此場次沒有可用語音"); sys.exit(1)
    results = {}
    for label, (emb, secs) in sorted(pooled.items()):
        # 鐵律一:UNKNOWN 是 fusion 的剩餘桶(沒對到任何 cluster 的詞),不是講者。
        # 拿它的音訊(多半是底噪+洩漏段)命名,等於用猜的取代「不知道」。
        if label == "UNKNOWN":
            results[label] = {"decision": "skipped", "name": None,
                              "note": "UNKNOWN 是剩餘桶,不參與命名",
                              "seconds": round(secs, 1)}
            log(f"– UNKNOWN({secs:.0f}s)→ skipped(剩餘桶不命名)")
            continue
        scores = {n: float(np.dot(emb, p["embedding"])) for n, p in profiles.items()}
        decision, name, best, runner = decide(scores)
        # 鐵律二:語音量太少的 cluster 不命名——幾秒底噪也能擠出 embedding,但不可信。
        note = None
        if decision == "named" and secs < MIN_NAME_SECONDS:
            decision, note = "unknown", f"語音僅 {secs:.1f}s < {MIN_NAME_SECONDS:.0f}s,不命名"
        results[label] = {"decision": decision, "name": name if decision == "named" else None,
                          "best": round(best, 3), "runner_up": round(runner, 3),
                          "seconds": round(secs, 1), "note": note,
                          "scores": {k: round(v, 3) for k, v in scores.items()}}
        mark = {"named": "✓", "unknown": "?", "nonmember?": "✗"}[decision]
        log(f"{mark} {label}({secs:.0f}s)→ {name if decision=='named' else decision}"
            f"{'(' + note + ')' if note else ''}"
            f"  best={best:.3f} runner={runner:.3f}  {results[label]['scores']}")
    # 鐵律三:一名一 cluster。同名多 cluster 時只留 best 最高者(平手取語音量多者),
    # 其餘降回 unknown 待人工——過切分是存在的,但安全的失敗模式是 UNKNOWN,不是猜。
    by_name = {}
    for label, r in results.items():
        if r["decision"] == "named":
            by_name.setdefault(r["name"], []).append(label)
    for name, labels in by_name.items():
        if len(labels) < 2:
            continue
        labels.sort(key=lambda l: (results[l]["best"], results[l]["seconds"]), reverse=True)
        for loser in labels[1:]:
            results[loser]["decision"] = "unknown"
            results[loser]["note"] = f"同名衝突:{name} 已由 {labels[0]} 取得,降回待人工"
            results[loser]["name"] = None
            log(f"⚠ {loser} 與 {labels[0]} 同判 {name},{loser} 降回 unknown")
    if args.apply:
        apply_names(Path(args.session), results)
    return results


def apply_names(session, results):
    rename = {lab: r["name"] for lab, r in results.items() if r["decision"] == "named" and r["name"]}
    if not rename:
        log("沒有達到命名門檻的講者,不改任何檔案")
        return
    orig = session / "_asr_original"
    orig.mkdir(exist_ok=True)
    for f in sorted(session.iterdir()):
        if f.is_dir() or f.suffix.lower() in (".m4a", ".wav") or f.name.startswith("."):
            continue
        if f.name.endswith(".capture.json"):
            continue
        backup = orig / f.name
        if not backup.exists():
            shutil.copy2(f, backup)
        if f.suffix == ".json":
            data = json.loads(f.read_text(encoding="utf-8"))
            for s in data.get("segments", []):
                if s.get("speaker") in rename:
                    s["display_speaker"] = rename[s["speaker"]]
            for w in data.get("words", []):
                if isinstance(w, dict) and w.get("speaker") in rename:
                    w["display_speaker"] = rename[w["speaker"]]
            data["speaker_id"] = {
                "model": MODEL.name, "applied": datetime.now().isoformat(timespec="seconds"),
                "results": {k: {kk: vv for kk, vv in v.items() if kk != "scores"} | {"scores": v.get("scores", {})}
                            for k, v in results.items()},
            }
            text = json.dumps(data, ensure_ascii=False, indent=1)
            f.write_text(text, encoding="utf-8")
        else:
            text = f.read_text(encoding="utf-8")
            for lab, name in rename.items():
                text = text.replace(lab, name)
            f.write_text(text, encoding="utf-8")
    log(f"已套用姓名:{rename}(原版備份於 _asr_original/)")


def cmd_profiles(_args):
    profiles = load_profiles()
    if not profiles:
        log("(尚無聲紋檔)"); return
    for n, p in profiles.items():
        log(f"{n}: {p['seconds']:.0f}s 語音,來源 {p['sessions']}")


def main():
    ap = argparse.ArgumentParser(description="聲紋註冊與命名閘門")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("enroll"); e.add_argument("--session", required=True); e.add_argument("--map", required=True)
    i = sub.add_parser("identify"); i.add_argument("--session", required=True); i.add_argument("--apply", action="store_true")
    sub.add_parser("profiles")
    args = ap.parse_args()
    {"enroll": cmd_enroll, "identify": cmd_identify, "profiles": cmd_profiles}[args.cmd](args)


if __name__ == "__main__":
    main()
