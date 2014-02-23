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
from traits.api import Button, List, Any, Event
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem
#============= standard library imports ========================
import os
from pyproj import Proj, transform

#============= local library imports  ==========================
from pychron.core.ui.preference_binding import bind_preference
from pychron.envisage.tasks.base_task import BaseManagerTask
from pychron.envisage.browser.browser_mixin import BrowserMixin
from pychron.geo.primitives import AgePoint
from pychron.geo.shape_file_writer import ShapeFileWriter
from pychron.geo.tasks.actions import ExportShapefileAction
from pychron.geo.tasks.panes import BrowserPane, GeoPane
from pychron.paths import paths


class GeoTask(BaseManagerTask, BrowserMixin):
    tool_bars = [SToolBar(ExportShapefileAction())]

    append_button = Button
    replace_button = Button
    points = List
    selected_point = Any
    dclicked_point = Event
    active_point = Any

    def activated(self):
        self.load_projects()
        bind_preference(self.search_criteria, 'recent_hours', 'pychron.processing.recent_hours')

        self.load_browser_selection()

    def prepare_destroy(self):
        self.dump_browser_selection()

    def create_central_pane(self):
        return GeoPane(model=self)

    def create_dock_panes(self):
        panes = [BrowserPane(model=self)]
        return panes

    def export_strat_canvas(self):
        self.manager.make_strat_canvas_file()

    def export_shapefile(self):
        writer = ShapeFileWriter()
        p = os.path.join(paths.disseration, 'data', 'minnabluff', 'gis', 'test_points.shp')
        if writer.write_points(p, points=self.points,
                               attrs=('sample', 'material', 'age', 'age_error')):

            if self.confirmation_dialog('Shape file saved to {}\n\n Do you want to open in QGIS ?'.format(p)):
                self.view_file(p, application='QGIS')
        else:
            self.warning_dialog('Failed saving shape file')

    def _append_button_fired(self):
        points = self._make_points(self.selected_samples)
        self.points.extend(points)

    def _replace_button_fired(self):
        points = self._make_points(self.selected_samples)
        self.points = points

    def _dclicked_point_fired(self):
        if self.selected_point:
            self.active_point = self.selected_point

    def _make_points(self, samples):
        p1 = Proj(proj='latlong', datum='WGS84')
        p2 = Proj(init='epsg:3031')
        db = self.manager.db
        with db.session_ctx():
            pts = [self._make_point(db, si, p1, p2) for si in samples]
        return pts

    def _make_point(self, db, sample, p1, p2):
        easting, northing = transform(p1, p2, sample.lon, sample.lat)
        histories = db.get_interpreted_age_histories((sample.labnumber,))
        ias = [db.interpreted_age_factory(db, hi) for hi in histories]

        ap = AgePoint(sample=sample.name,
                      x=easting, y=northing,
                      elevation=sample.elevation,
                      interpreted_ages=ias)
        if ias:
            ap.interpreted_age = ias[-1]

        return ap

    def _active_point_default(self):
        return AgePoint()

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.geo.browser'))

#============= EOF =============================================
