# ===============================================================================
# Copyright 2012 Jake Ross
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
from pickle import dumps

from pyface.qt import QtCore, QtGui
from pyface.qt.QtGui import QColor, QHeaderView, QApplication
from traits.api import Bool, Str, List, Any, Instance, Property, Int, HasTraits, Color, Either, Callable
from traits.trait_base import SequenceTypes
from traitsui.api import View, Item, TabularEditor, Handler
from traitsui.mimedata import PyMimeData
from traitsui.qt4.tabular_editor import TabularEditor as qtTabularEditor, \
    _TableView as TableView, HeaderEventFilter, _ItemDelegate
from traitsui.qt4.tabular_model import TabularModel, alignment_map

from pychron.core.helpers.ctx_managers import no_update


class myTabularEditor(TabularEditor):
    key_pressed = Str
    rearranged = Str
    pasted = Str
    autoscroll = Bool(False)
    # copy_cache = Str

    # link_copyable = Bool(True)
    pastable = Bool(True)

    paste_function = Str
    drop_factory = Either(Str, Callable)
    col_widths = Str
    drag_external = Bool(False)
    drag_enabled = Bool(True)

    bgcolor = Color
    row_height = Int
    mime_type = Str('pychron.tabular_item')

    # scroll_to_row_hint = 'top'

    # def _bgcolor_default(self):
    #     return '#646464'

    def _get_klass(self):
        return _TabularEditor


class MoveToRow(HasTraits):
    row = Property(Int)
    _row = Int(1)

    def _validate_row(self, v):
        if v > 0:
            return v

    def _get_row(self):
        return self._row

    def _set_row(self, v):
        self._row = v

    def traits_view(self):
        v = View(Item('row'),
                 buttons=['OK', 'Cancel'],
                 width=300,
                 title='Move Selected to Row',
                 kind='livemodal')
        return v


class TabularKeyEvent(object):
    def __init__(self, event):
        self.text = event.text().strip()
        mods = QtGui.QApplication.keyboardModifiers()
        self.shift = mods == QtCore.Qt.ShiftModifier


class UnselectTabularEditorHandler(Handler):
    refresh_name = Str('refresh_needed')
    selected_name = Str('selected')
    multiselect = Bool(True)

    def unselect(self, info, obj):
        v = [] if self.multiselect else None

        setattr(obj, self.selected_name, v)
        setattr(obj, self.refresh_name, True)


class TabularEditorHandler(UnselectTabularEditorHandler):
    def jump_to_start(self, info, obj):
        obj.jump_to_start()

    def jump_to_end(self, info, obj):
        obj.jump_to_end()

    def move_to_start(self, info, obj):
        obj.move_selected_first()

    def move_to_end(self, info, obj):
        obj.move_selected_last()

    def move_to_row(self, info, obj):
        obj.move_selected_to_row()

    def copy_to_start(self, info, obj):
        obj.copy_selected_first()

    def copy_to_end(self, info, obj):
        obj.copy_selected_last()

class ItemDelegate(_ItemDelegate):
    pass
    # def drawDecoration(self, painter, option, rect, pixmap):
    # print 'asdf', painter, option, rect, pixmap


