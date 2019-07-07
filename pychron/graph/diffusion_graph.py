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
from chaco.default_colormaps import color_map_name_dict

# ============= standard library imports ========================
from pychron.graph.graph import Graph, name_generator


# ============= local library imports  ==========================

# GROUPNAMES=['spectrum','logr_ro','arrhenius','cooling_history', 'unconstrained_thermal_history']
# GROUPNAMES = ['spectrum', 'logr_ro', 'arrhenius', 'cooling_history', 'unconstrained_thermal_history']
# GROUPNAMES = ['spectrum', 'arrhenius', 'cooling_history', 'unconstrained_thermal_history', 'logr_ro']
# LABELS = dict(spectrum='Spectrum', arrhenius='Arrhenius', logr_ro='LogR/Ro',
#               unconstrained_thermal_history='Uncon. Thermal History',
#               cooling_history='Cooling History'
#               )


class DiffusionGraph(Graph):
    """
    a graph for displaying diffusion data

    contains upto 5 plots
    1. age-spectrum
    2.log r/ro
    3.arrhenius
    4.cooling histories
    5.unconstrained thermal histories
    """

    zdataname_generators = None


    def new_graph(self, n, bgcolor=None, padding=None):
        self.plotcontainer = self.container_factory()
        # n = len(self.include_panels)
        # padding = [50, 5, 10, 30]  # if n>2 else [25,5,50,30]

        for _ in range(n):
            p = self.new_plot(pan=True,
                              zoom=True)
            if padding:
                p.padding = padding
            if bgcolor:
                p.bgcolor = bgcolor

    def build_spectrum(self, ar39, age, ar39_err=None, age_err=None, pid=0, **kw):
        """

        """
        plots = []
        if ar39_err is not None and age_err is not None:
            a, _p = self.new_series(ar39_err, age_err, plotid=pid,
                                    type='polygon',
                                    color=kw['color'] if 'color' in kw else 'orange')
            plots.append(a)

        b, _p = self.new_series(ar39, age, plotid=pid, **kw)
        plots.append(b)

        xtitle = 'Cum. 39Ar %'
        self.set_x_title(xtitle, plotid=pid)
        self.set_y_title('Age (Ma)', plotid=pid)
        return plots

    def build_logr_ro(self, ar39, logr, pid=1, **kw):
        """
        """
        a, _ = self.new_series(ar39, logr, plotid=pid, **kw)

        self.set_x_title('Cum. 39Ar %', plotid=pid)

        ytitle = 'log r/ro'

        self.set_y_title(ytitle, plotid=pid)
        return [a]

    def build_model_arrhenius(self, *args, **kw):
        return self.build_arrhenius(*args, **kw)

    def build_arrhenius(self, t, dta, pid=2, **kw):
        """
        """
        a, _p = self.new_series(t, dta, type='scatter', plotid=pid, marker_size=2.5, **kw)

        self.set_x_title('10000/T (K)', plotid=pid)
        ytitle = 'log D/a (1/s)'
        self.set_y_title(ytitle, plotid=pid)
        return [a]

    def build_cooling_history(self, ts, tsl, tsh, pid=3, colors=None):
        """
        """
        self.set_x_title('t (Ma)', plotid=pid)
        self.set_y_title('Temp (C)', plotid=pid)
        self.set_y_limits(min_=100, plotid=pid)

        if colors:
            p1, p2 = colors
        else:
            cg = self.color_generators[pid]
            p1 = next(cg)
            p2 = next(cg)

        if ts:
            self.new_series(ts, tsl, type='polygon', plotid=pid, color=p1)
            self.new_series(ts, tsh, type='polygon', plotid=pid, color=p2)

            self.redraw()

    def build_unconstrained_thermal_history(self, datacontainer, pid=4, contour=True):
        self.set_x_title('t (Ma)', plotid=pid)
        self.set_y_title('Temp (C)', plotid=pid)
        self.set_y_limits(min_=100, plotid=pid)

        if contour:
            if not self.zdataname_generators:
                self.zdataname_generators = [name_generator('z')]
            else:
                self.zdataname_generators.append(name_generator('z'))

            zname = next(self.zdataname_generators[-1])
            x = [10, 350]
            y = [100, 600]
            plot, names, rd = self._series_factory(x, y, plotid=pid)
            plot.data.set_data(zname, datacontainer)

            rd['xbounds'] = tuple(x)
            rd['ybounds'] = tuple(y)

            cmap = 'yarg'
            cmap = color_map_name_dict.get(cmap)
            rd['colormap'] = cmap

            #            contour = plot.img_plot(zname,
            #                                    hide_grids=False,
            #                                     **rd)[0]

            pline = plot.contour_plot(zname,
                                      hide_grids=False,
                                      **rd)[0]

            ppoly = plot.contour_plot(zname, type='poly', poly_cmap=cmap,
                                      hide_grids=False,
                                      **rd)[0]
            #            self.groups['unconstrained_thermal_history'].append([pline, ppoly])
            # remove zoom
            self.plots[pid].overlays.pop()

            return [pline, ppoly]
        else:
            plots = []
            for s in datacontainer:
                xs = s[:, 0]
                ys = s[:, 1]
                a, _ = self.new_series(xs, ys)
                plots.append(a)
            return plots

