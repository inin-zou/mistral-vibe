from __future__ import annotations

import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget

_CAN_JOIN_ALL_SPACES = 1 << 0
_FULLSCREEN_AUXILIARY = 1 << 8
_ACTIVATION_POLICY_ACCESSORY = 1


def hide_dock_icon() -> None:
    if sys.platform != "darwin":
        return
    try:
        import AppKit
    except ImportError:
        return
    ns_application = getattr(AppKit, "NSApplication", None)
    if ns_application is None:
        return
    try:
        ns_application.sharedApplication().setActivationPolicy_(
            _ACTIVATION_POLICY_ACCESSORY
        )
    except Exception:
        return


def make_visible_on_all_spaces(widget: QWidget) -> None:
    if sys.platform != "darwin" or QGuiApplication.platformName() != "cocoa":
        return
    try:
        import objc
    except ImportError:
        return
    objc_object = getattr(objc, "objc_object", None)
    if objc_object is None:
        return
    handle = int(widget.winId())
    if handle == 0:
        return
    try:
        view = objc_object(c_void_p=handle)
        ns_window = view.window()
        if ns_window is None:
            return
        ns_window.setCollectionBehavior_(_CAN_JOIN_ALL_SPACES | _FULLSCREEN_AUXILIARY)
    except Exception:
        return
