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
        from traitsui.ui_traits import SequenceTypes
    except Exception:
        return

    if getattr(tm, "_pychron_color_patch", False):
        return

    orig_data = tm.TabularModel.data

    def _to_qcolor(color):
        if color is None:
            return None

        if isinstance(color, SequenceTypes):
            comps = list(color)
        elif hasattr(color, "rgba"):
            rgba = color.rgba() if callable(color.rgba) else color.rgba
            if isinstance(rgba, int):
                return QtGui.QColor(rgba)
            comps = list(rgba)
        elif all(hasattr(color, attr) for attr in ("red", "green", "blue")):
            def _component(value):
                return value() if callable(value) else value

            comps = [
                _component(getattr(color, "red")),
                _component(getattr(color, "green")),
                _component(getattr(color, "blue")),
            ]
            alpha = getattr(color, "alpha", None)
            if alpha is not None:
                comps.append(_component(alpha))
        else:
            try:
                return QtGui.QColor(color)
            except Exception:
                return None

        if comps and max(comps) <= 1:
            comps = [int(round(c * 255)) for c in comps]

        if len(comps) >= 4:
            return QtGui.QColor(comps[0], comps[1], comps[2], comps[3])
        if len(comps) == 3:
            return QtGui.QColor(comps[0], comps[1], comps[2])
        return None

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
