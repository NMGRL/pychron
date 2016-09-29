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
import collections

from pyface.qt import QtGui, QtCore
from pyface.qt.QtCore import Qt
from pyface.qt.QtGui import QIcon, QTreeWidgetItemIterator, QColor
from traits.api import Str, Bool, Event
from traitsui.api import TreeEditor as _TreeEditor
from traitsui.qt4.tree_editor import SimpleEditor as _SimpleEditor


class SimpleEditor(_SimpleEditor):
    refresh_icons = Event
    refresh_all_icons = Event
    collapse_all = Event
    expand_all = Event
    update = Event

    def init(self, parent):
        super(SimpleEditor, self).init(parent)
        self.sync_value(self.factory.refresh_icons, 'refresh_icons', 'from')
        self.sync_value(self.factory.refresh_all_icons, 'refresh_all_icons', 'from')
        self.sync_value(self.factory.collapse_all, 'collapse_all', 'from')
        self.sync_value(self.factory.expand_all, 'expand_all', 'from')
        self.sync_value(self.factory.update, 'update', 'from')

    def _collapse_all_fired(self):
        ctrl = self.control
        if ctrl is None:
            return

        ctrl.collapseAll()

        # ctrl.setExpanded(ctrl.rootIndex(), True)
        # print ctrl.isExpanded(ctrl.rootIndex())
        # for i,item in enumerate(QTreeWidgetItemIterator(ctrl)):
        #     if i>2:
        #         break
        #     item = item.value()
        #     try:
        #         self._expand_node(item)
        #         self._update_icon(item)
        #     except AttributeError, e:
        # print 'exception', e
        #     print i, item, item.text(0),

    def _expand_all_fired(self):

        ctrl = self.control
        if ctrl is None:
            return

        ctrl.expandAll()

        for item in QTreeWidgetItemIterator(ctrl):
            item = item.value()
            try:
                self._expand_node(item)
                self._update_icon(item)
            except AttributeError:
                pass

    def _update_fired(self):
        self.update_editor()

    def _refresh_all_icons_fired(self):
        ctrl = self.control
        if ctrl is None:
            return

        item = ctrl.currentItem()
        if item:
            self._refresh_icons(item)
            parent = item.parent()
            if parent:
                self._refresh_icons(parent)

    def _refresh_icons(self, tree):
        """
            recursively refresh the nodes
        """
        if tree:
            n = tree.childCount()
            if n:
                for i in range(n):
                    node = tree.child(i)
                    try:
                        self._update_icon(node)
                    except AttributeError:
                        continue

                    self._refresh_icons(node)

    def _refresh_icons_fired(self):
        ctrl = self.control
        if ctrl is None:
            return

        item = ctrl.currentItem()
        self._update_icon(item)

    def _get_icon(self, node, obj, is_expanded=False):
        if not self.factory.show_disabled and not obj.enabled:
            return QIcon()
        return super(SimpleEditor, self)._get_icon(node, obj, is_expanded)


class PipelineDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, tree, show_icons, *args, **kwargs):
        self._tree = tree
        self._show_icons = show_icons
        # self._size_map = {}
        self._size_map = collections.defaultdict(lambda: QtCore.QSize(1, 21))
        super(PipelineDelegate, self).__init__(*args, **kwargs)

    def sizeHint(self, option, index):
        """ returns area taken by the text. """
        # return self._size_map[self._tree.itemFromIndex(index)]
        return QtCore.QSize(1, 30)

    def paint(self, painter, option, index):
        hint = painter.renderHints()
        painter.setRenderHints(hint | QtGui.QPainter.Antialiasing)

        painter.setBrush(QColor(100, 100, 100, 100))
        painter.setPen(QColor(100, 100, 100, 100))
        # rect = option.rect
        # top = rect.top()
        # if index.row() > 0:
        #     top += 6*index.row()

        painter.drawRoundedRect(option.rect, 5, 5)

        item = self._tree.itemFromIndex(index)

        expanded, node, obj = item._py_data
        text = node.get_label(obj)

        if self._show_icons:
            iconwidth = 24  # FIXME: get width from actual
        else:
            iconwidth = 0

        status_color = node.get_status_color(obj)

        c = status_color.darker()
        painter.setPen(c)
        pen = painter.pen()
        pen.setWidth(2)
        painter.setPen(pen)

        # if draw_line:
        #     x = rect.left() + 6 + r2
        #     y = rect.bottom() - rect.height() / 2.  # status_color.setAlpha(150)
        #     painter.drawLine(x, y, x, y + rect.height())

        painter.setBrush(status_color)

        r = 15
        x = option.rect.left() + 5
        y = option.rect.top() + (option.rect.height() - r) / 2

        painter.drawEllipse(x, y, r, r)
        # painter.drawEllipse(rect.left() + 3, top+3.5, r, r)

        # draw text
        painter.setPen(Qt.black)
        font = painter.font()
        font.setPointSize(14)
        painter.setFont(font)

        painter.drawText(option.rect.left() + iconwidth,
                         # option.rect.top(),
                         option.rect.top() + option.rect.height() / 3,
                         option.rect.width() - iconwidth,
                         option.rect.height(),
                         QtCore.Qt.TextWordWrap, text)
        # Need to set the appropriate sizeHint of the item.
        # if self._size_map[item] != rect.size():
        #     self._size_map[item] = rect.size()
        #     do_later(self.sizeHintChanged.emit, index)


class _PipelineEditor(SimpleEditor):
    def init(self, parent):
        super(_PipelineEditor, self).init(parent)
        if self._tree:
            item = PipelineDelegate(self._tree, self.factory.show_icons)
            self._tree.setItemDelegate(item)

    def _create_item(self, nid, node, obj, index=None):
        """ Create  a new TreeWidgetItem as per word_wrap policy.

        Index is the index of the new node in the parent:
            None implies append the child to the end. """
        if index is None:
            cnid = QtGui.QTreeWidgetItem(nid)
        else:
            cnid = QtGui.QTreeWidgetItem()
            nid.insertChild(index, cnid)

        # cnid.setIcon(0, self._get_icon(node, object))
        cnid.setToolTip(0, node.get_tooltip(obj))
        self._set_column_labels(cnid, node.get_column_labels(obj))

        color = node.get_background(obj)
        if color:
            cnid.setBackground(0, self._get_brush(color))
        color = node.get_foreground(obj)
        if color:
            cnid.setForeground(0, self._get_brush(color))

        return cnid


class TreeEditor(_TreeEditor):
    refresh_icons = Str
    refresh_all_icons = Str
    show_disabled = Bool
    collapse_all = Str
    expand_all = Str
    update = Str

    def _get_simple_editor_class(self):
        """
        """
        return SimpleEditor


class PipelineEditor(TreeEditor):
    def _get_simple_editor_class(self):
        """
        """
        return _PipelineEditor

# ============= EOF =============================================
