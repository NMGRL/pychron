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


def _patch_traitsui_tabular_colors():
    try:
        from pyface.qt import QtCore, QtGui
        from traitsui.qt import tabular_model as tm
    except Exception:
        return

    if getattr(tm, "_pychron_color_patch", False):
        return

    orig_data = tm.TabularModel.data
    from pychron.core.helpers.color_utils import coerce_qcolor

    def _to_qcolor(color):
        return coerce_qcolor(color, qcolor_class=QtGui.QColor)

    def _data(self, mi, role):
        if role in (
            QtCore.Qt.ItemDataRole.BackgroundRole,
            QtCore.Qt.ItemDataRole.ForegroundRole,
        ):
            editor = self._editor
            adapter = editor.adapter
            obj, name = editor.object, editor.name
            row, column = mi.row(), mi.column()
            if role == QtCore.Qt.ItemDataRole.BackgroundRole:
                color = adapter.get_bg_color(obj, name, row, column)
            else:
                color = adapter.get_text_color(obj, name, row, column)
            if color is not None:
                q_color = _to_qcolor(color)
                if q_color is not None:
                    return QtGui.QBrush(q_color)
        return orig_data(self, mi, role)

    tm.TabularModel.data = _data
    tm._pychron_color_patch = True


_patch_traitsui_tabular_colors()


def _patch_traitsui_range_spin_ints():
    try:
        from traitsui.qt import range_editor as re
    except Exception:
        return

    if getattr(re, "_pychron_range_spin_patch", False):
        return

    orig_init = re.SimpleSpinEditor.init

    def _init(self, parent):
        factory = self.factory
        if not factory.low_name:
            self.low = factory.low
        if not factory.high_name:
            self.high = factory.high
        self.sync_value(factory.low_name, "low", "from")
        self.sync_value(factory.high_name, "high", "from")
        low = self.low
        high = self.high

        self.control = re.QtGui.QSpinBox()
        try:
            self.control.setMinimum(int(low))
        except Exception:
            self.control.setMinimum(0)
        try:
            self.control.setMaximum(int(high))
        except Exception:
            self.control.setMaximum(100)
        self.control.setValue(int(self.value))
        self.control.valueChanged.connect(self.update_object)
        if not factory.auto_set:
            self.control.setKeyboardTracking(False)
        self.set_tooltip()

    re.SimpleSpinEditor.init = _init
    re._pychron_range_spin_patch = True


_patch_traitsui_range_spin_ints()
