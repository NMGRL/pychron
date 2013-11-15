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
from traits.etsconfig.etsconfig import ETSConfig
ETSConfig.toolkit = 'qt4'
#============= enthought library imports =======================
from traits.api import HasTraits, Int, Float, Instance
from traitsui.api import View, Item, UItem, ButtonEditor, HGroup

from pychron.mv.machine_vision_manager import MachineVisionManager
#============= standard library imports ========================
from numpy import random
import time
#============= local library imports  ==========================
from pychron.mv.lumen_detector import LumenDetector
from pychron.graph.stream_graph import StreamStackedGraph
from pychron.graph.stacked_graph import StackedGraph
from pychron.execute_mixin import ExecuteMixin
from pychron.mv.test_image import TestImage


class PID(HasTraits):
    _integral_err = 0
    _prev_err = 0
    Kp = Float(0.25)
    Ki = Float(0.0001)
    Kd = Float(0)
    min_output = 0
    max_output = 100
    def get_value(self, error, dt):
        self._integral_err += (error * dt)
        derivative = (error - self._prev_err) / dt
        output = (self.Kp * error) + (self.Ki * self._integral_err) + (self.Kd * derivative)
        self._prev_err = error
        return min(self.max_output, max(self.min_output, output))
    def traits_view(self):
        v = View(
               Item('Kp'),
               Item('Ki'),
               Item('Kd'),
               )
        return v
class Degasser(MachineVisionManager, ExecuteMixin):
    _period = 0.05
    crop_width = Int(5)
    crop_height = Int(5)

    _test_lumens = Float(100)
    _test_duration = Int(10)
    _test_graph = Instance(StackedGraph)
    _test_image = Instance(TestImage)
    _testing = False

    pid = Instance(PID, ())

    def degas(self, lumens, duration):
        '''
            degas for duration trying to maintain
            lumens
        '''
        if self.laser_manager:

            self.laser_manager.fiber_light.power_off()

        g = self._make_graph(lumens, duration)
        if self._testing:
            self._test_graph = g
        else:
            self.laser_manager.auxilary_graph = g.plotcontainer

        cw, ch = 2 * self.crop_width * self.pxpermm, 2 * self.crop_height * self.pxpermm
#         print cw, ch
        if not cw % 5 == 0:
            cw += cw % 5
        if not ch % 5 == 0:
            ch += ch % 5

        cw, ch = 200, 200
#         im = self.new_image(
# #                             frame=zeros((ch, cw)),
#                             title='Luminosity', view_id='lumens')
        im = TestImage()
        im.setup_images(1, (cw, ch))
        if self._testing:
            self._test_image = im
        else:
            self.view_image(im)

        self._detector = LumenDetector()
        dt = self._period

        pid = self.pid
        st = time.time()
        i = 0
        while 1:
            ct = time.time()
            tt = ct - st
            if not self.isAlive():
                break

            cl = self._get_current_lumens(im, cw, ch)

            err = lumens - cl
            out = pid.get_value(err, dt)
#             err = random.random()
            g.add_data(((tt, out), (tt, err), (tt, cl)))
#             g.redraw()
#             if i % 5 == 0:
            self._set_power(out, i)

            if tt > duration:
                break
            et = time.time() - ct
            time.sleep(max(0, dt - et))

            i += 1
            if i > 1e6:
                i = 0

        if self.laser_manager:
            self.laser_manager.fiber_light.power_on()

        self.executing = False

    def _set_power(self, pwr, cnt):
        if self.laser_manager:
            self.laser_manager.set_laser_power(pwr, verbose=cnt == 0)

    def _get_current_lumens(self, im, cw, ch):
        src = self.new_image_frame()
        if src:
            src = self._crop_image(src, cw, ch)
        else:
            src = random.random((ch, cw)) * 255
            src = src.astype('uint8')
#         return random.random()
        src, v = self._detector.get_value(src)
        im.set_image(src)
        return v

    def _make_graph(self, lumens, duration):
        g = StackedGraph(container_dict=dict(stack_order='top_to_bottom'))
        g.new_plot(
                   ytitle='Output (W)'
                   )
        g.new_series()
        g.new_plot(
                   ytitle='Residual'
                   )
        g.new_series(plotid=1)
        g.new_plot(
                   ytitle='Lumens',
                   xtitle='time (s)')
        g.new_series(plotid=2)

        g.add_horizontal_rule(lumens, plotid=2)
        g.set_x_limits(0, duration * 1.1)
        return g

    def _do_execute(self):

        self.debug('starting test degas {} {}'.format(self._test_lumens, self._test_duration))
        self._testing = True
        self.degas(self._test_lumens, self._test_duration)

    def traits_view(self):
        v = View(
                 UItem('execute', editor=ButtonEditor(label_value='execute_label')),
                 HGroup(Item('_test_lumens'), Item('_test_duration')),
                 UItem('pid', style='custom'),
                 HGroup(UItem('_test_graph',
                              height=400,
                              style='custom'),
                        UItem('_test_image', style='custom')
                        ),

                 resizable=True
                 )
        return v

if __name__ == '__main__':

    from pychron.image.video import Video

    d = Degasser(

                 )
    d.configure_traits()
#============= EOF =============================================
