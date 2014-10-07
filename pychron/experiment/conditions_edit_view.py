# ===============================================================================
# Copyright 2014 Jake Ross
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
from pychron.core.ui import set_qt

set_qt()
# ============= enthought library imports =======================
from pyface.file_dialog import FileDialog
from traits.api import HasTraits, List, Instance, Any, \
    Enum, Float, on_trait_change, Str, Int

from traitsui.tabular_adapter import TabularAdapter
from traitsui.api import View, Tabbed, Group, UItem, \
    TabularEditor, VGroup, EnumEditor, Item, HGroup, spring, Label
# ============= standard library imports ========================
import re
import os
# ============= local library imports  ==========================

import yaml
from pychron.core.helpers.ctx_managers import no_update
from pychron.core.helpers.filetools import get_path
from pychron.experiment.automated_run.condition import condition_from_dict, CONDITION_ATTRS, MAX_REGEX, STD_REGEX, \
    CP_REGEX, MIN_REGEX, TruncationCondition, TerminationCondition, ActionCondition, SLOPE_REGEX
from pychron.paths import paths

COMP_REGEX = re.compile(r'<=|>=|>|<|==')


class ConditionsAdapter(TabularAdapter):
    columns = [('Attribute', 'attr'),
               ('Start', 'start_count'),
               ('Frequency', 'frequency'),
               ('Check', 'comp'), ]

    attr_width = Int(100)
    check_width = Int(200)
    start_width = Int(50)
    frequency_width = Int(100)


MOD_DICT = {'Slope': 'slope({})', 'Max': 'max({})', 'Min': 'min({})',
            'Current': '{}.cur',
            'StdDev': '{}.std'}


class ConditionGroup(HasTraits):
    conditions = List
    selected = Any

    attr = Str
    comparator = Enum('>', '<', '>=', '<=', '==')
    # use_max = Bool
    # use_min = Bool
    # use_current = Bool
    # use_std_dev = Bool
    # use_slope = Bool
    modifier = Str
    window = Int
    mapper = Str
    value = Float
    start_count = Int
    frequency = Int
    _no_update = False

    def dump(self):
        cs = []
        for ci in self.conditions:
            d = {k: getattr(ci, k) for k in ('attr', 'frequency', 'window', 'mapper')}
            d['start'] = ci.start_count
            d['check'] = ci.comp
            cs.append(d)
        return cs

    @on_trait_change('modifier, comparator, value')
    def _refresh_comp(self):
        if not self._no_update:
            attr = self.attr
            try:
                s = MOD_DICT[self.modifier]
                attr = s.format(attr)
            except KeyError:
                pass

            self.selected.comp = '{}{}{}'.format(attr, self.comparator, self.value)

    @on_trait_change('start_count, frequency, attr, window, mapper')
    def _update_selected(self, name, new):
        setattr(self.selected, name, new)

    def _selected_changed(self, new):
        if new:
            with no_update(self):
                for a in ('start_count', 'frequency', 'attr', 'window', 'mapper'):
                    setattr(self, a, getattr(new, a))

                for r, a in ((MAX_REGEX, 'Max'), (MIN_REGEX, 'Min'),
                             (STD_REGEX, 'StdDev'), (CP_REGEX, 'Current'),
                             (SLOPE_REGEX, 'Slope')):
                    if r.findall(new.comp):
                        setattr(self, 'modifier', a)
                        break

                # extract comparator
                m = COMP_REGEX.findall(new.comp)
                if m:
                    self.comparator = c = m[0]
                    self.value = float(new.comp.split(c)[-1])

    def __init__(self, conditions, klass, *args, **kw):
        if not klass:
            raise NotImplementedError

        if conditions:
            for ci in conditions:
                cx = condition_from_dict(ci, klass)
                if cx:
                    self.conditions.append(cx)

            self.selected = self.conditions[0]
        else:
            self.selected = klass('', '')

        super(ConditionGroup, self).__init__(*args, **kw)

    def traits_view(self):
        edit_grp = VGroup(HGroup(spring,UItem('object.selected.comp', style='readonly'),spring),
                          HGroup(UItem('attr',
                                       editor=EnumEditor(values=CONDITION_ATTRS)),
                                 Item('modifier',
                                      editor=EnumEditor(values=['Max', 'Min',
                                                                'StdDev', 'Current', 'Slope']))),
                          HGroup(UItem('comparator', enabled_when='attr'),
                                 Item('value', enabled_when='attr')),
                          Item('start_count', label='Start'),
                          Item('frequency'))

        v = View(UItem('conditions',
                       editor=TabularEditor(adapter=ConditionsAdapter(),
                                            editable=False,
                                            auto_update=True,
                                            auto_resize=True,
                                            selected='selected')),
                 edit_grp)
        return v


