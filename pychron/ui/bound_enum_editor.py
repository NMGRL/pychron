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
from traits.api import Callable
#============= enthought library imports =======================
from traitsui.wx.enum_editor import SimpleEditor
from traitsui.editors.enum_editor \
    import ToolkitEditorFactory
#============= standard library imports ========================
import wx
#============= local library imports  ==========================


class _BoundEnumEditor(SimpleEditor):
# class _BoundEnumEditor(ListEditor):
# class _BoundEnumEditor(CustomEditor):
    def init(self, parent):
#        super(_BoundEnumEditor, self).init(parent)

        self.control = control = wx.ComboBox(parent, -1, self.names[0],
                               wx.Point(0, 0),
                               wx.Size(-1, -1),
                                self.names,
                                style=wx.CB_DROPDOWN
                               )

#         wx.EVT_CHOICE(parent, self.control.GetId(), self.update_object)
        control.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
#        parent.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
        parent.Bind(wx.EVT_COMBOBOX, self.update_object, control)

        self._no_enum_update = 0
        self.set_tooltip()
#        parent.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
#        self.control.Bind(wx.EVT_TEXT, None)
#        wx.EVT_CHOICE(parent, self.control.GetId(), None)
#        s = self.control.GetWindowStyle()
#        self.control.SetWindowStyle(s | wx.WANTS_CHARS)
#        self.control.Bind(wx.EVT_CHAR, self.onKeyDown)
#        parent.Bind(wx.EVT_CHAR, self.onKeyDown)
#        self.control.Bind(wx.EVT_CHAR_HOOK, self.onKeyDown)

#        print self.control
    def update_object(self, event):
        super(_BoundEnumEditor, self).update_object(event)
        if self._bind:
            if self.factory.do_binding is not None:
                self.factory.do_binding(self.value)

        self._bind = False

    def onKeyDown(self, event):
        if event.CmdDown():
            self._bind = True
#        else:
#            self._bind = False
#        event.RequestMore()
#        event.Skip()

class BoundEnumEditor(ToolkitEditorFactory):
    evaluate = lambda x: x
    do_binding = Callable
    def _get_custom_editor_class(self):
        return _BoundEnumEditor

    def _get_simple_editor_class(self):
        return _BoundEnumEditor
#============= EOF =============================================
