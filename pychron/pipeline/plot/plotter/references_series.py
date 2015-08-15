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
from chaco.array_data_source import ArrayDataSource
from chaco.legend import Legend
from enable.font_metrics_provider import font_metrics_provider
from traits.api import Property, on_trait_change, List, Array
# ============= standard library imports ========================
from math import isnan, isinf
from uncertainties import nominal_value, std_dev
from numpy import zeros_like, array, asarray
# ============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.core.regression.base_regressor import BaseRegressor
from pychron.core.regression.interpolation_regressor import InterpolationRegressor
from pychron.pipeline.plot.plotter.series import BaseSeries
from pychron.pychron_constants import PLUSMINUS


def calc_limits(ys, ye, n):
    ymi = (ys - (ye * n)).min()
    yma = (ys + (ye * n)).max()
    return ymi, yma


class ReferenceLegend(Legend):
    bgcolor = 'transparent'

    def get_preferred_size(self):
        """
        Computes the size and position of the legend based on the maximum size of
        the labels, the alignment, and position of the component to overlay.
        """
        # Gather the names of all the labels we will create
        if len(self.plots) == 0:
            return [0, 0]

        plot_names, visible_plots = map(list, zip(*sorted(self.plots.items())))
        label_names, names = zip(*self.labels)
        if len(label_names) == 0:
            if len(self.plots) > 0:
                label_names = plot_names
            else:
                self._cached_labels = []
                self._cached_label_sizes = []
                self._cached_label_names = []
                self._cached_visible_plots = []
                self.outer_bounds = [0, 0]
                return [0, 0]

        if self.hide_invisible_plots:
            visible_labels = []
            visible_plots = []
            for key, name in self.labels:
                # If the user set self.labels, there might be a bad value,
                # so ensure that each name is actually in the plots dict.
                if key in self.plots:
                    val = self.plots[key]
                    # Rather than checking for a list/TraitListObject/etc., we just check
                    # for the attribute first
                    if hasattr(val, 'visible'):
                        if val.visible:
                            visible_labels.append(name)
                            visible_plots.append(val)
                    else:
                        # If we have a list of renderers, add the name if any of them are
                        # visible
                        for renderer in val:
                            if renderer.visible:
                                visible_labels.append(name)
                                visible_plots.append(val)
                                break
            label_names = visible_labels

        # Create the labels
        labels = [self._create_label(text) for text in label_names]

        # For the legend title
        if self.title_at_top:
            labels.insert(0, self._create_label(self.title))
            label_names.insert(0, 'Legend Label')
            visible_plots.insert(0, None)
        else:
            labels.append(self._create_label(self.title))
            label_names.append(self.title)
            visible_plots.append(None)

        # We need a dummy GC in order to get font metrics
        dummy_gc = font_metrics_provider()
        label_sizes = array([label.get_width_height(dummy_gc) for label in labels])

        if len(label_sizes) > 0:
            max_label_width = max(label_sizes[:, 0])
            total_label_height = sum(label_sizes[:, 1]) + (len(label_sizes) - 1) * self.line_spacing
        else:
            max_label_width = 0
            total_label_height = 0

        legend_width = max_label_width + self.icon_spacing + self.icon_bounds[0] \
                       + self.hpadding + 2 * self.border_padding
        legend_height = total_label_height + self.vpadding + 2 * self.border_padding

        self._cached_labels = labels
        self._cached_label_sizes = label_sizes
        self._cached_label_positions = zeros_like(label_sizes)
        self._cached_label_names = label_names
        self._cached_visible_plots = visible_plots

        if "h" not in self.resizable:
            legend_width = self.outer_width
        if "v" not in self.resizable:
            legend_height = self.outer_height
        return [legend_width, legend_height]

    def _draw_as_overlay(self, gc, view_bounds=None, mode="normal"):
        """ Draws the overlay layer of a component.

        Overrides PlotComponent.
        """
        # Determine the position we are going to draw at from our alignment
        # corner and the corresponding outer_padding parameters.  (Position
        # refers to the lower-left corner of our border.)

        # First draw the border, if necesssary.  This sort of duplicates
        # the code in PlotComponent._draw_overlay, which is unfortunate;
        # on the other hand, overlays of overlays seem like a rather obscure
        # feature.

        with gc:
            self.y += self.height + 10
            gc.clip_to_rect(int(self.x), int(self.y),
                            int(self.width), int(self.height))
            edge_space = self.border_width + self.border_padding
            icon_width, icon_height = self.icon_bounds

            icon_x = self.x + edge_space
            text_x = icon_x + icon_width + self.icon_spacing
            y = self.y2 - edge_space

            if self._cached_label_positions is not None:
                if len(self._cached_label_positions) > 0:
                    self._cached_label_positions[:, 0] = icon_x

            for i, label_name in enumerate(self._cached_label_names):
                # Compute the current label's position
                label_height = self._cached_label_sizes[i][1]
                y -= label_height
                self._cached_label_positions[i][1] = y

                # Try to render the icon
                icon_y = y + (label_height - icon_height) / 2
                # plots = self.plots[label_name]
                plots = self._cached_visible_plots[i]
                render_args = (gc, icon_x, icon_y, icon_width, icon_height)

                try:
                    if isinstance(plots, list) or isinstance(plots, tuple):
                        # TODO: How do we determine if a *group* of plots is
                        # visible or not?  For now, just look at the first one
                        # and assume that applies to all of them
                        if not plots[0].visible:
                            # TODO: the get_alpha() method isn't supported on the Mac kiva backend
                            # old_alpha = gc.get_alpha()
                            old_alpha = 1.0
                            gc.set_alpha(self.invisible_plot_alpha)
                        else:
                            old_alpha = None
                        if len(plots) == 1:
                            plots[0]._render_icon(*render_args)
                        else:
                            self.composite_icon_renderer.render_icon(plots, *render_args)
                    elif plots is not None:
                        # Single plot
                        if not plots.visible:
                            # old_alpha = gc.get_alpha()
                            old_alpha = 1.0
                            gc.set_alpha(self.invisible_plot_alpha)
                        else:
                            old_alpha = None
                        plots._render_icon(*render_args)
                    else:
                        old_alpha = None  # Or maybe 1.0?

                    icon_drawn = True
                except:
                    icon_drawn = self._render_error(*render_args)

                if icon_drawn:
                    # Render the text
                    gc.translate_ctm(text_x, y)
                    gc.set_antialias(0)
                    self._cached_labels[i].draw(gc)
                    gc.set_antialias(1)
                    gc.translate_ctm(-text_x, -y)

                    # Advance y to the next label's baseline
                    y -= self.line_spacing
                if old_alpha is not None:
                    gc.set_alpha(old_alpha)

        return


