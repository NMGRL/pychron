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
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.experiment.conditional.conditional import conditional_from_dict, ActionConditional, TruncationConditional, \
    CancelationConditional, TerminationConditional
from pychron.experiment.conditional.regexes import CP_REGEX, STD_REGEX, ACTIVE_REGEX, BASELINECOR_REGEX, BASELINE_REGEX, \
    MAX_REGEX, MIN_REGEX, AVG_REGEX, COMP_REGEX, ARGS_REGEX, BETWEEN_REGEX, SLOPE_REGEX

set_qt()
# ============= enthought library imports =======================
from traitsui.menu import Action
from traits.api import HasTraits, List, Instance, Any, \
    Enum, Float, on_trait_change, Str, Int, Property, Button, Bool

from pyface.file_dialog import FileDialog
from traitsui.api import View, Tabbed, Group, UItem, \
    TabularEditor, VGroup, EnumEditor, Item, HGroup, spring, Label, Handler, HSplit
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
import os
import yaml
# ============= local library imports  ==========================
from pychron.core.helpers.ctx_managers import no_update
from pychron.core.helpers.filetools import get_path
from pychron.paths import paths


class PRConditionalsAdapter(TabularAdapter):
    columns = [('Attribute', 'attr'),
               ('Check', 'teststr'), ]

    attr_width = Int(100)
    teststr_width = Int(200)


class ConditionalsAdapter(TabularAdapter):
    columns = [('Attribute', 'attr'),
               ('Start', 'start_count'),
               ('Frequency', 'frequency'),
               ('Check', 'teststr'), ]

    attr_width = Int(100)
    teststr_width = Int(200)
    start_width = Int(50)
    frequency_width = Int(100)


FUNCTIONS = ['', 'Max', 'Min', 'Slope', 'Average', 'Between']
FUNC_DICT = {'Slope': 'slope({})', 'Max': 'max({})', 'Min': 'min({})', 'Averge': 'average({})'}
MOD_DICT = {'Current': '{}.cur', 'StdDev': '{}.std', 'Baseline': '{}.bs',
            'Inactive': '{}.inactive',
            'BaselineCorrected': '{}.bs_corrected',
            'Between': '{}.between'}

TAGS = 'start_count,frequency,attr,window,mapper,ntrips'


