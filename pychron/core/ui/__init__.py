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
def set_qt():
    set_toolkit("qt4")
