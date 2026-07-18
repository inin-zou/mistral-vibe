from __future__ import annotations

from pathlib import Path
import sys

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QCursor, QGuiApplication, QMouseEvent, QResizeEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QSizeGrip,
    QVBoxLayout,
    QWidget,
)

from vibe.core.pawgress.events import (
    ControlAction,
    ControlMessage,
    IslandState,
    encode_jsonl,
)
from vibe.overlay.cat import CatAnimator
from vibe.overlay.render import buttons_html, render_island_html

_ACTIONS: dict[str, ControlAction] = {
    "pause": ControlAction.PAUSE,
    "resume": ControlAction.RESUME,
    "stop": ControlAction.STOP,
    "focus_vibe": ControlAction.FOCUS_VIBE,
}

_STYLE = """
#island {
    background: rgb(17, 20, 28);
    border-radius: 18px;
    border: 1px solid rgb(255, 130, 5);
}
#divider {
    background: rgb(42, 46, 58);
    border: none;
}
QLabel {
    font-family: 'Menlo', 'Monaco', monospace;
    font-size: 14px;
    color: #e6e6e6;
}
"""

_MARGIN_SIDE = 18
_MARGIN_TOP = 14
_MARGIN_BOTTOM = 10
_SPACING = 8
_BORDER = 2


class IslandWindow(QWidget):
    def __init__(self, control_path: Path | None = None) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet(_STYLE)

        self._cat = CatAnimator()
        self._state: IslandState | None = None
        self._drag_offset: QPoint | None = None
        self._control_path = control_path
        self._ticks = 0
        self._user_moved = False
        self._user_resized = False
        self._programmatic_resize = False

        frame = QFrame(self)
        frame.setObjectName("island")
        self._label = QLabel(frame)
        self._label.setTextFormat(Qt.TextFormat.RichText)
        self._label.setOpenExternalLinks(False)
        self._label.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self._label.linkActivated.connect(self._on_link)
        self._label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        divider = QFrame(frame)
        divider.setObjectName("divider")
        divider.setFixedHeight(1)

        self._buttons = QLabel(frame)
        self._buttons.setTextFormat(Qt.TextFormat.RichText)
        self._buttons.setOpenExternalLinks(False)
        self._buttons.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self._buttons.linkActivated.connect(self._on_link)
        self._buttons.setAlignment(Qt.AlignmentFlag.AlignCenter)

        inner = QVBoxLayout(frame)
        inner.setContentsMargins(
            _MARGIN_SIDE, _MARGIN_TOP, _MARGIN_SIDE, _MARGIN_BOTTOM
        )
        inner.setSpacing(_SPACING)
        inner.addWidget(self._label, 1)
        inner.addWidget(divider)
        inner.addWidget(self._buttons)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        self._grip = QSizeGrip(self)
        self._grip.resize(16, 16)
        self.setMinimumSize(260, 150)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(160)
        self._render()
        self._resize()

    def update_state(self, state: IslandState) -> None:
        self._state = state
        self._render()
        self._resize()
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
            self._buttons.setText("")
            return
        self._label.setText(
            render_island_html(
                self._state, self._cat.current_frame(), self._ticks, with_buttons=False
            )
        )
        self._buttons.setText(buttons_html(self._state))

    def _resize(self) -> None:
        if not self._user_resized:
            content = self._label.sizeHint()
            buttons = self._buttons.sizeHint()
            width = max(content.width(), buttons.width()) + 2 * _MARGIN_SIDE + _BORDER
            height = (
                content.height()
                + buttons.height()
                + 1
                + 2 * _SPACING
                + _MARGIN_TOP
                + _MARGIN_BOTTOM
                + _BORDER
            )
            self._programmatic_resize = True
            self.resize(
                max(width, self.minimumWidth()), max(height, self.minimumHeight())
            )
            self._programmatic_resize = False
        self._reposition()

    def resizeEvent(self, event: QResizeEvent) -> None:
        dragging = bool(QApplication.mouseButtons() & Qt.MouseButton.LeftButton)
        if not self._programmatic_resize and dragging:
            self._user_resized = True
        self._grip.move(self.width() - 20, self.height() - 20)
        super().resizeEvent(event)

    def _reposition(self) -> None:
        screen = (
            QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        )
        if screen is None or self._user_moved:
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
            self._user_moved = True
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
