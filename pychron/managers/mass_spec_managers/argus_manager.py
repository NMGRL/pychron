# ===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import HasTraits, Property, \
    Str, Float, Button, Color, Int, Instance, Bool, List
from traitsui.api import View, Item, HGroup, VGroup, spring
# from pyface.timer.timer import Timer

# ============= standard library imports ========================

# ============= local library imports  ==========================

# ============= views ===================================

from pychron.managers.manager import Manager
import random
from pychron.graph.time_series_graph import TimeSeriesStreamGraph
from pychron.core.helpers.color_generators import colorname_generator
from threading import Thread, Condition
import time
colorname_gen = colorname_generator()

SCAN_INTERVAL = 500

class Detector(HasTraits):
    '''
        G{classtree}
    '''
    signal = Float
    name = Str
    graph = None
    series_id = 0
    color = Color
    enabled = Bool

    def _child_groups(self):
        '''
        '''
        pass
    def traits_view(self):
        '''
        '''
        vg = VGroup()
        vg.content.append(HGroup(Item('enabled', show_label=False),
                                 Item('signal', format_str='%0.5f', style='readonly'),
                                 Item('color', style='readonly', show_label=False, width=60),
                                 spring))

        cg = self._child_groups()
        if cg:
            vg.content.append(cg)
        v = View(vg
               )

        return v
    def collect_data(self, condition):
        '''
            @type condition: C{str}
            @param condition:
        '''
        self.enabled = True
        condition.acquire()
        num_integration = 5
        s = []
        for _i in range(num_integration):
            si = self.get_signal_from_device()
            s.append(si)
            if self.graph is not None:
                self.graph.record(si, series=self.series_id)
            time.sleep(1)

        self.enabled = False

        condition.notify()
        condition.release()

    def get_signal_from_device(self):
        '''
        '''
        self.signal = random.randint(0, 1000) / 1000.0

        self.signal = 5 + self.series_id
        return self.signal
#        if self.graph is not None:
#            if self.enabled:
#                v=self.signal
#            else:
#                v=None
#
#            self.graph.record(v,series=self.series_id)
#
class FaradayDetector(Detector):
    '''
    '''
    resistance = Int
    def __init__(self, *args, **kw):
        '''
                    '''
        super(FaradayDetector, self).__init__(**kw)
        if args:
            self.resistance = int(args[0])
    # def _child_groups(self):
    #    return HGroup(Item('resistance',style='readonly'),spring)
class IonCounterDetector(Detector):
    '''
    '''
    pass

class ArgusManager(Manager):
    '''
    '''
    magnet_position = Property(Float(enter_set=True, auto_set=False))
    _magnet_position = Float

    _detector_map = None
    detectors = List
    measure = Button
    graph = Instance(TimeSeriesStreamGraph)
    det_timers = None
    def load(self):
        '''
        '''
        config = self.get_configuration()
        # load the detectors

        if config is not None:
            #  config.

            self._detector_map = self.config_get(config, 'General', 'detector_map').split(',')
            for d in config.options('Detectors'):
                det_args = config.get('Detectors', d).split(',')

                det_name = det_args[0]

                _class_ = globals()['%sDetector' % det_name]
                det = _class_(name=d, *det_args[1:])
                self.add_trait(d, det)
                self.detectors.append(det)

    def _measure_fired(self):
        '''
        '''
        self.det_timers = []
        for d in self._detector_map:
            det = getattr(self, d)

            # if det.enabled:
                # setup graph
            xs, _ys = self.graph.new_series(type='scatter', marker='circle',
                                        marker_size=2.5, line_width=0)
            series_id = int(xs[1:])
            # setup timers
            det.series_id = series_id
            det.graph = self.graph
            det.color = colorname_gen.next()


            # self.det_timers.append(Timer(SCAN_INTERVAL,det.get_signal_from_device))


        self.measure_thread = Thread(target=self.measure_gas)
        self.measure_thread.start()
    def measure_gas(self):
        '''
        '''
        for _i in range(6):
            self.measure_cycle()
    def measure_cycle(self):
        '''
        '''
        cond = Condition()
        cond.acquire()
        for i, _d in enumerate(self._detector_map):
            t = Thread(target=self.detectors[i].collect_data, args=(cond,))
            t.start()
            # self.detectors[i].collect_data(cond)
            cond.wait()
        cond.release()


#    @on_trait_change('detectors.enabled')
#    def stop_timer(self, object, old,new):
#      #  print object,old,new
#
#        if self.det_timers:
#            id=object.series_id
#            if not new:
#
#                self.det_timers[id].Stop()
#            else:
#                self.det_timers[id]=Timer(500,object.get_signal_from_device)

    def _graph_default(self):
        '''
        '''
        t = TimeSeriesStreamGraph()
        t.new_plot(data_limit=300,
                   scan_delay=SCAN_INTERVAL / 1000.0)
        t.set_y_limits(min_=0, max_=10)
        return t


    def traits_view(self):
        '''
        '''
        detector_group = VGroup(show_border=True)

        for d in self._detector_map:
            detector_group.content.append(Item(d, style='custom'))



        v = View(VGroup(HGroup(Item('measure', show_label=False), spring),
                      HGroup(Item('magnet_position'), spring),
                      HGroup(detector_group, spring),
                      Item('graph', style='custom', show_label=False),
#                      spring,
                      ),
               width=self.window_width,
               height=self.window_height,
               resizable=True)
        return v


# ===============================================================================
# property methods
# ===============================================================================
    def _get_magnet_position(self):
        '''
        '''
        return self._magnet_position
    def _set_magnet_position(self, v):
        '''
            @type v: C{str}
            @param v:
        '''
        if v != self._magnet_position:
            self.info('user request magnet position %0.5f' % v)
            self._magnet_position = v

    def _validate_magnet_position(self, v):
        '''
            @type v: C{str}
            @param v:
        '''
        try:
            nv = float(v)
        except ValueError:
            nv = self._magnet_position
        return nv
# ============= EOF ====================================