class ConditionalGroup(HasTraits):
    editable = True

    conditionals = List
    selected = Any

    attr = Str
    available_attrs = List
    comparator = Enum('', '>', '<', '>=', '<=', '==')
    # secondary_comparator = Enum('', '>', '<', '>=', '<=', '==')
    secondary_value = Float
    use_invert = Bool

    modifier_enabled = Property(depends_on='function')
    modifier = Str
    function = Str
    window = Int
    mapper = Str
    value = Float
    start_count = Int
    frequency = Int
    ntrips = Int
    _no_update = False

    add_button = Button
    delete_button = Button

    dump_attrs = [('attr', ''), ('frequency', ''),
                  ('window', ''), ('mapper', ''),
                  ('start_count', ''),
                  ('teststr', ''),
                  ('ntrips', '')]

    tabular_adapter_klass = ConditionalsAdapter

    _conditional_klass = None

    def _add_button_fired(self):
        if self.selected:
            idx = self.conditionals.index(self.selected)

            k = self.selected.clone_traits()
            self.conditionals.insert(idx, k)
        else:
            k = self._conditional_klass('', '')
            self.conditionals.append()

    def _delete_button_fired(self):
        idx = self.conditionals.index(self.selected)
        self.conditionals.remove(self.selected)
        if not self.conditionals:
            sel = self._conditional_klass('', '')
        else:
            sel = self.conditionals[idx - 1]
        self.selected = sel

    def __init__(self, conditionals, klass, *args, **kw):
        if not klass:
            raise NotImplementedError

        if conditionals:
            for ci in conditionals:
                cx = conditional_from_dict(ci, klass)
                if cx:
                    self.conditionals.append(cx)

        if self.conditionals:
            self.selected = self.conditionals[0]
        else:
            self.selected = klass('', 0)
            self.conditionals = [self.selected]

        self._conditional_klass = klass
        super(ConditionalGroup, self).__init__(*args, **kw)

    def dump(self):
        cs = []
        for ci in self.conditionals:
            d = {}
            for a, b in self.dump_attrs:
                if not b:
                    b = a
                d[a] = getattr(ci, b)

            cs.append(d)
        return cs

    @on_trait_change('function, modifier, comparator, value, attr, use_invert, '
                     'use_between, secondary_value')
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

            func = self.function.lower()
            if func == 'between':
                comp = 'between({},{},{})'.format(attr,
                                                  self.value,
                                                  self.secondary_value)
            else:
                try:
                    s = FUNC_DICT[func]
                    attr = s.format(attr)
                except KeyError:
                    pass

                if self.comparator:
                    comp = '{}{}{}'.format(attr, self.comparator, self.value)
                else:
                    comp = '{}'.format(attr)

            if self.use_invert:
                comp = 'not {}'.format(comp)

            self.selected.teststr = comp


    @on_trait_change(TAGS)
    def _update_selected(self, name, new):
        setattr(self.selected, name, new)

    def _selected_changed(self, new):
        if new:
            teststr = new.teststr
            with no_update(self):
                for a in TAGS.split(','):
                    setattr(self, a, getattr(new, a))

                self.function = ''
                self.secondary_value = 0
                self.value = 0
                self.modifier = ''

                for r, a in ((CP_REGEX, 'Current'),
                             (STD_REGEX, 'StdDev'),
                             (ACTIVE_REGEX, 'Inactive'),
                             (BASELINECOR_REGEX, 'BaselineCorrected'),
                             (BASELINE_REGEX, 'Baseline')):
                    if r.search(teststr):
                        setattr(self, 'modifier', a)
                        break

                for r, a in ((MAX_REGEX, 'Max'),
                             (MIN_REGEX, 'Min'),
                             (AVG_REGEX, 'Average'),
                             (SLOPE_REGEX, 'Slope')):
                    if r.search(teststr):
                        setattr(self, 'function', a)
                        break
                else:
                    if BETWEEN_REGEX.search(teststr):
                        self.function = 'Between'
                        self.comparator = ''
                        args = ARGS_REGEX.findall(teststr)[0][1:-1].split(',')
                        self.value = float(args[1].strip())
                        self.secondary_value = float(args[2].strip())

                # extract comparator
                m = COMP_REGEX.findall(teststr)
                if m:
                    m1 = m[0]

                    self.comparator = c = m1
                    self.value = float(teststr.split(c)[-1])

                # extract use invert
                if teststr.startswith('not '):
                    self.use_invert = True

    def _get_modifier_enabled(self):
        return not self.function

    def _get_tool_group(self):
        g = HGroup(icon_button_editor('add_button', 'add'),
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
        edit_grp = VGroup(Item('attr',
                               label='Attribute',
                               editor=EnumEditor(name='available_attrs')),
                          VGroup(Item('function',
                                      editor=EnumEditor(values=FUNCTIONS)),
                                 Item('modifier',
                                      enabled_when='modifier_enabled',
                                      editor=EnumEditor(values=['', 'StdDev', 'Current', 'Inactive',
                                                                'Baseline', 'BaselineCorrected'])),
                                 Item('comparator', label='Operation',
                                      enabled_when='not function=="Between"'),
                                 Item('value'),
                                 Item('secondary_value', enabled_when='function=="Between"'),
                                 Item('use_invert', label='Invert'),
                                 Item('start_count',
                                      tooltip='Number of counts to wait until performing check',
                                      label='Start'),
                                 Item('frequency',
                                      tooltip='Number of counts between each check'),
                                 Item('ntrips',
                                      label='N Trips',
                                      tooltip='Number of trips (conditional evaluates True) '
                                              'before action is taken. Default=1'),
                                 enabled_when='attr'))
        return edit_grp

    def traits_view(self):
        if self.editable:
            v = View(HSplit(self._get_edit_group(),
                            VGroup(self._get_conditionals_grp(),
                                   self._get_tool_group())))
        else:
            v = View(self._get_conditionals_grp())
        return v


class PostRunGroup(ConditionalGroup):
    dump_attrs = [('attr', ''),
                  ('window', ''),
                  ('mapper', ''),
                  ('teststr', 'teststr')]
    tabular_adapter_klass = PRConditionalsAdapter

    def _get_edit_group(self):
        edit_grp = VGroup(Item('attr',
                               label='Attribute',
                               editor=EnumEditor(name='available_attrs')),
                          VGroup(Item('function',
                                      editor=EnumEditor(values=FUNCTIONS)),
                                 Item('modifier',
                                      enabled_when='modifier_enabled',
                                      editor=EnumEditor(values=['', 'StdDev', 'Current', 'Inactive',
                                                                'Baseline', 'BaselineCorrected'])),
                                 Item('comparator', label='Operation',
                                      enabled_when='not function=="Between"'),
                                 Item('value'),
                                 Item('secondary_value', enabled_when='function=="Between"'),
                                 Item('use_invert', label='Invert'),
                                 enabled_when='attr'))
        return edit_grp


class PreRunGroup(ConditionalGroup):
    dump_attrs = [('attr', ''), ('teststr', 'teststr')]
    tabular_adapter_klass = PRConditionalsAdapter

    def _get_edit_group(self):
        edit_grp = VGroup(UItem('attr',
                                editor=EnumEditor(name='available_attrs')),
                          Item('modifier',
                               enabled_when='modifier_enabled',
                               editor=EnumEditor(values=['', 'Inactive'])))
        return edit_grp


class CEHandler(Handler):
    def object_path_changed(self, info):
        info.ui.title = 'Edit Default Conditionals - [{}]'.format(info.object.name)

    def save_as(self, info):
        dlg = FileDialog(default_directory=paths.queue_conditionals_dir, action='save as')
        if dlg.open():
            if dlg.path:
                info.object.dump(dlg.path)


class ConditionalsViewable(HasTraits):
    actions_group = Instance(ConditionalGroup)
    cancelations_group = Instance(ConditionalGroup)
    terminations_group = Instance(ConditionalGroup)
    truncations_group = Instance(ConditionalGroup)
    post_run_terminations_group = Instance(ConditionalGroup)
    pre_run_terminations_group = Instance(ConditionalGroup)

    group_names = ('actions', 'truncations', 'cancelations', 'terminations',
                   'post_run_terminations', 'pre_run_terminations')
    title = Str

    def traits_view(self):
        vs = []
        for name in self.group_names:
            gname = '{}_group'.format(name)
            uname = ' '.join([ni.capitalize() for ni in name.split('_')])
            grp = Group(UItem(gname, style='custom'), label=uname)
            vs.append(grp)

        v = View(Tabbed(*vs),
                 width=800,
                 resizable=True,
                 handler=CEHandler(),
                 buttons=['OK', 'Cancel', Action(name='Save As', action='save_as')],
                 title=self.title)

        return v


class ConditionalsEditView(ConditionalsViewable):
    path = Str
    root = Str
    detectors = List
    title = 'Edit Default Conditionals'

    def __init__(self, detectors=None, *args, **kw):
        attrs = ['', 'age', 'kca', 'kcl', 'cak', 'clk', 'rad40_percent',
                 'Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36']

        ratio_matrix = ['{}/{}'.format(i, j) for i in ('40', '39', '38', '37', '36')
                        for j in ('40', '39', '38', '37', '36') if i != j]
        attrs.extend(ratio_matrix)
        if detectors:
            attrs.extend(detectors)
            self.detectors = detectors
        self.available_attrs = attrs
        super(ConditionalsEditView, self).__init__(*args, **kw)

    @property
    def name(self):
        v = ''
        if self.path:
            v = os.path.relpath(self.path, self.root)

        return v

    def open(self, path, save_as):
        self.load(path, save_as)

    def load(self, path, save_as):

        root, name = os.path.split(path)
        p = get_path(root, name, ('.yaml', '.yml'))
        yd = None
        if p:
            if not save_as:
                self.path = p

            with open(p, 'r') as fp:
                yd = yaml.load(fp)

        for name, klass, cklass in (('actions', ConditionalGroup, ActionConditional),
                                    ('truncations', ConditionalGroup, TruncationConditional),
                                    ('cancelations', ConditionalGroup, CancelationConditional),
                                    ('terminations', ConditionalGroup, TerminationConditional),
                                    ('post_run_terminations', PostRunGroup, TerminationConditional)):
            if name in self.group_names:
                grp = self._group_factory(yd, name, klass, cklass)
                setattr(self, '{}_group'.format(name), grp)

        if 'pre_run_terminations' in self.group_names:
            grp = self._group_factory(yd, 'pre_run_terminations', PreRunGroup)
            grp.available_attrs = self.detectors
            self.pre_run_terminations_group = grp

    def _group_factory(self, yd, name, klass, conditional_klass=None):
        if conditional_klass is None:
            conditional_klass = TerminationConditional

        items = yd.get(name, []) if yd else []
        group = klass(items, conditional_klass, available_attrs=self.available_attrs)
        return group

    def dump(self, path=None):
        if path is None:
            path = self.path
        else:
            self.path = path

        if not path:
            path = get_file_path(self.root, action='save as')

        if path:
            with open(path, 'w') as fp:
                d = {k: getattr(self, '{}_group'.format(k)).dump() for k in self.group_names}

                yaml.dump(d, fp, default_flow_style=False)


def get_file_path(root, action='open'):
    dlg = FileDialog(action=action,
                     wildcard=FileDialog.create_wildcard('YAML', '*.yaml *.yml'),
                     default_directory=root)
    if dlg.open():
        if dlg.path:
            return dlg.path


def edit_conditionals(name, detectors=None, app=None, root=None, save_as=False,
                      kinds=None, title=''):
    if not root:
        root = paths.queue_conditionals_dir

    if not save_as:
        if not name and not save_as:
            path = get_file_path(root)
            if not path:
                return
        else:
            path = os.path.join(root, name)
            #
            # if not os.path.isfile(path):
            # return
    else:
        path = ''

    cev = ConditionalsEditView(detectors, root=root, title=title)
    print path
    cev.open(path, save_as)
    if kinds:
        cev.group_names = kinds

    if app:
        info = app.open_view(cev, kind='livemodal')
    else:
        info = cev.edit_traits(kind='livemodal')

    if info.result:
        cev.dump()


if __name__ == '__main__':
    # c = ConditionalsEditView(detectors=['H2', 'H1', 'AX', 'L1', 'L2', 'CDD'])
    # c.open('normal', False)
    # c.configure_traits()
    # c.dump()
    class D(HasTraits):
        test = Button

        def _test_fired(self):
            edit_conditionals('foo', save_as=False)

    D().configure_traits(view=View('test'))
# ============= EOF =============================================


