# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from __future__ import absolute_import
from difflib import ndiff

from PySide import QtGui, QtCore
from pyface.qt.QtGui import (
    QPlainTextEdit,
    QColor,
    QTextCursor,
    QFont,
    QTextEdit,
    QTextFormat,
    QPen,
)
from pyface.ui.qt.code_editor.gutters import LineNumberWidget

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt.editor import Editor


class DiffGutter(LineNumberWidget):
    start = 0

    anti_tag = "-"
    adjust_width = 0

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setFont(self.font)

        # painter.setPen(QColor(200, 0, 100))#light grey
        painter.fillRect(event.rect(), self.background_color)

        p = QPen()
        p.setColor(QColor(100, 100, 100))
        painter.setPen(p)

        rect = event.rect()
        rect.adjust(0, -1, self.adjust_width, 1)
        painter.drawRect(rect)

        cw = self.parent()
        block = cw.firstVisibleBlock()
        blocknum = block.blockNumber()
        top = cw.blockBoundingGeometry(block).translated(cw.contentOffset()).top()
        bottom = top + int(cw.blockBoundingRect(block).height())

        lineno = self.start
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                if blocknum > 0:
                    text = block.text()
                    if not text.startswith(self.anti_tag):
                        painter.drawText(
                            0,
                            top,
                            self.width() - 2,
                            self.fontMetrics().height(),
                            QtCore.Qt.AlignRight,
                            str(lineno),
                        )
                        lineno += 1
                else:
                    painter.drawText(
                        0,
                        top,
                        self.width() - 2,
                        self.fontMetrics().height(),
                        QtCore.Qt.AlignRight,
                        "...",
                    )

            block = next(block)
            top = bottom
            bottom = top + int(cw.blockBoundingRect(block).height())
            blocknum += 1


class PatchWidget(QPlainTextEdit):
    def __init__(self, *args, **kw):
        super(PatchWidget, self).__init__(*args, **kw)
        self.aline_number_widget = DiffGutter(self)
        # self.aline_number_widget.min_char_width=3
        self.aline_number_widget.anti_tag = "+"
        self.bline_number_widget = DiffGutter(self)
        # self.bline_number_widget.min_char_width=3
        self.bline_number_widget.anti_tag = "-"
        self.bline_number_widget.adjust_width = -1

        font = QFont()
        self.set_font(font)

    def set_font(self, font):
        """Set the new QFont."""
        self.document().setDefaultFont(font)
        self.aline_number_widget.set_font(font)
        self.bline_number_widget.set_font(font)
        self.update_line_number_width()

    def set_gutter_starts(self, a, b):
        self.aline_number_widget.start = a
        self.bline_number_widget.start = b

    def update_line_number_width(self, nblocks=0):
        """Update the width of the line number widget."""
        left = 0
        if not self.aline_number_widget.isHidden():
            left += self.aline_number_widget.digits_width()

        if not self.bline_number_widget.isHidden():
            left += self.bline_number_widget.digits_width()

        self.setViewportMargins(left, 0, 0, 0)

    def resizeEvent(self, event):
        QtGui.QPlainTextEdit.resizeEvent(self, event)
        contents = self.contentsRect()
        awidth = self.aline_number_widget.digits_width()
        self.aline_number_widget.setGeometry(
            QtCore.QRect(contents.left(), contents.top(), awidth, contents.height())
        )

        self.bline_number_widget.setGeometry(
            QtCore.QRect(
                contents.left() + awidth,
                contents.top(),
                self.bline_number_widget.digits_width(),
                contents.height(),
            )
        )
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
        width = font_metrics.width(" ") * 80
        width += self.aline_number_widget.sizeHint().width()
        # width += self.status_widget.sizeHint().width()
        width += style.pixelMetric(QtGui.QStyle.PM_ScrollBarExtent, opt, self)
        height = font_metrics.height() * 40
        return QtCore.QSize(width, height)


class _PatchEditor(Editor):
    def init(self, parent):
        self.control = self._create_control(parent)

    def _create_control(self, parent):
        ctrl = PatchWidget()
        ctrl.setReadOnly(True)
        return ctrl

    def update_editor(self):
        def extract_bounds(line):
            """
            @@ -1,4 +1,4 @@
            """
            args = line.split("@@")
            line = args[1]

            a, b = line.strip().split(" ")

            sa, ea = a.split(",")
            sb, eb = b.split(",")

            return (int(sa[1:]), int(ea)), (int(sb), int(eb))

        if self.value:
            # remove first two lines of patch.
            # these display the file names
            lines = self.value.split("\n")
            a, b = extract_bounds(lines[2])
            self.control.set_gutter_starts(a[0], b[0])

            value = "\n".join(lines[2:])
            self.control.setPlainText(value)

            self._set_text_highlighting(lines[2:])
            self._set_line_highlighting(lines[2:])
        else:
            self.control.setPlainText("")

    def _set_line_highlighting(self, lines):
        ss = []
        for idx, li in enumerate(lines):
            if li.startswith("+"):
                sel = self._highlight(idx, "addition")
                ss.append(sel)
            elif li.startswith("-"):
                sel = self._highlight(idx, "deletion")
                ss.append(sel)
            else:
                self._fade(idx)

        self.control.setExtraSelections(ss)

    def _set_text_highlighting(self, lines):
        has_deletion = False
        for idx, li in enumerate(lines):
            if li.startswith("-"):
                has_deletion = True
                a = li
            if has_deletion and li.startswith("+"):
                # find diff
                b = li

                for i, s in enumerate(ndiff(a, b)):
                    if s[0] == " ":
                        continue
                    elif s[0] == "-":
                        if not s[-1] in ("-", "+"):
                            self._set_diff(idx - 2, i, QColor(200, 0, 0))
                    elif s[0] == "+":
                        if not s[-1] in ("-", "+"):
                            self._set_diff(idx - 1, i, QColor(0, 200, 0))

    def _set_diff(self, lineno, start, color):
        cursor = self._get_line_cursor(lineno)
        fmt = cursor.charFormat()
        fmt.setForeground(color)
        fmt.setFontUnderline(True)
        cp = cursor.position()

        cursor.setPosition(cp + start)
        cursor.setPosition(cp + start + 1, mode=QTextCursor.KeepAnchor)

        cursor.mergeCharFormat(fmt)

    def _fade(self, lineno):
        cursor = self._get_line_cursor(lineno)

        fmt = cursor.charFormat()
        color = QColor("black")
        color.setAlphaF(0.5)
        fmt.setForeground(color)
        cursor.beginEditBlock()
        cursor.mergeCharFormat(fmt)
        cursor.endEditBlock()

    def _highlight(self, lineno, kind):
        if kind == "addition":
            color = QColor(225, 254, 229)  # light green
        elif kind == "deletion":
            color = QColor(255, 228, 228)  # light red

        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(color)
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)

        ctrl = self.control
        doc = ctrl.document()
        block = doc.findBlockByLineNumber(lineno)
        pos = block.position()
        cursor = ctrl.textCursor()
        cursor.setPosition(pos)
        selection.cursor = cursor

        return selection

    def _get_line_cursor(self, lineno):
        ctrl = self.control
        doc = ctrl.document()
        block = doc.findBlockByLineNumber(lineno)

        pos = block.position()

        cursor = ctrl.textCursor()
        cursor.setPosition(pos)
        cursor.select(QTextCursor.LineUnderCursor)
        return cursor


class PatchEditor(BasicEditorFactory):
    klass = _PatchEditor


# ============= EOF =============================================
