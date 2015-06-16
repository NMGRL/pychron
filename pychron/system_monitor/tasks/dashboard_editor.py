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
import time
# from apptools.preferences.preference_binding import bind_preference
from traits.api import Instance, Int, Dict

# ============= standard library imports ========================
from numpy import array, vstack
# ============= local library imports  ==========================
from pychron.processing.plotter_options_manager import DashboardOptionsManager
from pychron.pipeline.plot.figure_container import FigureContainer
from pychron.pipeline.plot.models.series_model import DashboardSeriesModel
from pychron.pipeline.plot.editors.series_editor import SeriesEditor
from pychron.system_monitor.tasks.controls import SystemMonitorControls

"""
    subscribe to pyexperiment
    or poll database for changes

    use poll to check subscription availability
    suspend db poll when subscription becomes available

"""


class DashboardEditor(SeriesEditor):
    tool = Instance(SystemMonitorControls)

    plotter_options_manager_klass = DashboardOptionsManager
    pickle_path = 'dashboard'
    model_klass = DashboardSeriesModel
    name = 'Dashboard'
    measurements = Dict
    limit = Int(100)

    def _get_dump_tool(self):
        return self.tool

    def _load_tool(self, obj):
        self.tool = obj

    def set_measurements(self, keys):
        m = {}
        for ki in keys:
            m[ki] = None

        self.measurements = m
        po = self.plotter_options_manager.plotter_options
        po.load_aux_plots(self.measurements.keys())

    def _gather_unknowns(self, refresh_data,
                         exclude='invalid',
                         compress_groups=True):
        return self.measurements

    def get_component(self, ans, plotter_options):
        if plotter_options is None:
            pom = self.plotter_options_manager_klass()
            plotter_options = pom.plotter_options

        model = self.model_klass(plot_options=plotter_options)
        model.measurements = ans
        iv = FigureContainer(model=model)
        model.refresh()

        return model, iv.component

    def update_measurements(self, name, value):
        t = time.time()
        # if name in self.measurements:
        meas = self.measurements[name]
        if meas is None:
            ms = array([(t, value)])
        else:
            ms = vstack((meas[-self.limit:], [(t, value)]))

        self.measurements[name] = ms
        self.rebuild()

    def _load_refiso(self, ref):
        pass

    def _set_name(self):
        pass

    def _tool_default(self):
        tool = SystemMonitorControls()
        return tool

# ============= EOF =============================================
