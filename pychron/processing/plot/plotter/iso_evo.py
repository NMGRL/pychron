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
from pychron.processing.plot.plotter.arar_figure import BaseArArFigure


class IsoEvo(BaseArArFigure):
    ytitle = ''
    xtitle = 'Time (s)'

    def plot(self, plots, legend):
        for i, p in enumerate(plots):
            self._plot(i, p)

    def _plot(self, i, p):
        ai = self.analyses[0]
        name = p.name
        try:
            iso = ai.isotopes[name]
            xs = iso.xs
            ys = iso.ys

            self.graph.new_series(xs, ys,
                                  marker=p.marker,
                                  marker_size=p.marker_size,
                                  type='scatter',
                                  plotid=i,
                                  fit=iso.fit
                                  )
        except KeyError, e:
            print 'asdfasd', ai.record_id, e
            # self.graph.new_series([1,2,3,4], [1,2,3,40])

            # def post_make(self):
            #     pass

# ============= EOF =============================================
