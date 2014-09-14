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
from traits.etsconfig.etsconfig import ETSConfig

ETSConfig.toolkit = 'qt4'

from pychron.graph.graph import Graph

from pychron.core.ui.gui import invoke_in_main_thread
# from pychron.core.ui.thread import Thread
from threading import Event, Timer, Thread
# from pychron.graph.stacked_graph import StackedGraph
from traits.api import HasTraits, Instance, Button
from traitsui.api import View, UItem
# from pychron.consumer_mixin import consumable
# from pychron.graph.graph import Graph
# from pychron.graph.regression_graph import RegressionGraph, StackedRegressionGraph
import time
from pychron.core.codetools.memory_usage import mem_log, get_current_mem
#============= standard library imports ========================
#============= local library imports  ==========================

class PlotPanel(HasTraits):
    graph = Instance(Graph, ())
#     graph = Instance(StackedRegressionGraph, ())

#     graph = Instance(StackedGraph, ())
    def traits_view(self):
        v = View(UItem('graph', style='custom'))
        return v

class Looper(HasTraits):
    hp = None
    plot_panel = Instance(PlotPanel, ())
    test = Button
    def loop(self, s=5, n=100, d=3):
#         self._loop(n, d)
#         time.sleep(1)
#         print 'fffff'
#         self._loop(n, d)

#         for i in range(s):
#         self._loop(n)
        for i in range(s):
#             if i == 0:
#                 if self.hp:
#                     self.hp.setrelheap()

            self._loop2(n, d)
#             t = Thread(target=self._loop, args=(n, d))
#             self._t = t
#             t.start()
#             t.join()
#             print i

    def _build_graph(self, n, d):
        graph = self.plot_panel.graph

        graph.clear()

        for i in range(d):
            graph.new_plot()

#         count_instances(inst=Plot)
#
#         graph.set_x_limits(max_=n, pad='0.1')
#         mem_log('post new plot')
#
#         for i in range(d):
#             graph.new_series(marker='circle', type='scatter',
#                                      marker_size=1.25,
# #                                      fit='linear',
#                                      plotid=i,
# #                                      use_error_envelope=False
#                                      )
#
#         self.graph = graph

    def _loop2(self, n, d):

        invoke_in_main_thread(self._build_graph, n, d,)
        for i in range(100):
            if i % 10 == 0:
                print '{} {}'.format(i, get_current_mem())
            time.sleep(0.1)

    def _loop(self, n, d):

        mem_log('<loop start')

        invoke_in_main_thread(self._build_graph, n, d,)
        self._iter_event = Event()
        self._iter_event.wait(0.1)

        self._iter(n, d)
#         time.sleep(10)
        self._iter_event.wait(n * 1.1)

        mem_log('> loop finished')

#         mem_log('post new series')
#         m = 200
#         with consumable(func=self._iter_step) as con:
#             func=

#             func = lambda x: con.add_consumable((graph, x))
#             func = lambda i:self._iter_step((graph, i))
#             for i in range(n):
#                 do_after(m, func(i))
#                 con.add_consumable((graph, i))
#                 time.sleep(m)

#         mem_log('> loop finished')
    def _iter(self, n, d):
        self._iter_step(n, 0, d)
#         t = Timer(0.05, self._iter_step, n, 0, d)
#         t.start()

    def _iter_step(self, n, i, d):
        if i % 10 == 0:
            print '{:03n} {}'.format(i, get_current_mem())
#         invoke_in_main_thread(self._graph, d, i)
        if i < n:
            t = Timer(.1, self._iter_step, args=(n, i + 1, d))
            t.start()
#             do_after(100, self._iter_step, n, i + 1, d)
        else:
            self._iter_event.set()

    def _graph(self, d, i):
#         g = self.graph

        if i % 10 == 0:
            print '{:03n} {}'.format(i, get_current_mem())
#         for j in range(d):
#             g.add_datum((i, j + i * 0.1),
# #                         update_y_limits=True,
#                         plotid=j,
#                         ypadding='0.1')
#         if i % 5 == 0:
#         g.refresh()

    def _test_fired(self):
        t = Thread(target=self.loop)
        t.start()


    def traits_view(self):
        v = View(UItem('test'),
                 UItem('plot_panel', style='custom'))
        return v

def main():
#     from guppy import hpy

    l = Looper()
#     l.hp = hp = hpy()
#     l.loop()
#     t = Thread(target=l.loop)
#     t.start()
    l.configure_traits()

#     return hp

if __name__ == '__main__':
    main()



#============= EOF =============================================
