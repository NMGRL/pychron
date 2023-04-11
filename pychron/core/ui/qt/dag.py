# ===============================================================================
# Copyright 2019 ross
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

# this code is adapted from git-cola
# Copyright (C) 2007-2017 David Aguilar and contributors
# https://github.com/git-cola/git-cola

import collections
import itertools
import sys
from operator import attrgetter

from pyface.qt import QtGui, QtCore
from pyface.qt.QtCore import Qt
from pyface.qt.QtGui import QApplication, QGraphicsView, QGraphicsItem, QGraphicsScene

maxsize = sys.maxsize

Y_OFF = 12
X_OFF = 18


def get(widget):
    """Query a widget for its python value"""
    if hasattr(widget, "isChecked"):
        value = widget.isChecked()
    elif hasattr(widget, "value"):
        value = widget.value()
    elif hasattr(widget, "text"):
        value = widget.text()
    elif hasattr(widget, "toPlainText"):
        value = widget.toPlainText()
    elif hasattr(widget, "sizes"):
        value = widget.sizes()
    elif hasattr(widget, "date"):
        value = widget.date().toString(Qt.ISODate)
    else:
        value = None
    return value


class Cache(object):
    _label_font = None

    @classmethod
    def label_font(cls):
        font = cls._label_font
        if font is None:
            font = cls._label_font = QApplication.font()
            font.setPointSize(6)
        return font


class CommitGraphicsItem(QGraphicsItem):
    item_type = QGraphicsItem.UserType + 2
    commit_radius = 12.0
    merge_radius = 18.0

    item_shape = QtGui.QPainterPath()
    item_shape.addRect(
        commit_radius / -2.0, commit_radius / -2.0, commit_radius, commit_radius
    )
    item_bbox = item_shape.boundingRect()

    inner_rect = QtGui.QPainterPath()
    inner_rect.addRect(
        commit_radius / -2.0 + 2.0,
        commit_radius / -2.0 + 2.0,
        commit_radius - 4.0,
        commit_radius - 4.0,
    )
    inner_rect = inner_rect.boundingRect()

    commit_color = QtGui.QColor(Qt.white)
    outline_color = commit_color.darker()
    merge_color = QtGui.QColor(Qt.lightGray)

    commit_selected_color = QtGui.QColor(Qt.green)
    selected_outline_color = commit_selected_color.darker()

    commit_pen = QtGui.QPen()
    commit_pen.setWidth(1)
    commit_pen.setColor(outline_color)

    text_pen = QtGui.QPen()
    text_pen.setColor(QtGui.QColor(Qt.darkGray))
    text_pen.setWidth(1)

    def __init__(
        self,
        commit,
        notifier,
        selectable=QGraphicsItem.ItemIsSelectable,
        cursor=Qt.PointingHandCursor,
        xpos=commit_radius / 2.0 + 1.0,
        cached_commit_color=commit_color,
        cached_merge_color=merge_color,
    ):
        QGraphicsItem.__init__(self)

        self.commit = commit
        self.notifier = notifier
        self.selected = False

        self.setZValue(0)
        self.setFlag(selectable)
        self.setCursor(cursor)
        self.setToolTip(commit.oid[:12] + ": " + commit.summary + ":" + commit.authdate)

        if commit.tags:
            self.label = label = Label(commit)
            label.setParentItem(self)
            label.setPos(xpos + 1, -self.commit_radius / 2.0)
        else:
            self.label = None

        if len(commit.parents) > 1:
            self.brush = cached_merge_color
        else:
            self.brush = cached_commit_color

        self.pressed = False
        self.dragged = False

        self.edges = {}

    # def blockSignals(self, blocked):
    #     self.notifier.notification_enabled = not blocked

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            # Broadcast selection to other widgets
            selected_items = self.scene().selectedItems()
            commits = [item.commit for item in selected_items]
            self.scene().parent().set_selecting(True)
            self.notifier.selected_commits = commits
            # self.notifier.notify_observers(diff.COMMITS_SELECTED, commits)
            self.scene().parent().set_selecting(False)

            # Cache the pen for use in paint()
            if value:
                self.brush = self.commit_selected_color
                color = self.selected_outline_color
            else:
                if len(self.commit.parents) > 1:
                    self.brush = self.merge_color
                else:
                    self.brush = self.commit_color
                color = self.outline_color
            commit_pen = QtGui.QPen()
            commit_pen.setWidth(1.0)
            commit_pen.setColor(color)
            self.commit_pen = commit_pen

        return QGraphicsItem.itemChange(self, change, value)

    def type(self):
        return self.item_type

    def boundingRect(self):
        return self.item_bbox

    def shape(self):
        return self.item_shape

    def paint(self, painter, option, _widget, cache=Cache):
        # Do not draw outside the exposed rect
        # painter.setClipRect(option.exposedRect)

        # Draw ellipse
        painter.setPen(self.commit_pen)
        painter.setBrush(self.brush)
        painter.drawEllipse(self.inner_rect)

    def mousePressEvent(self, event):
        QGraphicsItem.mousePressEvent(self, event)
        self.pressed = True
        self.selected = self.isSelected()

    def mouseMoveEvent(self, event):
        if self.pressed:
            self.dragged = True
        QGraphicsItem.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        QGraphicsItem.mouseReleaseEvent(self, event)
        if not self.dragged and self.selected and event.button() == Qt.LeftButton:
            return
        self.pressed = False
        self.dragged = False


