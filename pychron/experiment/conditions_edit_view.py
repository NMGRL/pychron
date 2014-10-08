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
    Enum, Float, on_trait_change, Str, Int, Property

from traitsui.tabular_adapter import TabularAdapter
from traitsui.api import View, Tabbed, Group, UItem, \
    TabularEditor, VGroup, EnumEditor, Item, HGroup, spring, Label, Handler
# ============= standard library imports ========================
import re
import os
# ============= local library imports  ==========================

import yaml
from pychron.core.helpers.ctx_managers import no_update
from pychron.core.helpers.filetools import get_path
from pychron.experiment.automated_run.condition import condition_from_dict, MAX_REGEX, STD_REGEX, \
    CP_REGEX, MIN_REGEX, TruncationCondition, TerminationCondition, ActionCondition, SLOPE_REGEX, BASELINE_REGEX, \
    BASELINECOR_REGEX, COMP_REGEX, AVG_REGEX, ACTIVE_REGEX
from pychron.paths import paths


class PRConditionsAdapter(TabularAdapter):
    columns = [('Attribute', 'attr'),
               ('Check', 'comp'), ]

    attr_width = Int(100)
    check_width = Int(200)


class ConditionsAdapter(TabularAdapter):
    columns = [('Attribute', 'attr'),
               ('Start', 'start_count'),
               ('Frequency', 'frequency'),
               ('Check', 'comp'), ]

    attr_width = Int(100)
    check_width = Int(200)
    start_width = Int(50)
    frequency_width = Int(100)


FUNC_DICT = {'Slope': 'slope({})', 'Max': 'max({})', 'Min': 'min({})', 'Averge': 'average({})'}
MOD_DICT = {'Current': '{}.cur', 'StdDev': '{}.std', 'Baseline': '{}.bs',
            'Inactive':'{}.inactive',
            'BaselineCorrected': '{}.bs_corrected'}


class ConditionGroup(HasTraits):
    conditions = List
    selected = Any

    attr = Str
    available_attrs=List
    comparator = Enum('', '>', '<', '>=', '<=', '==')
    # use_max = Bool
    # use_min = Bool
    # use_current = Bool
    # use_std_dev = Bool
    # use_slope = Bool

    modifier_enabled = Property(depends_on='function')
    modifier = Str
    function = Str
    window = Int
    mapper = Str
    value = Float
    start_count = Int
    frequency = Int
    _no_update = False

    dump_attrs = [('attr', ''), ('frequency', ''),
                  ('window', ''), ('mapper', ''),
                  ('start', 'start_count'),
                  ('check', 'comp')]

    def _get_modifier_enabled(self):
        return not self.function

    def dump(self):
        cs = []
        for ci in self.conditions:
            d = {}
            for a, b in self.dump_attrs:
                if not b:
                    b = a
                d[a] = getattr(ci, b)

            # d = {k: getattr(ci, k) for k in ('attr', 'frequency', 'window', 'mapper')}
            # d['start'] = ci.start_count
            # d['check'] = ci.comp
            cs.append(d)
        return cs

    @on_trait_change('function, modifier, comparator, value, attr')
    def _refresh_comp(self, name, new):
        if not self._no_update:

            with no_update(self):
                if name == 'function':
                    self.modifier = ''
                elif name == 'modifier':
                    self.function = ''

            attr = self.attr
            try:
                s = MOD_DICT[self.modifier]
                attr = s.format(attr)
            except KeyError:
                pass

            try:
                s = FUNC_DICT[self.function]
                attr = s.format(attr)
            except KeyError:
                pass

            if self.comparator:
                self.selected.comp = '{}{}{}'.format(attr, self.comparator, self.value)
            else:
                self.selected.comp = '{}'.format(attr)

    @on_trait_change('start_count, frequency, attr, window, mapper')
    def _update_selected(self, name, new):
        setattr(self.selected, name, new)

    def _selected_changed(self, new):
        if new:
            with no_update(self):
                for a in ('start_count', 'frequency', 'attr', 'window', 'mapper'):
                    setattr(self, a, getattr(new, a))

                for r, a in ((MAX_REGEX, 'Max'), (MIN_REGEX, 'Min'),
                             (AVG_REGEX, 'Average'),
                             (SLOPE_REGEX, 'Slope')):
                    if r.findall(new.comp):
                        setattr(self, 'function', a)
                        break

                for r, a in ((CP_REGEX, 'Current'),
                             (STD_REGEX, 'StdDev'),
                             (ACTIVE_REGEX, 'Active'),
                             (BASELINECOR_REGEX, 'BaselineCorrected'),
                             (BASELINE_REGEX, 'Baseline')):
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
        edit_grp = VGroup(HGroup(spring, UItem('object.selected.comp', style='readonly'), spring),
                          HGroup(UItem('attr',
                                       editor=EnumEditor(name='available_attrs')),
                                 Item('function',
                                      editor=EnumEditor(values=['', 'Average', 'Max', 'Min', 'Slope'])),
                                 Item('modifier',
                                      enabled_when='modifier_enabled',
                                      editor=EnumEditor(values=['', 'StdDev', 'Current', 'Active',
                                                                'Baseline', 'BaselineCorrected']))),
                          HGroup(UItem('comparator', enabled_when='attr'),
                                 Item('value', enabled_when='attr')),
                          HGroup(Item('start_count',
                                      tooltip='Number of counts to wait until performing check',
                                      label='Start')),
                          Item('frequency',
                               tooltip='Number of counts between each check'))

        v = View(UItem('conditions',
                       editor=TabularEditor(adapter=ConditionsAdapter(),
                                            editable=False,
                                            auto_update=True,
                                            auto_resize=True,
                                            selected='selected')),
                 edit_grp)
        return v


