#!/usr/bin/env python3
"""Pure-Python timeline fusion and output rendering."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from pathlib import Path
from typing import Iterable
import unicodedata


@dataclass
class SpeakerInterval:
    start: float
    end: float
    raw_speaker: str
    canonical_speaker: str = ""


@dataclass
class Word:
    text: str
    start: float
    end: float
    speaker: str = "UNKNOWN"
    display_speaker: str = "UNKNOWN"
    overlap: bool = False
    assignment: str = "unknown"


@dataclass
class Segment:
    text: str
    start: float
    end: float
    speaker: str
    display_speaker: str
    overlap: bool


def parse_rttm(path: Path) -> list[SpeakerInterval]:
    intervals: list[SpeakerInterval] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 8 or parts[0] != "SPEAKER":
            continue
        start = float(parts[3])
        duration = float(parts[4])
        intervals.append(SpeakerInterval(start, start + duration, parts[7]))
    if not intervals:
        raise ValueError("RTTM contains no speaker intervals")
    intervals.sort(key=lambda item: (item.start, item.end, item.raw_speaker))
    return intervals


def canonicalize_speakers(
    intervals: list[SpeakerInterval],
) -> dict[str, str]:
    first_seen: dict[str, float] = {}
    for item in intervals:
        first_seen[item.raw_speaker] = min(
            item.start, first_seen.get(item.raw_speaker, item.start)
        )
    ordered = sorted(first_seen, key=lambda key: (first_seen[key], key))
    mapping = {raw: _speaker_label(index) for index, raw in enumerate(ordered)}
    for item in intervals:
        item.canonical_speaker = mapping[item.raw_speaker]
    return mapping


def _speaker_label(index: int) -> str:
    # A, B, ..., Z, AA, AB...
    value = index + 1
    letters = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        letters = chr(65 + remainder) + letters
    return f"Speaker {letters}"


def _intersection(start_a: float, end_a: float, start_b: float, end_b: float) -> float:
    return max(0.0, min(end_a, end_b) - max(start_a, start_b))


def assign_words(
    words: list[Word],
    intervals: list[SpeakerInterval],
    display_map: dict[str, str] | None = None,
    nearest_seconds: float = 0.75,
) -> list[Word]:
    display_map = display_map or {}
    for word in words:
        scores: dict[str, float] = {}
        intersecting: set[str] = set()
        for interval in intervals:
            overlap = _intersection(word.start, word.end, interval.start, interval.end)
            if overlap > 0:
                scores[interval.canonical_speaker] = (
                    scores.get(interval.canonical_speaker, 0.0) + overlap
                )
                intersecting.add(interval.canonical_speaker)
        if scores:
            word.speaker = sorted(scores, key=lambda key: (-scores[key], key))[0]
            word.overlap = len(intersecting) > 1
            word.assignment = "overlap"
        else:
            midpoint = (word.start + word.end) / 2
            candidates: list[tuple[float, str]] = []
            for interval in intervals:
                if interval.start <= midpoint <= interval.end:
                    distance = 0.0
                else:
                    distance = min(abs(midpoint - interval.start), abs(midpoint - interval.end))
                candidates.append((distance, interval.canonical_speaker))
            distance, speaker = min(candidates, default=(float("inf"), "UNKNOWN"))
            if distance <= nearest_seconds:
                word.speaker = speaker
                word.assignment = "nearest"
        word.display_speaker = display_map.get(word.speaker, word.speaker)
    return words


def _is_significant(char: str) -> bool:
    return not char.isspace() and not unicodedata.category(char).startswith("P")


def restore_transcript_formatting(words: list[Word], transcript: str) -> bool:
    """Restore ASR punctuation/spacing when aligned significant text is identical."""
    originals = [word.text for word in words]
    formatted: list[str] = []
    position = 0
    try:
        for original in originals:
            target = "".join(char for char in original if _is_significant(char))
            start = position
            matched = 0
            while matched < len(target):
                if position >= len(transcript):
                    return False
                char = transcript[position]
                position += 1
                if not _is_significant(char):
                    continue
                if char != target[matched]:
                    return False
                matched += 1
            while position < len(transcript) and not _is_significant(transcript[position]):
                position += 1
            formatted.append(transcript[start:position])
        if any(_is_significant(char) for char in transcript[position:]):
            return False
    except (IndexError, TypeError):
        return False
    for word, text in zip(words, formatted):
        word.text = text
    return True


_CJK_RE = re.compile(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]")
_NO_SPACE_BEFORE = set("，。！？；：、,.!?;:)]}」』》〉")
_NO_SPACE_AFTER = set("([{「『《〈")


def smart_join(tokens: Iterable[str]) -> str:
    output = ""
    for raw in tokens:
        token = raw.strip()
        if not token:
            continue
        if not output:
            output = token
            continue
        previous = output[-1]
        if (
            token[0] in _NO_SPACE_BEFORE
            or previous in _NO_SPACE_AFTER
            or _CJK_RE.search(previous)
            or _CJK_RE.search(token[0])
        ):
            output += token
        else:
            output += " " + token
    return output


def _display_width(text: str) -> int:
    return sum(2 if _CJK_RE.match(char) else 1 for char in text)


def build_segments(
    words: list[Word],
    *,
    max_gap: float = 0.8,
    max_duration: float = 6.0,
    max_width: int = 42,
) -> list[Segment]:
    if not words:
        return []
    ordered = sorted(words, key=lambda item: (item.start, item.end))
    groups: list[list[Word]] = []
    current: list[Word] = []
    for word in ordered:
        candidate = smart_join([item.text for item in current] + [word.text])
        should_split = bool(
            current
            and (
                word.speaker != current[-1].speaker
                or word.start - current[-1].end > max_gap
                or word.end - current[0].start > max_duration
                or _display_width(candidate) > max_width
            )
        )
        if should_split:
            groups.append(current)
            current = []
        current.append(word)
    if current:
        groups.append(current)
    return [
        Segment(
            text=smart_join(item.text for item in group),
            start=max(0.0, group[0].start),
            end=max(group[0].start, group[-1].end),
            speaker=group[0].speaker,
            display_speaker=group[0].display_speaker,
            overlap=any(item.overlap for item in group),
        )
        for group in groups
    ]


def _clock(seconds: float, *, srt: bool = False) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    separator = "," if srt else "."
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}"


def render_txt(segments: list[Segment]) -> str:
    return "\n\n".join(
        f"[{_clock(item.start)}] {item.display_speaker}: {item.text}"
        for item in segments
    ) + "\n"


def render_srt(segments: list[Segment]) -> str:
    blocks = []
    for index, item in enumerate(segments, start=1):
        blocks.append(
            f"{index}\n{_clock(item.start, srt=True)} --> {_clock(item.end, srt=True)}\n"
            f"[{item.display_speaker}] {item.text}"
        )
    return "\n\n".join(blocks) + "\n"


def render_vtt(segments: list[Segment]) -> str:
    blocks = ["WEBVTT"]
    for item in segments:
        blocks.append(
            f"{_clock(item.start)} --> {_clock(item.end)}\n"
            f"[{item.display_speaker}] {item.text}"
        )
    return "\n\n".join(blocks) + "\n"


def write_outputs(
    *,
    output_dir: Path,
    stem: str,
    metadata: dict,
    words: list[Word],
    segments: list[Segment],
    speaker_mapping: dict[str, str],
    display_map: dict[str, str],
    transcript: str,
    warnings: list[str],
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "txt": output_dir / f"{stem}.txt",
        "srt": output_dir / f"{stem}.srt",
        "vtt": output_dir / f"{stem}.vtt",
        "json": output_dir / f"{stem}.json",
    }
    payload = {
        "metadata": metadata,
        "speakers": [
            {
                "raw_speaker": raw,
                "canonical": canonical,
                "display": display_map.get(canonical, canonical),
            }
            for raw, canonical in speaker_mapping.items()
        ],
        "words": [asdict(item) for item in words],
        "segments": [asdict(item) for item in segments],
        "transcript": transcript,
        "warnings": warnings,
    }
    contents = {
        "txt": render_txt(segments),
        "srt": render_srt(segments),
        "vtt": render_vtt(segments),
        "json": json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    }
    for kind, path in paths.items():
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(contents[kind], encoding="utf-8")
        temporary.replace(path)
    return paths