class Label(QGraphicsItem):
    item_type = QGraphicsItem.UserType + 3

    head_color = QtGui.QColor(Qt.green)
    other_color = QtGui.QColor(Qt.white)
    remote_color = QtGui.QColor(Qt.yellow)

    head_pen = QtGui.QPen()
    head_pen.setColor(head_color.darker().darker())
    head_pen.setWidth(1)

    text_pen = QtGui.QPen()
    text_pen.setColor(QtGui.QColor(Qt.darkGray))
    text_pen.setWidth(1)

    alpha = 180
    head_color.setAlpha(alpha)
    other_color.setAlpha(alpha)
    remote_color.setAlpha(alpha)

    border = 2
    item_spacing = 5
    text_offset = 1

    def __init__(self, commit):
        QGraphicsItem.__init__(self)
        self.setZValue(-1)
        self.commit = commit

    def type(self):
        return self.item_type

    def boundingRect(self, cache=Cache):
        QPainterPath = QtGui.QPainterPath
        QRectF = QtCore.QRectF

        width = 72
        height = 18
        current_width = 0
        spacing = self.item_spacing
        border = self.border + self.text_offset  # text offset=1 in paint()

        font = cache.label_font()
        item_shape = QPainterPath()

        base_rect = QRectF(0, 0, width, height)
        base_rect = base_rect.adjusted(-border, -border, border, border)
        item_shape.addRect(base_rect)

        for tag in self.commit.tags:
            text_shape = QPainterPath()
            text_shape.addText(current_width, 0, font, tag)
            text_rect = text_shape.boundingRect()
            box_rect = text_rect.adjusted(-border, -border, border, border)
            item_shape.addRect(box_rect)
            current_width = item_shape.boundingRect().width() + spacing

        return item_shape.boundingRect()

    def paint(self, painter, _option, _widget, cache=Cache):
        # Draw tags and branches
        font = cache.label_font()
        painter.setFont(font)

        current_width = 0
        border = self.border
        offset = self.text_offset
        spacing = self.item_spacing
        QRectF = QtCore.QRectF

        HEAD = "HEAD"
        remotes_prefix = "remotes/"
        tags_prefix = "tags/"
        heads_prefix = "heads/"
        remotes_len = len(remotes_prefix)
        tags_len = len(tags_prefix)
        heads_len = len(heads_prefix)

        for tag in self.commit.tags:
            if tag == HEAD:
                painter.setPen(self.text_pen)
                painter.setBrush(self.remote_color)
            elif tag.startswith(remotes_prefix):
                tag = tag[remotes_len:]
                painter.setPen(self.text_pen)
                painter.setBrush(self.other_color)
            elif tag.startswith(tags_prefix):
                tag = tag[tags_len:]
                painter.setPen(self.text_pen)
                painter.setBrush(self.remote_color)
            elif tag.startswith(heads_prefix):
                tag = tag[heads_len:]
                painter.setPen(self.head_pen)
                painter.setBrush(self.head_color)
            else:
                painter.setPen(self.text_pen)
                painter.setBrush(self.other_color)

            text_rect = painter.boundingRect(
                QRectF(current_width, 0, 0, 0), Qt.TextSingleLine, tag
            )
            box_rect = text_rect.adjusted(-offset, -offset, offset, offset)

            painter.drawRoundedRect(box_rect, border, border)
            painter.drawText(text_rect, Qt.TextSingleLine, tag)
            current_width += text_rect.width() + spacing


