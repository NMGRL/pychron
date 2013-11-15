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
from traits.api import Str, Instance, Color, Enum, Bool, Int
# from traitsui.api import View, Item, TableEditor
from traitsui.wx.code_editor import SourceEditor
# from traitsui.editors.code_editor import CodeEditor
from traitsui.basic_editor_factory import BasicEditorFactory
from pyface.wx.drag_and_drop import PythonDropTarget

#============= standard library imports ========================
import wx
#============= local library imports  ==========================
class _CodeEditor(SourceEditor):
    def init(self, parent):
        super(_CodeEditor, self).init(parent)

        if PythonDropTarget is not None:
            self.control.SetDropTarget(PythonDropTarget(self))

        keywords = '''and del from not while as elif global or with assert else if  
            pass yield break except import print class exec in raise continue finally is return def for lambda try'''
        if self.factory.keywords:
            keywords = ' '.join((keywords, self.factory.keywords))
        self.control.SetKeyWords(0, keywords)
        self.change_default_style()


        self.control.Bind(wx.EVT_KEY_UP, self._on_key_up)

    def _on_key_up(self, event):
        key = event.GetKeyCode()
        control = self.control
        if key == wx.WXK_NUMPAD_ENTER or key == wx.WXK_RETURN:
            pchar = control.GetCharAt(control.GetCurrentPos() - 1)
            if pchar == 10:  # newline, :
                line = control.GetCurrentLine()
                txt = control.GetLine(line - 1)
                indent = len(txt) - len(txt.lstrip())
                spchar = control.GetCharAt(control.GetCurrentPos() - 2)
                spchar = spchar == 58
                if indent or spchar:
                    control.SetLineIndentation(line, indent + control.GetTabWidth())
                    if not indent:
                        indent = 4
                    else:
                        if spchar:
                            indent += 4
                    control.GotoPos(control.GetCurrentPos() + indent)

        event.Skip()


    def change_default_style(self):
        from wx import stc
        self.control.SetEdgeMode(stc.STC_EDGE_LINE)
        self.control.SetEdgeColumn(200)

        self.set_style(stc.STC_P_DEFAULT, "#000000", "#ffffff")

        # Comment
        self.set_style(stc.STC_P_COMMENTLINE, "#007f00", "#ffffff")

        # Number
        self.set_style(stc.STC_P_NUMBER, "#007f7f", "#ffffff")

        # String
        self.set_style(stc.STC_P_STRING, "#7f007f", "#ffffff")

        # Single quoted string
        self.set_style(stc.STC_P_CHARACTER, "#7f007f", "#ffffff")

        # Keyword
        self.set_style(stc.STC_P_WORD, "#00007f", "#ffffff")

        # Triple quotes
        self.set_style(stc.STC_P_TRIPLE, "#7f0000", "#ffffff")

        # Triple double quotes
        self.set_style(stc.STC_P_TRIPLEDOUBLE, "#ff0000", "#ffffff")

        # Class name definition
        self.set_style(stc.STC_P_CLASSNAME, "#0000ff", "#ffffff")

        # Function or method name definition
        self.set_style(stc.STC_P_DEFNAME, "#007f7f", "#ffffff")

        # Operators
        self.set_style(stc.STC_P_OPERATOR, "#000000", "#ffffff")

        # Identifiers
        self.set_style(stc.STC_P_IDENTIFIER, "#000000", "#ffffff")

        # Comment-blocks
        self.set_style(stc.STC_P_COMMENTBLOCK, "#007f00", "#ffffff")

        # End of line where string is not closed
        self.set_style(stc.STC_P_STRINGEOL, "#000000", "#ffffff")


    def set_style(self, n, fore, back):
        fontname = 'courier new'
        if self.factory.fontname:
            fontname = self.factory.fontname

        fontsize = 12
        if self.factory.fontsize:
            fontsize = self.factory.fontsize

        self.control.StyleSetForeground(n, fore)
        # self.StyleSetBackground(n, '#c0c0c0')
        # self.StyleSetBackground(n, '#ffffff')
        self.control.StyleSetBackground(n, back)
        self.control.StyleSetFaceName(n, fontname)
        self.control.StyleSetSize(n, fontsize)

    def wx_dropped_on(self, x, y, data, result):
        control = self.control
        p = control.PositionFromPoint(wx.Point(x, y))
        control.SetCurrentPos(p)
        control.SetSelectionStart(p)

        m = self.object._command_text_factory(str(data))
        m = '\n{}'.format(m)
        control.AddText(m)


class PyScriptCodeEditor(BasicEditorFactory):
    klass = _CodeEditor

    fontsize = Int(12)
    fontname = Str('menlo regular')
    keywords = ''


    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------

    # Object trait containing list of line numbers to mark (optional)
    mark_lines = Str

    # Background color for marking lines
    mark_color = Color(0xECE9D8)

    # Object trait containing the currently selected line (optional)
    selected_line = Str

    # Object trait containing the currently selected text (optional)
    selected_text = Str

    # Object trait containing the currently selected text start position (optional)
    selected_start_pos = Str

    # Object trait containing the currently selected text end position (optional)
    selected_end_pos = Str

    # Background color for selected lines
    selected_color = Color(0xA4FFFF)

    # Where should the search toolbar be placed?
    search = Enum('top', 'bottom', 'none')

    # Background color for lines that match the current search
    search_color = Color(0xFFFF94)

    # Current line
    line = Str

    # Current column
    column = Str

    # Should code folding be enabled?
    foldable = Bool(True)

    # Should line numbers be displayed in the margin?
    show_line_numbers = Bool(True)

    # Is user input set on every change?
    auto_set = Bool(True)

    # Should the editor auto-scroll when a new **selected_line** value is set?
    auto_scroll = Bool(True)

    # Optional key bindings associated with the editor
    key_bindings = Instance('traitsui.key_bindings.KeyBindings')

    # Calltip clicked event
    calltip_clicked = Str

    # The lexer to use. Default is 'python'; 'null' indicates no lexing.
    lexer = Str('python')

    # Object trait containing the list of line numbers to dim (optional)
    dim_lines = Str

    # Object trait to dim lines to. Can be of form #rrggbb or a color spec. If
    # not specified, dark grey is used.
    dim_color = Str

    # Object trait containing the list of line numbers to put squiggles under
    # (optional)
    squiggle_lines = Str

    # Object trait for the color of squiggles. If not specified, red is used.
    squiggle_color = Str
#============= EOF =============================================
