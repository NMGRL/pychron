#===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema_addition import SchemaAddition
from pyface.action.group import Group

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.entry.tasks.actions import SaveLabbookPDFAction, MakeIrradiationTemplateAction, LabnumberEntryAction, SensitivityEntryAction, AddMolecularWeightAction
from pychron.entry.molecular_weight_factory import MolecularWeightFactory
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin


class EntryPlugin(BaseTaskPlugin):
    id = 'pychron.entry'

    def _service_offers_default(self):
        so1=self.service_offer_factory(factory=MolecularWeightFactory,
                                       protocol=MolecularWeightFactory)
        return [so1]

    def _my_task_extensions_default(self):
        return [
            TaskExtension(task_id='pychron.entry.labnumber',
                          actions=[
                              SchemaAddition(factory=lambda: Group(SaveLabbookPDFAction(),
                                                                   MakeIrradiationTemplateAction()),
                                             path='MenuBar/Tools'
                              )]),

            TaskExtension(
                actions=[
                    SchemaAddition(id='labnumber_entry',
                                   factory=LabnumberEntryAction,
                                   path='MenuBar/Edit',
                                   absolute_position='first'
                    ),
                    SchemaAddition(id='sensitivity_entry',
                                   factory=SensitivityEntryAction,
                                   path='MenuBar/Edit',
                                   absolute_position='first'),
                    SchemaAddition(id='molecular_weight_entry',
                                   factory=AddMolecularWeightAction,
                                   path='MenuBar/Edit',
                                   absolute_position='first'
                                   )])]

    def _tasks_default(self):
        return [TaskFactory(id='pychron.entry.labnumber',
                            factory=self._labnumber_entry_task_factory,
                            include_view_menu=False),
                TaskFactory(id='pychron.entry.sensitivity',
                            factory=self._sensitivity_entry_task_factory,
                            include_view_menu=False)]

    def _labnumber_entry_task_factory(self):
        from pychron.entry.tasks.labnumber_entry_task import LabnumberEntryTask

        return LabnumberEntryTask()

    def _sensitivity_entry_task_factory(self):
        from pychron.entry.tasks.sensitivity_entry_task import SensitivityEntryTask

        return SensitivityEntryTask()

#============= EOF =============================================
