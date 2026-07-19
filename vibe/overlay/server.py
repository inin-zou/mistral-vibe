"""The overlay-side broker: a ``QLocalServer`` that accepts persistent
connections from Vibe sessions, feeds a ``SessionRegistry``, and routes control
messages back to the right session's socket.

Each connection's lifetime is the reference count: when it closes (clean exit
or ``kill -9``), the kernel signals ``disconnected`` and the session is dropped.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from vibe.core.pawgress.protocol import (
    ByeMsg,
    ControlMsg,
    HelloMsg,
    StateMsg,
    decode_line,
    encode_line,
)
from vibe.overlay.registry import SessionRegistry


class OverlayServer(QObject):
    state_changed = Signal()
    empty = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.registry = SessionRegistry()
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_new_connection)
        self._sockets: dict[str, QLocalSocket] = {}
        self._sid_of: dict[int, str] = {}
        self._buffers: dict[int, bytes] = {}

    def listen(self, socket_path: str) -> bool:
        # We hold the flock, so any existing path is stale and safe to clear.
        QLocalServer.removeServer(socket_path)
        return self._server.listen(socket_path)

    def send_control(self, sid: str, msg: ControlMsg) -> None:
        sock = self._sockets.get(sid)
        if (
            sock is not None
            and sock.state() == QLocalSocket.LocalSocketState.ConnectedState
        ):
            sock.write(encode_line(msg).encode("utf-8"))
            sock.flush()

    def _on_new_connection(self) -> None:
        while self._server.hasPendingConnections():
            sock = self._server.nextPendingConnection()
            self._buffers[id(sock)] = b""
            sock.readyRead.connect(lambda s=sock: self._on_ready_read(s))
            sock.disconnected.connect(lambda s=sock: self._on_disconnected(s))

    def _on_ready_read(self, sock: QLocalSocket) -> None:
        buf = self._buffers.get(id(sock), b"") + bytes(sock.readAll().data())
        while b"\n" in buf:
            raw, _, buf = buf.partition(b"\n")
            self._handle_line(sock, raw.decode("utf-8", "replace"))
        self._buffers[id(sock)] = buf

    def _handle_line(self, sock: QLocalSocket, line: str) -> None:
        msg = decode_line(line)
        if isinstance(msg, HelloMsg):
            self._bind(sock, msg.sid)
            self.registry.upsert_hello(msg.sid, msg.label, msg.terminal, msg.model)
            self.state_changed.emit()
        elif isinstance(msg, StateMsg):
            self._bind(sock, msg.sid)
            self.registry.upsert_state(msg.sid, msg.state)
            self.state_changed.emit()
        elif isinstance(msg, ByeMsg):
            self._drop(msg.sid)

    def _bind(self, sock: QLocalSocket, sid: str) -> None:
        self._sockets[sid] = sock
        self._sid_of[id(sock)] = sid

    def _on_disconnected(self, sock: QLocalSocket) -> None:
        sid = self._sid_of.pop(id(sock), None)
        self._buffers.pop(id(sock), None)
        if sid is not None:
            self._drop(sid)
        sock.deleteLater()

    def _drop(self, sid: str) -> None:
        self.registry.remove(sid)
        self._sockets.pop(sid, None)
        self.state_changed.emit()
        if self.registry.count() == 0:
            self.empty.emit()