class Edge(QGraphicsItem):
    item_type = QGraphicsItem.UserType + 1

    def __init__(self, source, dest):
        QGraphicsItem.__init__(self)

        self.setAcceptedMouseButtons(Qt.NoButton)
        self.source = source
        self.dest = dest
        self.commit = source.commit
        self.setZValue(-2)

        self.recompute_bound()
        self.path = None
        self.path_valid = False

        # Choose a new color for new branch edges
        if self.source.x() < self.dest.x():
            color = EdgeColor.cycle()
            line = Qt.SolidLine
        elif self.source.x() != self.dest.x():
            color = EdgeColor.current()
            line = Qt.SolidLine
        else:
            color = EdgeColor.current()
            line = Qt.SolidLine

        self.pen = QtGui.QPen(color, 2.0, line, Qt.SquareCap, Qt.RoundJoin)

    def recompute_bound(self):
        dest_pt = CommitGraphicsItem.item_bbox.center()

        self.source_pt = self.mapFromItem(self.source, dest_pt)
        self.dest_pt = self.mapFromItem(self.dest, dest_pt)
        self.line = QtCore.QLineF(self.source_pt, self.dest_pt)

        width = self.dest_pt.x() - self.source_pt.x()
        height = self.dest_pt.y() - self.source_pt.y()
        rect = QtCore.QRectF(self.source_pt, QtCore.QSizeF(width, height))
        self.bound = rect.normalized()

    def commits_were_invalidated(self):
        self.recompute_bound()
        self.prepareGeometryChange()
        # The path should not be recomputed immediately because just small part
        # of DAG is actually shown at same time. It will be recomputed on
        # demand in course of 'paint' method.
        self.path_valid = False
        # Hence, just queue redrawing.
        self.update()

    # Qt overrides
    def type(self):
        return self.item_type

    def boundingRect(self):
        return self.bound

    def recompute_path(self):
        QRectF = QtCore.QRectF
        QPointF = QtCore.QPointF

        arc_rect = 8
        connector_length = -Y_OFF / 4.0

        path = QtGui.QPainterPath()

        if self.source.x() == self.dest.x():
            path.moveTo(self.source.x(), self.source.y())
            path.lineTo(self.dest.x(), self.dest.y())
        else:
            if self.source.y() - self.dest.y() > 24:
                dev = (self.dest.x() - self.source.x()) / 2
                p1 = QPointF(self.source.x(), self.source.y())
                p2 = QPointF(self.source.x() + dev, self.source.y())
                p3 = QPointF(self.source.x() + dev, self.dest.y() + 12)
                p4 = QPointF(self.dest.x(), self.dest.y())
                path.moveTo(p1)
                path.lineTo(p2)
                path.lineTo(p3)
                path.lineTo(p4)
            else:
                sp = QPointF(self.source.x(), self.source.y())
                dp = QPointF(self.dest.x(), self.dest.y())
                path.moveTo(sp)
                path.lineTo(dp)

            # # Define points starting from source
            # point1 = QPointF(self.source.x(), self.source.y())
            # point2 = QPointF(point1.x(), point1.y() - connector_length)
            # point3 = QPointF(point2.x() + arc_rect, point2.y() - arc_rect)
            #
            # # Define points starting from dest
            # point4 = QPointF(self.dest.x(), self.dest.y())
            # point5 = QPointF(point4.x(), point3.y() - arc_rect)
            # point6 = QPointF(point5.x() - arc_rect, point5.y() + arc_rect)
            #
            # start_angle_arc1 = 180
            # span_angle_arc1 = 90
            # start_angle_arc2 = 90
            # span_angle_arc2 = -90
            #
            # # If the dest is at the left of the source, then we
            # # need to reverse some values
            # if self.source.x() > self.dest.x():
            #     point3 = QPointF(point2.x() - arc_rect, point3.y())
            #     point6 = QPointF(point5.x() + arc_rect, point6.y())
            #
            #     span_angle_arc1 = 90
            #
            # path.moveTo(point1)
            # path.lineTo(point2)
            # path.arcTo(QRectF(point2, point3),
            #            start_angle_arc1, span_angle_arc1)
            # path.lineTo(point6)
            # path.arcTo(QRectF(point6, point5),
            #            start_angle_arc2, span_angle_arc2)
            # path.lineTo(point4)

        self.path = path
        self.path_valid = True

    def paint(self, painter, _option, _widget):
        if not self.path_valid:
            self.recompute_path()
        painter.setPen(self.pen)
        painter.drawPath(self.path)


