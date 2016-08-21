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
import re

from traits.api import HasTraits, Str, Property, List, Enum, Button, Bool
from traitsui.api import View, UItem, HGroup, EnumEditor, InstanceEditor, Item
from traitsui.editors import ListEditor
from uncertainties import std_dev, nominal_value

from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.pipeline.nodes.base import BaseNode

COMP_RE = re.compile(r'<=|>=|>|<|==|between|not between')


class PipelineFilter(HasTraits):
    attribute = Str
    comparator = Enum('<', '>', '<=', '>=', '!=', 'between', 'not between')
    criterion = Str
    attributes = ('age', 'age error', 'kca', 'kca error', 'aliquot', 'step')

    def __init__(self, txt=None, *args, **kw):
        super(PipelineFilter, self).__init__(*args, **kw)
        if txt:
            self.parse_string(txt)

    def evaluate(self, item):
        attr = self.attribute
        comp = self.comparator
        crit = self.criterion
        val = self._get_value(item, attr)
        if comp in ('between', 'not between'):
            try:
                low, high = crit.split(',')
            except ValueError:
                return
            if comp == 'between':
                test = '{}<{}<{}'.format(low, attr, high)
            else:
                test = '{}>{} or {}>{}'.format(low, attr, attr, high)
        else:
            test = '{}{}{}'.format(attr, comp, crit)

        result = eval(test, {attr: val})
        return result

    def _get_value(self, item, attr):
        val = None
        if attr in ('aliquot', 'step'):
            val = getattr(item, attr)
        elif attr in ('age', 'age error'):
            val = getattr(item, 'uage')
            val = nominal_value(val) if attr == 'age' else std_dev(val)
        elif attr in ('kca', 'kca error'):
            val = getattr(item, 'kca')
            val = nominal_value(val) if attr == 'kca' else std_dev(val)

        return val

    def traits_view(self):
        v = View(HGroup(UItem('attribute',
                              editor=EnumEditor(name='attributes')), UItem('comparator'), UItem('criterion')))
        return v

    def to_string(self):
        return '{}{}{}'.format(self.attribute, self.comparator, self.criterion)

    def parse_string(self, s):
        c = COMP_RE.findall(s)[0]
        a, b = s.split(c)

        self.attribute = a
        self.comparator = c
        self.criterion = b


class FilterNode(BaseNode):
    name = Property(depends_on='filters')
    analysis_kind = 'unknowns'
    filters = List
    add_filter_button = Button
    remove = Bool(False)

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
            Item('remove', label='Remove Analyses'),
            kind='livemodal',
            buttons=['OK', 'Cancel'])
        return v

    def _generate_filter(self):
        def func(item):
            for fi in self.filters:
                if fi.evaluate(item):
                    return False
            else:
                return True

        return func

    def run(self, state):
        filterfunc = self._generate_filter()
        if self.remove:
            vs = filter(filterfunc, getattr(state, self.analysis_kind))
            setattr(state, self.analysis_kind, vs)
        else:
            ans = getattr(state, self.analysis_kind)
            for a in ans:
                if not filterfunc(a):
                    a.tag = 'omit'

    def add_filter(self, attr, comp, crit):
        self.filters.append(PipelineFilter(attribute=attr, comparator=comp, criterion=crit))

    def _get_name(self):
        return 'Filter ({})'.format(','.join((fi.to_string() for fi in self.filters)))

    def _to_template(self, d):
        vs = [fi.to_string() for fi in self.filters] * 3
        d['filters'] = vs

# ============= EOF =============================================
