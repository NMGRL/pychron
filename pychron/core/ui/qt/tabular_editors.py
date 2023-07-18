# ===============================================================================
# Copyright 2014 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
from __future__ import absolute_import

from pyface.qt.QtCore import QRegExp, Qt
from pyface.qt.QtGui import (
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QLineEdit,
    QCheckBox,
    QSortFilterProxyModel,
)
from traits.trait_types import Str, Bool, Any, Int

from pychron.core.ui.qt.tabular_editor import (
    myTabularEditor,
    _TableView,
    _TabularEditor,
)
from pychron.envisage.resources import icon


# class _myFilterTableView(_TableView):
#     pass
# def sizeHint(self):
# sh = QtGui.QTableView.sizeHint(self)
# print sh, sh.width(), sh.height()
#
#     width = 0
#     for column in xrange(len(self._editor.adapter.columns)):
#         width += self.sizeHintForColumn(column)
#     sh.setWidth(width)
#
#     return sh


class _FilterTableView(_TableView):
    def __init__(self, editor, layout=None, *args, **kw):
        super(_FilterTableView, self).__init__(editor, *args, **kw)

        # vlayout = QVBoxLayout()
        # layout.setSpacing(2)
        # self.table = table = _myFilterTableView(parent)
        # self.table = table = _TableView(parent)

        # table.setSizePolicy(QSizePolicy.Fixed,
        # QSizePolicy.Fixed)
        # table.setMinimumHeight(100)
        # table.setMaximumHeight(50)
        # table.setFixedHeight(50)
        # table.setFixedWidth(50)

        hl = QHBoxLayout()
        self.button = button = QPushButton()
        button.setIcon(icon("delete").create_icon())
        button.setEnabled(False)
        button.setFlat(True)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        button.setFixedWidth(15)
        button.setFixedHeight(15)

        self.text = text = QLineEdit()
        hl.addWidget(text)
        hl.addWidget(button)
        # vlayout.addLayout(hl)

        layout.addLayout(hl)
        # layout.addWidget(self)
        # layout.addWidget(table)
        # self.setLayout(layout)
        # print self.layout()
        # def setSizePolicy(self, *args, **kwargs):
        # super(_FilterTableView, self).setSizePolicy(*args, **kwargs)
        # print args, kwargs

    def get_text(self):
        return self.text.text()

    def __getattr__(self, item):
        return getattr(self.table, item)


class _EnableFilterTableView(_FilterTableView):
    def __init__(self, editor, layout=None, *args, **kw):
        super(_FilterTableView, self).__init__(editor, *args, **kw)
        # layout = QVBoxLayout()
        # layout.setSpacing(1)
        # self.table = table = _TableView(parent)

        hl = QHBoxLayout()
        # hl.setSpacing(10)
        #
        self.button = button = QPushButton()
        button.setIcon(icon("delete").create_icon())
        button.setEnabled(False)
        button.setFlat(True)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.setFixedWidth(15)
        button.setFixedHeight(15)

        self.text = text = QLineEdit()
        self.cb = cb = QCheckBox()
        #
        text.setEnabled(False)
        button.setEnabled(False)
        # table.setEnabled(False)
        # cb.setSizePolicy(QSizePolicy.Fixed,
        # QSizePolicy.Fixed)
        # cb.setFixedWidth(20)
        # cb.setFixedHeight(20)
        #
        hl.addWidget(cb)
        hl.addWidget(text)
        hl.addWidget(button)
        layout.addLayout(hl)
        # # hl.addStretch()
        # layout.addLayout(hl)
        # layout.addWidget(table)
        # layout.setSpacing(1)
        # self.setLayout(layout)


class mQSortFilterProxyModel(QSortFilterProxyModel):
    use_fuzzy = Bool

    def lessThan(self, left, right):
        if self.use_fuzzy:
            return self._fuzzy_sort(left, right)
        else:
            return super(mQSortFilterProxyModel, self).lessThan(left, right)

    def _fuzzy_sort(self, left, right):
        sm = self.sourceModel()
        leftData = sm.data(left)
        rightData = sm.data(right)
        regex = self.filterRegExp()

        lp = regex.indexIn(leftData)
        lg = regex.matchedLength()

        rp = regex.indexIn(rightData)
        rg = regex.matchedLength()

        if lg == rg:
            if lp == rp:
                return leftData < rightData
            else:
                return lp < rp
        else:
            return lg < rg


