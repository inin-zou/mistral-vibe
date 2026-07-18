from __future__ import annotations

from pathlib import Path
import sys

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from vibe.core.pawgress.events import IslandState, parse_island_state


def _try_parse(line: str) -> IslandState | None:
    line = line.strip()
    if not line:
        return None
    try:
        return parse_island_state(line)
    except ValueError:
        return None


class StdinReader(QThread):
    received = Signal(object)

    def run(self) -> None:
        for line in sys.stdin:
            state = _try_parse(line)
            if state is not None:
                self.received.emit(state)


class FileTailReader(QObject):
    received = Signal(object)

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._path = path
        self._pos = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)

    def start(self) -> None:
        self._timer.start(200)

    def _poll(self) -> None:
        if not self._path.exists():
            return
        if self._path.stat().st_size < self._pos:
            self._pos = 0
        with self._path.open("r", encoding="utf-8") as fh:
            fh.seek(self._pos)
            for line in fh:
                state = _try_parse(line)
                if state is not None:
                    self.received.emit(state)
            self._pos = fh.tell()