class ConditionsEditView(HasTraits):
    # actions = List
    # truncations = List
    # terminations = List
    actions_group = Instance(ConditionGroup)
    terminations_group = Instance(ConditionGroup)
    truncations_group = Instance(ConditionGroup)
    path = Str

    def open(self, name):
        self.load(name)

    def load(self, name):
        root = paths.default_conditions_dir
        p = get_path(root, name, ('.yaml', '.yml'))
        if p:
            with open(p, 'r') as fp:
                self.path = p
                yd = yaml.load(fp)
                actions = yd['actions']
                if actions:
                    self.actions_group = ConditionGroup(actions, ActionCondition)

                truncs = yd['truncations']
                if truncs:
                    self.truncations_group = ConditionGroup(truncs, TruncationCondition)

                terms = yd['terminations']
                if terms:
                    self.terminations_group = ConditionGroup(terms, TerminationCondition)

    def dump(self):
        if self.path:
            with open(self.path, 'w') as fp:
                d = {'terminations': self.terminations_group.dump() if self.terminations_group else [],
                     'actions': self.actions_group.dump() if self.actions_group else [],
                     'truncations': self.truncations_group.dump() if self.truncations_group else []}

                yaml.dump(d, fp, default_flow_style=False)

    def traits_view(self):
        noact = VGroup(spring, HGroup(spring, Label('No Actions Defined'), spring), spring,
                       defined_when='not actions_group')
        agrp = Group(UItem('actions_group',
                           defined_when='actions_group', style='custom'),
                     noact,
                     label='Actions')

        notrunc = VGroup(spring, HGroup(spring, Label('No Truncations Defined'), spring), spring,
                         defined_when='not truncations_group')
        trgrp = Group(UItem('truncations_group',
                            defined_when='truncations_group', style='custom'),
                      notrunc,
                      label='Truncations')

        noterm = VGroup(spring, HGroup(spring, Label('No Terminations Defined'), spring), spring,
                        defined_when='not terminations_group')
        tegrp = Group(UItem('terminations_group',
                            defined_when='terminations_group', style='custom'),
                      noterm,
                      label='Terminations')

        v = View(Tabbed(agrp, trgrp, tegrp),
                 width=800,
                 resizable=True,
                 buttons=['OK', 'Cancel'],
                 title='Edit Default Conditions')
        return v


def edit_conditions(name, app=None):
    if not name:
        dlg = FileDialog(action='open',
                         wildcard=FileDialog.create_wildcard('YAML', '*.yaml *.yml'),
                         default_directory=paths.default_conditions_dir)
        if dlg.open():
            if dlg.path:
                name = os.path.basename(dlg.path)

    if name:
        cev = ConditionsEditView()
        cev.open(name)
        if app:
            info = app.open_view(cev, kind='livemodal')
        else:
            info = cev.edit_traits(kind='livemodal')
            # info=cev.configure_traits(kind='livemodal')
        if info.result:
            cev.dump()


if __name__ == '__main__':
    c = ConditionsEditView()
    c.open('default_conditions')
    c.configure_traits()
    c.dump()
    # edit_conditions(None)
# ============= EOF =============================================


