#!/usr/bin/env python3
"""Run local Qwen ASR, alignment, SpeakerKit diarization, and fusion."""

from __future__ import annotations

import argparse
import gc
import json
import os
import re
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import wave

from setup_runtime import (
    RUNTIME_ROOT,
    SPEAKERKIT_BINARY,
    VENV_PYTHON,
    ensure_speakerkit,
    ensure_venv,
    write_stamp,
)


# bf16 over 8bit: proper-noun accuracy — 8bit kept mishearing rare domain terms
# (龍巖→龍眼) even with context biasing; full precision plus biasing got every
# known term right in the 2026-08-01 four-config comparison. ~3x slower, still
# well above realtime on M4.
ASR_REPO = "mlx-community/Qwen3-ASR-1.7B-bf16"
ASR_REVISION = "e1f6c266914abc5a46e8756e02580f834a6cf8a7"
ALIGNER_REPO = "mlx-community/Qwen3-ForcedAligner-0.6B-8bit"
ALIGNER_REVISION = "0e1a68e91d815300c7c9754b2a7639378b23db15"
DIARIZER_NAME = "SpeakerKit / Pyannote Community-1 Core ML"

SAMPLE_RATE = 16000

# The aligner cannot see a whole recording at once, and fails silently when asked
# to. It predicts each timestamp as one of `classify_num` (5000) classes worth
# `timestamp_segment_time` (80 ms) each, so no timestamp beyond 5000 * 80 ms =
# 400 s is representable; and its text model has 8192 position embeddings to hold
# ~13 audio tokens per second plus two timestamp tokens per word, which a
# ~370 s recording already exhausts. Past either limit the timestamps collapse
# onto a handful of values instead of erroring. So audio and transcript are cut
# into chunks that stay far inside both budgets: 120 s costs ~1560 audio tokens
# plus ~1100 timestamp tokens of the 8192, and lands under a third of 400 s.
ALIGN_CHUNK_SECONDS = 120.0

# Below this fraction of the audio covered by aligned words, treat the timeline
# as untrustworthy rather than shipping it silently.
MIN_TIMELINE_COVERAGE = 0.5


ICLOUD_DRIVE = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs"
NOTES_LIBRARY = ICLOUD_DRIVE / "Coding/Experiments/Claude/錄音"


def notes_library() -> Path:
    """The folder holding the note subfolders, with a fallback off iCloud."""
    if ICLOUD_DRIVE.is_dir():
        return NOTES_LIBRARY
    return Path.home() / "Documents/錄音"


def archive_source_audio(source: Path, output_dir: Path, stem: str) -> Path:
    """Put the recording in its note folder so the folder stands on its own.

    Moves when the recording already sits inside the notes library — leaving a
    duplicate in the same library is the mess this is meant to avoid. Copies
    when it came from outside, since the original often lives in a scratch
    folder the user still wants it in.
    """
    destination = output_dir / f"{stem}{source.suffix}"
    if destination.exists() and destination.samefile(source):
        return destination
    output_dir.mkdir(parents=True, exist_ok=True)
    if source.is_relative_to(notes_library()):
        shutil.move(str(source), str(destination))
    else:
        shutil.copy2(source, destination)
    return destination


def default_output_dir(source: Path, name: str | None = None) -> Path:
    """One dated folder per recording inside the notes library."""
    stamp = datetime.fromtimestamp(source.stat().st_mtime).strftime("%Y-%m-%d")
    return (notes_library() / f"{stamp} {name or source.stem}").resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe local audio with speaker labels."
    )
    parser.add_argument("audio", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Defaults to a dated folder under the iCloud Drive Voice Notes library.",
    )
    parser.add_argument(
        "--name",
        help="Descriptive name for the note folder and its files, in place of the recording's filename.",
    )
    parser.add_argument("--speakers", default="auto")
    parser.add_argument("--language", default="auto")
    parser.add_argument(
        "--asr-context",
        help="Domain vocabulary to bias recognition toward: proper nouns and terms "
        "separated by 、. Keep it to bare terms — descriptive sentences can pull "
        "the model toward hallucinating them.",
    )
    parser.add_argument(
        "--text-variant", choices=("preserve", "zh-tw"), default="zh-tw"
    )
    parser.add_argument("--speaker-map", type=Path)
    parser.add_argument(
        "--no-copy-audio",
        action="store_true",
        help="Leave the source recording where it is instead of copying it into the output folder.",
    )
    parser.add_argument("--runtime-ready", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args()


def bootstrap_and_reexec(args: argparse.Namespace) -> None:
    ensure_venv()
    ensure_speakerkit()
    write_stamp()
    command = [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]]
    command.append("--runtime-ready")
    os.execv(str(VENV_PYTHON), command)


