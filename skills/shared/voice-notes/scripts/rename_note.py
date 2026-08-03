#!/usr/bin/env python3
"""Rename a finished note folder and every file inside it.

A recording's own filename ("新錄音 9") says nothing about what is in it, and
the useful name only becomes apparent after reading the transcript. This
renames the folder, the transcript files, the archived audio, and the HTML
note page in one step, keeping the folder's date prefix and repairing the
paths recorded in the JSON and the audio reference inside the HTML.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote

DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2}) ")
ILLEGAL = re.compile(r"[/:\x00]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="The note folder to rename.")
    parser.add_argument("name", help="New descriptive name, without a date prefix.")
    return parser.parse_args()


def rename_note(folder: Path, name: str) -> dict[str, str]:
    folder = folder.expanduser().resolve()
    if not folder.is_dir():
        raise NotADirectoryError(folder)
    if ILLEGAL.search(name) or name in (".", ".."):
        raise ValueError(f"Name cannot contain / or : — got {name!r}")

    notes = sorted(folder.glob("*.json"))
    if len(notes) != 1:
        raise RuntimeError(f"Expected exactly one .json in {folder}, found {len(notes)}")
    old_stem = notes[0].stem

    # Check every destination before touching anything, so a collision cannot
    # leave the folder half-renamed.
    match = DATE_PREFIX.match(folder.name)
    new_folder = folder.with_name(f"{match.group(1)} {name}" if match else name)
    if new_folder != folder and new_folder.exists():
        raise FileExistsError(new_folder)
    for path in folder.iterdir():
        target = path.with_name(f"{name}{path.suffix}")
        if path.is_file() and path.stem == old_stem and target != path and target.exists():
            raise FileExistsError(target)

    # Rename every sibling that shares the recording's stem: the four
    # transcripts plus the archived audio.
    renamed: dict[str, str] = {}
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.stem == old_stem:
            target = path.with_name(f"{name}{path.suffix}")
            if target != path:
                path.rename(target)
            renamed[path.suffix.lstrip(".")] = target.name

    # The JSON records where the audio landed; that path just moved.
    note_path = folder / f"{name}.json"
    payload = json.loads(note_path.read_text(encoding="utf-8"))
    archived = payload.get("metadata", {}).get("archived_audio")
    if archived:
        payload["metadata"]["archived_audio"] = str(
            Path(archived).with_name(f"{name}{Path(archived).suffix}")
        )
        note_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    # Keep the date prefix so folders stay in chronological order.
    if new_folder != folder:
        folder.rename(new_folder)

    # Rewrite the archived_audio path a second time: the folder moved too.
    final_note = new_folder / f"{name}.json"
    payload = json.loads(final_note.read_text(encoding="utf-8"))
    if payload.get("metadata", {}).get("archived_audio"):
        suffix = Path(payload["metadata"]["archived_audio"]).suffix
        payload["metadata"]["archived_audio"] = str(new_folder / f"{name}{suffix}")
        final_note.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    # The HTML page references its siblings (the audio player src) by the old
    # filenames. Repair both plain and percent-encoded forms.
    html_path = new_folder / f"{name}.html"
    if html_path.exists():
        text = html_path.read_text(encoding="utf-8")
        for suffix in sorted(renamed):
            old_file = f"{old_stem}.{suffix}"
            new_file = f"{name}.{suffix}"
            text = text.replace(old_file, new_file)
            text = text.replace(quote(old_file), quote(new_file))
        html_path.write_text(text, encoding="utf-8")

    return {"folder": str(new_folder), **renamed}


def main() -> int:
    args = parse_args()
    print(json.dumps(rename_note(args.folder, args.name), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
