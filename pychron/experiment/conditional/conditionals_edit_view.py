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
from traitsui.menu import Action
from traits.api import HasTraits, List, Instance, Any, \
    Enum, Float, on_trait_change, Str, Int, Property, Button, Bool

from pyface.file_dialog import FileDialog
from traitsui.api import View, Tabbed, Group, UItem, \
    TabularEditor, VGroup, EnumEditor, Item, HGroup, spring, Label, Handler
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
import os
import yaml
# ============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.core.helpers.ctx_managers import no_update
from pychron.core.helpers.filetools import get_path
from pychron.experiment.conditional.conditional import conditional_from_dict, MAX_REGEX, STD_REGEX, \
    CP_REGEX, MIN_REGEX, TruncationConditional, TerminationConditional, ActionConditional, SLOPE_REGEX, BASELINE_REGEX, \
    BASELINECOR_REGEX, COMP_REGEX, AVG_REGEX, ACTIVE_REGEX
from pychron.paths import paths


class PRConditionalsAdapter(TabularAdapter):
    columns = [('Attribute', 'attr'),
               ('Check', 'comp'), ]

    attr_width = Int(100)
    check_width = Int(200)


class ConditionalsAdapter(TabularAdapter):
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
            'Inactive': '{}.inactive',
            'BaselineCorrected': '{}.bs_corrected'}


class ConditionalGroup(HasTraits):
    editable=True


    conditionals = List
    selected = Any

    attr = Str
    available_attrs = List
    comparator = Enum('', '>', '<', '>=', '<=', '==')
    secondary_comparator = Enum('', '>', '<', '>=', '<=', '==')
    secondary_value=Float
    use_between = Bool
    use_invert = Bool
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

    add_button = Button
    delete_button = Button

    dump_attrs = [('attr', ''), ('frequency', ''),
                  ('window', ''), ('mapper', ''),
                  ('start', 'start_count'),
                  ('check', 'comp')]
    tabular_adapter_klass = ConditionalsAdapter

    _conditional_klass=None

    def _add_button_fired(self):
        if self.selected:
            idx=self.conditionals.index(self.selected)

            k=self.selected.clone_traits()
            self.conditionals.insert(idx, k)
        else:
            k=self._conditional_klass('','')
            self.conditionals.append()

    def _delete_button_fired(self):
        idx=self.conditionals.index(self.selected)
        self.conditionals.remove(self.selected)
        if not self.conditionals:
            sel=self._conditional_klass('','')
        else:
            sel = self.conditionals[idx-1]
        self.selected=sel

    def __init__(self, conditionals, klass, *args, **kw):
        if not klass:
            raise NotImplementedError

        if conditionals:
            for ci in conditionals:
                cx = conditional_from_dict(ci, klass)
                if cx:
                    self.conditionals.append(cx)

            self.selected = self.conditionals[0]
        else:
            self.selected = klass('', '')
            self.conditionals=[self.selected]

        self._conditional_klass= klass
        super(ConditionalGroup, self).__init__(*args, **kw)

    def dump(self):
        cs = []
        for ci in self.conditionals:
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

    @on_trait_change('function, modifier, comparator, value, attr, use_invert',
                     'use_between, secondary_comparator, secondary_value')
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

            if self.use_between:
                if self.comparator and self.secondary_comparator:
                    comp = '{}{}{}{}{}'.format(self.secondary_value, self.secondary_comparator,
                                               attr,
                                               self.comparator, self.value)
                else:
                    comp = '{}'.format(attr)
            else:
                if self.comparator:
                    comp = '{}{}{}'.format(attr, self.comparator, self.value)
                else:
                    comp = '{}'.format(attr)

            if self.use_invert:
                comp='not {}'.format(comp)

            self.selected.comp=comp

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
                             (ACTIVE_REGEX, 'Inactive'),
                             (BASELINECOR_REGEX, 'BaselineCorrected'),
                             (BASELINE_REGEX, 'Baseline')):
                    if r.findall(new.comp):
                        setattr(self, 'modifier', a)
                        break

                # extract comparator
                m = COMP_REGEX.findall(new.comp)
                if m:
                    m1=m[0]
                    if len(m)==2:
                        self.use_between=True
                        self.secondary_comparator = c =m[0]
                        self.secondary_value = float(new.comp.split(c)[0])
                        m1=m[1]

                    self.comparator = c = m1
                    self.value = float(new.comp.split(c)[-1])

                # extract use invert
                if new.comp.startswith('not '):
                    self.use_invert=True

    def _get_modifier_enabled(self):
        return not self.function

    def _get_tool_group(self):
        g=HGroup(icon_button_editor('add_button', 'add'),
                 icon_button_editor('delete_button', 'delete'))
        return g

    def _get_conditionals_grp(self):
        item = UItem('conditionals',
                     editor=TabularEditor(adapter=self.tabular_adapter_klass(),
                                          editable=False,
                                          auto_update=True,
                                          auto_resize=True,
                                          selected='selected'))
        return item

    def _get_edit_group(self):
        edit_grp = VGroup(HGroup(spring, UItem('object.selected.comp', style='readonly'), spring),
                          HGroup(UItem('attr',
                                       editor=EnumEditor(name='available_attrs')),
                                 Item('function',
                                      editor=EnumEditor(values=['', 'Average', 'Max', 'Min', 'Slope'])),
                                 Item('modifier',
                                      enabled_when='modifier_enabled',
                                      editor=EnumEditor(values=['', 'StdDev', 'Current', 'Inactive',
                                                                'Baseline', 'BaselineCorrected']))),
                          HGroup(UItem('comparator'),
                                 Item('value'),
                                 Item('use_between', label='Between'),
                                 UItem('secondary_value', enabled_when='use_between'),
                                 UItem('secondary_comparator', enabled_when='use_between'),
                                 Item('use_invert', label='Invert'),
                                 enabled_when='attr'),
                          HGroup(Item('start_count',
                                      tooltip='Number of counts to wait until performing check',
                                      label='Start')),
                          Item('frequency',
                               tooltip='Number of counts between each check'))
        return edit_grp

    def traits_view(self):
        if self.editable:
            v = View(self._get_conditionals_grp(),
                     self._get_tool_group(),
                     self._get_edit_group())
        else:
            v=View(self._get_conditionals_grp())
        return v


