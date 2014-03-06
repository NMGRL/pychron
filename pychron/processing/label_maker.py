#===============================================================================
# Copyright 2014 Jake Ross
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
from pychron.core.ui import set_qt

set_qt()


#============= enthought library imports =======================
from traits.api import HasTraits, List, String, Property, Any, Button
from traitsui.api import View, ListStrEditor, UItem, HGroup

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor


class LabelMaker(HasTraits):
    attributes = List(['Sample', 'Aliquot', 'Step', '<SPACE>'])
    attribute_formats = {'step': '',
                         'aliquot': '02n',
                         'sample': ''}

    keywords = List
    non_keywords = List
    label = String
    activated = Any
    example = Property(depends_on='label')

    example_context = {'step': 'A', 'aliquot': 1, 'sample': 'NM-001'}
    formatter = Property(depends_on='label')
    clear_button = Button

    def _get_formatter(self):
        ns = []
        for k in self.label.split(' '):
            if k in self.attributes:
                if k == '<SPACE>':
                    k = ' '
                else:
                    k = k.lower()
                    f = self.attribute_formats[k]
                    k = '{{{}:{}}}'.format(k, f)
            ns.append(k)
        s = ''.join(ns)
        return s

    def _get_example(self):
        f = self.formatter
        return f.format(**self.example_context)

    def _clear_button_fired(self):
        self.label = ''

    def _activated_changed(self, new):
        if new:
            self.keywords.append(self.activated)
            if self.label:
                self.label += ' {}'.format(new)
            else:
                self.label = new
            self.activated = None

    def traits_view(self):
        v = View(UItem('attributes',
                       editor=ListStrEditor(
                           editable=False,
                           activated='activated')),
                 HGroup(UItem('label'),
                        icon_button_editor('clear_button', 'edit-clear',
                                           tooltip='Clear current label'),
                        label='Label',
                        show_border=True),
                 HGroup(UItem('example', style='readonly'), label='Example',
                        show_border=True),
                 resizable=True,
                 title='Label Maker',
                 buttons=['OK', 'Cancel'],
                 kind='livemodal')
        return v


if __name__ == '__main__':
    lm = LabelMaker()
    lm.configure_traits()
#============= EOF =============================================

