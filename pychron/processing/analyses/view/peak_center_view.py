# ===============================================================================
# Copyright 2014 Jake Ross
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

from __future__ import absolute_import

# ============= enthought library imports =======================
from numpy import array, linspace
from scipy.interpolate import interpolate
from traits.api import HasTraits, Instance
from traitsui.api import View, UItem
# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import nominal_value

from pychron.core.stats.peak_detection import calculate_resolution, calculate_resolving_power
from pychron.graph.stacked_graph import StackedGraph


def calculate_peak_statistics(xs, ys, det, center=None):
    r, rdata = calculate_resolution(xs, ys, format_str='{:0.1f}', return_all=True)
    lrp, hrp, lrpdata, hrpdata = calculate_resolving_power(xs, ys, format_str='{:0.1f}', return_all=True)
    if center is not None:
        txt = '{} Center={:0.5f} V'.format(det, center)
    else:
        txt = '{}'.format(det)

    txt = '{}\nRes={}, LRP,HRP={}, {}'.format(txt, r, lrp, hrp)
    return txt, rdata, lrpdata, hrpdata


class PeakCenterView(HasTraits):
    graph = Instance(StackedGraph, ())
    name = 'PeakCenter'

    def load(self, an):

        if an.peak_center_data:
            g = self.graph
            g.plotcontainer.spacing = 10
            g.equi_stack = False
            p = g.new_plot(xtitle='DAC', ytitle='Intensity', padding_left=70,
                           padding_right=5)

            g.add_axis_tool(p, p.x_axis)
            g.add_axis_tool(p, p.y_axis)

            ref_xs, ref_ys = list(map(array, an.peak_center_data))
            ref_k = an.peak_center_reference_detector
            s, p = g.new_series(ref_xs, ref_ys, type='scatter')
            s.index.sort_order = 'ascending'

            f = interpolate.interp1d(ref_xs, ref_ys, kind='cubic')
            xs = linspace(ref_xs.min(), ref_xs.max(), 1000)
            ys = f(xs)
            g.new_series(xs, ys, color=s.color)

            # t = CursorTool(s,
            #                drag_button="left",
            #                marker_size=5,
            #                color='darkgreen')
            # s.overlays.append(t)
            # dto = CursorToolOverlay(
            #     component=p,
            #     tool=t)
            # p.overlays.append(dto)
            v = nominal_value(an.peak_center)
            label_text = None
            if v is not None:
                # t.current_position = v, 0
                g.add_vertical_rule(v)
                txt, rdata, lrpdata, hrpdata = calculate_peak_statistics(xs, ys, ref_k, v)
                label_text = [txt]
                # g.new_series(rdata[0], rdata[1], type='scatter', marker_size=4, edge_color='black', color=s.color)
                # g.new_series(lrpdata[0], lrpdata[1], type='scatter', marker_size=4, edge_color='green')
                # g.new_series(hrpdata[0], hrpdata[1], type='scatter', marker_size=4, edge_color='blue')

            g.set_y_limits(pad='0.05', plotid=0)

            miR = min(ref_ys)
            maR = max(ref_ys)
            R = maR - miR

            if an.peak_center:
                # idx = where(ref_xs < an.peak_center)[0][-1]

                # kw = {'padding_left': 70, 'padding_right': 5, 'show_legend': True,
                #       'bounds': (1, 100)}

                if an.additional_peak_center_data:
                    # add peak centering ratios
                    # p = g.new_plot(ytitle='Ratios', **kw)
                    # g.add_axis_tool(p, p.x_axis)
                    # g.add_axis_tool(p, p.y_axis)

                    # p = g.new_plot(ytitle='Delta Ratios (%)', **kw)
                    # g.add_axis_tool(p, p.x_axis)
                    # g.add_axis_tool(p, p.y_axis)

                    for k, (xs, ys) in an.additional_peak_center_data.items():
                        ys = array(ys)
                        mir = ys.min()
                        r = ys.max() - mir

                        ys1 = (ys - mir) * R / r + miR

                        s, p = g.new_series(xs, ys1, type='scatter', plotid=0)

                        f = interpolate.interp1d(xs, ys1, kind='cubic')
                        xs = linspace(min(xs), max(xs), 500)
                        ys = f(xs)
                        g.new_series(xs, ys, color=s.color, plotid=0)
                        txt, rdata, lrp, hrp = calculate_peak_statistics(xs, ys, k)
                        label_text.append(txt)
                        # zid = ys != 0

                        # ys2 = ref_ys[zid] / ys[zid]
                        # xs = array(xs)[zid]

                        # plot ratios
                        # g.new_series(xs, ys2, plotid=1)
                        # g.set_series_label('{}/{}'.format(ref_k, k), plotid=1)

                        # ref = ref_ys[idx] / ys[idx]
                        # ys3 = (ys2 - ref) / ref * 100

                        # # plot delta ratios
                        # g.new_series(xs, ys3, plotid=2)
                        # g.set_series_label('{}/{}'.format(ref_k, k), plotid=2)
                        # g.set_y_limits(-200, 200, plotid=2)
            if label_text:
                g.add_plot_label('\n'.join(label_text),
                                 font='modern 12',
                                 color='darkgreen')
            return True

    def traits_view(self):
        v = View(UItem('graph', style='custom'))
        return v

# ============= EOF =============================================
