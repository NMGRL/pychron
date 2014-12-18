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
from pychron.core.ui import set_qt
from pychron.experiment.utilities.conditionals import CONDITIONAL_GROUP_TAGS

set_qt()

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
        self._add_pre_post('post_run_terminations_group', 'PostRunTerminations', items, PostRunGroup)

    def add_pre_run_terminations(self, items):
        self._add_pre_post('pre_run_terminations_group', 'PreRunTerminations', items, PreRunGroup)

    def _add_pre_post(self, name, label, items, klass):
        if not items:
            items = []

        # grp = getattr(self, name)
        grp = next((gi for gi in self.groups if gi.label == label), None)

        print name, label, grp, [gi.label for gi in self.groups]
        if not grp:
            self._group_factory(items, klass, auto_select=False, label=label)
            # setattr(self, name, self._group_factory(items, klass, auto_select=False))
        else:
            grp.conditionals.extend(items)

    def add_system_conditionals(self, ditems):
        for name, klass, cklass in (('actions', ConditionalGroup, ActionConditional),
                                    ('truncations', ConditionalGroup, TruncationConditional),
                                    ('cancelations', ConditionalGroup, CancelationConditional),
                                    ('terminations', ConditionalGroup, TerminationConditional)):
            items = ditems.get(name, [])
            self._group_factory(items, klass, conditional_klass=cklass,
                                auto_select=False, label=name.capitalize())

            # setattr(self, '{}_group'.format(name), grp)

    def add_conditionals(self, ditems):
        for tag in CONDITIONAL_GROUP_TAGS:
            tag = '{}s'.format(tag)
            # grp = getattr(self, '{}s_group'.format(tag))
            grp = next((gi for gi in self.groups if gi.label == tag.capitalize()), None)
            items = ditems.get(tag)
            if items:
                grp.conditionals.extend(items)

    # def add_run_conditionals(self, ditems):
    # for tag in TAGS:
    #         # grp = getattr(self, '{}s_group'.format(tag))
    #         # items = getattr(run, '{}_conditionals'.format(tag))
    #         # grp.conditionals.extend(items)

    def traits_view(self):
        v = View(self._view_tabs(),
                 buttons=['OK'],
                 title=self.title,
                 width=800)
        return v

# ============= EOF =============================================



