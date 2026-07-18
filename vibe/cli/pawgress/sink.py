from __future__ import annotations

from pathlib import Path

from vibe.core.logger import logger
from vibe.core.paths import VIBE_HOME
from vibe.core.pawgress.events import IslandState, encode_jsonl


class PawgressSink:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path if path is not None else VIBE_HOME.path / "pawgress.jsonl"

    @property
    def path(self) -> Path:
        return self._path

    def reset(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text("", encoding="utf-8")
        except OSError as e:
            logger.warning("Failed to reset pawgress sink %s: %s", self._path, e)

    def write(self, state: IslandState) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(encode_jsonl(state))
                fh.flush()
        except OSError as e:
            logger.warning(
                "Failed to write pawgress island state to %s: %s", self._path, e
            )
