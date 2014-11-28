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



#============= enthought library imports =======================
from traits.api import HasTraits, Instance, Int, Bool
from traitsui.api import View, Item, HGroup
#============= standard library imports ========================

#============= local library imports  ==========================

import os
from pychron.paths import paths
from pychron.graph.time_series_graph import TimeSeriesGraph
from numpy import loadtxt


class Grapher(HasTraits):
    downs = Int(100)
    graph = Instance(TimeSeriesGraph, ())
    use_smooth = Bool

    def traits_view(self):
        v = View(HGroup(Item('downs'), Item('use_smooth')),

                 Item('graph', show_label=False, style='custom'),
                 resizable=True
        )
        return v

    def _downs_changed(self):
        self.replot()

    def _use_smooth_changed(self):
        self.replot()

    def get_data(self):
        p1 = os.path.join(paths.data_dir, 'furnace_calibration', 'DPi32TemperatureMonitor001.txt')
        p2 = os.path.join(paths.data_dir, 'furnace_calibration', 'Eurotherm001.txt')
        func = lambda x: 1
        #        func = lambda x: time.mktime(dparser.parse(x.split('+')[0]).timetuple())
        data1 = loadtxt(p1, unpack=True,
                        converters={0: float, 1: func},
                        skiprows=1, delimiter='\t')
        data2 = loadtxt(p2, unpack=True,
                        converters={0: float, 1: func},
                        skiprows=1, delimiter='\t')
        return data1, data2

    def replot(self):
        g = self.graph
        g.clear()
        data1, data2 = self.get_data()
        x = data1[0]
        #        print x
        y = data1[2]

        x2 = data2[0]
        y2 = data2[2]

        g.new_plot(show_legend=True, zoom=True, pan=True,

                   xtitle='Time (s)',
                   ytitle='Temperature (C)'
        )
        g.new_series(x=x, y=y, downsample=self.downs,
                     use_smooth=self.use_smooth,
                     time_series=False,
                     normalize=True,
                     scale=1 / 3600.
        )
        g.new_series(x=x2, y=y2, downsample=self.downs,
                     use_smooth=self.use_smooth,
                     time_series=False,
                     normalize=True,
                     scale=1 / 3600.
        )

        g.set_series_label('Tin')

        g.set_series_label('Tout', series=1)

#    g.configure_traits()



def extract_data(p):
    '''
    '''
    import csv

    reader = csv.reader(open(p, 'U'), delimiter='\t')
    x = []
    y = []

    ma = 40000
    for i, row in enumerate(reader):
        if i == 0:
            continue

        if i == 1:
            t_zero = float(row[0])
            t = 0
        else:
            t = float(row[0]) - t_zero

        if i == ma:
            break
        x.append(t)
        y.append(float(row[2]))

    return x, y

# def plot_data(data1, data2):
#    '''
#    '''
#    g = TimeSeriesGraph()


if __name__ == '__main__':
    g = Grapher()
    g.replot()
    #    do_later(g.plot)
    g.configure_traits()
# #    p1 = os.path.join(paths.data_dir, 'furnace_calibration', 'DPi32TemperatureMonitor002.txt')
#    p1 = os.path.join(paths.data_dir, 'furnace_calibration', 'DPi32TemperatureMonitor001.txt')
# #    p2 = os.path.join(paths.data_dir, 'furnace_calibration', 'Eurotherm002.txt')
#    p2 = os.path.join(paths.data_dir, 'furnace_calibration', 'Eurotherm001.txt')
#    func = lambda x: 1
#    func = lambda x: time.mktime(dparser.parse(x.split('+')[0]).timetuple())
#    data1 = loadtxt(p1, unpack=True,
#                    converters={0:float, 1:func},
#                     skiprows=1, delimiter='\t')
#    data2 = loadtxt(p2, unpack=True,
#                    converters={0:float, 1:func},
#                    skiprows=1, delimiter='\t')
#
#
# #    x, y = extract_data(p1)
# #    x1, y1 = extract_data(p2)
#
#    plot_data(data1, data2)

#============= EOF ====================================