# ============= EOF ====================================
# def set_group_binding(self, pid, value):
#     '''
#
#     '''
#     if self.bindings is None:
#         self.bindings = []
#     try:
#         self.bindings[pid] = value
#     except IndexError:
#         self.bindings.append(value)
# def update_group_attribute(self, plot, attr, value, dataid=0):
#     '''
#
#     '''
#     try:
#         if self.bindings[dataid]:
#             index = None
#             for k in self.groups:
#                 g = self.groups[k]
#                 for i, pp in enumerate(g):
#
#                     try:
#                         index = pp.index(plot)
#                         break
#                     except ValueError:
#                         continue
#
#                 if index is not None:
#                     break
#
#             if k == 'logr_ro':
#                 if not attr in ['line_width']:
#                     try:
#                         g[i][index].trait_set(**{attr: value})
#                     except KeyError:
#                         pass
#
#                 try:
#                     g = self.groups['arrhenius']
#
#                     n = 1
#                     if hasattr(g[i][0], 'scatter'):
#                         n = 2
#
#                     plot = g[i][index * n]
#                     plot.trait_set(**{attr: value})
#                     if attr == 'color':
#                         if hasattr(plot, 'scatter'):
#                             plot.scatter.color = value
#                             plot.scatter.outline_color = value
#
#                 except KeyError:
#                     pass
#                 try:
#                     g = self.groups['spectrum']
#                     if index % 2 == 0:
#                         g[i][index].trait_set(**{attr: value})
#                 except KeyError:
#                     pass
#
#             elif k == 'spectrum':
#                 if index % 2 == 0:
#                     if not attr in ['line_width']:
#                         try:
#                             g = self.groups['arrhenius']
#                             g[i][index].trait_set(**{attr: value})
#                         except KeyError:
#                             pass
#
#                     try:
#                         g = self.groups['logr_ro']
#                         g[i][index].trait_set(**{attr: value})
#                     except KeyError:
#                         pass
#             elif k == 'arrhenius':
#
#                 try:
#                     g = self.groups['logr_ro']
#                     g[i][index].trait_set(**{attr: value})
#                 except KeyError:
#                     pass
#
#                 try:
#                     g = self.groups['spectrum']
#                     if index % 2 == 0:
#                         g[i][index].trait_set(**{attr: value})
#                 except KeyError:
#                     pass
#             self.redraw()
#     except IndexError:
#         pass

#    def set_group_color(self, gid=0, series=None):
#        '''
#
#        '''
#        for k in ['spectrum', 'arrhenius', 'logr_ro', 'cooling_history']:
#            g = self.groups[k]
#            try:
#                plots = g[gid]
#                for p in plots:
#                    print p
#            except IndexError:
#                pass
