#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from fusion import (
    SpeakerInterval,
    Word,
    assign_words,
    build_segments,
    canonicalize_speakers,
    render_srt,
    render_vtt,
    restore_transcript_formatting,
    smart_join,
    write_outputs,
)
from transcribe import normalize_language


class FusionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.intervals = [
            SpeakerInterval(0.0, 1.0, "spk9"),
            SpeakerInterval(1.0, 2.0, "spk2"),
            SpeakerInterval(2.0, 3.0, "spk7"),
        ]
        self.mapping = canonicalize_speakers(self.intervals)

    def test_first_appearance_mapping(self) -> None:
        self.assertEqual(
            self.mapping,
            {"spk9": "Speaker A", "spk2": "Speaker B", "spk7": "Speaker C"},
        )

    def test_overlap_and_nearest_assignment(self) -> None:
        overlapping = self.intervals + [
            SpeakerInterval(0.45, 0.8, "spk2", "Speaker B")
        ]
        words = [
            Word("你", 0.1, 0.3),
            Word("好", 0.5, 0.7),
            Word("嗎", 3.2, 3.3),
            Word("遠", 4.5, 4.6),
        ]
        assign_words(words, overlapping)
        self.assertEqual(words[0].speaker, "Speaker A")
        self.assertTrue(words[1].overlap)
        self.assertEqual(words[2].speaker, "Speaker C")
        self.assertEqual(words[2].assignment, "nearest")
        self.assertEqual(words[3].speaker, "UNKNOWN")

    def test_speaker_change_and_gap_split(self) -> None:
        words = [
            Word("早", 0.0, 0.2, "Speaker A", "Speaker A"),
            Word("安", 0.2, 0.4, "Speaker A", "Speaker A"),
            Word("你好", 0.5, 0.8, "Speaker B", "Speaker B"),
            Word("再見", 2.0, 2.3, "Speaker B", "Speaker B"),
        ]
        segments = build_segments(words)
        self.assertEqual([item.text for item in segments], ["早安", "你好", "再見"])

    def test_chinese_and_latin_join(self) -> None:
        self.assertEqual(smart_join(["我", "用", "MLX", "模型", "。"]), "我用MLX模型。")
        self.assertEqual(smart_join(["hello", "world", "!"]), "hello world!")
        self.assertEqual(normalize_language(["Chinese"]), "Chinese")
        words = [Word("你", 0.0, 0.1), Word("好", 0.1, 0.2)]
        self.assertTrue(restore_transcript_formatting(words, "你，好！"))
        self.assertEqual([word.text for word in words], ["你，", "好！"])

    def test_formats_and_atomic_outputs(self) -> None:
        words = [Word("測試", 0.1, 0.5, "Speaker A", "黃先生")]
        segments = build_segments(words)
        self.assertIn("00:00:00,100 --> 00:00:00,500", render_srt(segments))
        self.assertTrue(render_vtt(segments).startswith("WEBVTT"))
        with tempfile.TemporaryDirectory() as directory:
            paths = write_outputs(
                output_dir=Path(directory),
                stem="sample",
                metadata={"duration_seconds": 1.0},
                words=words,
                segments=segments,
                speaker_mapping={"raw": "Speaker A"},
                display_map={"Speaker A": "黃先生"},
                transcript="測試",
                warnings=[],
            )
            self.assertEqual(set(paths), {"txt", "srt", "vtt", "json"})
            payload = json.loads(paths["json"].read_text(encoding="utf-8"))
            self.assertEqual(payload["segments"][0]["display_speaker"], "黃先生")


if __name__ == "__main__":
    unittest.main()
