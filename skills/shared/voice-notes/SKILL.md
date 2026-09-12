---
name: voice-notes
compat: [claude-code, codex]
description: Turn local multi-speaker recordings into private, time-aligned voice notes entirely on Apple Silicon with Qwen3-ASR MLX, Qwen3 ForcedAligner, and SpeakerKit/Pyannote diarization. Use when the user wants to transcribe local M4A, WAV, MP3, or FLAC audio into speaker-labeled TXT, SRT, VTT, and JSON files, optionally with a known speaker count or custom speaker names. Chinese output is normalized to Taiwan Traditional Chinese by default.
---

# Voice Notes

Create a time-aligned, speaker-labeled transcript without uploading audio.

This skill is installed at `~/.claude/skills/voice-notes` (Claude Code) and `~/.codex/skills/voice-notes` (Codex). Always invoke its scripts by absolute path from the running platform's install location — the working directory is the user's project, not this folder.

## Run the workflow

1. Confirm the input audio path, the expected speaker count when known, and an optional speaker-name mapping. Decide the rest without asking: the output directory, the descriptive `--name`, and the text variant all have correct defaults below, and the language follows from the audio.
2. Tell the user before the first run that local runtimes and several gigabytes of models will be downloaded and cached.
3. Run:

```bash
python3 ~/.claude/skills/voice-notes/scripts/transcribe.py \
  "/absolute/path/to/recording.m4a" \
  --name "佛經與聖經句子對照" \
  --speakers 3 \
  --language Chinese
```

4. Use `--speakers auto` when the count is unknown. Output is Taiwan Traditional Chinese by default; pass `--text-variant preserve` only when the user wants the ASR model's raw output, which for Chinese is Simplified.
5. Use `--speaker-map /absolute/path/to/map.json` to replace generic labels. The file maps canonical labels to names:

```json
{"Speaker A": "Alice", "Speaker B": "Bob"}
```

6. Use `--asr-context "詞1、詞2、…"` to bias recognition toward domain vocabulary — proper nouns and fixed terms only, separated by 、. Never put descriptive sentences in it: they can pull the model toward hallucinating them. Supply your own vocabulary; no team roster or voiceprint profiles are included.

7. The first run builds the runtime and downloads models, so it can take a long time. Run it with `run_in_background: true` and check the output rather than letting a foreground call time out.
8. Inspect the generated TXT, SRT, VTT, and JSON. Report warnings from the pipeline, especially `UNKNOWN` assignments or a detected speaker count different from the requested count.
9. Render the note as a designed HTML page in the same folder — see "Render the note as HTML" below.
10. Link only the user-facing output files in the final response.

## Naming the note

Never leave a note named after the recording's filename. `新錄音 9` says nothing about what is in it, and a folder of such names is unusable a month later.

Give `--name` a short descriptive title in the transcript's own language — what the recording is *about*, not its format. Roughly 4 to 12 characters of Chinese, or a handful of words in English. `佛經與聖經句子對照`, not `錄音轉錄` or `Meeting`. It becomes the folder name and the stem of all five files.

When the recording's subject is not yet known, transcribe first and rename afterwards from what the transcript actually says:

```bash
python3 ~/.claude/skills/voice-notes/scripts/rename_note.py \
  "/absolute/path/to/2026-07-30 新錄音 9" \
  "佛經與聖經句子對照"
```

That renames the folder, all four transcripts, and the archived audio together, keeps the date prefix, and repairs `archived_audio` inside the JSON. It refuses before touching anything if the target name is taken, so a collision cannot half-rename a folder.

## Where output goes

Never write transcripts to `~/Downloads` or leave a recording loose after transcribing it — recordings arrive as scratch, but the notes are a keeper.

With no `--output-dir`, the script writes one dated folder per recording into the notes library:

```text
~/Library/Mobile Documents/com~apple~CloudDocs/Coding/Experiments/Claude/錄音/<YYYY-MM-DD> <name>/
```

The date comes from the recording's own modification time, so folders sort by when the audio was recorded rather than when it was transcribed. It falls back to `~/Documents/錄音/` when iCloud Drive is absent. Pass `--output-dir` only when the user names a specific destination.

The recording itself ends up in the folder too, renamed to match, so each folder holds the audio plus its four transcripts and stands on its own:

- A recording already inside the notes library is **moved** into its note folder — a second copy in the same library is the clutter this exists to prevent, and it leaves the library's top level holding only recordings still waiting to be transcribed.
- A recording from anywhere else (`~/Downloads`, an external drive) is **copied**, leaving the user's original where they put it.

Either way the JSON records the result as `archived_audio` next to the original `source_path`. Pass `--no-copy-audio` to leave the recording alone entirely.

