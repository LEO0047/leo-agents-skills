#!/usr/bin/env python3
"""Create the isolated MLX and SpeakerKit runtime used by this skill."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


RUNTIME_ROOT = Path.home() / "Library" / "Caches" / "local-speaker-transcriber"
VENV_DIR = RUNTIME_ROOT / "venv"
VENV_PYTHON = VENV_DIR / "bin" / "python"
SPEAKERKIT_SOURCE = RUNTIME_ROOT / "src" / "argmax-oss-swift"
SPEAKERKIT_BINARY = SPEAKERKIT_SOURCE / ".build" / "release" / "argmax-cli"
SPEAKERKIT_COMMIT = "8fcbfed028415b0b90f0f10ee7b0303c53b600a0"
MLX_AUDIO_COMMIT = "5fac1de4e29a38e3d1e73b9ad94ae2dae616d151"
STAMP_PATH = RUNTIME_ROOT / "runtime.json"


def run(command: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def ensure_venv() -> None:
    if not VENV_PYTHON.exists():
        RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
    probe = subprocess.run(
        [
            str(VENV_PYTHON),
            "-c",
            "import mlx, mlx_audio, huggingface_hub; print('runtime-ok')",
        ],
        text=True,
        capture_output=True,
    )
    if probe.returncode == 0:
        return
    run([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip", "wheel"])
    package = (
        "mlx-audio[stt] @ "
        f"git+https://github.com/Blaizzy/mlx-audio.git@{MLX_AUDIO_COMMIT}"
    )
    run(
        [
            str(VENV_PYTHON),
            "-m",
            "pip",
            "install",
            package,
            "opencc-python-reimplemented==0.1.7",
        ]
    )


def ensure_speakerkit() -> None:
    SPEAKERKIT_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    if not (SPEAKERKIT_SOURCE / ".git").exists():
        run(
            [
                "git",
                "clone",
                "--filter=blob:none",
                "https://github.com/argmaxinc/argmax-oss-swift.git",
                str(SPEAKERKIT_SOURCE),
            ]
        )
    current = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=SPEAKERKIT_SOURCE,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    if current != SPEAKERKIT_COMMIT:
        run(["git", "fetch", "origin", SPEAKERKIT_COMMIT], cwd=SPEAKERKIT_SOURCE)
        run(["git", "checkout", "--detach", SPEAKERKIT_COMMIT], cwd=SPEAKERKIT_SOURCE)
    if not SPEAKERKIT_BINARY.exists():
        run(
            ["swift", "build", "-c", "release", "--product", "argmax-cli"],
            cwd=SPEAKERKIT_SOURCE,
        )


def write_stamp() -> None:
    STAMP_PATH.write_text(
        json.dumps(
            {
                "python": str(VENV_PYTHON),
                "mlx_audio_commit": MLX_AUDIO_COMMIT,
                "speakerkit_commit": SPEAKERKIT_COMMIT,
                "speakerkit_binary": str(SPEAKERKIT_BINARY),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def status() -> int:
    data = {
        "runtime_root": str(RUNTIME_ROOT),
        "venv_python": str(VENV_PYTHON),
        "python_ready": VENV_PYTHON.exists(),
        "speakerkit_binary": str(SPEAKERKIT_BINARY),
        "speakerkit_ready": SPEAKERKIT_BINARY.exists(),
    }
    print(json.dumps(data, indent=2))
    return 0 if data["python_ready"] and data["speakerkit_ready"] else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    if args.status:
        return status()
    if sys.platform != "darwin" or os.uname().machine != "arm64":
        raise SystemExit("This runtime requires an Apple Silicon Mac.")
    if not shutil.which("afconvert"):
        raise SystemExit("macOS afconvert is required.")
    ensure_venv()
    ensure_speakerkit()
    write_stamp()
    return status()


if __name__ == "__main__":
    raise SystemExit(main())
