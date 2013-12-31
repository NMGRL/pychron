#===============================================================================
# Copyright 2013 Jake Ross
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
from PySide import QtGui, QtCore
from PySide.QtGui import QPlainTextEdit, QColor, QTextCursor, QFont
from pyface.ui.qt4.code_editor.gutters import LineNumberWidget

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.qt4.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor

class DiffGutter(LineNumberWidget):
    start=1
    end=4
    tag='+'
    anti_tag='-'
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setFont(self.font)
        painter.fillRect(event.rect(), self.background_color)

        cw = self.parent()
        block = cw.firstVisibleBlock()
        blocknum = block.blockNumber()
        top = cw.blockBoundingGeometry(block).translated(
            cw.contentOffset()).top()
        bottom = top + int(cw.blockBoundingRect(block).height())

        lineno=1
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                if blocknum>0:
                    text=block.text()
                    if not text.startswith(self.anti_tag):
                        painter.setPen(QtCore.Qt.black)
                        painter.drawText(0, top, self.width() - 2,
                                         self.fontMetrics().height(),
                                         QtCore.Qt.AlignRight, str(lineno))
                        lineno+=1
                else:
                    painter.setPen(QtCore.Qt.black)
                    painter.drawText(0, top, self.width() - 2,
                                     self.fontMetrics().height(),
                                     QtCore.Qt.AlignRight, '...')

            block = block.next()
            top = bottom
            bottom = top + int(cw.blockBoundingRect(block).height())
            blocknum += 1


class PatchWidget(QPlainTextEdit):

    def __init__(self, *args, **kw):
        super(PatchWidget, self).__init__(*args, **kw)
        self.aline_number_widget = DiffGutter(self)
        self.aline_number_widget.min_char_width=3
        self.aline_number_widget.anti_tag='+'
        self.bline_number_widget = DiffGutter(self)
        self.bline_number_widget.min_char_width=3
        self.bline_number_widget.anti_tag='-'

        font =QFont()
        self.set_font(font)

    def set_font(self, font):
        """ Set the new QFont.
        """
        self.document().setDefaultFont(font)
        self.aline_number_widget.set_font(font)
        self.bline_number_widget.set_font(font)
        self.update_line_number_width()

    def update_line_number_width(self, nblocks=0):
        """ Update the width of the line number widget.
        """
        left = 0
        if not self.aline_number_widget.isHidden():
            left += self.aline_number_widget.digits_width()

        if not self.bline_number_widget.isHidden():
            left += self.bline_number_widget.digits_width()

        self.setViewportMargins(left, 0, 0, 0)

    def resizeEvent(self, event):
        QtGui.QPlainTextEdit.resizeEvent(self, event)
        contents = self.contentsRect()
        awidth=self.aline_number_widget.digits_width()
        self.aline_number_widget.setGeometry(QtCore.QRect(contents.left(),
                                                         contents.top(), awidth,
                                                         contents.height()))

        self.bline_number_widget.setGeometry(QtCore.QRect(contents.left()+awidth,
                                                          contents.top(), self.bline_number_widget.digits_width(),
                                                          contents.height()))
        # use the viewport width to determine the right edge. This allows for
        # the propper placement w/ and w/o the scrollbar
        # right_pos = self.viewport().width() + self.aline_number_widget.width() + 1
                    # - self.status_widget.sizeHint().width()
        # self.status_widget.setGeometry(QtCore.QRect(right_pos,
        #                                             contents.top(), self.status_widget.sizeHint().width(),
        #                                             contents.height()))

    def sizeHint(self):
        # Suggest a size that is 80 characters wide and 40 lines tall.
        style = self.style()
        opt = QtGui.QStyleOptionHeader()
        font_metrics = QtGui.QFontMetrics(self.document().defaultFont())
        width = font_metrics.width(' ') * 80
        width += self.aline_number_widget.sizeHint().width()
        # width += self.status_widget.sizeHint().width()
        width += style.pixelMetric(QtGui.QStyle.PM_ScrollBarExtent, opt, self)
        height = font_metrics.height() * 40
        return QtCore.QSize(width, height)

class _PatchEditor(Editor):
    def init( self, parent ):
        self.control=self._create_control(parent)

    def _create_control(self, parent):
        ctrl=PatchWidget()
        ctrl.setReadOnly(True)
        return ctrl

    def update_editor(self):

        #remove first two lines of patch.
        # this display the file names
        value='\n'.join(self.value.split('\n')[2:])

        self.control.setPlainText(value)
        self._set_highlighting(value)

    def _set_highlighting(self, txt):
        lines=txt.split('\n')
        for idx, li in enumerate(lines):
            if li.startswith('+') and not li.startswith('+++'):
                self._highlight(idx, 'addition')
            elif li.startswith('-') and not li.startswith('---'):
                self._highlight(idx, 'deletion')
            else:
                self._fade(idx)

    def _fade(self, lineno):
        cursor = self._get_line_cursor(lineno)

        fmt = cursor.charFormat()
        color=QColor('black')
        color.setAlphaF(0.5)
        fmt.setForeground(color)
        cursor.beginEditBlock()
        cursor.setCharFormat(fmt)
        cursor.endEditBlock()

    def _highlight(self, lineno, kind):

        if kind=='addition':
            color=QColor(225,254,229) #light green
        elif kind=='deletion':
            color=QColor(255, 228, 228) #light red

        cursor=self._get_line_cursor(lineno)

        fmt = cursor.charFormat()
        fmt.setBackground(color)

        cursor.beginEditBlock()
        cursor.setCharFormat(fmt)
        cursor.endEditBlock()

    def _get_line_cursor(self, lineno):
        ctrl = self.control
        doc = ctrl.document()
        block = doc.findBlockByLineNumber(lineno)

        pos = block.position()

        cursor = ctrl.textCursor()
        cursor.setPosition(pos)
        cursor.select(QTextCursor.LineUnderCursor)
        # cursor.select(QTextCursor.BlockUnderCursor)
        return cursor

    #

class PatchEditor(BasicEditorFactory):
    klass=_PatchEditor
#============= EOF =============================================
