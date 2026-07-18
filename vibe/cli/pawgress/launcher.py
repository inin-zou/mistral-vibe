from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from vibe.core.logger import logger

_state: dict[str, subprocess.Popen[bytes] | None] = {"process": None}


def launch_overlay(sink_path: Path) -> None:
    existing = _state["process"]
    if existing is not None and existing.poll() is None:
        return
    try:
        _state["process"] = subprocess.Popen(
            [sys.executable, "-m", "vibe.overlay", "--file", str(sink_path)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as e:
        logger.warning("Failed to launch pawgress overlay: %s", e)
