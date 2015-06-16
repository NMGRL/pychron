# ===============================================================================
# Copyright 2015 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
from numpy import Inf

from pychron.pipeline.plot.plotter.arar_figure import BaseArArFigure


def min_max(a, b, vs):
    return min(a, vs.min()), max(b, vs.max())


class IsoEvo(BaseArArFigure):
    ytitle = ''
    xtitle = 'Time (s)'
    show_sniff = True
    show_baseline = False

    def plot(self, plots, legend):
        for i, p in enumerate(plots):
            self._plot(i, p)

    def _plot(self, i, p):
        ai = self.analyses[0]
        name = p.name
        try:
            iso = ai.isotopes[name]
        except KeyError, e:
            print 'asdfasd', ai.record_id, e
            return

        ymi, yma = Inf, -Inf
        xmi, xma = 0, -Inf

        if self.show_sniff:
            xs, ys = iso.sniff.xs, iso.sniff.ys
            self.graph.new_series(xs, ys,
                                  marker=p.marker,
                                  marker_size=p.marker_size,
                                  type='scatter',
                                  plotid=i,
                                  fit=None,
                                  color='red')
            ymi, yma = min_max(ymi, yma, iso.sniff.ys)
            xmi, xma = min_max(xmi, xma, iso.sniff.xs)

        xs = iso.xs
        ys = iso.ys

        self.graph.new_series(xs, ys,
                              marker=p.marker,
                              marker_size=p.marker_size,
                              type='scatter',
                              plotid=i,
                              fit=iso.fit,
                              filter_outliers_dict=iso.filter_outliers_dict,
                              color='black')
        ymi, yma = min_max(ymi, yma, iso.ys)
        xmi, xma = min_max(xmi, xma, iso.xs)

        if self.show_baseline:
            self.graph.new_series(iso.baseline.xs, iso.baseline.ys,
                                  marker=p.marker,
                                  marker_size=p.marker_size,
                                  type='scatter',
                                  plotid=i,
                                  fit=iso.baseline.fit,
                                  color='black')
            ymi, yma = min_max(ymi, yma, iso.baseline.ys)
            xmi, xma = min_max(xmi, xma, iso.baseline.xs)

        self.graph.set_x_limits(min_=xmi, max_=xma * 1.05, plotid=i)
        self.graph.set_y_limits(min_=ymi, max_=yma, pad='0.05', plotid=i)

# ============= EOF =============================================