# class _TableView(TableView, ConsumerMixin):
class _TableView(TableView):
    """
        for drag and drop reference see
        https://github.com/enthought/traitsui/blob/master/traitsui/qt4/tree_editor.py

    """
    paste_func = None
    drop_factory = None
    # link_copyable = True
    copyable = True
    # _copy_cache = None
    # _linked_copy_cache = None
    _dragging = None
    _cut_indices = None
    option_select = False
    drag_enabled = True

    def __init__(self, editor, layout=None, *args, **kw):
        super(_TableView, self).__init__(editor, *args, **kw)

        # self.setItemDelegate(ItemDelegate(self))
        # self.setup_consumer(main=True)
        editor = self._editor

        # # reimplement row height
        vheader = self.verticalHeader()

        # size = vheader.minimumSectionSize()
        height = None
        font = editor.adapter.get_font(editor.object, editor.name, 0)
        if font is not None:
            fnt = QtGui.QFont(font)
            size = QtGui.QFontMetrics(fnt)
            height = size.height() + 6
            vheader.setFont(fnt)
            hheader = self.horizontalHeader()
            hheader.setFont(fnt)

        if editor.factory.row_height:
            height = editor.factory.row_height

        if height:
            vheader.setDefaultSectionSize(height)
        else:
            vheader.ResizeMode(QHeaderView.ResizeToContents)

    def set_bg_color(self, bgcolor):
        if isinstance(bgcolor, tuple):
            if len(bgcolor) == 3:
                bgcolor = 'rgb({},{},{})'.format(*bgcolor)
            elif len(bgcolor) == 4:
                bgcolor = 'rgba({},{},{},{})'.format(*bgcolor)
        elif isinstance(bgcolor, QColor):
            bgcolor = 'rgba({},{},{},{})'.format(bgcolor.red(), bgcolor.green(), bgcolor.blue(), bgcolor.alpha())
        self.setStyleSheet('QTableView {{background-color: {}}}'.format(bgcolor))

    def set_vertical_header_font(self, fnt):
        fnt = QtGui.QFont(fnt)
        vheader = self.verticalHeader()
        vheader.setFont(fnt)
        size = QtGui.QFontMetrics(fnt)
        vheader.setDefaultSectionSize(size.height() + 6)

    def set_horizontal_header_font(self, fnt):
        fnt = QtGui.QFont(fnt)
        vheader = self.horizontalHeader()
        vheader.setFont(fnt)

    def set_drag_enabled(self, d):
        if d:
            self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
            self.setDragEnabled(True)

    def startDrag(self, actions):
        if self._editor.factory.drag_external:
            idxs = self.selectedIndexes()
            rows = sorted(list(set([idx.row() for idx in idxs])))
            drag_object = [(ri, self._editor.value[ri]) for ri in rows]

            md = PyMimeData.coerce(drag_object)

            self._dragging = self.currentIndex()
            drag = QtGui.QDrag(self)
            drag.setMimeData(md)
            drag.exec_(actions)
        else:
            super(_TableView, self).startDrag(actions)

    def dragEnterEvent(self, e):
        if self.is_external():
            # Assume the drag is invalid.
            e.ignore()

            # Check what is being dragged.
            ed = e.mimeData()
            md = PyMimeData.coerce(ed)
            if md is None:
                return
            else:
                try:
                    if not hasattr(ed.instance(), '__iter__'):
                        return
                except AttributeError:
                    return

            # We might be able to handle it (but it depends on what the final
            # target is).
            e.acceptProposedAction()
        else:
            super(_TableView, self).dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if self.is_external():
            e.acceptProposedAction()
        else:
            super(_TableView, self).dragMoveEvent(e)

    def dropEvent(self, e):
        if self.is_external():
            data = PyMimeData.coerce(e.mimeData()).instance()
            if not hasattr(data, '__iter__'):
                return

            df = self.drop_factory
            if not df:
                df = lambda x: x

            row = self.rowAt(e.pos().y())
            n = len(self._editor.value)
            if row == -1:
                row = n

            model = self._editor.model
            if self._dragging:
                rows = [ri for ri, _ in data]
                model.moveRows(rows, row)
            else:
                data = [di for _, di in data]
                with no_update(self._editor.object):
                    for i, di in enumerate(reversed(data)):
                        if isinstance(di, tuple):
                            di = di[1]
                        model.insertRow(row=row, obj=df(di))

                    for i, di in enumerate(reversed(df(data))):
                        model.insertRow(row=row, obj=di)

            e.accept()
            self._dragging = None

        else:
            super(_TableView, self).dropEvent(e)

    def is_external(self):
        # print 'is_external', self._editor.factory.drag_external and not self._dragging
        return self._editor.factory.drag_external  # and not self._dragging

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            # self._copy_cache = [self._editor.value[ci.row()] for ci in
            # self.selectionModel().selectedRows()]
            # self._copy_cache = self._get_selection()
            # self._editor.copy_cache = self._copy_cache
            self._cut_indices = None

            # add the selected rows to the clipboard
            self._copy()

        elif event.matches(QtGui.QKeySequence.Cut):
            self._cut_indices = [ci.row() for ci in self.selectionModel().selectedRows()]

            # self._copy_cache = [self._editor.value[ci] for ci in self._cut_indices]
            # self._copy_cache = self._get_selection(self._cut_indices)
            # self._editor.copy_cache = self._copy_cache

        elif event.matches(QtGui.QKeySequence.Paste):
            if self.pastable:
                self._paste()
        else:
            self._editor.key_pressed = TabularKeyEvent(event)

            self._key_press_hook(event)

    # private
    def _copy(self):
        rows = sorted({ri.row() for ri in self.selectedIndexes()})
        copy_object = [(ri, self._editor.value[ri].tocopy()) for ri in rows]
        # copy_object = [ri.row(), self._editor.value[ri.row()]) for ri in self.selectedIndexes()]
        mt = self._editor.factory.mime_type
        try:
            pdata = dumps(copy_object)
        except BaseException, e:
            print 'tabular editor copy failed'
            self._editor.value[rows[0]].tocopy(verbose=True)
            return

        qmd = PyMimeData()
        qmd.MIME_TYPE = mt
        qmd.setData(unicode(mt), dumps(copy_object.__class__) + pdata)

        clipboard = QApplication.clipboard()
        clipboard.setMimeData(qmd)

    def _paste(self):
        clipboard = QApplication.clipboard()
        md = clipboard.mimeData()
        items = md.instance()
        if items is not None:
            editor = self._editor
            model = editor.model

            insert_mode = 'after'
            selection = self.selectedIndexes()
            if len(selection):
                offset = 1 if insert_mode == 'after' else 0
                idx = selection[-1].row() + offset
            else:
                idx = len(editor.value)

            if self._cut_indices:
                if not any((ci <= idx for ci in self._cut_indices)):
                    idx += len(self._cut_indices)

                model = editor.model
                for ci in self._cut_indices:
                    model.removeRow(ci)

            self._cut_indices = None

            # paste_func = self.paste_func
            # if paste_func is None:
            #     paste_func = lambda x: x.clone_traits()

            for ri, ci in reversed(items):
                model.insertRow(idx, obj=ci)

    # def _paste(self):
    # selection = self.selectedIndexes()
    # idx = None
    #     if len(selection):
    #         idx = selection[-1].row()
    #
    #     if self._cut_indices:
    #         if not any((ci <= idx for ci in self._cut_indices)):
    #             idx += len(self._cut_indices)
    #
    #         model = self._editor.model
    #         for ci in self._cut_indices:
    #             model.removeRow(ci)
    #
    #     self._cut_indices = None
    #
    #     items = None
    #     if self.link_copyable:
    #         items = self._linked_copy_cache
    #
    #     if not items:
    #         items = self._copy_cache
    #
    #     if items:
    #         insert_mode = 'after'
    #         if idx is None:
    #             if len(selection):
    #                 offset = 1 if insert_mode == 'after' else 0
    #                 idx = selection[-1].row() + offset
    #             else:
    #                 idx = len(self._editor.value)
    #
    #         paste_func = self.paste_func
    #         if paste_func is None:
    #             paste_func = lambda x: x.clone_traits()
    #
    #         editor = self._editor
    #         # with no_update(editor.object):
    #         model = editor.model
    #         for ci in reversed(items):
    #             model.insertRow(idx, obj=paste_func(ci))
    #
    #             # self._add(items, idx=idx)
    #             # func = lambda a: self._add(a, idx=idx)
    #             # self.add_consumable((self._add, (items,), {'idx':idx}))
    #             # self.add_consumable((self._add, items))
    #             # invoke_in_main_thread(self._add, items, idx=idx)

    def _get_selection(self, rows=None):
        if rows is None:
            rows = self._get_selection_indices()

        return [self._editor.value[ci] for ci in rows]

    def _get_selection_indices(self):
        rows = self.selectionModel().selectedRows()
        return [ci.row() for ci in rows]

    def _key_press_hook(self, event):
        """ Reimplemented to support edit, insert, and delete by keyboard.

            reimplmented to support no_update context manager.

        """
        editor = self._editor
        factory = editor.factory

        # Note that setting 'EditKeyPressed' as an edit trigger does not work on
        # most platforms, which is why we do this here.
        if (event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return) and
                    self.state() != QtGui.QAbstractItemView.EditingState and
                factory.editable and 'edit' in factory.operations):
            if factory.multi_select:
                rows = editor.multi_selected_rows
                row = rows[0] if len(rows) == 1 else -1
            else:
                row = editor.selected_row

            if row != -1:
                event.accept()
                self.edit(editor.model.index(row, 0))

        elif (event.key() in (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete) and
                  factory.editable and 'delete' in factory.operations):
            event.accept()
            '''
                sets _no_update and update_needed on the editor.object e.g

                editor.object== ExperimentQueue
                editor is editing ExperimentQueue.automated_runs

            '''

            with no_update(editor.object):
                if factory.multi_select:
                    for row in reversed(sorted(editor.multi_selected_rows)):
                        editor.model.removeRow(row)
                elif editor.selected_row != -1:
                    editor.model.removeRow(editor.selected_row)

        elif (event.key() == QtCore.Qt.Key_Insert and
                  factory.editable and 'insert' in factory.operations):
            event.accept()

            if factory.multi_select:
                rows = sorted(editor.multi_selected_rows)
                row = rows[0] if len(rows) else -1
            else:
                row = editor.selected_row
            if row == -1:
                row = editor.adapter.len(editor.object, editor.name)
            editor.model.insertRow(row)
            self.setCurrentIndex(editor.model.index(row, 0))

        else:
            QtGui.QTableView.keyPressEvent(self, event)


