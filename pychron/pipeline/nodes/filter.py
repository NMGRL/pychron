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
from operator import attrgetter

from traits.api import HasTraits, Str, Property, List, Enum, Button, Bool, Float, Range
from traitsui.api import View, UItem, HGroup, EnumEditor, InstanceEditor, Item, VGroup
from traitsui.editors import ListEditor
from uncertainties import std_dev, nominal_value

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.stats import calculate_mswd, validate_mswd
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.pipeline.nodes.base import BaseNode

COMP_RE = re.compile(r'<=|>=|>|<|==|between|not between')


class PipelineFilter(HasTraits):
    attribute = Str
    comparator = Enum('=', '<', '>', '<=', '>=', '!=', 'between', 'not between')
    criterion = Str
    attributes = ('age', 'age error', 'kca', 'kca error',
                  'aliquot', 'step', 'run date',
                  'extract_value', 'duration', 'cleanup', 'tag')

    chain_operator = Enum('and', 'or')
    show_chain = Bool
    remove_button = Button
    _eval_func = None

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
            except (AttributeError, ValueError, TypeError) as e:
                print('filter evaluation failed e={} test={}, dict={}'.format(e, test, edict))
                result = False

            return result

        self._eval_func = func

    def evaluate(self, item):
        attr = self.attribute
        comp = self.comparator
        crit = self.criterion
        ret = True
        if attr and comp and crit:
            val = self._get_value(item, attr)
            attr = attr.replace(' ', '_')
            edict = {attr: val}
            ret = self._eval_func(edict)

        return ret

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
        v = View(HGroup(icon_button_editor('remove_button', 'delete'),
                        UItem('chain_operator', visible_when='show_chain'),
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
        v = View(VGroup(VGroup(icon_button_editor('add_filter_button', 'add'),
                               UItem('filters', editor=ListEditor(mutable=False,
                                                                  style='custom',
                                                                  editor=InstanceEditor())),
                               show_border=True,
                               label='Filters'),
                        VGroup(Item('remove', label='Remove Analyses',
                                    tooltip='Remove Analyses from the list if checked  otherwise '
                                            'set temporary tag to "omit"'),
                               show_border=True),
                        VGroup(UItem('help_str', style='readonly'), label='Help', show_border=True)),
                 height=400,
                 width=600,
                 kind='livemodal',
                 title='Edit Filter',
                 resizable=True,
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

        ans = getattr(state, self.analysis_kind)
        if self.remove:
            # vs = list(filter(filterfunc, getattr(state, self.analysis_kind)))
            vs = [a for a in ans if filterfunc(a)]
            setattr(state, self.analysis_kind, vs)
        else:
            for a in ans:
                if not filterfunc(a):
                    a.temp_status = 'omit'

    def add_filter(self, attr, comp, crit):
        self.filters.append(PipelineFilter(attribute=attr, comparator=comp, criterion=crit))

    def _get_name(self):
        return 'Filter ({})'.format(','.join((fi.to_string() for fi in self.filters)))

    def _to_template(self, d):
        vs = [fi.to_string() for fi in self.filters] * 3
        d['filters'] = vs


class MSWDFilterNode(BaseNode):
    name = 'MSWD Filter'
    kind = Enum('Mahon', 'Threshold', 'Plateau')
    mswd_threshold = Float
    plateau_threshold = Range(0.0, 5.0)
    attr = Enum('Age', 'KCa')
    _prev_mswd = 0

    def traits_view(self):
        v = okcancel_view(VGroup(HGroup(UItem('kind'), UItem('attr')),
                          VGroup(Item('mswd_threshold', label='Threshold', visible_when='kind=="Threshold"'),
                                 Item('plateau_threshold', label='% Threshold', visible_when='kind=="Plateau"'))),
                          title='Configure MSWD Filter',
                          width=300,
                          height=100,
                          resizable=True)
        return v

    def run(self, state):
        unks = state.unknowns
        unks = [ui for ui in unks if not ui.is_omitted_by_tag()]
        attr = self.attr.lower()
        unks = sorted(unks, key=attrgetter(attr))
        kind = self.kind.lower()
        self._prev_mswd = 0
        for i in range(len(unks) - 2):
            if self._validate_mswd(kind, unks, attr):
                break
            else:
                unks = self._filter_mswd(unks)

    def _validate_mswd(self, kind, unks, attr):
        if attr == 'age':
            xs = [u.age for u in unks]
            es = [u.age_err_wo_j for u in unks]
        elif attr == 'kca':
            vs = [u.kca for u in unks]
            xs = [nominal_value(v) for v in vs]
            es = [std_dev(v) for v in vs]

        mswd = calculate_mswd(xs, es)
        if kind == 'mahon':
            v = validate_mswd(mswd, len(xs))
        elif kind == 'threshold':
            v = mswd < self.mswd_threshold
        else:
            v = abs(mswd - self._prev_mswd) / mswd * 100 < self.plateau_threshold
            self._prev_mswd = mswd

        return v

    def _filter_mswd(self, unks):
        # remove oldest age
        unks[-1].temp_status = 'omit'
        return unks[:-1]


if __name__ == '__main__':
    a = FilterNode()
    a.configure_traits()
# ============= EOF =============================================