class EdgeColor(object):
    """An edge color factory"""

    current_color_index = 0
    colors = [
        QtGui.QColor(Qt.red),
        QtGui.QColor(Qt.green),
        QtGui.QColor(Qt.blue),
        QtGui.QColor(Qt.black),
        QtGui.QColor(Qt.darkRed),
        QtGui.QColor(Qt.darkGreen),
        QtGui.QColor(Qt.darkBlue),
        QtGui.QColor(Qt.cyan),
        QtGui.QColor(Qt.magenta),
        # Orange; Qt.yellow is too low-contrast
        # qtutils.rgba(0xff, 0x66, 0x00),
        QtGui.QColor(Qt.gray),
        QtGui.QColor(Qt.darkCyan),
        QtGui.QColor(Qt.darkMagenta),
        QtGui.QColor(Qt.darkYellow),
        QtGui.QColor(Qt.darkGray),
    ]

    @classmethod
    def cycle(cls):
        cls.current_color_index += 1
        cls.current_color_index %= len(cls.colors)
        color = cls.colors[cls.current_color_index]
        color.setAlpha(128)
        return color

    @classmethod
    def current(cls):
        return cls.colors[cls.current_color_index]

    @classmethod
    def reset(cls):
        cls.current_color_index = 0


class DAGraphView(QGraphicsView):
    x_adjust = int(CommitGraphicsItem.commit_radius) + 10
    y_adjust = int(CommitGraphicsItem.commit_radius) + 10

    x_off = -X_OFF
    y_off = -Y_OFF

    def __init__(self, context, notifier, parent):
        QGraphicsView.__init__(self, parent)

        self.context = context
        self.columns = {}
        self.selection_list = []
        self.menu_actions = None
        self.notifier = notifier
        self.commits = []
        self.items = {}
        self.mouse_start = [0, 0]
        self.saved_matrix = self.transform()
        self.max_column = 0
        self.min_column = 0
        self.frontier = {}
        self.tagged_cells = set()

        self.x_start = 24
        self.x_min = 24
        self.x_offsets = collections.defaultdict(lambda: self.x_min)

        self.is_panning = False
        self.pressed = False
        self.selecting = False
        self.last_mouse = [0, 0]
        self.zoom = 0

        scene = QGraphicsScene(self)
        scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.setScene(scene)

    def selected_items(self):
        return self.scene().selectedItems()

    def set_initial_view(self):
        items = []
        selected = self.selected_items()
        if selected:
            items.extend(selected)

        if not selected and self.commits:
            commit = self.commits[0]
            items.append(self.items[commit.oid])

        self.setSceneRect(self.scene().itemsBoundingRect())
        self.fit_view_to_items(items)

    def fit_view_to_items(self, items):
        if not items:
            rect = self.scene().itemsBoundingRect()
        else:
            x_min = y_min = maxsize
            x_max = y_max = -maxsize

            for item in items:
                pos = item.pos()
                x = pos.x()
                y = pos.y()
                x_min = min(x_min, x)
                x_max = max(x_max, x)
                y_min = min(y_min, y)
                y_max = max(y_max, y)

            rect = QtCore.QRectF(x_min, y_min, abs(x_max - x_min), abs(y_max - y_min))

        x_adjust = abs(DAGraphView.x_adjust)
        y_adjust = abs(DAGraphView.y_adjust)

        count = max(2.0, 10.0 - len(items) / 2.0)
        y_offset = int(y_adjust * count)
        x_offset = int(x_adjust * count)

        rect.setX(rect.x() - x_offset // 2)
        rect.setY(rect.y() - y_adjust // 2)
        rect.setHeight(rect.height() + y_offset)
        rect.setWidth(rect.width() + x_offset)

        self.fitInView(rect, Qt.KeepAspectRatio)
        self.scene().invalidate()

    def save_selection(self, event):
        if event.button() != Qt.LeftButton:
            return
        elif Qt.ShiftModifier != event.modifiers():
            return
        self.selection_list = self.selected_items()

    def restore_selection(self, event):
        if Qt.ShiftModifier != event.modifiers():
            return
        for item in self.selection_list:
            item.setSelected(True)

    def handle_event(self, event_handler, event):
        self.save_selection(event)
        event_handler(self, event)
        self.restore_selection(event)
        self.update()

    def set_selecting(self, selecting):
        self.selecting = selecting
        if not selecting:
            self.scene().invalidate()

    def clear(self):
        self.scene().clear()
        self.items.clear()
        self.commits = []

    def set_commits(self, cs):
        EdgeColor.reset()

        self.commits = cs = [ci for ci in cs if ci.oid]
        scene = self.scene()
        for commit in cs:
            item = CommitGraphicsItem(commit, self.notifier)
            self.items[commit.oid] = item

            for ref in commit.tags:
                self.items[ref] = item
            scene.addItem(item)
            # print(commit.oid, commit.parents, commit.children)

        self.layout_commits()
        self.link(cs)
        self.set_initial_view()

    def link(self, commits):
        """Create edges linking commits with their parents"""
        scene = self.scene()
        for commit in commits:
            try:
                commit_item = self.items[commit.oid]
            except KeyError:
                # TODO - Handle truncated history viewing
                continue

            for parent in reversed(commit.parents):
                try:
                    parent_item = self.items[parent.oid]
                except KeyError:
                    # print('invalid parent', parent.oid, self.items.keys())
                    # TODO - Handle truncated history viewing
                    continue
                try:
                    edge = parent_item.edges[commit.oid]
                except KeyError:
                    edge = Edge(parent_item, commit_item)
                else:
                    continue

                parent_item.edges[commit.oid] = edge
                commit_item.edges[parent.oid] = edge
                scene.addItem(edge)

    def layout_commits(self):
        positions = self.position_nodes()

        # Each edge is accounted in two commits. Hence, accumulate invalid
        # edges to prevent double edge invalidation.
        invalid_edges = set()

        for oid, (x, y) in positions.items():
            item = self.items[oid]

            pos = item.pos()
            if pos != (x, y):
                item.setPos(x, y)

                for edge in item.edges.values():
                    invalid_edges.add(edge)

        for edge in invalid_edges:
            edge.commits_were_invalidated()

    def reset_columns(self):
        # Some children of displayed commits might not be accounted in
        # 'commits' list. It is common case during loading of big graph.
        # But, they are assigned a column that must be reseted. Hence, use
        # depth-first traversal to reset all columns assigned.
        for node in self.commits:
            if node.column is None:
                continue
            stack = [node]
            while stack:
                node = stack.pop()
                node.column = None
                for child in node.children:
                    if child.column is not None:
                        stack.append(child)

        self.columns = {}
        self.max_column = 0
        self.min_column = 0

    def reset_rows(self):
        self.frontier = {}
        self.tagged_cells = set()

    def declare_column(self, column):
        if self.frontier:
            # Align new column frontier by frontier of nearest column. If all
            # columns were left then select maximum frontier value.
            if not self.columns:
                self.frontier[column] = max(list(self.frontier.values()))
                return
            # This is heuristic that mostly affects roots. Note that the
            # frontier values for fork children will be overridden in course of
            # propagate_frontier.
            for offset in itertools.count(1):
                for c in [column + offset, column - offset]:
                    if c not in self.columns:
                        # Column 'c' is not occupied.
                        continue
                    try:
                        frontier = self.frontier[c]
                    except KeyError:
                        # Column 'c' was never allocated.
                        continue

                    frontier -= 1
                    # The frontier of the column may be higher because of
                    # tag overlapping prevention performed for previous head.
                    try:
                        if self.frontier[column] >= frontier:
                            break
                    except KeyError:
                        pass

                    self.frontier[column] = frontier
                    break
                else:
                    continue
                break
        else:
            # First commit must be assigned 0 row.
            self.frontier[column] = 0

    def alloc_column(self, column=0):
        columns = self.columns
        # First, look for free column by moving from desired column to graph
        # center (column 0).
        for c in range(column, 0, -1 if column > 0 else 1):
            if c not in columns:
                if c > self.max_column:
                    self.max_column = c
                elif c < self.min_column:
                    self.min_column = c
                break
        else:
            # If no free column was found between graph center and desired
            # column then look for free one by moving from center along both
            # directions simultaneously.
            for c in itertools.count(0):
                if c not in columns:
                    if c > self.max_column:
                        self.max_column = c
                    break
                c = -c
                if c not in columns:
                    if c < self.min_column:
                        self.min_column = c
                    break
        self.declare_column(c)
        columns[c] = 1
        return c

    def alloc_cell(self, column, tags):
        # Get empty cell from frontier.
        cell_row = self.frontier[column]

        if tags:
            # Prevent overlapping of tag with cells already allocated a row.
            if self.x_off > 0:
                can_overlap = list(range(column + 1, self.max_column + 1))
            else:
                can_overlap = list(range(column - 1, self.min_column - 1, -1))
            for c in can_overlap:
                frontier = self.frontier[c]
                if frontier > cell_row:
                    cell_row = frontier

        # Avoid overlapping with tags of commits at cell_row.
        if self.x_off > 0:
            can_overlap = list(range(self.min_column, column))
        else:
            can_overlap = list(range(self.max_column, column, -1))
        for cell_row in itertools.count(cell_row):
            for c in can_overlap:
                if (c, cell_row) in self.tagged_cells:
                    # Overlapping. Try next row.
                    break
            else:
                # No overlapping was found.
                break
            # Note that all checks should be made for new cell_row value.

        if tags:
            self.tagged_cells.add((column, cell_row))

        # Propagate frontier.
        self.frontier[column] = cell_row + 1
        return cell_row

    def recompute_grid(self):
        self.reset_columns()
        self.reset_rows()

        for i, node in enumerate(sort_by_generation(list(self.commits))):
            # print(node.oid)
            if node.column is None:
                # Node is either root or its parent is not in items. The last
                # happens when tree loading is in progress. Allocate new
                # columns for such nodes.
                node.column = self.alloc_column()
            node.row = i
            # node.row = self.alloc_cell(node.column, node.tags)

            # Allocate columns for children which are still without one. Also
            # propagate frontier for children.
            if node.is_fork():
                sorted_children = sorted(
                    node.children, key=lambda c: c.generation, reverse=True
                )
                citer = iter(sorted_children)
                for child in citer:
                    if child.column is None:
                        # Top most child occupies column of parent.
                        child.column = node.column
                        # Note that frontier is propagated in course of
                        # alloc_cell.
                        break
                    else:
                        self.propagate_frontier(child.column, node.row + 1)
                else:
                    # No child occupies same column.
                    self.leave_column(node.column)
                    # Note that the loop below will pass no iteration.

                # Rest children are allocated new column.
                for child in citer:
                    if child.column is None:
                        child.column = self.alloc_column(node.column)
                    self.propagate_frontier(child.column, node.row + 1)
            elif node.children:
                child = node.children[0]
                if child.column is None:
                    child.column = node.column
                    # Note that frontier is propagated in course of alloc_cell.
                elif child.column != node.column:
                    # Child node have other parents and occupies column of one
                    # of them.
                    self.leave_column(node.column)
                    # But frontier must be propagated with respect to this
                    # parent.
                    self.propagate_frontier(child.column, node.row + 1)
            else:
                # This is a leaf node.
                self.leave_column(node.column)

        for i, c in enumerate(sorted(self.commits, key=attrgetter("timestamp"))):
            c.row = i

    def position_nodes(self):
        self.recompute_grid()

        x_start = self.x_start
        x_min = self.x_min
        x_off = self.x_off
        y_off = self.y_off

        positions = {}

        for node in self.commits:
            x_pos = x_start + node.column * x_off
            y_pos = y_off + node.row * y_off

            positions[node.oid] = (x_pos, y_pos)
            x_min = min(x_min, x_pos)

        self.x_min = x_min

        return positions

    def propagate_frontier(self, column, value):
        current = self.frontier[column]
        if current < value:
            self.frontier[column] = value

    def leave_column(self, column):
        count = self.columns[column]
        if count == 1:
            del self.columns[column]
        else:
            self.columns[column] = count - 1


def sort_by_generation(commits):
    if len(commits) < 2:
        return commits
    commits.sort(key=lambda x: x.generation)
    return commits


# ============= EOF =============================================