def convert_audio(source: Path, target: Path) -> None:
    subprocess.run(
        [
            "/usr/bin/afconvert",
            str(source),
            str(target),
            "-f",
            "WAVE",
            "-d",
            "LEI16@16000",
            "-c",
            "1",
        ],
        check=True,
    )


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


def clear_mlx() -> None:
    gc.collect()
    try:
        import mlx.core as mx

        mx.clear_cache()
    except Exception:
        pass


def normalize_text(text: str, variant: str) -> str:
    if variant == "preserve":
        return text
    from opencc import OpenCC

    return OpenCC("s2twp").convert(text)


# ---------------------------------------------------------------------------
# Prompt-echo removal.
#
# On chunks with little or no speech, the ASR model regurgitates the
# --asr-context system prompt as if someone had read it aloud. Two things made
# the original exact-prefix filter miss every echo in practice:
#   1. the model echoes in its own orthography (简体 "词汇" / mixed "詞匯"),
#      while the filter compared the traditional prompt against the *raw*
#      output — normalization to zh-tw happens later, so the echo only looks
#      identical to the prompt after the filter has already let it through;
#   2. the model often starts mid-list ("禪、Dotdotzen、…") with no header at
#      all, which no prefix match can catch.
# So: match the header by character-variant regex on the raw text, and catch
# headerless echoes by hotword coverage — a run of text between punctuation
# marks that is ≥ ECHO_COVERAGE composed of context vocabulary is an echo, not
# speech. Real sentences keep their function words (的/是/我/你…), which the
# vocabulary cannot cover. Runs are split on sentence/comma punctuation but
# NOT on 、 — the echo is one long 、-separated run, while real speech around
# it is comma-separated, so real fragments in the same chunk survive.
ECHO_HEADER_RE = re.compile(r"本[录錄]音可能包含以下[词詞][汇匯彙][::]?")
ECHO_RUN_SPLIT_RE = re.compile(r"([。..!!??;;,,\n]+)")
ECHO_STRIP_RE = re.compile(r"[\s、,,。..::;;!!??()()「」『』…-]+")
ECHO_COVERAGE = 0.85  # 覆蓋率達此比例的 run 判為回聲
ECHO_MIN_RUN = 10     # 短 run 不判(單獨講一個專名是正常對話)


def echo_normalize(text: str) -> str:
    """回聲比對用的摺疊:去空白與標點、拉丁字母歸小寫、簡繁摺疊。"""
    text = ECHO_STRIP_RE.sub("", text).lower()
    if not text:
        return ""
    from opencc import OpenCC

    return OpenCC("s2twp").convert(text)


def build_echo_tokens(context: str | None) -> list[str]:
    if not context:
        return []
    tokens = {echo_normalize(term) for term in context.split("、")}
    return sorted((t for t in tokens if t), key=len, reverse=True)


def hotword_coverage(run: str, tokens: list[str]) -> float:
    """run(已摺疊)被詞彙表 token 覆蓋的字符比例。"""
    if not run:
        return 0.0
    residual = run
    for token in tokens:
        residual = residual.replace(token, "")
    return 1.0 - len(residual) / len(run)


def strip_prompt_echo(text: str, tokens: list[str]) -> str:
    """剔除 system_prompt 回聲:標頭(含簡繁變體)一律刪,無頭回聲靠覆蓋率抓。"""
    text = ECHO_HEADER_RE.sub("", text)
    if not tokens:
        return text.strip()
    parts = ECHO_RUN_SPLIT_RE.split(text)
    kept: list[str] = []
    for index in range(0, len(parts), 2):
        run = parts[index]
        delim = parts[index + 1] if index + 1 < len(parts) else ""
        folded = echo_normalize(run)
        if (
            len(folded) >= ECHO_MIN_RUN
            and hotword_coverage(folded, tokens) >= ECHO_COVERAGE
        ):
            continue  # 整個 run 是詞彙表回聲——丟棄,連同其後標點
        kept.append(run + delim)
    return "".join(kept).strip()