class PostRunGroup(ConditionalGroup):
    dump_attrs = [('attr', ''),
                  ('window', ''),
                  ('mapper', ''),
                  ('check', 'comp')]
    tabular_adapter_klass = PRConditionalsAdapter

    def _get_edit_group(self):
        edit_grp = VGroup(HGroup(spring, UItem('object.selected.comp', style='readonly'), spring),
                          HGroup(UItem('attr',
                                       editor=EnumEditor(name='available_attrs')),
                                 Item('function',
                                      editor=EnumEditor(values=['', 'Max', 'Min', 'Slope', 'Average'])),
                                 Item('modifier',
                                      enabled_when='modifier_enabled',
                                      editor=EnumEditor(values=['', 'StdDev', 'Current', 'Inactive',
                                                                'Baseline', 'BaselineCorrected']))),
                          HGroup(UItem('comparator', enabled_when='attr'),
                                 Item('value', enabled_when='attr and comparator')))
        return edit_grp


class PreRunGroup(ConditionalGroup):
    dump_attrs = [('attr', ''), ('check', 'comp')]
    tabular_adapter_klass = PRConditionalsAdapter
    # def traits_view(self):
    def _get_edit_group(self):
        edit_grp = VGroup(HGroup(spring, UItem('object.selected.comp', style='readonly'), spring),
                          HGroup(UItem('attr',
                                       editor=EnumEditor(name='available_attrs')),
                                 # Item('function',
                                 #      editor=EnumEditor(values=['', 'Max', 'Min', 'Slope', 'Average'])),
                                 Item('modifier',
                                      enabled_when='modifier_enabled',
                                      editor=EnumEditor(values=['', 'Inactive']))),
                          # HGroup(UItem('comparator', enabled_when='attr'),
                          #        Item('value', enabled_when='attr and comparator'))
                        )
        return edit_grp


