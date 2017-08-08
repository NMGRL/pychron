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
# ============= enthought library imports =======================
from traits.api import HasTraits, List, Any, \
    Enum, Float, on_trait_change, Str, Int, Property, Button, Bool, CStr
from traitsui.api import View, UItem, \
    TabularEditor, VGroup, Item, HGroup, HSplit

from pychron.core.helpers.ctx_managers import no_update
from pychron.core.ui.enum_editor import myEnumEditor
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.experiment.conditional.conditional import conditional_from_dict, BaseConditional, MODIFICATION_ACTIONS, \
    ExtractionStr
from pychron.experiment.conditional.regexes import CP_REGEX, STD_REGEX, ACTIVE_REGEX, BASELINECOR_REGEX, BASELINE_REGEX, \
    MAX_REGEX, MIN_REGEX, AVG_REGEX, COMP_REGEX, ARGS_REGEX, BETWEEN_REGEX, SLOPE_REGEX
from pychron.experiment.conditional.tabular_adapters import EActionConditionalsAdapter, EPRConditionalsAdapter, \
    EConditionalsAdapter, EModificationConditionalsAdapter, PRConditionalsAdapter, ConditionalsAdapter

FUNCTIONS = ['', 'Max', 'Min', 'Slope', 'Average', 'Between']
FUNC_DICT = {'slope': 'slope({})', 'max': 'max({})', 'min': 'min({})', 'average': 'average({})'}
MOD_DICT = {'Current': '{}.cur', 'StdDev': '{}.std', 'Baseline': '{}.bs',
            'Inactive': '{}.inactive',
            'BaselineCorrected': '{}.bs_corrected',
            'Between': '{}.between'}

TAGS = 'start_count,frequency,attr,window,mapper,ntrips'


