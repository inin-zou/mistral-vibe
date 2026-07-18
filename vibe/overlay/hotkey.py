from __future__ import annotations

from PySide6.QtCore import QObject, Signal

_keep_alive: list[object] = []


class HotkeyBridge(QObject):
    triggered = Signal()


def install_toggle_hotkey(bridge: HotkeyBridge) -> None:
    try:
        from pynput import keyboard
    except ImportError:
        return
    try:
        listener = keyboard.GlobalHotKeys({"<alt>+<enter>": bridge.triggered.emit})
        listener.start()
        _keep_alive.append(listener)
    except Exception:
        return
