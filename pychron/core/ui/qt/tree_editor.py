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

from PySide import QtGui, QtCore
from PySide.QtCore import Qt
from PySide.QtGui import QIcon, QTreeWidgetItemIterator, QColor
from traits.api import Str, Bool, Event
from traitsui.api import TreeEditor as _TreeEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================


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
        item = ctrl.currentItem()
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
        item = ctrl.currentItem()
        self._update_icon(item)

    def _get_icon(self, node, obj, is_expanded=False):
        if not self.factory.show_disabled and not obj.enabled:
            return QIcon()
        return super(SimpleEditor, self)._get_icon(node, obj, is_expanded)


class _PipelineEditor(SimpleEditor):
    class PipelineDelegate(QtGui.QStyledItemDelegate):
        def __init__(self, *args, **kwargs):
            self.size_map = collections.defaultdict(lambda: QtCore.QSize(1, 21))
            QtGui.QStyledItemDelegate.__init__(self, *args, **kwargs)

        def sizeHint(self, option, index):
            """ returns area taken by the text. """
            return self.size_map[self.editor._tree.itemFromIndex(index)]

        def paint(self, painter, option, index):
            QtGui.QStyledItemDelegate.paint(self, painter, option, index)

            # print idx.row(), option
            # painter.begin()
            # painter.draw(0,0,'Fasdfe'
            # painter.setPen(QColor('white'))
            hint = painter.renderHints()
            painter.setRenderHints(hint | QtGui.QPainter.Antialiasing)

            painter.setBrush(QColor(100, 100, 100, 100))
            painter.setPen(QColor(100, 100, 100, 100))
            rect = option.rect
            painter.drawRoundedRect(rect, 5, 5)

            item = self.editor._tree.itemFromIndex(index)
            # print index, self.editor._tree.model().rowCount()
            draw_line = index.row() != self.editor._tree.model().rowCount() - 1

            expanded, node, object = self.editor._get_node_data(item)
            text = node.get_label(object)

            if self.editor.factory.show_icons:
                iconwidth = 24  # FIXME: get width from actual
            else:
                iconwidth = 0

            offset = 20
            r = 13  # rect.height() - 10
            r2 = r / 2.
            status_color = node.get_status_color(object)

            painter.setPen(status_color.darker())
            pen = painter.pen()
            pen.setWidth(2)
            painter.setPen(pen)

            if draw_line:
                x = rect.left() + 6 + r2
                y = rect.bottom() - rect.height() / 2.  # status_color.setAlpha(150)
                painter.drawLine(x, y, x, y + rect.height())

            painter.setBrush(status_color)
            painter.drawEllipse(rect.left() + 5, rect.bottom() - r - 4, r, r)

            # draw text
            painter.setPen(Qt.black)
            rect = painter.drawText(rect.left() + iconwidth + offset,
                                    rect.top() + rect.height() / 3.,
                                    rect.width() - iconwidth,
                                    rect.height(),
                                    QtCore.Qt.TextWordWrap, text)
            if self.size_map[item] != rect.size():
                size = rect.size()
                size.setHeight(size.height() + 10)
                self.size_map[item] = size
                self.sizeHintChanged.emit(index)

    def _create_item(self, nid, node, object, index=None):
        """ Create  a new TreeWidgetItem as per word_wrap policy.

        Index is the index of the new node in the parent:
            None implies append the child to the end. """
        if index is None:
            cnid = QtGui.QTreeWidgetItem(nid)
        else:
            cnid = QtGui.QTreeWidgetItem()
            nid.insertChild(index, cnid)

        item = self.PipelineDelegate()
        item.editor = self
        self._tree.setItemDelegate(item)

        # cnid.setIcon(0, self._get_icon(node, object))
        cnid.setToolTip(0, node.get_tooltip(object))
        self._set_column_labels(cnid, node.get_column_labels(object))

        color = node.get_background(object)
        if color: cnid.setBackground(0, self._get_brush(color))
        color = node.get_foreground(object)
        if color: cnid.setForeground(0, self._get_brush(color))

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
