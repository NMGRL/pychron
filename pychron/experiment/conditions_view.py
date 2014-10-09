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
from pychron.experiment.condition.condition import ActionCondition, TruncationCondition, TerminationCondition
from pychron.experiment.condition.conditions_edit_view import ConditionsViewable, ConditionGroup, PostRunGroup, \
    PreRunGroup


# class ConditionsAdapter(TabularAdapter):
#     columns = [('Attribute', 'attr'),
#                ('Check', 'comp'),
#                ('Start', 'start_count'),
#                ('Frequency', 'frequency'),
#                ('Value', 'value')]
#
#     attr_width=Int(100)
#     check_width=Int(200)
#     start_width=Int(50)
#     frequency_width=Int(100)
#     value_width=Int(120)


class ConditionsView(ConditionsViewable):
    def __init__(self, run, pret, postt, *args, **kw):
        super(ConditionsView, self).__init__(*args, **kw)
        self._load(run, pret, postt)

    def _load(self, run, pret, postt):
        for name, items, klass, cklass in (('actions', ConditionGroup, ActionCondition),
                                    ('truncations', ConditionGroup, TruncationCondition),
                                    ('terminations', ConditionGroup, TerminationCondition)):
            items=getattr(run, '{}_conditions'.format(name[:-1]))
            grp = self._group_factory(items, klass, cklass)
            setattr(self, '{}_group'.format(name), grp)


            grp = self._group_factory(pret, 'pre_run_terminations', PreRunGroup)
            self.pre_run_terminations_group=grp

            grp = self._group_factory(postt, 'post_run_terminations', PostRunGroup)
            self.post_run_terminations_group=grp

    def _group_factory(self, items, klass, condition_klass=None):
        if condition_klass is None:
            condition_klass = TerminationCondition

        group = klass(items, condition_klass,
                      editable=False)
        return group

    # termination_conditions = List
    #
    # def traits_view(self):
    #     editor = TabularEditor(adapter=ConditionsAdapter(),
    #                            editable=False,
    #                            auto_update=True)
    #
    #     v = View(UItem('termination_conditions',
    #                    editor=editor),
    #              title='Current Conditions',
    #              width=800,
    #              resizable=True)
    #     return v

#============= EOF =============================================



