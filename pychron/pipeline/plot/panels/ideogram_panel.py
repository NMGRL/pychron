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
from __future__ import absolute_import
from traits.api import on_trait_change
# ============= standard library imports ========================
from numpy import Inf

from pychron.pipeline.plot.panels.figure_panel import FigurePanel
from pychron.pipeline.plot.plotter.ideogram import Ideogram
from six.moves import zip


# ============= local library imports  ==========================


class IdeogramPanel(FigurePanel):
    _figure_klass = Ideogram

    # _index_attr = 'uage'

    # @on_trait_change('figures:xlimits_updated')
    # def _handle_limits(self, obj, name, new):
    #     for f in self.figures:
    #         f.replot()

    def _handle_rescale(self, obj, name, new):
        if new == 'y':
            m = -1
            for f in self.figures:
                mi, ma = f.get_ybounds()
                m = max(ma * 1.025, m)

            obj.set_y_limits(0, m, pad='0.025', pad_style='upper', plotid=obj.selected_plotid)
        elif new == 'valid':
            l, h = None, None
            for f in self.figures:
                ll, hh = f.get_valid_xbounds()
                if l is None:
                    l, h = ll, hh

                l = min(l, ll)
                h = max(h, hh)

            obj.set_x_limits(l, h)

        elif new == 'x':
            center, xmi, xma = self._get_init_xlimits()
            obj.set_x_limits(xmi, xma)
            for f in self.figures:
                f.replot()

    def _get_init_xlimits(self):
        po = self.plot_options
        attr = po.index_attr
        center = None
        mi, ma = Inf, -Inf
        if attr:
            if po.use_static_limits:
                mi, ma = po.xlow, po.xhigh
            else:
                xmas, xmis = list(zip(*[(i.max_x(attr), i.min_x(attr))
                                   for i in self.figures]))
                mi, ma = min(xmis), max(xmas)

                cs = [i.mean_x(attr) for i in self.figures]
                center = sum(cs) / len(cs)
                if po.use_centered_range:
                    w2 = po.centered_range / 2.0
                    mi, ma = center - w2, center + w2

        return center, mi, ma
# ============= EOF =============================================
