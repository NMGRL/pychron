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
from traits.api import HasTraits, List, String, Property, \
    Any, Button, Str, Dict
from traitsui.api import View, ListStrEditor, UItem, HGroup, Item, EnumEditor, VGroup

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor


class BaseMaker(HasTraits):
    formatter = Property(depends_on='label')
    clear_button = Button
    keywords = List
    non_keywords = List
    label = String
    activated = Any
    example = Property(depends_on='label')
    view_title = Str
    predefined_label = Str
    attribute_keys = Property(depends_on='label')

    def _get_attribute_keys(self):
        ks = []
        for k in self.label.split(' '):
            if k in self.attributes:
                ks.append(k.lower())

        return ks

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

    def _predefined_label_changed(self, new):
        self.label = new

    def _get_main_view(self):
        return VGroup(HGroup(Item('predefined_label',
                                  editor=EnumEditor(name='predefined_labels'))),
                      UItem('attributes',
                            editor=ListStrEditor(
                                editable=False,
                                activated='activated')),
                      HGroup(UItem('label'),
                             icon_button_editor('clear_button', 'edit-clear',
                                                tooltip='Clear current label'),
                             label='Label',
                             show_border=True),
                      HGroup(UItem('example', style='readonly'), label='Example',
                             show_border=True))

    def _get_additional_groups(self):
        pass

    def traits_view(self):
        vg = VGroup(self._get_main_view())
        grps = self._get_additional_groups()
        if grps:
            vg.content.extend(grps)

        v = View(
            vg,
            resizable=True,
            title=self.view_title,
            buttons=['OK', 'Cancel'],
            kind='livemodal')
        return v


class TitleMaker(BaseMaker):
    attributes = List(['Sample', 'Identifier', '<SPACE>'])

    attribute_formats = {'sample': '',
                         'identifier': ''}

    example_context = {'sample': 'NM-001', 'identifier': '20001'}
    view_title = 'Title Maker'
    predefined_labels = List(['Sample ( Identifier )',
                              'Sample'])

    delimiter = Str
    delimiters = Dict({',': 'Comma',
                       '\t': 'Tab',
                       ' ': 'Space',
                       ':': 'Colon',
                       ';': 'Semicolon'})

    def _get_additional_groups(self):
        return HGroup(Item('delimiter', editor=EnumEditor(name='delimiters'))),


class LabelMaker(BaseMaker):
    attributes = List(['Sample', 'Aliquot', 'Step', '<SPACE>'])
    attribute_formats = {'step': '',
                         'aliquot': '02n',
                         'sample': ''}

    example_context = {'step': 'A', 'aliquot': 1, 'sample': 'NM-001'}
    predefined_labels = List(['Sample - Aliquot Step',
                              'Sample',
                              'Aliquot Step'])
    view_title = 'Label Maker'


if __name__ == '__main__':
    lm = TitleMaker()
    lm.configure_traits()
#============= EOF =============================================

