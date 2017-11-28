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
from chaco.default_colormaps import hot
from chaco.plot import Plot
from chaco.plot_containers import HPlotContainer
from enable.component_editor import ComponentEditor
from skimage.color import gray2rgb
from traits.api import HasTraits, Int, Float, Instance, Range, on_trait_change, Button
from traitsui.api import View, Item, UItem, ButtonEditor, HGroup, VGroup

from pychron.core.pid import PID
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.graph.graph import Graph
from pychron.graph.stream_graph import StreamGraph, StreamStackedGraph
from pychron.loggable import Loggable
from threading import Event, Thread
# from pychron.mv.machine_vision_manager import MachineVisionManager
# ============= standard library imports ========================
from numpy import uint8, zeros, random
import time


# ============= local library imports  ==========================
# from pychron.mv.lumen_detector import LumenDetector
# from pychron.graph.stacked_graph import StackedGraph
# from pychron.execute_mixin import ExecuteMixin
# from pychron.mv.mv_image import MVImage

class LM:
    def __init__(self, t, dt=1):
        self._pid = PID(kp=-0.5, ki=0.1)
        self._dt = dt
        self._target_value = t

    def set_laser_power_hook(self, *args, **kw):
        pass

    def get_brightness(self, v):
        err = self._target_value - v
        out = self._pid.get_value(err, self._dt)
        src = random.randint(0, 255, (150, 150))
        return src.astype(uint8), out


class Degasser(Loggable):
    laser_manager = None

    p = Range(0.0, 1.0)
    i = Range(0.0, 1.0)
    d = Range(0.0, 1.0)

    lumens = Float(50)
    dt = Float(1)
    pid = None
    stream_graph = Instance(StreamStackedGraph, ())
    img_graph = Instance(Graph, ())
    plot_container = Instance(HPlotContainer, ())
    test = Button

    _lum_thread = None
    _lum_evt = None
    _luminosity_value = 0

    def _test_fired(self):
        self.degas()

    def stop(self):
        self.debug('stop')
        self._lum_evt.set()

    def degas(self, lumens=None):
        if lumens is None:
            lumens = self.lumens

        self._setup_graph()
        self.edit_traits()

        self._lum_evt = Event()
        self._lum_thread = Thread(target=self._degas, args=(lumens,))
        self._lum_thread.start()

    def _setup_graph(self):
        g = self.stream_graph
        g.clear()
        g.new_plot(padding_left=70, padding_right=10)
        g.new_series(plotid=0)
        g.set_y_title('Lumens', plotid=0)
        g.new_plot(padding_left=70, padding_right=10)
        g.new_series(plotid=1)
        g.set_y_title('Error', plotid=1)
        g.new_plot(padding_left=70, padding_right=10)
        g.new_series(plotid=2)
        g.set_y_title('Output', plotid=2)

        imgplot = self.img_graph.new_plot(padding_right=10)
        imgplot.aspect_ratio = 1.0
        imgplot.x_axis.visible = False
        imgplot.y_axis.visible = False
        imgplot.x_grid.visible = False
        imgplot.y_grid.visible = False

        imgplot.data.set_data('imagedata', zeros((150, 150, 3), dtype=uint8))
        imgplot.img_plot('imagedata', origin='top left')

        self.plot_container.add(self.stream_graph.plotcontainer)
        self.plot_container.add(self.img_graph.plotcontainer)

    def _degas(self, lumens):

        self.lumens = lumens
        g = self.stream_graph
        img = self.img_graph.plots[0]

        def update(c, e, o, src):
            g.record(c, plotid=0)
            g.record(e, plotid=1)
            g.record(o, plotid=2)
            img.data.set_data('imagedata', gray2rgb(src))

        evt = self._lum_evt
        set_laser_power = self.laser_manager.set_laser_power_hook
        self.pid = pid = PID()

        get_brightness = self.laser_manager.get_brightness
        dt = self.dt
        target = self.lumens
        out = 0
        while not evt.is_set():
            src, current = get_brightness(out)

            err = target - current
            out = pid.get_value(err, dt)

            invoke_in_main_thread(update, current, err, out, src)

            # set_laser_power(out)
            evt.wait(dt)

    @on_trait_change('p,i,d')
    def update_pid_params(self, name, value):
        if self.pid:
            setattr(self.pid, 'k{}'.format(name), value)

    def traits_view(self):
        v = View(VGroup(HGroup(Item('p'), Item('i'), Item('d'), Item('dt')),
                        Item('test'),
                        UItem('plot_container', style='custom', editor=ComponentEditor())))
        return v


