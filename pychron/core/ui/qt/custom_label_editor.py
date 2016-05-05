# ===============================================================================
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
# ===============================================================================
# ============= enthought library imports =======================
from traits.api import HasTraits, Str, Int, Color, \
    Button, Any, Instance, on_trait_change
from traitsui.api import View, UItem
from traitsui.qt4.editor import Editor
from traitsui.basic_editor_factory import BasicEditorFactory
# ============= standard library imports ========================
import random
from PySide.QtGui import QLabel
# ============= local library imports  ==========================


class _CustomLabelEditor(Editor):
#    txtctrl = Any
    color = Any
    bgcolor = Any
    weight = Any
    text_size = Any

    def init(self, parent):
        self.control = self._create_control(parent)
        #        self.item.on_trait_change(self._set_color, 'color')
        self.sync_value(self.factory.color, 'color', mode='from')
        self.sync_value(self.factory.bgcolor, 'bgcolor', mode='from')
        self.sync_value(self.factory.weight, 'weight', mode='from')
        self.sync_value(self.factory.text_size, 'text_size', mode='from')

    @on_trait_change('color, bgcolor, weight, text_size')
    def _update_style(self):
        self._set_style()

    def _set_style(self, control=None,
                   color=None, bgcolor=None,
                   size=None, weight=None):
        if control is None:
            control = self.control

        if color is None:
            color = self.color.name()

        if bgcolor is None:
            if self.bgcolor is None:
                bgcolor = 'transparent'
            else:
                bgcolor = self.bgcolor.name()

        if size is None:
            size = self.text_size
            if not size:
                size = self.item.size

        if weight is None:
            weight = self.weight
            if not weight:
                weight = self.item.weight

        css = '''QLabel {{color:{};
        background-color:{};
        font-size:{}px;
        font-weight:{};}}
        '''.format(color,
                   bgcolor,
                   size,
                   weight)

        control.setStyleSheet(css)

    def update_editor(self):
        if self.control:
        #             print self.object, self.value
            if isinstance(self.value, (str, int, float, long, unicode)):
                self.control.setText(str(self.value))
                #            self.control.SetLabel(self.value)

    def _create_control(self, parent):
        control = QLabel()
        color = self.item.color.name()
        self._set_style(color=color,
                        control=control)

        control.setMargin(5)
        parent.setSpacing(0)

        return control


class CustomLabelEditor(BasicEditorFactory):
    klass = _CustomLabelEditor
    color = Str
    bgcolor = Str
    weight = Str
    text_size = Str


class CustomLabel(UItem):
    editor = Instance(CustomLabelEditor, ())
    size = Int(12)
    size_name = Str

    color = Color('black')
    color_name = Str

    bgcolor = Color('transparent')
    bgcolor_name = Str

    weight = Str('normal')

    top_padding = Int(5)
    bottom_padding = Int(5)
    left_padding = Int(5)
    right_padding = Int(5)

    def _size_name_changed(self):
        self.editor.text_size = self.size_name

    def _color_name_changed(self):
        self.editor.color = self.color_name

    def _bgcolor_name_changed(self):
        self.editor.bgcolor = self.bgcolor_name

# ===============================================================================
# demo
# ===============================================================================
class Demo(HasTraits):
    a = Str('asdfsdf')
    foo = Button
    color = Color('blue')
    bgcolor = Color('green')
    cnt = 0
    size = Int(12)

    def _foo_fired(self):
        self.a = 'fffff {}'.format(random.random())
        if self.cnt % 2 == 0:
            self.color = 'red'
            self.bgcolor = 'blue'
        else:
            self.bgcolor = 'red'
            self.color = 'blue'
        self.cnt += 1

    def traits_view(self):

        v = View(
            UItem('size'),
            'foo',
            CustomLabel('a',
                        #                             color='blue',
                        size=24,
                        size_name='size',
                        top_padding=10,
                        left_padding=10,
                        color_name='color',
                        bgcolor_name='bgcolor'
            ),
            resizable=True,
            width=400,
            height=100)
        return v


if __name__ == '__main__':
    d = Demo()
    d.configure_traits()
    # ============= EOF =============================================
    #        css = '''QLabel {{ color:{}; font-size:{}px; font-weight:{};}}
    # # '''.format(self.item.color.name(), self.item.size, self.item.weight)
    #        control.setStyleSheet(css)


    #        control.setAlignment(Qt.AlignCenter)
    #        control.setGeometry(0, 0, self.item.width, self.item.height)
    #        vbox = QVBoxLayout()
    #        vbox.setSpacing(0)

    #        hbox = QHBoxLayout()

    #        hbox.addLayout(vbox)
    #        parent.addLayout(vbox)
    #        print vbox.getContentsMargins()
    #        vbox.setContentsMargins(5, 5, 5, 5)
    #        vbox.setSpacing(-1)
    #        vbox.addSpacing(5)
    #        vbox.addSpacing(10)
    #        vbox.addWidget(control)
    #        vbox.addSpacing(5)
    #        vbox.addStretch()

    #        vbox.setSpacing(-1)
    #        vbox.setMargin(10)
    #        control.setLayout(vbox)
    #        parent.addWidget(control)