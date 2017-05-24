# ===============================================================================
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
# ===============================================================================
# ============= enthought library imports =======================
from traits.api import List, Property, \
    Str, Dict
from traitsui.api import UItem, HGroup, Item, EnumEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.templater.base_templater import BaseTemplater
from pychron.core.templater.templater_view import BaseTemplateView


class TitleTemplater(BaseTemplater):
    attributes = List(['Project', 'Sample', 'Identifier', 'Aliquot', 'Material',
                       'AlphaCounter',
                       'NumericCounter', '<SPACE>'])

    attribute_formats = {'sample': '',
                         'identifier': '',
                         'project': '',
                         'aliquot': '02n',
                         'material': '',
                         'numericcounter': '',
                         'alphacounter': ''}

    example_context = {'sample': 'NM-001',
                       'identifier': '20001',
                       'project': 'J-Curve',
                       'aliquot': 1,
                       'material': 'GMC',
                       'numericcounter': 1,
                       'alphacounter': 'A'}

    base_predefined_labels = List(['Sample ( Identifier )',
                                   'Sample ( Identifier - Aliquot )',
                              'Sample ( Identifier - Aliquot , Material )',
                              'AlphaCounter . <SPACE> Sample ( Identifier - Aliquot , Material )',
                              'Sample',
                              'Project <SPACE> Sample ( Identifier )'])

    delimiter = Str
    delimiters = Dict({',': 'Comma',
                       '\t': 'Tab',
                       ' ': 'Space',
                       ':': 'Colon',
                       ';': 'Semicolon'})

    example = Property(depends_on='label, delimiter, leading_text, trailing_text')
    multi_group_example = Property(depends_on='label, delimiter, leading_text, trailing_text')
    leading_text = Str
    trailing_text = Str
    leading_texts = List(['Project'])
    trailing_texts = List(['Project'])
    persistence_name = 'title_maker'

    def _get_example(self):
        return self._assemble_example(1)

    def _get_multi_group_example(self):
        return self._assemble_example(2)

    def _assemble_example(self, n):
        f = self.formatter
        ts = []
        for _ in range(n):
            ts.append(f.format(**self.example_context))

        t = self.delimiter.join(ts)
        lt = self.leading_text
        if lt:
            if lt.lower() in self.example_context:
                lt = self.example_context[lt.lower()]
            t = '{} {}'.format(lt, t)

        tt = self.trailing_text
        if tt:
            if tt.lower() in self.example_context:
                tt = self.example_context[tt.lower()]
            t = '{} {}'.format(t, tt)
        return t


class LabelTemplater(BaseTemplater):
    attributes = List(['Sample', 'Aliquot', 'Step', 'Name', '<SPACE>'])
    attribute_formats = {'step': '',
                         'aliquot': '02n',
                         'sample': '',
                         'name': ''}

    example_context = {'step': 'A', 'aliquot': 1, 'sample': 'NM-001', 'name': 'Foo'}
    base_predefined_labels = List(['Sample - Aliquot Step',
                                   'Sample',
                              'Aliquot Step'])
    persistence_name = 'label_maker'


class LabelTemplateView(BaseTemplateView):
    view_title = 'Label Maker'


class TitleTemplateView(BaseTemplateView):
    view_title = 'Title Maker'

    def _get_additional_groups(self):
        return (HGroup(UItem('multi_group_example', style='readonly'),
                       show_border=True, label='Multi Group Example'),
                HGroup(Item('leading_text', label='Leading'),
                       UItem('leading_text',
                             width=-25,
                             editor=EnumEditor(name='leading_texts')),
                       Item('trailing_text', label='Trailing'),
                       UItem('trailing_text',
                             width=-25,
                             editor=EnumEditor(name='trailing_texts'))),
                HGroup(Item('delimiter', editor=EnumEditor(name='delimiters'))))


# if __name__ == '__main__':
#     # lm = TitleMaker()
#     lm = LabelTemplater()
#     lm.configure_traits()
# ============= EOF =============================================

