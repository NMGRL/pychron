#===============================================================================
# Copyright 2012 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from PySide.QtGui import QKeySequence, QDrag, QAbstractItemView, QTableView, QApplication
from PySide.QtGui import QFont, QFontMetrics

from PySide import QtCore
from traits.api import Bool, Str, List, Any
from traitsui.editors.tabular_editor import TabularEditor
from traitsui.qt4.tabular_editor import TabularEditor as qtTabularEditor, \
    _TableView
from traitsui.mimedata import PyMimeData
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.helpers.ctx_managers import no_update
from pychron.consumer_mixin import ConsumerMixin

class TabularKeyEvent(object):
    def __init__(self, event):
        self.text = event.text().strip()
        mods = QApplication.keyboardModifiers()
        self.shift = mods == QtCore.Qt.ShiftModifier


class _myTableView(_TableView, ConsumerMixin):
    '''
        for drag and drop reference see
        https://github.com/enthought/traitsui/blob/master/traitsui/qt4/tree_editor.py
        
    '''
    _copy_cache = None
    _linked_copy_cache = None
    paste_func = None
    drop_factory = None
    _dragging = None

    _cut_indices = None

    def __init__(self, *args, **kw):
        super(_myTableView, self).__init__(*args, **kw)
        self.setDragDropMode(QAbstractItemView.DragDrop)

        self.setup_consumer()
        editor = self._editor

#        # reimplement row height
        vheader = self.verticalHeader()
        size = vheader.minimumSectionSize()

        font = editor.adapter.get_font(editor.object, editor.name, 0)
        if font is not None:
            fnt = QFont(font)
            size = QFontMetrics(fnt)
            vheader.setDefaultSectionSize(size.height() + 2)
            hheader = self.horizontalHeader()
            #hheader.setStretchLastSection(editor.factory.stretch_last_section)

            hheader.setFont(fnt)

    def super_keyPressEvent(self, event):
        """ Reimplemented to support edit, insert, and delete by keyboard.
        
            reimplmented to support no_update context manager.
        
        """
        editor = self._editor
        factory = editor.factory

        # Note that setting 'EditKeyPressed' as an edit trigger does not work on
        # most platforms, which is why we do this here.
        if (event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return) and
            self.state() != QAbstractItemView.EditingState and
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
            QTableView.keyPressEvent(self, event)

    def _add(self, items):
        si = self.selectedIndexes()
        paste_func = self.paste_func
        if paste_func is None:
            paste_func = lambda x: x.clone_traits()

        if len(si):
            idx = si[-1].row() + 1
        else:
            idx = len(self._editor.value)

        editor = self._editor
        with no_update(editor.object):
            for ci in reversed(items):
                editor.model.insertRow(idx, obj=paste_func(ci))

    def keyPressEvent(self, event):

        if event.matches(QKeySequence.Copy):
            self._copy_cache = [self._editor.value[ci.row()] for ci in
                                    self.selectionModel().selectedRows()]
            self._editor.copy_cache = self._copy_cache
            self._cut_indices = None
        elif event.matches(QKeySequence.Cut):

            self._cut_indices = [ci.row() for ci in
                                 self.selectionModel().selectedRows()]

            self._copy_cache = [self._editor.value[ci] for ci in self._cut_indices]
            #self._copy_cache = [self._editor.value[ci.row()] for ci in
            #                        self.selectionModel().selectedRows()]
            self._editor.copy_cache = self._copy_cache

        elif event.matches(QKeySequence.Paste):
            if self._cut_indices:
                for ci in self._cut_indices:
                    self._editor.model.removeRow(ci)

            self._cut_indices = None

            items = self._copy_cache
            if not items:
                items = self._linked_copy_cache

            if items:
                self.add_consumable((self._add, items))

        else:
            self._editor.key_pressed = TabularKeyEvent(event)

            self.super_keyPressEvent(event)
