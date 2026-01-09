from __future__ import absolute_import


def set_toolkit(name):
    from traits.etsconfig.etsconfig import ETSConfig

    ETSConfig.toolkit = name


def _patch_qdialog_exec():
    try:
        from pyface.qt.QtWidgets import QDialog
    except Exception:
        try:
            from pyface.qt.QtGui import QDialog
        except Exception:
            return

    if hasattr(QDialog, "exec"):
        def _exec_(self):
            return self.exec()

        QDialog.exec_ = _exec_

_patch_qdialog_exec()


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
def set_qt():
    set_toolkit("qt4")
