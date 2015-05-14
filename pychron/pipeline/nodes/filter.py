# ===============================================================================
# Copyright 2015 Jake Ross
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
from traits.api import HasTraits, Str, Property, List, Enum, Button
from traitsui.api import View, UItem, HGroup, EnumEditor, InstanceEditor
# ============= standard library imports ========================
import re
# ============= local library imports  ==========================
from traitsui.editors import ListEditor
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.pipeline.nodes.base import BaseNode

COMP_RE = re.compile(r'<=|>=|>|<|==')


class PipelineFilter(HasTraits):
    attribute = Str
    comparator = Enum('<', '>', '<=', '>=', '!=')
    criterion = Str
    attributes = ('uage', 'aliquot', 'step')

    def __init__(self, txt=None, *args, **kw):
        super(PipelineFilter, self).__init__(*args, **kw)
        if txt:
            self.parse_string(txt)

    def evaluate(self, item):
        attr = self.attribute
        comp = self.comparator
        crit = self.criterion
        val = getattr(item, attr)
        return eval('{}{}{}'.format(attr, comp, crit), {attr: val})

    def traits_view(self):
        v = View(HGroup(UItem('attribute',
                              editor=EnumEditor(name='attributes')), UItem('comparator'), UItem('criterion')))
        return v

    def to_string(self):
        return '{}{}{}'.format(self.attribute, self.comparator, self.criterion)

    def parse_string(self, s):
        c = COMP_RE.findall(s)[0]
        a, b = s.split(c)

        print s
        print a
        print c
        print b

        self.attribute = a
        self.comparator = c
        self.criterion = b


class FilterNode(BaseNode):
    name = Property(depends_on='filters')
    analysis_kind = 'unknowns'
    filters = List
    add_filter_button = Button

    def load(self, nodedict):
        fs = [PipelineFilter(fi) for fi in nodedict['filters']]
        self.filters = fs

    def _filters_default(self):
        return [PipelineFilter()]

    def _add_filter_button_fired(self):
        self.filters.append(PipelineFilter())

    def traits_view(self):
        v = View(
            icon_button_editor('add_filter_button', 'add'),
            UItem('filters', editor=ListEditor(mutable=False,
                                               style='custom',
                                               editor=InstanceEditor())),
            kind='livemodal',
            buttons=['OK', 'Cancel'])
        return v

    def configure(self):
        info = self.edit_traits()
        if info.result:
            return True

    def _generate_filter(self):
        def func(item):
            for fi in self.filters:
                if fi.evaluate(item):
                    return False
            else:
                return True

        return func

    def run(self, state):
        vs = filter(self._generate_filter(), getattr(state, self.analysis_kind))
        setattr(state, self.analysis_kind, vs)

    def add_filter(self, attr, comp, crit):
        self.filters.append(PipelineFilter(attribute=attr, comparator=comp, criterion=crit))

    def _get_name(self):
        return 'Filter ({})'.format(','.join((fi.to_string() for fi in self.filters)))

    def _to_template(self, d):
        vs = [fi.to_string() for fi in self.filters] * 3
        d['filters'] = vs
# ============= EOF =============================================