class _TabularModel(TabularModel):
    def data(self, mi, role=None):
        """ Reimplemented to return the data.
        """
        if role is None:
            role = QtCore.Qt.DisplayRole

        editor = self._editor
        adapter = editor.adapter
        obj, name = editor.object, editor.name
        row, column = mi.row(), mi.column()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return adapter.get_text(obj, name, row, column)

        elif role == QtCore.Qt.DecorationRole:
            image = editor._get_image(adapter.get_image(obj, name, row, column))

            if image is not None:
                return image

        elif role == QtCore.Qt.ToolTipRole:
            tooltip = adapter.get_tooltip(obj, name, row, column)
            if tooltip:
                return tooltip

        elif role == QtCore.Qt.FontRole:
            font = adapter.get_font(obj, name, row, column)
            if font is not None:
                return QtGui.QFont(font)

        elif role == QtCore.Qt.TextAlignmentRole:
            string = adapter.get_alignment(obj, name, column)
            alignment = alignment_map.get(string, QtCore.Qt.AlignLeft)
            return int(alignment | QtCore.Qt.AlignVCenter)

        elif role == QtCore.Qt.BackgroundRole:
            color = adapter.get_bg_color(obj, name, row, column)
            if color is not None:
                if isinstance(color, SequenceTypes):
                    q_color = QtGui.QColor(*color)
                else:
                    q_color = QtGui.QColor(color)
                return QtGui.QBrush(q_color)

        elif role == QtCore.Qt.ForegroundRole:
            color = adapter.get_text_color(obj, name, row, column)
            if color is not None:
                if isinstance(color, SequenceTypes):
                    q_color = QtGui.QColor(*color)
                else:
                    q_color = QtGui.QColor(color)
                return QtGui.QBrush(q_color)

        return None


