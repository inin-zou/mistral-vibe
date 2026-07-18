from __future__ import annotations

import argparse
from pathlib import Path
import signal
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from vibe.core.paths import VIBE_HOME
from vibe.overlay.hotkey import HotkeyBridge, install_toggle_hotkey
from vibe.overlay.macos import hide_dock_icon, make_visible_on_all_spaces
from vibe.overlay.reader import FileTailReader, StdinReader
from vibe.overlay.window import IslandWindow


def main() -> None:
    parser = argparse.ArgumentParser(prog="vibe.overlay")
    parser.add_argument(
        "--file", nargs="?", const=str(VIBE_HOME.path / "pawgress.jsonl"), default=None
    )
    parser.add_argument(
        "--control-file", default=str(VIBE_HOME.path / "pawgress-control.jsonl")
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    window = IslandWindow(control_path=Path(args.control_file))
    window.show()
    make_visible_on_all_spaces(window)
    hide_dock_icon()
    QTimer.singleShot(200, hide_dock_icon)

    if args.file is not None:
        tail = FileTailReader(Path(args.file))
        tail.received.connect(window.update_state)
        tail.start()
    else:
        stdin_reader = StdinReader()
        stdin_reader.received.connect(window.update_state)
        stdin_reader.start()

    bridge = HotkeyBridge()
    bridge.triggered.connect(window.toggle_visibility)
    install_toggle_hotkey(bridge)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
