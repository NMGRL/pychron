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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.experiment.conditional.conditional import ActionConditional, TruncationConditional, TerminationConditional
from pychron.experiment.conditional.conditionals_edit_view import ConditionalsViewable, ConditionalGroup, PostRunGroup, \
    PreRunGroup


class ConditionalsView(ConditionalsViewable):
    title = 'Active Conditionals'

    def __init__(self, run, pret, postt, *args, **kw):
        super(ConditionalsView, self).__init__(*args, **kw)
        self._load(run, pret, postt)

    def _load(self, run, pret, postt):
        for name, items, klass, cklass in (('action', ConditionalGroup, ActionConditional),
                                           ('truncation', ConditionalGroup, TruncationConditional),
                                           ('termination', ConditionalGroup, TerminationConditional)):
            items = getattr(run, '{}_conditionals'.format(name))
            grp = self._group_factory(items, klass, cklass)
            setattr(self, '{}s_group'.format(name), grp)

            grp = self._group_factory(pret, 'pre_run_terminations', PreRunGroup)
            self.pre_run_terminations_group = grp

            grp = self._group_factory(postt, 'post_run_terminations', PostRunGroup)
            self.post_run_terminations_group = grp

    def _group_factory(self, items, klass, conditional_klass=None):
        if conditional_klass is None:
            conditional_klass = TerminationConditional

        group = klass(items, conditional_klass,
                      editable=False)
        return group

# ============= EOF =============================================