class CEHandler(Handler):
    def object_path_changed(self, info):
        info.ui.title = 'Edit Default Conditionals - [{}]'.format(info.object.name)

    def save_as(self, info):
        dlg=FileDialog(default_directory=paths.queue_conditionals_dir, action='save as')
        if dlg.open():
            if dlg.path:
                info.object.dump(dlg.path)

class ConditionalsViewable(HasTraits):
    actions_group = Instance(ConditionalGroup)
    terminations_group = Instance(ConditionalGroup)
    truncations_group = Instance(ConditionalGroup)
    post_run_terminations_group = Instance(ConditionalGroup)
    pre_run_terminations_group = Instance(ConditionalGroup)

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
        prertegrp = Group(UItem('pre_run_terminations_group',
                                defined_when='pre_run_terminations_group', style='custom'),
                          nopterm,
                          label='Pre Run Terminations')

        v = View(Tabbed(prertegrp, agrp, trgrp, tegrp, prtegrp),
                 width=800,
                 resizable=True,
                 handler=CEHandler(),
                 buttons=['OK', 'Cancel', Action(name='Save As', action='save_as')],
                 title='Edit Default Conditionals')
        return v


class ConditionalsEditView(ConditionalsViewable):
    path = Str

    def __init__(self, detectors=None, *args, **kw):
        self.available_attrs = ['', 'Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36',
                                'kca', 'kcl']
        if detectors:
            self.available_attrs.extend(detectors)
            self.detectors = detectors

        super(ConditionalsEditView, self).__init__(*args, **kw)

    @property
    def name(self):
        return os.path.relpath(self.path, paths.queue_conditionals_dir)

    def open(self, name):
        self.load(name)

    def load(self, name):
        root = paths.queue_conditionals_dir
        p = get_path(root, name, ('.yaml', '.yml'))
        if p:
            self.path = p
            with open(p, 'r') as fp:
                yd = yaml.load(fp)
                for name, klass, cklass in (('actions', ConditionalGroup, ActionConditional),
                                            ('truncations', ConditionalGroup, TruncationConditional),
                                            ('terminations', ConditionalGroup, TerminationConditional),
                                            ('post_run_terminations', PostRunGroup, TerminationConditional)):
                    grp = self._group_factory(yd, name, klass, cklass)
                    setattr(self, '{}_group'.format(name), grp)

                grp = self._group_factory(yd, 'pre_run_terminations', PreRunGroup)
                grp.available_attrs = self.detectors
                self.pre_run_terminations_group = grp

    def _group_factory(self, yd, name, klass, conditional_klass=None):
        if conditional_klass is None:
            conditional_klass = TerminationConditional

        items = yd.get(name, [])
        group = klass(items, conditional_klass, available_attrs=self.available_attrs)
        return group

    def dump(self, path=None):
        if path is None:
            path = self.path
        else:
            self.path=path

        if path:
            with open(path, 'w') as fp:
                d = {k: getattr(self, '{}_group'.format(k)).dump() for k in ('actions', 'terminations', 'truncations',
                                                                             'post_run_terminations',
                                                                             'pre_run_terminations')}

                yaml.dump(d, fp, default_flow_style=False)


def edit_conditionals(name, detectors=None, app=None):
    if not name:
        dlg = FileDialog(action='open',
                         wildcard=FileDialog.create_wildcard('YAML', '*.yaml *.yml'),
                         default_directory=paths.queue_conditionals_dir)
        if dlg.open():
            if dlg.path:
                name = os.path.basename(dlg.path)

    if name:
        cev = ConditionalsEditView(detectors)
        cev.open(name)
        if app:
            info = app.open_view(cev, kind='livemodal')
        else:
            info = cev.edit_traits(kind='livemodal')
            # info=cev.configure_traits(kind='livemodal')
        if info.result:
            cev.dump()


if __name__ == '__main__':
    c = ConditionalsEditView(detectors=['H2', 'H1', 'AX', 'L1', 'L2', 'CDD'])
    c.open('normal')
    c.configure_traits()
    c.dump()
    # edit_conditions(None)
# ============= EOF =============================================


