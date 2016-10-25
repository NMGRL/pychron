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
import datetime
import re

from traits.api import HasTraits, Str, Property, List, Enum, Button, Bool
from traitsui.api import View, UItem, HGroup, EnumEditor, InstanceEditor, Item, VGroup
from traitsui.editors import ListEditor
from uncertainties import std_dev, nominal_value

from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.pipeline.nodes.base import BaseNode

COMP_RE = re.compile(r'<=|>=|>|<|==|between|not between')


class PipelineFilter(HasTraits):
    attribute = Str
    comparator = Enum('=', '<', '>', '<=', '>=', '!=', 'between', 'not between')
    criterion = Str
    attributes = ('age', 'age error', 'kca', 'kca error', 'aliquot', 'step', 'run date')

    chain_operator = Enum('and', 'or')
    show_chain = Bool

    def __init__(self, txt=None, *args, **kw):
        super(PipelineFilter, self).__init__(*args, **kw)
        if txt:
            self.parse_string(txt)

    def generate_evaluate_func(self):
        def func(edict):
            attr = self.attribute
            comp = self.comparator
            crit = self.criterion

            # val = self._get_value(item, attr)
            # edict = {attr: val}

            attr = attr.replace(' ', '_')

            if comp == '=':
                comp = '=='

            if comp in ('between', 'not between'):

                try:
                    low, high = crit.split(',')
                except ValueError:
                    return
                if attr == 'run_date':
                    low = self._convert_date(low)
                    high = self._convert_date(high)
                    edict['lowtag'] = low
                    edict['hightag'] = high
                    if comp == 'between':
                        test = 'lowtag<{}<=hightag'.format(attr)
                    else:
                        test = 'lowtag>{} or {}>high'.format(attr, attr)
                else:
                    if attr == 'step':
                        low = '"{}"'.format(low)
                        high = '"{}"'.format(high)

                    if comp == 'between':
                        test = '{}<{}<{}'.format(low, attr, high)
                    else:
                        test = '{}>{} or {}>{}'.format(low, attr, attr, high)
            else:
                if attr == 'step':
                    crit = '"{}"'.format(crit)

                if attr == 'run_date':
                    crit = self._convert_date(crit)
                    test = '{}{}crittag'.format(attr, comp)
                    edict['crittag'] = crit
                else:
                    test = '{}{}{}'.format(attr, comp, crit)

            try:
                result = eval(test, edict)
            except (AttributeError, ValueError):
                result = False

            return result

        self._eval_func = func

    def evaluate(self, item):
        attr = self.attribute
        val = self._get_value(item, attr)
        attr = attr.replace(' ', '_')
        edict = {attr: val}
        return self._eval_func(edict)

    def _convert_date(self, d):
        for s in ('%B', '%b', '%m',
                  '%m/%d', '%m/% %H:%M'
                           '%m/%d/%y', '%m/%d/%Y',
                  '%m/%d/%y %H:%M', '%m/%d/%Y %H:%M',):
            try:
                return datetime.datetime.strptime(d, s)
            except ValueError:
                pass

    def _get_value(self, item, attr):
        val = None
        if attr in ('aliquot', 'step'):
            val = getattr(item, attr)
        elif attr == 'run date':
            val = item.rundate
        elif attr in ('age', 'age error'):
            val = getattr(item, 'uage')
            val = nominal_value(val) if attr == 'age' else std_dev(val)
        elif attr in ('kca', 'kca error'):
            val = getattr(item, 'kca')
            val = nominal_value(val) if attr == 'kca' else std_dev(val)

        return val

    def traits_view(self):
        v = View(HGroup(UItem('chain_operator', visible_when='show_chain'),
                        UItem('attribute',
                              editor=EnumEditor(name='attributes')),
                        UItem('comparator'),
                        UItem('criterion')))
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

    help_str = '''The behavior is filter-in NOT filter-out. Analyses that match the filter are kept'''

    def load(self, nodedict):
        fs = [PipelineFilter(fi) for fi in nodedict['filters']]
        self.filters = fs

    def _filters_default(self):
        return [PipelineFilter()]

    def _add_filter_button_fired(self):
        self.filters.append(PipelineFilter())

    def _filters_items_changed(self):
        for i, fi in enumerate(self.filters):
            fi.show_chain = i != 0

    def traits_view(self):
        v = View(VGroup(icon_button_editor('add_filter_button', 'add'),
                        UItem('filters', editor=ListEditor(mutable=False,
                                                           style='custom',
                                                           editor=InstanceEditor())),
                        Item('remove', label='Remove Analyses',
                             tooltip='Remove Analyses from the list if checked  otherwise '
                                     'set temporary tag to "omit"'),
                        VGroup(UItem('help_str', style='readonly'), label='Help', show_border=True)),
                 kind='livemodal',
                 buttons=['OK', 'Cancel'])
        return v

    def _generate_filter(self):
        def func(item):
            fo = self.filters[0]
            flag = fo.evaluate(item)
            for fi in self.filters[1:]:
                b = fi.evaluate(item)
                if fi.chain_operator == 'and':
                    flag = flag and b
                else:
                    flag = flag or b
            return flag

        return func

    def run(self, state):
        for fi in self.filters:
            fi.generate_evaluate_func()

        def filterfunc(item):
            fo = self.filters[0]
            flag = fo.evaluate(item)
            for f in self.filters[1:]:
                b = f.evaluate(item)
                if fi.chain_operator == 'and':
                    flag = flag and b
                else:
                    flag = flag or b
            return flag

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