class PostRunGroup(ConditionGroup):
    dump_attrs = [('attr', ''),
                  ('window', ''),
                  ('mapper', ''),
                  ('check', 'comp')]

    def traits_view(self):
        edit_grp = VGroup(HGroup(spring, UItem('object.selected.comp', style='readonly'), spring),
                          HGroup(UItem('attr',
                                       editor=EnumEditor(name='available_attrs')),
                                 Item('function',
                                      editor=EnumEditor(values=['', 'Max', 'Min', 'Slope'])),
                                 Item('modifier',
                                      enabled_when='modifier_enabled',
                                      editor=EnumEditor(values=['', 'StdDev', 'Current',
                                                                'Baseline', 'BaselineCorrected']))),
                          HGroup(UItem('comparator', enabled_when='attr'),
                                 Item('value', enabled_when='attr and comparator')))

        v = View(UItem('conditions',
                       editor=TabularEditor(adapter=PRConditionsAdapter(),
                                            editable=False,
                                            auto_update=True,
                                            auto_resize=True,
                                            selected='selected')),
                 edit_grp)
        return v


class CEHandler(Handler):
    def object_path_changed(self, info):
        info.ui.title += ' - [{}]'.format(info.object.name)


class ConditionsEditView(HasTraits):
    actions_group = Instance(ConditionGroup)
    terminations_group = Instance(ConditionGroup)
    truncations_group = Instance(ConditionGroup)
    post_run_terminations_group = Instance(ConditionGroup)
    path = Str

    def __init__(self, detectors=None, *args, **kw):
        self.available_attrs = ['', 'Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36',
                                'kca', 'kcl']
        if detectors:
            self.available_attrs.extend(detectors)

        super(ConditionsEditView, self).__init__(*args, **kw)

    @property
    def name(self):
        return os.path.relpath(self.path, paths.default_conditions_dir)

    def open(self, name):
        self.load(name)

    def load(self, name):
        root = paths.default_conditions_dir
        p = get_path(root, name, ('.yaml', '.yml'))
        if p:
            self.path = p
            with open(p, 'r') as fp:
                yd = yaml.load(fp)
                actions = yd['actions']
                if actions:
                    self.actions_group = ConditionGroup(actions, ActionCondition, available_attrs=self.available_attrs)

                truncs = yd['truncations']
                if truncs:
                    self.truncations_group = ConditionGroup(truncs, TruncationCondition,
                                                            available_attrs=self.available_attrs)

                terms = yd['terminations']
                if terms:
                    self.terminations_group = ConditionGroup(terms, TerminationCondition,
                                                             available_attrs=self.available_attrs)

                post = yd['post_run_terminations']
                if post:
                    self.post_run_terminations_group = PostRunGroup(post, TerminationCondition,
                                                                    available_attrs=self.available_attrs)

    def dump(self):
        if self.path:
            with open(self.path, 'w') as fp:
                d = dict(post_run_terminations=self.post_run_terminations_group.dump()
                if self.post_run_terminations_group else [],
                         terminations=self.terminations_group.dump()
                         if self.terminations_group else [],
                         actions=self.actions_group.dump()
                         if self.actions_group else [],
                         truncations=self.truncations_group.dump()
                         if self.truncations_group else [])

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

        nopterm = VGroup(spring, HGroup(spring, Label('No Post Run Terminations Defined'), spring), spring,
                         defined_when='not post_run_terminations_group')
        prtegrp = Group(UItem('post_run_terminations_group',
                              defined_when='post_run_terminations_group', style='custom'),
                        nopterm,
                        label='Post Run Terminations')

        v = View(Tabbed(agrp, trgrp, tegrp, prtegrp),
                 width=800,
                 resizable=True,
                 handler=CEHandler(),
                 buttons=['OK', 'Cancel'],
                 title='Edit Default Conditions')
        return v


def edit_conditions(name, detectors=None, app=None):
    if not name:
        dlg = FileDialog(action='open',
                         wildcard=FileDialog.create_wildcard('YAML', '*.yaml *.yml'),
                         default_directory=paths.default_conditions_dir)
        if dlg.open():
            if dlg.path:
                name = os.path.basename(dlg.path)

    if name:
        cev = ConditionsEditView(detectors)
        cev.open(name)
        if app:
            info = app.open_view(cev, kind='livemodal')
        else:
            info = cev.edit_traits(kind='livemodal')
            # info=cev.configure_traits(kind='livemodal')
        if info.result:
            cev.dump()


if __name__ == '__main__':
    c = ConditionsEditView(detectors=['H2', 'H1', 'AX', 'L1', 'L2', 'CDD'])
    c.open('default_conditions')
    c.configure_traits()
    c.dump()
    # edit_conditions(None)
# ============= EOF =============================================