class ReferencesSeries(BaseSeries):
    references = List
    sorted_references = Property(depends_on='references')
    show_current = True
    rxs = Array

    _normalization_factor = 3600.

    def set_interpolated_values(self, iso, reg, fit):
        mi, ma = self._get_min_max()
        # mi =
        ans = self.sorted_analyses

        xs = [(ai.timestamp - ma) / self._normalization_factor for ai in ans]

        p_uys = reg.predict(xs)
        p_ues = reg.predict_error(xs)
        if any(map(isnan, p_ues)) or any(map(isinf, p_ues)):
            p_ues = zeros_like(p_ues)

        if any(map(isnan, p_uys)) or any(map(isinf, p_uys)):
            p_uys = zeros_like(p_uys)

        self._set_interpolated_values(iso, fit, ans, p_uys, p_ues)
        return asarray(p_uys), asarray(p_ues)

    def post_make(self):
        self.graph.refresh()

    def plot(self, plots, legend):

        if plots:
            _, mx = self._get_min_max()

            self.xs = self._get_xs(plots, self.sorted_analyses, tzero=mx)
            self.rxs = self._get_xs(plots, self.sorted_references, tzero=mx)

            for i, p in enumerate(plots):
                self._new_fit_series(i, p)

            mi, ma = self._get_min_max()
            self.xmi, self.xma = (mi - ma) / 3600., 0
            self.xpad = '0.1'

            legend = ReferenceLegend(plots=self.graph.plots[0].plots,
                                     labels=[('data0', 'Reference'), ('plot0', 'Saved'),
                                             ('Unknowns-predicted0', 'Interpolated')])
            self.graph.plots[-1].overlays.append(legend)

    # private
    @on_trait_change('graph:regression_results')
    def _update_regression(self, new):
        key = 'Unknowns-predicted{}'
        key = key.format(0)
        for plotobj, reg in new:
            if isinstance(reg, BaseRegressor):
                self._set_values(plotobj, reg, key)

    def _calc_limits(self, ys, ye):
        return calc_limits(ys, ye, self.options.nsigma)

    def _new_fit_series(self, pid, po):
        ymi, yma = self._plot_unknowns_current(pid, po)
        reg, a, b = self._plot_references(pid, po)
        ymi = min(ymi, a)
        yma = max(yma, b)
        # print 'asdfa', reg
        if reg:
            a, b = self._plot_interpolated(pid, po, reg)
            ymi = min(ymi, a)
            yma = max(yma, b)

        self.graph.set_y_limits(ymi, yma, pad='0.05', plotid=pid)

    def _get_min_max(self):
        mi = min(self.sorted_references[0].timestamp, self.sorted_analyses[0].timestamp)
        ma = max(self.sorted_references[-1].timestamp, self.sorted_analyses[-1].timestamp)
        return mi, ma

    # def _get_reference_values(self, name):
    #     ys = self._get_references_ve(name)
    #     return array(map(nominal_value, ys))
    #
    # def _get_reference_errors(self, name):
    #     ys = self._get_references_ve(name)
    #     return array(map(std_dev, ys))

    # def _get_references_ve(self, name):
    #     raise NotImplementedError

    def _get_sorted_references(self):
        return sorted(self.references,
                      key=self._cmp_analyses,
                      reverse=self._reverse_sorted_analyses)

    def _set_values(self, plotobj, reg, key):
        iso = plotobj.isotope
        fit = plotobj.fit
        if key in plotobj.plots:
            scatter = plotobj.plots[key][0]
            p_uys, p_ues = self.set_interpolated_values(iso, reg, fit)
            scatter.value.set_data(p_uys)
            scatter.yerror.set_data(p_ues)

    def reference_data(self, po):
        rs = self._get_reference_data(po)
        return array(map(nominal_value, rs)), array(map(std_dev, rs))

    def current_data(self, po):
        cs = self._get_current_data(po)
        return array(map(nominal_value, cs)), array(map(std_dev, cs))

    def _get_current_data(self, po):
        return self._unpack_attr(po.name)

    def _get_reference_data(self, po):
        pass

    # plotting
    def _plot_unknowns_current(self, pid, po):
        ymi, yma = 0, 0

        if self.analyses and self.show_current:
            graph = self.graph
            n = [ai.record_id for ai in self.sorted_analyses]

            ys, ye = self.current_data(po)
            ymi, yma = self._calc_limits(ys, ye)

            kw = dict(y=ys, yerror=ye, type='scatter')

            args = graph.new_series(x=self.xs,
                                    display_index=ArrayDataSource(data=n),
                                    fit=False,
                                    # fit=po.fit,
                                    plotid=pid,
                                    # type='scatter',
                                    add_tools=False,
                                    add_inspector=False,
                                    marker=po.marker,
                                    marker_size=po.marker_size, **kw)
            if len(args) == 2:
                scatter, p = args
            else:
                p, scatter, l = args

            sel = scatter.index.metadata.get('selections', [])
            # sel += omits
            scatter.index.metadata['selections'] = list(set(sel))

            def af(i, x, y, analysis):
                v, e = self._get_interpolated_value(po, analysis)
                return (u'Interpolated: {}{}{}'.format(floatfmt(v), PLUSMINUS, floatfmt(e)),
                        'Run Date: {}'.format(analysis.rundate.strftime('%m-%d-%Y %H:%M')),
                        'Rel. Time: {:0.4f}'.format(x))

            self._add_error_bars(scatter, ye, 'y', self.options.nsigma, True)
            self._add_scatter_inspector(scatter,
                                        add_selection=False,
                                        additional_info=af)
        return ymi, yma

    def _plot_interpolated(self, pid, po, reg, series_id=0):
        iso = po.name
        p_uys, p_ues = self.set_interpolated_values(iso, reg, po.fit)
        ymi, yma = 0, 0
        if len(p_uys):
            ymi, yma = self._calc_limits(p_uys, p_ues)

            graph = self.graph
            # display the predicted values
            s, p = graph.new_series(self.xs,
                                    p_uys,
                                    isotope=iso,
                                    yerror=ArrayDataSource(p_ues),
                                    fit=False,
                                    add_tools=False,
                                    add_inspector=False,
                                    type='scatter',
                                    marker_size=3,
                                    color='blue',
                                    plotid=pid,
                                    bind_id=-1)
            series = len(p.plots) - 1
            graph.set_series_label('Unknowns-predicted{}'.format(series_id), plotid=pid,
                                   series=series)

            self._add_error_bars(s, p_ues, 'y', self.options.nsigma, True)
        return ymi, yma

    def _plot_references(self, pid, po):
        graph = self.graph
        efit = po.fit.lower()
        r_xs = self.rxs
        r_ys, r_es = self.reference_data(po)

        ymi, yma = self._calc_limits(r_ys, r_es)

        reg = None
        kw = dict(add_tools=False, add_inspector=False, color='red',
                  plotid=pid,
                  selection_marker=po.marker,
                  marker=po.marker,
                  marker_size=po.marker_size, )

        if efit in ['preceding', 'bracketing interpolate', 'bracketing average']:
            reg = InterpolationRegressor(xs=r_xs,
                                         ys=r_ys,
                                         yserr=r_es,
                                         kind=efit)
            scatter, _p = graph.new_series(r_xs, r_ys,
                                           yerror=r_es,
                                           type='scatter',
                                           fit=False,
                                           **kw
                                           )
            # self._add_inspector(s, self.sorted_references)
            self._add_error_bars(scatter, r_es, 'y', self.options.nsigma, True)
            # series_id = (series_id+1) * 2
        else:

            # series_id = (series_id+1) * 3
            _, scatter, l = graph.new_series(r_xs, r_ys,
                                             # display_index=ArrayDataSource(data=display_xs),
                                             yerror=ArrayDataSource(data=r_es),
                                             fit='{}_{}'.format(po.fit, po.error_type),
                                             **kw)
            # print self.graph, po.fit, args
            # print l
            if hasattr(l, 'regressor'):
                reg = l.regressor

                # l.regression_bounds = regression_bounds

                # self._add_inspector(s, self.sorted_references)
            self._add_error_bars(scatter, r_es, 'y', self.options.nsigma, True)

        def af(i, x, y, analysis):
            return ('Run Date: {}'.format(analysis.rundate.strftime('%m-%d-%Y %H:%M')),
                    'Rel. Time: {:0.4f}'.format(x))

        self._add_scatter_inspector(scatter,
                                    add_selection=True,
                                    additional_info=af,
                                    items=self.sorted_references)
        plot = self.graph.plots[pid]
        plot.isotope = po.name
        plot.fit = '{}_{}'.format(po.fit, po.error_type)
        # scatter.index.on_trait_change(self._update_metadata, 'metadata_changed')

        return reg, ymi, yma

    def _set_interpolated_values(self, iso, fit, ans, p_uys, p_ues):
        pass

# ============= EOF =============================================
