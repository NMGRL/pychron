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

        # name is either an isotope "Ar40" or a detector "H1"
        # if its a detector only plot the baseline
        name = p.name

        is_baseline = False
        try:
            iso = ai.isotopes[name]
        except KeyError, e:
            is_baseline = True
            iso = next((iso for iso in ai.isotopes.itervalues() if iso.detector == name), None)
            if iso is None:
                print 'iso_evo _plot', ai.record_id, ai.isotopes_keys, name
                return

        ymi, yma = Inf, -Inf
        xmi, xma = 0, -Inf
        if is_baseline:
            xma, xmi, yma, ymi = self._plot_baseline(i, iso, p, xma, xmi, yma, ymi)
            # print xma, xmi, yma, ymi
        else:
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
                xma, xmi, yma, ymi = self._plot_baseline(i, iso, p, xma, xmi, yma, ymi)

        self.graph.set_x_limits(min_=xmi, max_=xma * 1.05, plotid=i)
        self.graph.set_y_limits(min_=ymi, max_=yma, pad='0.05', plotid=i)
        self.graph.refresh()

    def _plot_baseline(self, i, iso, p, xma, xmi, yma, ymi):
        xs = iso.baseline.xs
        ys = iso.baseline.ys
        self.graph.new_series(xs, ys,
                              marker=p.marker,
                              marker_size=p.marker_size,
                              type='scatter',
                              plotid=i,
                              fit=iso.baseline.fit,
                              filter_outliers_dict=iso.baseline.filter_outliers_dict,
                              color='black')

        xmi, xma = min_max(xmi, xma, xs)
        ymi, yma = min_max(ymi, yma, ys)
        return xma, xmi, yma, ymi

# ============= EOF =============================================
