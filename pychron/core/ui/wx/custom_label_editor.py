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
from traits.api import HasTraits, Str, Int, Color, Button, Any, Instance
from traitsui.api import View, UItem
from traitsui.wx.editor import Editor
from traitsui.basic_editor_factory import BasicEditorFactory
# from traitsui.wx.basic_editor_factory import BasicEditorFactory
import wx
import random
#============= standard library imports ========================
#============= local library imports  ==========================

class _CustomLabelEditor(Editor):
    txtctrl = Any

    def init(self, parent):
        self.control = self._create_control(parent)

    def update_editor(self):
        self.txtctrl.SetLabel(self.value)

    def _create_control(self, parent):
        panel = wx.Panel(parent, -1)
        size = None
        if self.item.width > 1 and self.item.height > 1:
            size = (self.item.width, self.item.height)
        txtctrl = wx.StaticText(panel, label=self.value,
                                size=size
                                )
        family = wx.FONTFAMILY_DEFAULT
        style = wx.FONTSTYLE_NORMAL
        weight = wx.FONTWEIGHT_NORMAL
        font = wx.Font(self.item.size, family, style, weight)
        txtctrl.SetFont(font)
        txtctrl.SetForegroundColour(self.item.color)
        self.txtctrl = txtctrl

        vsizer = wx.BoxSizer(wx.VERTICAL)
#
        if self.item.top_padding is not None:
            self.add_linear_space(vsizer, self.item.top_padding)
#
        vsizer.Add(txtctrl)
#
        if self.item.bottom_padding is not None:
            self.add_linear_space(vsizer, self.item.bottom_padding)
        sizer = vsizer

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        if self.item.left_padding is not None:
            self.add_linear_space(hsizer, self.item.left_padding)

        hsizer.Add(sizer)
        if self.item.right_padding is not None:
            self.add_linear_space(hsizer, self.item.right_padding)
        sizer = hsizer

        panel.SetSizer(sizer)
        return panel


    def add_linear_space(self, sizer, pad):
        orientation = sizer.GetOrientation()
        if orientation == wx.HORIZONTAL:
            sizer.Add((pad, 0))
        else:
            sizer.Add((0, pad))

class CustomLabelEditor(BasicEditorFactory):
    klass = _CustomLabelEditor


class CustomLabel(UItem):
    editor = Instance(CustomLabelEditor, ())
    size = Int
    color = Color('green')
    top_padding = Int(5)
    bottom_padding = Int(5)
    left_padding = Int(5)
    right_padding = Int(5)
#===============================================================================
# demo
#===============================================================================
class Demo(HasTraits):
    a = Str('asdfsdf')
    foo = Button
    def _foo_fired(self):
        self.a = 'fffff {}'.format(random.random())

    def traits_view(self):
        v = View(
#                 'foo',
                 CustomLabel('a',
                             color='blue',
                             size=15,
                             top_padding=10,
                             left_padding=10,
                             ),
                  width=100,
                 height=100)
        return v

if __name__ == '__main__':
    d = Demo()
    d.configure_traits()
#============= EOF =============================================
