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
from PySide import QtCore
from PySide.QtGui import QTextEdit, QWidget, QHBoxLayout, QTextFormat, QColor, QPainter, QFrame, \
    QSizePolicy, QPainterPath
from traits.trait_errors import TraitError
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor
from pychron.git_archive.diff_util import extract_line_numbers

def get_ranges(data):
    from operator import itemgetter
    from itertools import groupby
    # data = [2, 3, 4, 5, 12, 13, 14, 15, 16, 17]
    for k, g in groupby(enumerate(data), lambda (i,x):i-x):
        v=map(itemgetter(1), g)
        # print v
        yield v

class QDiffConnector(QFrame):
    _left_y=0
    _right_y=0
    def __init__(self):
        super(QDiffConnector, self).__init__()

        self.color = QColor(0,100,0,100)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,
                                       QSizePolicy.Ignored))
        self.setFixedWidth(30)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        qp.setRenderHint(QPainter.Antialiasing)
        qp.setBrush(self.color)
        qp.setPen(self.color)

        rect=event.rect()
        x= rect.x()
        w=rect.width()
        lineheight=16
        # print '-------------------'
        # print 'lefts', self.lefts
        # print 'rights', self.rights
        # print '-------------------'
        ly=self._left_y+5
        ry=self._right_y+5
        for l,r in zip(self.lefts, self.rights):
            path=QPainterPath()
            sl,el=l[0], l[-1]
            sr,er=r[0], r[-1]
            y=ly+lineheight*sl
            y2=ry+lineheight*sr

            path.moveTo(x,y)
            path.lineTo(x,y+lineheight*(el-sl+1))
            path.lineTo(x+w,y2+lineheight*(er-sr+1))
            path.lineTo(x+w,y2)
            qp.drawPath(path)

        qp.end()

    def set_left_y(self, y):
        self._left_y+=y

    def set_right_y(self, y):
        self._right_y+=y

class LinkedTextEdit(QTextEdit):
    linked_widget=None
    connector=None
    orientation='left'
    no_update=False

    def scrollContentsBy(self, x,y):
        if self.linked_widget and not self.no_update:
            sb = self.linked_widget.verticalScrollBar()
            v = sb.value()-y
            self.linked_widget.no_update=True
            sb.setSliderPosition(v)
            self.linked_widget.no_update=False

        if self.connector:
            if self.orientation=='left':
                self.connector.set_left_y(y)
            else:
                self.connector.set_right_y(y)

            self.connector.update()
        super(LinkedTextEdit, self).scrollContentsBy(x,y)

class QDiffEdit(QWidget):
    def __init__(self, parent, *args, **kw):
        super(QDiffEdit, self).__init__(*args, **kw)
        self.left = LinkedTextEdit()
        self.left.orientation='left'
        self.left.setReadOnly(True)
        # self.left.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,
        #                                     QSizePolicy.Fixed))

        self.right = LinkedTextEdit()
        self.right.orientation='right'
        self.right.setReadOnly(True)
        # self.right.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,
        #                                     QSizePolicy.Fixed))

        self.connector = QDiffConnector()

        self.left.linked_widget=self.right
        self.right.linked_widget=self.left
        self.left.connector=self.connector
        self.right.connector=self.connector

        layout = QHBoxLayout()
        layout.addWidget(self.left)
        layout.addWidget(self.connector)
        layout.addWidget(self.right)
        self.setLayout(layout)

    def set_left_text(self, txt):
        self.left.setText(txt)

    def set_right_text(self, txt):
        self.right.setText(txt)

    def highlight(self, ctrl, lineno):
        selection = QTextEdit.ExtraSelection()
        selection.cursor = ctrl.textCursor()
        selection.format.setBackground(QColor(100, 200, 100))
        selection.format.setProperty(
            QTextFormat.FullWidthSelection, True)

        doc = ctrl.document()

        block = doc.findBlockByLineNumber(lineno)
        selection.cursor.setPosition(block.position())

        ss = ctrl.extraSelections()
        ss.append(selection)
        ctrl.setExtraSelections(ss)
        selection.cursor.clearSelection()

    def _clear_selection(self):
        for ctrl in (self.left, self.right):
            ctrl.setExtraSelections([])

    def set_diff(self):
        self._clear_selection()

        ls, rs = extract_line_numbers(self.left.toPlainText(),
                                      self.right.toPlainText())
        for li in ls:
            self.highlight(self.left, li)
        for ri in rs:
            self.highlight(self.right, ri)

        self._set_connectors(ls, rs)

    def _set_connectors(self, ls, rs):
        self.connector.lefts=list(get_ranges(ls))
        self.connector.rights=list(get_ranges(rs))
        self.connector.update()


class _DiffEditor(Editor):
    _no_update = False

    def init(self, parent):
        self.control = self._create_control(parent)

    def _create_control(self, parent):
        ctrl = QDiffEdit(parent)
        QtCore.QObject.connect(ctrl.left,
                               QtCore.SIGNAL('textChanged()'), self.update_left_object)
        QtCore.QObject.connect(ctrl.right,
                               QtCore.SIGNAL('textChanged()'), self.update_right_object)

        return ctrl

    def update_editor(self):
        if self.value:
            self.control.set_left_text(self.value.left_text)
            self.control.set_right_text(self.value.right_text)
            self.control.set_diff()

    def update_right_object(self):
        """ Handles the user entering input data in the edit control.
        """
        self._update_object('right')

    def update_left_object(self):
        """ Handles the user entering input data in the edit control.
        """
        self._update_object('left')

    def _get_user_left_value(self):
        return self._get_user_value('left')

    def _get_user_right_value(self):
        return self._get_user_value('left')

    def _update_object(self, attr):
        if (not self._no_update) and (self.control is not None):
            try:
                setattr(self.value, '{}_text'.format(attr),
                        getattr(self, '_get_user_{}_value'.format(attr))())
                self.control.set_diff()
                if self._error is not None:
                    self._error = None
                    self.ui.errors -= 1

                self.set_error_state(False)

            except TraitError, excp:
                pass
    def _get_user_value(self, attr):
        ctrl=getattr(self.control, attr)
        try:
            value = ctrl.text()
        except AttributeError:
            value = ctrl.toPlainText()

        value = unicode(value)

        try:
            value = self.evaluate(value)
        except:
            pass

        try:
            ret = self.factory.mapping.get(value, value)
        except (TypeError, AttributeError):
            # The value is probably not hashable.
            ret = value

        return ret

class DiffEditor(BasicEditorFactory):
    klass = _DiffEditor

# ============= EOF =============================================



