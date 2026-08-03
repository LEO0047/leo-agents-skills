# Output schema

The pipeline writes four files plus the recording itself into one note folder. All five share a single stem: the `--name` value when given, otherwise the recording's own filename.

- `.txt`: one timestamped speaker segment per paragraph.
- `.srt`: numbered subtitle cues with `[Speaker A]`-style prefixes.
- `.vtt`: WebVTT cues with the same speaker prefixes.
- `.json`: the lossless machine-readable result.
- the recording, renamed to match, so the folder is self-contained. Moved when it already sat inside the notes library, copied when it came from outside. Suppressed by `--no-copy-audio`.

A sixth file, `<name>.html`, is authored by the agent after the pipeline finishes (see "Render the note as HTML" in SKILL.md) — the pipeline itself never writes it, so JSON consumers should not expect it.

## JSON fields

```text
metadata
  source_path, archived_audio, duration_seconds, language, text_variant, requested_speakers
  models.asr, models.aligner, models.diarizer
speakers
  canonical label, display label, original diarizer label
words[]
  text, start, end, speaker, display_speaker, overlap, assignment
segments[]
  text, start, end, speaker, display_speaker, overlap
transcript
warnings[]
```

`source_path` is where the recording was read from; `archived_audio` is where it now lives alongside the transcripts, or `null` when `--no-copy-audio` was passed. Always prefer `archived_audio` when reopening the audio: `source_path` is a historical record and points at nothing when the recording was moved out of the notes library, or when the user later moves the original.

`rename_note.py` rewrites `archived_audio` but deliberately leaves `source_path` alone, so it keeps naming the file the recording arrived as.

`assignment` is `overlap`, `nearest`, or `unknown`. `overlap: true` means more than one diarized speaker intersected the word; subtitle formats retain only the primary speaker while JSON preserves the flag.
