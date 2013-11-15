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
from traits.api import on_trait_change
from pyface.tasks.task_layout import TaskLayout, VSplitter, PaneItem, \
    HSplitter, Tabbed
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.tasks.analysis_edit.interpolation_task import InterpolationTask


class IntercalibrationFactorTask(InterpolationTask):
    id = 'pychron.analysis_edit.ic_factor'
    ic_factor_editor_count = 1
    name = 'Detector Intercalibration'

    def _default_layout_default(self):
        return TaskLayout(
            id='pychron.analysis_edit.ic_factor',
            left=HSplitter(
                PaneItem('pychron.browser'),
                VSplitter(
                    Tabbed(PaneItem('pychron.analysis_edit.unknowns'),
                           PaneItem('pychron.analysis_edit.references')),
                    PaneItem('pychron.analysis_edit.controls'),
                )
            )
        )

    def new_ic_factor(self):
        from pychron.processing.tasks.detector_calibration.intercalibration_factor_editor import IntercalibrationFactorEditor

        editor = IntercalibrationFactorEditor(name='ICFactor {:03n}'.format(self.ic_factor_editor_count),
                                              processor=self.manager
        )
        self._open_editor(editor)
        self.ic_factor_editor_count += 1

        #selector = self.manager.db.selector
        #self.unknowns_pane.items = selector.records[156:159]
        #self.references_pane.items = selector.records[150:155]

    @on_trait_change('active_editor:tool:[analysis_type]')
    def _handle_analysis_type(self, obj, name, old, new):
        if name == 'analysis_type':
            records = self.unknowns_pane.items
            if records is None:
                records = self.analysis_table.selected

            if records:
                ans = self._load_references(records, new)
                ans = self.manager.make_analyses(ans)
                self.references_pane.items = ans


#============= EOF =============================================
