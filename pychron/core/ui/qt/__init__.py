def _patch_qt_ignore_action():
    try:
        from pyface.qt import QtCore
    except Exception:
        return

    qt = QtCore.Qt
    if hasattr(qt, "IgnoreAction"):
        return

    ignore_action = None
    drop_action = getattr(qt, "DropAction", None)
    if drop_action is not None:
        ignore_action = getattr(drop_action, "IgnoreAction", None)
    if ignore_action is None:
        ignore_action = 0
    qt.IgnoreAction = ignore_action


_patch_qt_ignore_action()