#
# class PID(HasTraits):
#     _integral_err = 0
#     _prev_err = 0
#     Kp = Float(0.25)
#     Ki = Float(0.0001)
#     Kd = Float(0)
#     min_output = 0
#     max_output = 100
#
#     def get_value(self, error, dt):
#         self._integral_err += (error * dt)
#         derivative = (error - self._prev_err) / dt
#         output = (self.Kp * error) + (self.Ki * self._integral_err) + (
#             self.Kd * derivative)
#         self._prev_err = error
#         return min(self.max_output, max(self.min_output, output))
#
#     def traits_view(self):
#         v = View(
#                 Item('Kp'),
#                 Item('Ki'),
#                 Item('Kd'))
#         return v
#
#
# class Degasser(MachineVisionManager, ExecuteMixin):
#     _period = 0.05
#     crop_width = Int(5)
#     crop_height = Int(5)
#
#     _test_lumens = Float(100)
#     _test_duration = Int(10)
#     _test_graph = Instance(StackedGraph)
#     _test_image = Instance(MVImage)
#     _testing = False
#
#     pid = Instance(PID, ())
#     _detector = Instance(LumenDetector)
#
#     def degas(self, lumens, duration):
#         """
#             degas for duration trying to maintain
#             lumens
#         """
#         if self.laser_manager:
#             self.laser_manager.fiber_light.power_off()
#
#         g = self._make_graph(lumens, duration)
#         if self._testing:
#             self._test_graph = g
#         else:
#             self.laser_manager.auxilary_graph = g.plotcontainer
#
#         cw, ch = 2 * self.crop_width * self.pxpermm, 2 * self.crop_height * self.pxpermm
#
#         # if not cw % 5 == 0:
#         #     cw += cw % 5
#         # if not ch % 5 == 0:
#         #     ch += ch % 5
#         #
#         # cw, ch = 200, 200
#
#         im = MVImage()
#         im.setup_images(1, (cw, ch))
#         if self._testing:
#             self._test_image = im
#         else:
#             self.view_image(im)
#
#         self._detector = LumenDetector()
#         dt = self._period
#
#         pid = self.pid
#         st = time.time()
#         i = 0
#         while 1:
#             ct = time.time()
#             tt = ct - st
#             if not self.isAlive():
#                 break
#
#             cl = self._get_current_lumens(im, cw, ch)
#
#             err = lumens - cl
#             out = pid.get_value(err, dt)
#             g.add_data(((tt, out), (tt, err), (tt, cl)))
#
#             self._set_power(out, i)
#
#             if tt > duration:
#                 break
#             et = time.time() - ct
#             time.sleep(max(0, dt - et))
#
#             i += 1
#             if i > 1e6:
#                 i = 0
#
#         if self.laser_manager:
#             self.laser_manager.fiber_light.power_on()
#
#         self.executing = False
#
#     def _set_power(self, pwr, cnt):
#         if self.laser_manager:
#             self.laser_manager.set_laser_power(pwr, verbose=cnt == 0)
#
#     def _get_current_lumens(self, im, cw, ch):
#         src = self.new_image_frame()
#         if src:
#             src = self._crop_image(src, cw, ch)
#         else:
#             src = random.random((ch, cw)) * 255
#             src = src.astype('uint8')
#         src, v = self._detector.get_value(src)
#         im.set_image(src)
#         return v
#
#     def _make_graph(self, lumens, duration):
#         g = StackedGraph(container_dict=dict(stack_order='top_to_bottom'))
#         g.new_plot(ytitle='Output (W)')
#         g.new_series()
#         g.new_plot(ytitle='Residual')
#         g.new_series(plotid=1)
#         g.new_plot(ytitle='Lumens', xtitle='time (s)')
#         g.new_series(plotid=2)
#
#         g.add_horizontal_rule(lumens, plotid=2)
#         g.set_x_limits(0, duration * 1.1)
#         return g
#
#     def _do_execute(self):
#
#         self.debug('starting test degas {} {}'.format(self._test_lumens,
#                                                       self._test_duration))
#         self._testing = True
#         self.degas(self._test_lumens, self._test_duration)
#
#     def traits_view(self):
#         v = View(UItem('execute',
#                        editor=ButtonEditor(label_value='execute_label')),
#                  HGroup(Item('_test_lumens'), Item('_test_duration')),
#                  UItem('pid', style='custom'),
#                  HGroup(UItem('_test_graph',
#                               height=400,
#                               style='custom'),
#                         UItem('_test_image', style='custom')),
#                  resizable=True)
#         return v
#
#
if __name__ == '__main__':
    d = Degasser(laser_manager=LM(30))
    d.configure_traits()
# # ============= EOF =============================================
