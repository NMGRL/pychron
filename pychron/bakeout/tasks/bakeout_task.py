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
from traits.api import HasTraits, Any
from pyface.tasks.task_layout import TaskLayout, PaneItem
from pyface.tasks.action.schema import SMenu, SMenuBar
from pyface.tasks.action.task_action import TaskAction

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_task import BaseTask
from pychron.bakeout.tasks.bakeout_pane import  GraphPane, \
    ControllerPane, ControlsPane


class BakeoutTask(BaseTask):
    id = 'bakeout.main'
    name = 'Bakeout'
    bakeout = Any

    def _default_layout_default(self):
        return TaskLayout(top=PaneItem('bakeout.controller'),
                          left=PaneItem('bakeout.controls'),
                          )
    def prepare_destroy(self):
        self.bakeout.destroy()
        
    def activated(self):
        self.bakeout.activate()

    def find_bakeout(self):
        self.bakeout.find_bakeout()

    def open_latest_bakeout(self):
        self.bakeout.open_latest_bake()

    def _menu_bar_default(self):
        file_menu = SMenu(
                          TaskAction(id='find_bake',
                                     name='Find Bake...',
                                     accelerator='Ctrl+F',
                                     method='find_bakeout'),
                          TaskAction(name='Open Latest Bake...',
                                       method='open_latest_bakeout'),
                          id='File', name='&File'
                          )

        mb = SMenuBar(
                      file_menu,
                      self._view_menu(),
                      )
        return mb

    def create_central_pane(self):
        bp = GraphPane(model=self.bakeout)
        return bp

    def create_dock_panes(self):
        panes = [
                 ControlsPane(model=self.bakeout),
                 ControllerPane(model=self.bakeout),
#                  ScanPane(model=self.bakeout)
                 ]

        return panes
#============= EOF =============================================
