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
from traits.api import Any
from pyface.tasks.task_layout import TaskLayout, PaneItem, Splitter, Tabbed
from pyface.tasks.action.schema import SMenu
#============= standard library imports ========================
#============= local library imports  ==========================

from pychron.envisage.tasks.base_task import BaseExtractionLineTask
from pychron.spectrometer.tasks.spectrometer_panes import ScanPane, ControlsPane, \
    ReadoutPane, IntensitiesPane


class SpectrometerTask(BaseExtractionLineTask):
    scan_manager = Any
    name = 'Scan'
    id = 'pychron.spectrometer'

    def prepare_destroy(self):
        self.scan_manager.stop_scan()
        super(SpectrometerTask, self).prepare_destroy()

    def activated(self):
        self.scan_manager.setup_scan()
        super(SpectrometerTask, self).activated()

    def _default_layout_default(self):
        return TaskLayout(
            left=Splitter(
                PaneItem('pychron.spectrometer.controls'),
                Tabbed(PaneItem('pychron.spectrometer.intensities'),
                       PaneItem('pychron.spectrometer.readout')),
                orientation='vertical'
            )

            #                          right=Splitter(
            #                                         PaneItem('pychron.experiment.stats'),
            #                                         PaneItem('pychron.experiment.console'),
            #                                         orientation='vertical'
            #                                         ),
            #                          bottom=PaneItem('pychron.experiment.console'),
            #                          top=PaneItem('pychron.experiment.controls')
        )


    def create_central_pane(self):
        g = ScanPane(
            model=self.scan_manager,
        )
        return g

    def create_dock_panes(self):
        panes = [ControlsPane(model=self.scan_manager),
                 ReadoutPane(model=self.scan_manager),
                 IntensitiesPane(model=self.scan_manager)
        ]

        panes = self._add_canvas_pane(panes)

        #         app = self.window.application
        #         man = app.get_service('pychron.extraction_line.extraction_line_manager.ExtractionLineManager')
        #         if man:
        #             from pychron.extraction_line.tasks.extraction_line_pane import CanvasDockPane
        #             panes.append(CanvasDockPane(canvas=man.new_canvas()))

        #             panes.append(CanvasDockPane(model=man))
        return panes


#============= EOF =============================================