#            super(_myTableView, self).keyPressEvent(event)

    def startDrag(self, actions):
        if self._editor.factory.drag_external:
            idxs = self.selectedIndexes()
            rows = sorted(list(set([idx.row() for idx in idxs])))
            drag_object = [
                           (ri, self._editor.value[ri])
                            for ri in rows]

            md = PyMimeData.coerce(drag_object)

            self._dragging = self.currentIndex()
            drag = QDrag(self)
            drag.setMimeData(md)
    #        drag.setPixmap(pm)
    #        drag.setHotSpot(hspos)
            drag.exec_(actions)
        else:
            super(_myTableView, self).startDrag(actions)


    def dragEnterEvent(self, e):
        if self.is_external():
            # Assume the drag is invalid.
            e.ignore()

            # Check what is being dragged.
            md = PyMimeData.coerce(e.mimeData())
            if md is None:
                return

            # We might be able to handle it (but it depends on what the final
            # target is).
            e.acceptProposedAction()
        else:
            super(_myTableView, self).dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if self.is_external():
            e.acceptProposedAction()
        else:
            super(_myTableView, self).dragMoveEvent(e)

    def dropEvent(self, e):
        if self.is_external():
            data = PyMimeData.coerce(e.mimeData()).instance()
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
#                self._editor._no_update = True
#                parent = QtCore.QModelIndex()
#                model.beginInsertRows(parent, row, row)
#                editor = self._editor
#                 self._editor.object._no_update = True

                with no_update(self._editor.object):
                    for i, (_, di) in enumerate(reversed(data)):
    #                    print 'insert'
    #                    obj = paste_func1(di)
    #                    editor.callx(editor.adapter.insert, editor.object, editor.name, row + i, obj)
                        model.insertRow(row=row, obj=df(di))

    #                 model.insertRow(row=row, obj=paste_func(data[0][1]))
#                 self._editor.object._no_update = False


#                model.endInsertRows()
#                self._editor._no_update = False

            e.accept()
            self._dragging = None

        else:

            super(_myTableView, self).dropEvent(e)


    def is_external(self):
#        print 'is_external', self._editor.factory.drag_external and not self._dragging
        return self._editor.factory.drag_external  # and not self._dragging

class _TabularEditor(qtTabularEditor):

    widget_factory = _myTableView
    copy_cache = List
    col_widths = List
    key_pressed = Any

    def init(self, parent):
        super(_TabularEditor, self).init(parent)

#        self.sync_value(self.factory.rearranged, 'rearranged', 'to')
        self.sync_value(self.factory.col_widths, 'col_widths', 'to')
#        self.sync_value(self.factory.pasted, 'pasted', 'to')
        self.sync_value(self.factory.copy_cache, 'copy_cache', 'both')
        self.sync_value(self.factory.key_pressed, 'key_pressed', 'to')

        if hasattr(self.object, self.factory.paste_function):
            self.control.paste_func = getattr(self.object, self.factory.paste_function)
        if hasattr(self.object, self.factory.drop_factory):
            self.control.drop_func = getattr(self.object, self.factory.drop_factory)

        control = self.control
        signal = QtCore.SIGNAL('sectionResized(int,int,int)')

        QtCore.QObject.connect(control.horizontalHeader(), signal,
                               self._on_column_resize)

    def dispose(self):
        self.control._should_consume = False
        super(_TabularEditor, self).dispose()

    def _copy_cache_changed(self):
        if self.control:
            self.control._linked_copy_cache = self.copy_cache

#     def _key_pressed_changed(self):
#         print 'asdsfd'
#     def _paste_function_changed(self):
#         if self.control:
#             self.control.paste_func = self.paste_function

    def refresh_editor(self):
        if self.control:
            super(_TabularEditor, self).refresh_editor()

    def _on_column_resize(self, idx, old, new):
        control = self.control
        header = control.horizontalHeader()
        cs = [header.sectionSize(i) for i in range(header.count())]
        self.col_widths = cs

    def _scroll_to_row_changed(self, row):
        row=min(row, self.model.rowCount(None))-1
        qtTabularEditor._scroll_to_row_changed(self, 0)
        qtTabularEditor._scroll_to_row_changed(self, row)


class myTabularEditor(TabularEditor):
#     scroll_to_bottom = Bool(True)
#     scroll_to_row_hint = 'visible'
#    scroll_to_row_hint = 'bottom'
#    drag_move = Bool(False)
    key_pressed = Str
    rearranged = Str
    pasted = Str
    copy_cache = Str
    paste_function = Str
    '''
        extended trait name of function to use to create an object
        when dropped onto this table
    '''
    drop_factory = Str

    col_widths = Str

    drag_external = Bool(False)
    def _get_klass(self):
        return _TabularEditor
#============= EOF =============================================