class _FilterTabularEditor(_TabularEditor):
    widget_factory = _FilterTableView
    proxyModel = Any
    use_fuzzy = Bool

    def init(self, parent):
        super(_FilterTabularEditor, self).init(parent)

        self.control.text.textChanged.connect(self.on_text_change)
        self.control.button.clicked.connect(self.on_action)
        self.proxyModel = proxyModel = mQSortFilterProxyModel()
        # print 'afasd',self.use_fuzzy
        self.use_fuzzy = self.factory.use_fuzzy
        proxyModel.setFilterKeyColumn(self.factory.column_index)
        proxyModel.use_fuzzy = self.use_fuzzy
        proxyModel.setSourceModel(self.model)
        self.control.setSortingEnabled(True)
        self.control.setModel(proxyModel)

        if self.factory and self.factory.multi_select:
            slot = self._on_rows_selection
        else:
            slot = self._on_row_selection
        # signal = 'selectionChanged(QItemSelection,QItemSelection)'
        # QtCore.QObject.connect(self.control.selectionModel(),
        #                        QtCore.SIGNAL(signal), slot)
        self.control.selectionModel().selectionChanged.connect(slot)

    def _scroll_to_row_changed(self, row):
        scroll_hint = self.scroll_to_row_hint_map.get(
            self.factory.scroll_to_row_hint, self.control.PositionAtCenter
        )
        if self.proxyModel:
            self.control.scrollTo(self.proxyModel.index(row, 0), scroll_hint)

    def on_action(self):
        self.control.text.setText("")

    def on_text_change(self):
        ft = self.control.get_text()
        if self.use_fuzzy:
            reg = QRegExp(".*".join(ft), Qt.CaseInsensitive)
        else:
            reg = QRegExp("^{}".format(ft), Qt.CaseInsensitive)

        self.proxyModel.setFilterRegExp(reg)
        self.control.sortByColumn(0, self.proxyModel.sortOrder())
        self.control.button.setEnabled(bool(ft))

    def _on_row_selection(self, added, removed):
        """Handle the row selection being changed."""
        self._no_update = True
        try:
            indexes = self.control.selectionModel().selectedRows()
            index = self.proxyModel.mapToSource(indexes[0])

            if index:
                self.selected_row = index.row()
                self.selected = self.adapter.get_item(
                    self.object, self.name, self.selected_row
                )
            else:
                self.selected_row = -1
                self.selected = None
        finally:
            self._no_update = False

    def _on_rows_selection(self, added, removed):
        """Handle the rows selection being changed."""
        self._no_update = True
        try:
            indexes = self.control.selectionModel().selectedRows()
            selected_rows = []
            selected = []
            for index in indexes:
                index = self.proxyModel.mapToSource(index)
                row = index.row()
                selected_rows.append(row)
                selected.append(self.adapter.get_item(self.object, self.name, row))
            self.multi_selected_rows = selected_rows
            self.multi_selected = selected
        finally:
            self._no_update = False


class _EnableFilterTabularEditor(_FilterTabularEditor):
    widget_factory = _EnableFilterTableView
    enabled_cb = Bool

    def init(self, parent):
        super(_EnableFilterTabularEditor, self).init(parent)

        self.control.cb.stateChanged.connect(self.on_cb)
        if self.factory.enabled_cb:
            self.sync_value(self.factory.enabled_cb, "enabled_cb", "both")

    def _enabled_cb_changed(self, new):
        self.control.text.setEnabled(new)
        if self.control.get_text():
            self.control.button.setEnabled(new)
        self.control.setEnabled(new)
        self.control.cb.setChecked(new)

    def on_cb(self, v):
        v = bool(v)
        self.enabled_cb = v


class FilterTabularEditor(myTabularEditor):
    enabled_cb = Str
    use_fuzzy = Bool
    column_index = Int(0)

    def _get_klass(self):
        if self.enabled_cb:
            return _EnableFilterTabularEditor
        else:
            return _FilterTabularEditor


# ============= EOF =============================================
