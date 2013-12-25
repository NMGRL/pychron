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
from traits.api import Button, List
#============= standard library imports ========================
#============= local library imports  ==========================
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem
from pychron.envisage.tasks.base_task import BaseManagerTask
from pychron.envisage.browser.browser_mixin import BrowserMixin
from pychron.geo.primitives import AgePoint
from pychron.geo.tasks.actions import ExportShapefileAction
from pychron.geo.tasks.panes import BrowserPane, GeoPane


class GeoTask(BaseManagerTask, BrowserMixin):
    tool_bars = [SToolBar(ExportShapefileAction())]

    append_button=Button
    replace_button=Button
    points=List

    def activated(self):
        self.activate()

    def create_central_pane(self):
        return GeoPane(model=self)

    def create_dock_panes(self):
        panes=[BrowserPane(model=self)]

        return panes

    def export_shapefile(self):
        print 'export shape file'

    def _append_button_fired(self):
        points=self._make_points(self.selected_samples)
        self.points.extend(points)

    def _replace_button_fired(self):
        points = self._make_points(self.selected_samples)
        self.points= points

    def _make_points(self, samples):
        pts=[self._make_point(si) for si in samples]
        return pts

    def _make_point(self, sample):
        return AgePoint(sample=sample.name,
                        x=sample.lon,
                        y=sample.lat,
                        elevation=sample.elevation)

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.geo.browser'))
#============= EOF =============================================
