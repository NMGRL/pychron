# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import HasTraits, Int, Any, List, Instance, Button, Dict
from traitsui.api import View, UItem, Item, HGroup, InstanceEditor, ListStrEditor


# ============= standard library imports ========================
# ============= local library imports  ==========================

# QLineEdit {font-size: 14px}
# QGroupBox {background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
#                                       stop: 0 #E0E0E0, stop: 1 #FFFFFF);
#            border: 2px solid gray;
#            border-radius: 5px;
#            margin-top: 1ex; /* leave space at the top for the title */
#            font-size: 14px;
#            font-weight: bold;}
# QGroupBox::title {subcontrol-origin: margin;
#                   subcontrol-position: top left; /* position at the top center */
#                   padding: 2 3px;}
# QComboBox {font-size: 14px}
# QLabel {font-size: 14px}
# QToolBox::tab {font-size: 15px}
# QToolTip {font-size: 14px}'''}
class Element(HasTraits):
    def generate_css(self):
        return 'Q{} {{{}}}'.format(self.__class__.__name__, self._generate_css())

    def _generate_css(self):
        return ''


class FontElement(Element):
    font_size = Int

    def _generate_font_size(self):
        return 'font-size: {}px'.format(self.font_size)

    def _generate_css(self):
        return ';'.join((self._generate_font_size(),))


class LineEdit(FontElement):
    pass


class GroupBox(Element):
    pass


class ComboBox(FontElement):
    pass


class Label(FontElement):
    pass


class ToolTip(FontElement):
    pass


class StyleSheetEditor(HasTraits):
    element_names = List(['LineEdit', 'GroupBox', 'ComboBox', 'Label', 'ToolTip'])
    elements = Dict
    active_element = Instance(Element)
    selected = Any

    test = Button

    def __init__(self, *args, **kw):
        super(StyleSheetEditor, self).__init__(*args, **kw)

        self.elements = {'LineEdit': LineEdit(),
                         'GroupBox': GroupBox(),
                         'ComboBox': ComboBox(),
                         'Label': Label(),
                         'ToolTip': ToolTip()}

        self.selected = 'LineEdit'

    def _test_fired(self):
        txt = self.generate_css()

    def generate_css(self):
        txt = []
        for ei in self.elements.itervalues():
            txt.append(ei.generate_css())

        return '\n'.join(txt)

    def _selected_changed(self):
        self.active_element = self.elements[self.selected]

    def traits_view(self):
        v = View(Item('test'),
                 HGroup(UItem('element_names', editor=ListStrEditor(selected='selected')),
                        UItem('active_element', style='custom', editor=InstanceEditor())))
        return v


if __name__ == '__main__':
    s = StyleSheetEditor()
    s.configure_traits()
# ============= EOF =============================================