## Render the note as HTML

After the four files are verified and the note has its descriptive name, build one more artifact by hand: `<name>.html` in the same folder — the note as a page someone actually reads, not raw subtitle files.

Load the `/openai-frontend-design` skill before writing any markup, and follow it. The design judgment comes from the transcript itself: first decide what this recording *is* — a two-person planning chat, an interview, a lecture, a memo to self — and let that verdict drive the layout, typography, and mood. A page for a casual task briefing should not look like a page for a formal lecture.

Hard requirements, independent of the design direction:

- One self-contained file: all CSS and JS inline, no external requests. The only relative reference allowed is the sibling audio file.
- An `<audio controls>` player whose `src` is the audio file's exact filename (e.g. `src="佛經與聖經句子對照.m4a"`), so the page plays straight out of the folder.
- The full speaker-labeled transcript with timestamps — read the JSON for structured segments rather than scraping the TXT.
- Surface the note's metadata where the design wants it: recording date, duration, detected speakers.
- Readable in both light and dark via `prefers-color-scheme`.
- When the page seeks the audio (tap a timestamp to play from there), queue the seek until the target time is inside `audio.seekable` — an early `currentTime` set silently resets to 0 on cold loads and on servers without Range support — and use `preload="auto"`; bound the wait to a few seconds, then allow ordinary playback if seeking remains unavailable.

For local playback checks, run the bundled [Range server](scripts/range_server.py):

```bash
python3 ~/.claude/skills/voice-notes/scripts/range_server.py 8124 "/absolute/path/to/notes"
```

Open `http://127.0.0.1:8124/` and actually test a timestamp jump. Use an existing project preview server when it already supports byte ranges. HTTP success alone does not verify playback or page rendering. This public server binds to loopback only.

`rename_note.py` renames the HTML together with everything else and repairs the audio filename inside it, so building the page before a later rename is safe.

## Runtime behavior

- Keep the Python environment, ASR/aligner snapshots, SpeakerKit source, and compiled CLI under `~/Library/Caches/local-speaker-transcriber/`. SpeakerKit CoreML downloads go under `~/Library/Application Support/local-speaker-transcriber/huggingface/` to avoid iCloud eviction and memory-mapping failures.
- Transcription limits aligned words to two seconds, flags the clamp, filters short repetitive ASR loops, and retries diarization once. These heuristics do not establish timestamp accuracy; inspect flagged output against the audio.
- Convert source audio to a temporary 16 kHz mono WAV with macOS `afconvert`.
- Run Qwen3-ASR, unload it, run Qwen3-ForcedAligner, then run SpeakerKit. Never upload audio.
- Delete temporary audio and intermediate files after either success or failure.
- Do not invent speaker identities. Assign Speaker A, B, C, and so on by first appearance unless a mapping is supplied.
- Treat the four final files as one atomic result: do not claim completion if any format is missing or invalid.

## Validation and troubleshooting

Run the deterministic fusion tests after changing scripts:

```bash
python3 ~/.claude/skills/voice-notes/scripts/test_fusion.py
```

Read [references/output-schema.md](references/output-schema.md) when consuming the JSON programmatically or debugging speaker assignment.

## Repair existing subtitle spans

[reclamp.py](scripts/reclamp.py) rebuilds subtitles from stored word timings without model inference. Use a session folder containing transcript JSON, with unrelated JSON moved elsewhere first.

```bash
python3 ~/.claude/skills/voice-notes/scripts/reclamp.py --session "/absolute/path/to/session" --report
python3 ~/.claude/skills/voice-notes/scripts/reclamp.py --session "/absolute/path/to/session"
```

The first command is read-only; the second creates `_reclamped/` for inspection. Only use `--in-place` when replacing the transcript is authorized: it backs up the originals to `_before_reclamp/` and removes old speaker-identification metadata. A two-second cap prevents long frozen subtitles; it does not recover the true word end. Recheck names against audio before applying any identity mapping.

The optional legacy `speaker_id.py` needs your own enrolled profiles in `~/Library/Application Support/local-speaker-transcriber/voiceprints/profiles.json`. It is not part of the default workflow and its thresholds have not been validated for your microphones or speakers. Unknown speakers retain generic labels; transcript content must not be used to identify them.

## Keeping the two copies in sync

An equivalent skill lives at `~/.codex/skills/voice-notes`, and both share the same runtime cache. After changing scripts here, mirror them so the two copies stay identical:

```bash
rsync -av --exclude '__pycache__' --exclude '.DS_Store' ~/.claude/skills/voice-notes/scripts/ ~/.codex/skills/voice-notes/scripts/
```
