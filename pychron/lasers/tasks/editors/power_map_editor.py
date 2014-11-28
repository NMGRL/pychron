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
from pychron.core.ui import set_qt

set_qt()
#============= enthought library imports =======================
from traits.api import HasTraits, \
    Instance, Float, Int, Bool, DelegatesTo, Range
from traitsui.api import View, Item, UItem, VGroup, \
    HGroup, spring
# from pychron.envisage.tasks.base_editor import BaseTraitsEditor
# from pychron.loggable import Loggable
# from pychron.canvas.canvas2D.raster_canvas import RasterCanvas
from enable.component_editor import ComponentEditor
from pychron.lasers.power.power_mapper import PowerMapper
from pychron.core.ui.thread import Thread
from pychron.lasers.power.power_map_processor import PowerMapProcessor
from pychron.managers.data_managers.h5_data_manager import H5DataManager
# from pychron.graph.graph import Graph
# from pychron.graph.contour_graph import ContourGraph
# from chaco.plot_containers import HPlotContainer
from pychron.lasers.tasks.editors.laser_editor import LaserEditor
#============= standard library imports ========================
#============= local library imports  ==========================


class PowerMapControls(HasTraits):
    beam_diameter = Float(1)
    request_power = Float(1)
    padding = Float(1.0)
    step_length = Float(0.25)
    center_x = Float(0)
    center_y = Float(0)
    integration = Int(1)
    discrete_scan = Bool(False)

    def traits_view(self):
        v = View(VGroup(

            Item('discrete_scan'),
            Item('beam_diameter'),
            Item('request_power'),
            Item('padding'),
            Item('step_length'),
            Item('center_x'),
            Item('center_y'),

        )
        )
        return v


class PowerMapEditor(LaserEditor):
    percent_threshold = Range(0.0, 100.0)

    beam_diameter = Float
    power = Float

    #     canvas = Instance(RasterCanvas, ())
    editor = Instance(PowerMapControls, ())
    mapper = Instance(PowerMapper, ())
    completed = DelegatesTo('mapper')
    #was_executed = False

    processor = Instance(PowerMapProcessor)

    def _percent_threshold_changed(self, new):
        if self.processor:
            self.processor.set_percent_threshold(new)

    def load(self, path):
        pmp = PowerMapProcessor()

        reader = H5DataManager()
        reader.open_data(path)
        cg = pmp.load_graph(reader)

        self.beam_diameter, self.power = pmp.extract_attrs(['beam_diameter', 'power'])
        self.component = cg.plotcontainer
        self.was_executed = True
        self.processor = pmp

    def _do_execute(self):
        mapper = self.mapper
        mapper.laser_manager = self._laser_manager

        editor = self.editor
        padding = editor.padding

        #         if editor.discrete_scan:
        #             mapper.canvas = self.canvas
        #             self.component = self.canvas
        #         else:

        c = mapper.make_component(padding)
        self.component = c

        bd = editor.beam_diameter
        rp = editor.request_power
        cx = editor.center_x
        cy = editor.center_y
        step_len = editor.step_length

        t = Thread(target=mapper.do_power_mapping,
                   args=(bd, rp, cx, cy, padding, step_len))
        t.start()
        self._execute_thread = t

        return True

    def stop(self):
        self.mapper.stop()

    def traits_view(self):
        v = View(
            HGroup(spring,
                   Item('beam_diameter', style='readonly'),
                   Item('power', style='readonly'),
                   Item('percent_threshold', label='% Threshold'),
                   visible_when='was_executed'
            ),
            UItem('component', editor=ComponentEditor()),
            resizable=True
        )
        return v


if __name__ == '__main__':
    e = PowerMapEditor()
    p = '/Users/ross/Sandbox/powermap/powermap-2013-07-26005.hdf5'
    p = '/Users/ross/Sandbox/powermap/powermap-2013-07-27008.hdf5'
    e.load(p)
    e.configure_traits()
# ============= EOF =============================================
