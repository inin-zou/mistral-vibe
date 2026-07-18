from __future__ import annotations

from pathlib import Path
import sys

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QVBoxLayout, QWidget

from vibe.core.pawgress.events import (
    ControlAction,
    ControlMessage,
    IslandState,
    encode_jsonl,
)
from vibe.overlay.cat import CatAnimator
from vibe.overlay.render import render_island_html

_ACTIONS: dict[str, ControlAction] = {
    "pause": ControlAction.PAUSE,
    "stop": ControlAction.STOP,
    "focus_vibe": ControlAction.FOCUS_VIBE,
}

_STYLE = """
#island {
    background: rgb(18, 18, 22);
    border-radius: 14px;
    border: 1px solid rgb(255, 130, 5);
}
QLabel {
    font-family: 'Menlo', 'Monaco', monospace;
    font-size: 13px;
    color: #e6e6e6;
}
"""


class IslandWindow(QWidget):
    def __init__(self, control_path: Path | None = None) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(_STYLE)

        self._cat = CatAnimator()
        self._state: IslandState | None = None
        self._drag_offset: QPoint | None = None
        self._control_path = control_path
        self._ticks = 0

        frame = QFrame(self)
        frame.setObjectName("island")
        self._label = QLabel(frame)
        self._label.setTextFormat(Qt.TextFormat.RichText)
        self._label.setOpenExternalLinks(False)
        self._label.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self._label.linkActivated.connect(self._on_link)

        inner = QVBoxLayout(frame)
        inner.setContentsMargins(16, 12, 16, 12)
        inner.addWidget(self._label)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(160)
        self._render()

    def update_state(self, state: IslandState) -> None:
        self._state = state
        self._render()
        self.raise_()

    def toggle_visibility(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    def _tick(self) -> None:
        self._ticks += 1
        self._cat.next_frame()
        self._render()

    def _render(self) -> None:
        if self._state is None:
            self._label.setText(
                '<span style="color:#8a8a8a">\U0001f43e Pawgress · idle</span>'
            )
        else:
            self._label.setText(
                render_island_html(self._state, self._cat.current_frame(), self._ticks)
            )
        self.adjustSize()
        self._reposition()

    def _reposition(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None or self._drag_offset is not None:
            return
        geo = screen.availableGeometry()
        self.move(geo.x() + (geo.width() - self.width()) // 2, geo.y() + 8)

    def _on_link(self, href: str) -> None:
        if href == "quit":
            instance = QApplication.instance()
            if instance is not None:
                instance.quit()
            return
        action = _ACTIONS.get(href)
        if action is None:
            return
        self._emit_control(action)

    def _emit_control(self, action: ControlAction) -> None:
        line = encode_jsonl(ControlMessage(action=action))
        if self._control_path is None:
            sys.stdout.write(line)
            sys.stdout.flush()
            return
        try:
            self._control_path.parent.mkdir(parents=True, exist_ok=True)
            with self._control_path.open("a", encoding="utf-8") as fh:
                fh.write(line)
                fh.flush()
        except OSError:
            pass

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
