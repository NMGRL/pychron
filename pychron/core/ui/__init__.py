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

    if not hasattr(QDialog, "exec_") and hasattr(QDialog, "exec"):
        QDialog.exec_ = QDialog.exec


def set_qt():
    set_toolkit("qt4")
    _patch_qdialog_exec()
