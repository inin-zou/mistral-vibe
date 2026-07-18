from __future__ import annotations

import atexit
import contextlib
import os
from pathlib import Path
import signal
import subprocess
import sys

from vibe.core.logger import logger
from vibe.core.paths import VIBE_HOME

_state: dict[str, subprocess.Popen[bytes] | None] = {"process": None}
_atexit_registered = False


def _pid_path() -> Path:
    return VIBE_HOME.path / "pawgress-overlay.pid"


def _kill_stale() -> None:
    path = _pid_path()
    if not path.exists():
        return
    with contextlib.suppress(OSError, ValueError):
        os.kill(int(path.read_text().strip()), signal.SIGTERM)
    with contextlib.suppress(OSError):
        path.unlink()


def terminate_overlay() -> None:
    process = _state["process"]
    if process is not None and process.poll() is None:
        with contextlib.suppress(OSError):
            process.terminate()
    _state["process"] = None
    with contextlib.suppress(OSError):
        _pid_path().unlink()


def launch_overlay(sink_path: Path) -> None:
    global _atexit_registered
    existing = _state["process"]
    if existing is not None and existing.poll() is None:
        return
    _kill_stale()
    try:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "vibe.overlay",
                "--file",
                str(sink_path),
                "--parent-pid",
                str(os.getpid()),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as e:
        logger.warning("Failed to launch pawgress overlay: %s", e)
        return
    _state["process"] = process
    with contextlib.suppress(OSError):
        _pid_path().write_text(str(process.pid), encoding="utf-8")
    if not _atexit_registered:
        atexit.register(terminate_overlay)
        _atexit_registered = True
