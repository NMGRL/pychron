# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from pychron.envisage.tasks.base_task import BaseManagerTask
# ============= standard library imports ========================
# ============= local library imports  ==========================

from pychron.entry.tasks.sensitivity_entry_panes import SensitivityPane
from pychron.entry.entry_views.sensitivity_entry import SensitivityEntry
from pyface.tasks.action.schema import SToolBar
from pychron.entry.tasks.actions import SaveSensitivityAction, \
    AddSensitivityAction


class SensitivityEntryTask(BaseManagerTask):
    name = 'Sensitivity Entry'

    tool_bars = [
        SToolBar(
            SaveSensitivityAction(),
            AddSensitivityAction(),
            image_size=(16, 16)
        ),
    ]

    def activated(self):
        self.manager.activate()

    def create_central_pane(self):
        return SensitivityPane(model=self.manager)

    #     def create_dock_panes(self):
    #         return [
    #                 IrradiationPane(model=self.manager),
    #                 ImporterPane(model=self.extractor),
    #                 IrradiationEditorPane(model=self.manager)
    #                 ]


    #     @on_trait_change('extractor:update_irradiations_needed')
    #     def _update_irradiations(self):
    #         self.manager.updated = True
    # ===========================================================================
    # GenericActon Handlers
    # ===========================================================================
    def save_as(self):
        self.debug('sensitivity entry save as')
        self.save()

    def save(self):
        self.debug('sensitivity entry save')
        self.manager.save()

    def add(self):
        self.debug('sensitivity entry add')
        self.manager.add()

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _manager_default(self):
        man = self.application.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManage')
        return SensitivityEntry(db=man.db)

        #
        #     def _default_layout_default(self):

#         return TaskLayout(
#                           left=Splitter(
#                                         PaneItem('pychron.labnumber.irradiation'),
#                                         Tabbed(
#                                                PaneItem('pychron.labnumber.extractor'),
#                                                PaneItem('pychron.labnumber.editor')
#                                                ),
#                                         orientation='vertical'
#                                         )
#                           )

# ============= EOF =============================================
