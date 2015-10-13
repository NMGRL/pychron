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
from traitsui.view import View
# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.experiment.conditional.conditional import ActionConditional, TruncationConditional, TerminationConditional, \
    CancelationConditional
from pychron.experiment.conditional.conditionals_edit_view import ConditionalsViewable, ConditionalGroup, PostRunGroup, \
    PreRunGroup


class ConditionalsView(ConditionalsViewable):
    title = 'Active Conditionals'

    def add_post_run_terminations(self, items):
        self._add_pre_post('PostRunTerminations', items, PostRunGroup)

    def add_pre_run_terminations(self, items):
        self._add_pre_post('PreRunTerminations', items, PreRunGroup)

    def _add_pre_post(self, label, items, klass):
        if not items:
            items = []

        grp = next((gi for gi in self.groups if gi.label == label), None)

        if not grp:
            self._group_factory(items, klass, auto_select=False, label=label)
        else:
            grp.conditionals.extend(items)

    def add_system_conditionals(self, ditems):
        if ditems:
            for name, klass, cklass in (('actions', ConditionalGroup, ActionConditional),
                                        ('truncations', ConditionalGroup, TruncationConditional),
                                        ('cancelations', ConditionalGroup, CancelationConditional),
                                        ('terminations', ConditionalGroup, TerminationConditional)):
                items = ditems.get(name, [])
                self._group_factory(items, klass, conditional_klass=cklass,
                                    auto_select=False, label=name.capitalize())

    def add_conditionals(self, ditems, **kw):
        if ditems:
            for name, klass, cklass in (('actions', ConditionalGroup, ActionConditional),
                                        ('truncations', ConditionalGroup, TruncationConditional),
                                        ('cancelations', ConditionalGroup, CancelationConditional),
                                        ('terminations', ConditionalGroup, TerminationConditional)):
                items = ditems.get(name, [])
                grp = next((gi for gi in self.groups if gi.label == name.capitalize()), None)
                if not grp:
                    self._group_factory(items, klass, auto_select=False,
                                        label=name.capitalize(), **kw)
                else:
                    grp.conditionals.extend(items)

    def traits_view(self):
        v = View(self._view_tabs(),
                 buttons=['OK'],
                 title=self.title,
                 width=800)
        return v

# ============= EOF =============================================