def load_display_map(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in data.items()
    ):
        raise ValueError("speaker map must be a JSON object of string labels to names")
    return data


def normalize_language(value: object, fallback: str = "Chinese") -> str:
    if isinstance(value, (list, tuple)):
        value = value[0] if value else fallback
    text = str(value or fallback).strip()
    return text or fallback


def plan_chunks(wav_path: Path) -> list[tuple["object", float]]:
    """Cut the audio at low-energy points into aligner-sized pieces.

    Each piece carries its own offset in seconds so word timings can be shifted
    back onto the full recording's timeline.
    """
    import numpy as np
    from mlx_audio.stt.models.qwen3_asr.qwen3_asr import split_audio_into_chunks
    from mlx_audio.stt.utils import load_audio

    waveform = np.asarray(load_audio(str(wav_path))).astype(np.float32).reshape(-1)
    return split_audio_into_chunks(
        waveform, SAMPLE_RATE, chunk_duration=ALIGN_CHUNK_SECONDS
    )


def run_pipeline(args: argparse.Namespace) -> dict[str, str]:
    from huggingface_hub import snapshot_download
    from mlx_audio.stt import load

    from fusion import (
        Word,
        assign_words,
        build_segments,
        canonicalize_speakers,
        parse_rttm,
        restore_transcript_formatting,
        smart_join,
        write_outputs,
    )

    source = args.audio.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else default_output_dir(source, args.name)
    )
    stem = args.name or source.stem
    speaker_count: int | None
    if str(args.speakers).lower() == "auto":
        speaker_count = None
    else:
        speaker_count = int(args.speakers)
        if speaker_count < 1:
            raise ValueError("--speakers must be auto or a positive integer")
    language_hint = None if args.language.lower() == "auto" else args.language
    display_map = load_display_map(args.speaker_map)
    warnings: list[str] = []
    temp_root = Path(tempfile.mkdtemp(prefix="local-speaker-transcriber-"))
    try:
        wav_path = temp_root / "audio.wav"
        rttm_path = temp_root / "speakers.rttm"
        print("[1/4] Converting audio to 16 kHz mono WAV", flush=True)
        convert_audio(source, wav_path)
        duration = wav_duration(wav_path)

        chunks = plan_chunks(wav_path)

        model_cache = RUNTIME_ROOT / "models"
        print("[2/4] Downloading/loading Qwen3-ASR 1.7B 8-bit", flush=True)
        asr_path = snapshot_download(
            repo_id=ASR_REPO,
            revision=ASR_REVISION,
            cache_dir=model_cache,
        )
        asr = load(asr_path)
        asr_kwargs: dict = {"language": language_hint}
        echo_tokens: list[str] = []
        sanitized_context = None
        if args.asr_context:
            # surrogateescape leftovers from a mis-encoded argv crash the tokenizer
            sanitized_context = args.asr_context.encode("utf-8", "replace").decode(
                "utf-8"
            )
            asr_kwargs["system_prompt"] = f"本錄音可能包含以下詞彙:{sanitized_context}"
            echo_tokens = build_echo_tokens(sanitized_context)
        chunk_texts: list[str] = []
        detected_language = language_hint or "Chinese"
        for index, (chunk_audio, offset) in enumerate(chunks, start=1):
            print(
                f"      transcribing chunk {index}/{len(chunks)} at {offset:.0f}s",
                flush=True,
            )
            asr_result = asr.generate(chunk_audio, **asr_kwargs)
            chunk_texts.append(
                strip_prompt_echo(str(asr_result.text).strip(), echo_tokens)
            )
            if index == 1:
                detected_language = normalize_language(
                    getattr(asr_result, "language", None),
                    language_hint or "Chinese",
                )
            del asr_result
        raw_transcript = smart_join(chunk_texts)
        if not raw_transcript:
            if echo_tokens:
                raise RuntimeError(
                    "No speech transcribed: ASR output was entirely prompt echo "
                    "(the recording likely contains no real speech)"
                )
            raise RuntimeError("Qwen3-ASR returned an empty transcript")
        del asr
        clear_mlx()

        print("[3/4] Aligning transcript and diarizing speakers", flush=True)
        aligner_path = snapshot_download(
            repo_id=ALIGNER_REPO,
            revision=ALIGNER_REVISION,
            cache_dir=model_cache,
        )
        aligner = load(aligner_path)
        words: list[Word] = []
        for index, ((chunk_audio, offset), chunk_text) in enumerate(
            zip(chunks, chunk_texts), start=1
        ):
            if not chunk_text:
                continue
            print(f"      aligning chunk {index}/{len(chunks)}", flush=True)
            aligned = aligner.generate(
                chunk_audio, text=chunk_text, language=detected_language
            )
            chunk_end = min(duration, offset + len(chunk_audio) / SAMPLE_RATE)
            for item in aligned:
                if not str(item.text).strip():
                    continue
                start = min(chunk_end, offset + max(0.0, float(item.start_time)))
                end = min(chunk_end, offset + float(item.end_time))
                words.append(Word(text=str(item.text), start=start, end=max(start, end)))
            del aligned
        del aligner
        clear_mlx()
        if not words:
            raise RuntimeError("ForcedAligner returned no timed words")
        coverage = max(word.end for word in words) / duration if duration else 0.0
        if coverage < MIN_TIMELINE_COVERAGE:
            warnings.append(
                f"Aligned words span only {coverage:.0%} of the {duration:.0f}s "
                "recording; timestamps are unreliable."
            )
        if not restore_transcript_formatting(words, raw_transcript):
            warnings.append("ASR punctuation could not be restored to aligned words.")
        for word in words:
            word.text = normalize_text(word.text, args.text_variant)

        diarize_command = [
            str(SPEAKERKIT_BINARY),
            "diarize",
            "--audio-path",
            str(wav_path),
            "--rttm-path",
            str(rttm_path),
        ]
        if speaker_count is not None:
            diarize_command += ["--num-speakers", str(speaker_count)]
        subprocess.run(diarize_command, check=True)

        print("[4/4] Fusing timelines and writing outputs", flush=True)
        intervals = parse_rttm(rttm_path)
        speaker_mapping = canonicalize_speakers(intervals)
        if speaker_count is not None and len(speaker_mapping) != speaker_count:
            warnings.append(
                f"Requested {speaker_count} speakers but diarizer returned "
                f"{len(speaker_mapping)}."
            )
        assign_words(words, intervals, display_map)
        unknown_count = sum(item.speaker == "UNKNOWN" for item in words)
        if unknown_count:
            warnings.append(f"{unknown_count} aligned words could not be assigned.")
        segments = build_segments(words)
        normalized_transcript = normalize_text(raw_transcript, args.text_variant)
        archived_audio = (
            None
            if args.no_copy_audio
            else archive_source_audio(source, output_dir, stem)
        )
        metadata = {
            "source_path": str(source),
            "archived_audio": str(archived_audio) if archived_audio else None,
            "duration_seconds": round(duration, 6),
            "language": detected_language,
            "text_variant": args.text_variant,
            "requested_speakers": speaker_count or "auto",
            # sanitized: raw argv can carry surrogateescape bytes that crash write
            "asr_context": sanitized_context,
            "models": {
                "asr": {"repo": ASR_REPO, "revision": ASR_REVISION},
                "aligner": {"repo": ALIGNER_REPO, "revision": ALIGNER_REVISION},
                "diarizer": DIARIZER_NAME,
            },
        }
        paths = write_outputs(
            output_dir=output_dir,
            stem=stem,
            metadata=metadata,
            words=words,
            segments=segments,
            speaker_mapping=speaker_mapping,
            display_map=display_map,
            transcript=normalized_transcript,
            warnings=warnings,
        )
        return {kind: str(path) for kind, path in paths.items()}
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def main() -> int:
    args = parse_args()
    if not args.runtime_ready:
        bootstrap_and_reexec(args)
    paths = run_pipeline(args)
    print(json.dumps(paths, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