class ConditionalGroup(HasTraits):
    editable = False
    label = Str
    conditionals = List
    selected = Any
    help_str = Str

    attr = Str
    available_attrs = List
    comparator = Enum('', '>', '<', '>=', '<=', '==')
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

    dump_attrs = List([('attr', ''), ('frequency', ''),
                       ('window', ''), ('mapper', ''),
                       ('start_count', ''),
                       ('teststr', ''),
                       ('ntrips', '')])

    tabular_adapter_klass = ConditionalsAdapter

    _conditional_klass = None

    def __init__(self, conditionals, klass, auto_select=True, *args, **kw):
        if not klass:
            raise NotImplementedError

        if conditionals:
            for ci in conditionals:
                cx = ci if isinstance(ci, BaseConditional) else conditional_from_dict(ci, klass)
                if cx:
                    self.conditionals.append(cx)
        if auto_select:
            if self.conditionals:
                self.selected = self.conditionals[0]
            else:
                self.selected = klass('', 0)
                self.conditionals = [self.selected]

        self._conditional_klass = klass
        super(ConditionalGroup, self).__init__(*args, **kw)

    def set_attrs(self, **kw):
        for ci in self.conditionals:
            ci.trait_set(**kw)

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

    def _add_button_fired(self):
        if self.selected:
            idx = self.conditionals.index(self.selected)

            k = self.selected.clone_traits()
            self.conditionals.insert(idx, k)
        else:
            k = self._conditional_klass('', '')
            self.conditionals.append(k)

    def _delete_button_fired(self):
        idx = self.conditionals.index(self.selected)
        self.conditionals.remove(self.selected)
        if not self.conditionals:
            sel = self._conditional_klass('', '')
        else:
            sel = self.conditionals[idx - 1]
        self.selected = sel

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
        try:
            setattr(self.selected, name, new)
        except AttributeError:
            pass

    def _selected_changed(self, new):
        if new:
            teststr = new.teststr
            with no_update(self):
                for a in TAGS.split(','):
                    try:
                        setattr(self, a, getattr(new, a))
                    except AttributeError:
                        continue

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

                self._selected_changed_hook()

    def _selected_changed_hook(self):
        pass

    def _get_modifier_enabled(self):
        return not self.function

    def _get_tool_group(self):
        g = HGroup(icon_button_editor('add_button', 'add'),
                   icon_button_editor('delete_button', 'delete'))
        return g

    def _get_conditionals_grp(self):
        item = UItem('conditionals',
                     width=750,
                     editor=TabularEditor(adapter=self.tabular_adapter_klass(),
                                          editable=False,
                                          auto_update=True,
                                          # auto_resize=True,
                                          selected='selected'))
        return item

    def _get_opt_grp(self):
        opt_grp = VGroup(Item('function',
                              editor=myEnumEditor(values=FUNCTIONS),
                              tooltip='Optional. Apply a predefined function to this attribute. '
                                      'Functions include {}'.format(','.join(FUNCTIONS[1:]))),
                         Item('window', enabled_when='not modifier_enabled'),
                         Item('modifier',
                              enabled_when='modifier_enabled',
                              tooltip='Optional. Apply a modifier to this attribute.'
                                      'For example to check if CDD is active use '
                                      'Atttribute=CDD, Modifier=Inactive',
                              editor=myEnumEditor(values=['', 'StdDev', 'Current', 'Inactive',
                                                        'Baseline', 'BaselineCorrected'])),
                         show_border=True,
                         label='Optional')
        return opt_grp

    def _get_cmp_grp(self):
        cmp_grp = VGroup(Item('comparator', label='Operation',
                              enabled_when='not function=="Between"',
                              tooltip='Numeric and logical comparisons. Conditional trips when it '
                                      'evaluates to True'),
                         Item('value'),
                         Item('secondary_value', enabled_when='function=="Between"'),
                         Item('use_invert', label='Invert'),
                         show_border=True,
                         label='Comparison')
        return cmp_grp

    def _get_cnt_grp(self):
        cnt_grp = VGroup(Item('start_count',
                              tooltip='Number of counts to wait until performing check',
                              label='Start'),
                         Item('frequency',
                              tooltip='Number of counts between each check'),
                         Item('ntrips',
                              label='N Trips',
                              tooltip='Number of trips (conditional evaluates True) '
                                      'before action is taken. Default=1'),
                         show_border=True, label='Counts')
        return cnt_grp

    def _get_edit_group(self):

        cnt_grp = self._get_cnt_grp()
        cmp_grp = self._get_cmp_grp()
        opt_grp = self._get_opt_grp()

        edit_grp = VGroup(Item('attr',
                               label='Attribute',
                               editor=myEnumEditor(name='available_attrs')),
                          opt_grp,
                          VGroup(cmp_grp,
                                 cnt_grp,
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


class ActionConditionalGroup(ConditionalGroup):
    action = CStr

    def __init__(self, *args, **kw):
        super(ActionConditionalGroup, self).__init__(*args, **kw)
        self.dump_attrs.append(('action', ''))

    def _get_edit_group(self):
        cnt_grp = self._get_cnt_grp()
        cmp_grp = self._get_cmp_grp()
        opt_grp = self._get_opt_grp()

        act_grp = VGroup(Item('action'),
                         show_border=True,
                         label='Action')
        edit_grp = VGroup(Item('attr',
                               label='Attribute',
                               editor=myEnumEditor(name='available_attrs')),
                          opt_grp,
                          VGroup(cmp_grp,
                                 cnt_grp,
                                 act_grp,
                                 enabled_when='attr'))
        return edit_grp


class PostRunGroup(ConditionalGroup):
    dump_attrs = [('attr', ''),
                  ('window', ''),
                  ('mapper', ''),
                  ('teststr', 'teststr')]
    tabular_adapter_klass = PRConditionalsAdapter

    def _get_edit_group(self):
        edit_grp = VGroup(Item('attr',
                               label='Attribute',
                               editor=myEnumEditor(name='available_attrs')),
                          VGroup(Item('function',
                                      editor=myEnumEditor(values=FUNCTIONS)),
                                 Item('window', enabled_when='not modifier_enabled'),
                                 Item('modifier',
                                      enabled_when='modifier_enabled',
                                      editor=myEnumEditor(values=['', 'StdDev', 'Current', 'Inactive',
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
                                editor=myEnumEditor(name='available_attrs')),
                          Item('modifier',
                               enabled_when='modifier_enabled',
                               editor=myEnumEditor(values=['', 'Inactive'])))
        return edit_grp


class EConditionalGroup(ConditionalGroup):
    tabular_adapter_klass = EConditionalsAdapter


class ModificationGroup(ConditionalGroup):
    tabular_adapter_klass = EModificationConditionalsAdapter
    action = Enum(MODIFICATION_ACTIONS)
    nskip = Int
    use_truncation = Bool
    use_termination = Bool
    extraction_str = ExtractionStr

    def __init__(self, *args, **kw):
        super(ModificationGroup, self).__init__(*args, **kw)
        self.dump_attrs.append(('action', ''))
        self.dump_attrs.append(('nskip', ''))
        self.dump_attrs.append(('use_truncation', ''))
        self.dump_attrs.append(('use_termination', ''))
        self.dump_attrs.append(('extraction_str', ''))

    def _selected_changed_hook(self):
        for a in ('action', 'nskip', 'use_truncation', 'use_termination', 'extraction_str'):
            setattr(self, a, getattr(self.selected, a))

    @on_trait_change('action, nskip, use_truncation, use_termination')
    def _update_selected2(self, name, new):
        self._update_selected(name, new)
        if new:
            if name == 'use_truncation':
                self.use_termination = False
            elif name == 'use_termination':
                self.use_truncation = False

    def _get_edit_group(self):
        cnt_grp = self._get_cnt_grp()
        cmp_grp = self._get_cmp_grp()
        opt_grp = self._get_opt_grp()

        act_grp = VGroup(HGroup(Item('action'), Item('nskip', enabled_when='action=="Skip N Runs"', label='N')),
                         HGroup(Item('use_truncation', label='Truncate'),
                                Item('use_termination', label='Terminate')),
                         HGroup(UItem('extraction_str', tooltip='''modify extract value for associated runs. e.g.
1. 1,2,3 (increase step i by 1W, step i+1 by 2W, step i+2 by 3W)
2. 10%,50% (increase step i by 10%, step i+1 by 50%)'''),
                                visible_when='action=="Set Extract"',
                                show_border=True,
                                label='Extraction'),
                         show_border=True,
                         label='Modification')
        edit_grp = VGroup(Item('attr',
                               label='Attribute',
                               editor=myEnumEditor(name='available_attrs')),
                          opt_grp,
                          VGroup(cmp_grp,
                                 cnt_grp,
                                 act_grp,
                                 enabled_when='attr'))
        return edit_grp


class ActionGroup(ActionConditionalGroup):
    tabular_adapter_klass = EActionConditionalsAdapter
    help_str = 'Action:  Perform a specified action'

    @on_trait_change('action')
    def _update_selected2(self, name, new):
        self._update_selected(name, new)


class TerminationGroup(EConditionalGroup):
    help_str = 'Termination: STOP this run and CONTINUE to next'


class CancelationGroup(EConditionalGroup):
    help_str = 'Cancelation: STOP this run and STOP experiment'


class TruncationGroup(EConditionalGroup):
    help_str = 'Truncation: Stop current measurement and CONTINUE run'


class EPostRunGroup(PreRunGroup):
    tabular_adapter_klass = EPRConditionalsAdapter
    help_str = 'PostRunTermination: Checked after run is completed. Cancels experiment.'


class EPreRunGroup(PreRunGroup):
    tabular_adapter_klass = EPRConditionalsAdapter
    help_str = 'PreRunTermination: Checked before run is started. Cancels experiment.'

# ============= EOF =============================================