class _TabularEditor(qtTabularEditor):
    widget_factory = _TableView
    # copy_cache = List
    col_widths = List
    key_pressed = Any
    model = Instance(_TabularModel)
    image_size = (32, 32)

    def init(self, layout):
        factory = self.factory

        self.adapter = factory.adapter
        self.model = _TabularModel(editor=self)

        # Create the control
        control = self.control = self.widget_factory(self, layout=layout)

        control.set_drag_enabled(factory.drag_enabled)

        # Set up the selection listener
        if factory.multi_select:
            self.sync_value(factory.selected, 'multi_selected', 'both',
                            is_list=True)
            self.sync_value(factory.selected_row, 'multi_selected_rows', 'both',
                            is_list=True)
        else:
            self.sync_value(factory.selected, 'selected', 'both')
            self.sync_value(factory.selected_row, 'selected_row', 'both')

        # Connect to the mode specific selection handler
        if factory.multi_select:
            slot = self._on_rows_selection
        else:
            slot = self._on_row_selection
        signal = 'selectionChanged(QItemSelection,QItemSelection)'
        QtCore.QObject.connect(self.control.selectionModel(),
                               QtCore.SIGNAL(signal), slot)

        # Synchronize other interesting traits as necessary:
        self.sync_value(factory.update, 'update', 'from')
        self.sync_value(factory.refresh, 'refresh', 'from')
        self.sync_value(factory.activated, 'activated', 'to')
        self.sync_value(factory.activated_row, 'activated_row', 'to')
        self.sync_value(factory.clicked, 'clicked', 'to')
        self.sync_value(factory.dclicked, 'dclicked', 'to')
        self.sync_value(factory.right_clicked, 'right_clicked', 'to')
        self.sync_value(factory.right_dclicked, 'right_dclicked', 'to')
        self.sync_value(factory.column_clicked, 'column_clicked', 'to')
        self.sync_value(factory.column_right_clicked, 'column_right_clicked', 'to')
        self.sync_value(factory.scroll_to_row, 'scroll_to_row', 'from')

        # Connect other signals as necessary
        signal = QtCore.SIGNAL('activated(QModelIndex)')
        QtCore.QObject.connect(control, signal, self._on_activate)
        signal = QtCore.SIGNAL('clicked(QModelIndex)')
        QtCore.QObject.connect(control, signal, self._on_click)
        signal = QtCore.SIGNAL('clicked(QModelIndex)')
        QtCore.QObject.connect(control, signal, self._on_right_click)
        signal = QtCore.SIGNAL('doubleClicked(QModelIndex)')
        QtCore.QObject.connect(control, signal, self._on_dclick)
        signal = QtCore.SIGNAL('sectionClicked(int)')
        QtCore.QObject.connect(control.horizontalHeader(), signal, self._on_column_click)

        control.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        signal = QtCore.SIGNAL('customContextMenuRequested(QPoint)')
        QtCore.QObject.connect(control, signal, self._on_context_menu)

        self.header_event_filter = HeaderEventFilter(self)
        control.horizontalHeader().installEventFilter(self.header_event_filter)

        # Make sure we listen for 'items' changes as well as complete list
        # replacements:
        try:
            self.context_object.on_trait_change(
                self.update_editor, self.extended_name + '_items', dispatch='ui')
        except:
            pass

        # If the user has requested automatic update, attempt to set up the
        # appropriate listeners:
        if factory.auto_update:
            self.context_object.on_trait_change(
                self.refresh_editor, self.extended_name + '.-', dispatch='ui')

        # Create the mapping from user supplied images to QImages:
        for image_resource in factory.images:
            self._add_image(image_resource)

        # Refresh the editor whenever the adapter changes:
        self.on_trait_change(self.refresh_editor, 'adapter.+update',
                             dispatch='ui')

        # Rebuild the editor columns and headers whenever the adapter's
        # 'columns' changes:
        self.on_trait_change(self.update_editor, 'adapter.columns',
                             dispatch='ui')

        self.my_init()

    def my_init(self):
        factory = self.factory
        self.sync_value(factory.col_widths, 'col_widths', 'to')
        # self.sync_value(factory.copy_cache, 'copy_cache', 'both')
        self.sync_value(factory.key_pressed, 'key_pressed', 'to')

        control = self.control

        if factory.bgcolor:
            control.set_bg_color(factory.bgcolor)

        if hasattr(self.object, factory.paste_function):
            control.paste_func = getattr(self.object, factory.paste_function)

        if factory.drop_factory:
            if hasattr(factory.drop_factory, '__call__'):
                control.drop_factory = factory.drop_factory

            elif hasattr(self.object, factory.drop_factory):
                control.drop_factory = getattr(self.object, factory.drop_factory)

        # control.link_copyable = factory.link_copyable
        control.pastable = factory.pastable
        signal = QtCore.SIGNAL('sectionResized(int,int,int)')

        QtCore.QObject.connect(control.horizontalHeader(), signal,
                               self._on_column_resize)

    # def dispose(self):
    #     # self.control._should_consume = False
    #     super(_TabularEditor, self).dispose()

    def refresh_editor(self):
        if self.control:
            self.control.set_vertical_header_font(self.adapter.font)
            self.control.set_horizontal_header_font(self.adapter.font)

            super(_TabularEditor, self).refresh_editor()

    def _add_image(self, image_resource):
        """ Adds a new image to the image map.

            reimplement to display images instead of icons
            images respect their original size
            icons are scaled down to 16x16
        """
        image = image_resource.create_image()

        self.image_resources[image_resource] = image
        self.images[image_resource.name] = image

        return image

    def _on_column_resize(self, idx, old, new):
        control = self.control
        header = control.horizontalHeader()
        cs = [header.sectionSize(i) for i in xrange(header.count())]
        self.col_widths = cs

    def _multi_selected_rows_changed(self, selected_rows):
        super(_TabularEditor, self)._multi_selected_rows_changed(selected_rows)
        if selected_rows:
            self._auto_scroll(selected_rows[0])

    def _selected_changed(self, new):
        super(_TabularEditor, self)._selected_changed(new)
        self._auto_scroll(new)

    def _auto_scroll(self, row):
        if self.factory.autoscroll and row:
            if not isinstance(row, int):
                row = self.value.index(row)
            self.scroll_to_row = row

    def _scroll_to_row_changed(self, row):
        row = min(row, self.model.rowCount(None)) - 1
        qtTabularEditor._scroll_to_row_changed(self, 0)
        qtTabularEditor._scroll_to_row_changed(self, row)

# ============= EOF =============================================
