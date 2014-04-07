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
import math

from traits.api import HasTraits, Instance, on_trait_change, Float, Str, \
    Dict, Property, Event, Int, Bool, List, cached_property, Button, Any
from traits.trait_errors import TraitError
from traitsui.api import View, UItem, InstanceEditor, TableEditor, \
    VSplit, HGroup, VGroup, spring, Item

# from pychron.envisage.tasks.base_editor import BaseTraitsEditor
# from pychron.processing.tasks.analysis_edit.graph_editor import GraphEditor
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
#============= standard library imports ========================
from numpy import linspace, array, min, max, zeros, meshgrid, \
    vstack, arctan2, sin, cos, unravel_index

#============= local library imports  ==========================
from pychron.core.stats.monte_carlo import monte_carlo_error_estimation
from pychron.envisage.browser.record_views import RecordView
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.graph.contour_graph import ContourGraph
from pychron.graph.error_bar_overlay import ErrorBarOverlay
from pychron.graph.graph import Graph
from pychron.core.helpers.formatting import floatfmt, calc_percent_error
from pychron.core.helpers.iterfuncs import partition
from pychron.processing.tasks.analysis_edit.graph_editor import GraphEditor
from pychron.processing.tasks.flux.irradiation_tray_overlay import IrradiationTrayOverlay
from pychron.core.regression.flux_regressor import BowlFluxRegressor, PlaneFluxRegressor
from pychron.processing.tasks.flux.tool import FluxTool


def make_grid(r, n):
    xi = linspace(-r, r, n)
    yi = linspace(-r, r, n)
    return meshgrid(xi, yi)


#Position = namedtuple('Positon', 'position x y')
class FluxMonitorRecordView(RecordView):
    age = Float
    age_err = Float
    name = Str
    sample = Str

    def _create(self, dbrecord):
        for attr in ('age', 'age_err', 'name'):
            try:
                setattr(self, attr, getattr(dbrecord, attr))
            except TraitError:
                pass

        if dbrecord.sample:
            self.sample = dbrecord.sample.name

    def __repr__(self):
        return '{} {:0.3f}Ma'.format(self.name, self.age * 1e-6)


class MonitorPosition(HasTraits):
    hole_id = Int
    identifier = Str
    sample = Str
    x = Float
    y = Float
    z = Float
    theta = Float
    saved_j = Float
    saved_jerr = Float

    mean_j = Float
    mean_jerr = Float

    n = Int

    j = Float(enter_set=True, auto_set=False)
    jerr = Float(enter_set=True, auto_set=False)
    use = Bool(True)
    save = Bool(False)
    dev = Float

    percent_saved_error = Property
    percent_mean_error = Property
    percent_pred_error = Property

    def _get_percent_saved_error(self):
        return calc_percent_error(self.saved_j, self.saved_jerr)

    def _get_percent_mean_error(self):
        if self.mean_jerr and self.mean_jerr:
            return calc_percent_error(self.mean_j, self.mean_jerr)

    def _get_percent_pred_error(self):
        if self.j and self.jerr:
            return calc_percent_error(self.j, self.jerr)


class FluxEditor(GraphEditor):
    tool = Instance(FluxTool)
    monitor_positions = Dict

    positions_dirty = Event
    positions = Property(depends_on='positions_dirty')
    geometry = List
    suppress_update = Bool(False)

    save_all_button = Button
    save_unknowns_button = Button
    _save_all = True
    _save_unknowns = True
    irradiation_tray_overlay = Instance(IrradiationTrayOverlay)

    recalculate_button = Button('Recalculate')

    min_j = Float
    max_j = Float
    percent_j_change = Float
    j_gradient = Float
    cmap_scatter = Any
    _regressor = Any

    def set_save_all(self, v):
        self._save_all = True
        self._save_unknowns = True
        self._save_all_button_fired()
        self.positions_dirty = True

    def set_save_unknowns(self, v):
        self._save_unknowns = v
        self._save_unknowns_button_fired()

    def save(self):
        self._save_db()

    def _save_db(self):
        db = self.processor.db
        with db.session_ctx():
            for pp in self.monitor_positions.itervalues():
                if pp.save:
                    db.save_flux(pp.identifier, pp.j, pp.jerr, inform=False)
                    #remove all analyses of this identifier from the cache
                    self._remove_analyses(pp.identifier)

    def _remove_analyses(self, identifier):
        proc = self.processor
        db = proc.db
        with db.session_ctx():
            ln = db.get_labnumber(identifier)
            if ln:
                for ai in ln.analyses:
                    if ai.uuid:
                        proc.remove_from_cache(ai)

    def _gather_unknowns(self, refresh_data,
                         exclude='invalid',
                         compress_groups=True):
        pass

    def _update_unknowns(self, obj, name, old, new):
        pass

    @cached_property
    def _get_positions(self):

        hkey = lambda x: x.hole_id
        if self.tool.group_positions:
            mons, unks = map(list, partition(self.monitor_positions.itervalues(),
                                             lambda x: x.sample == self.tool.monitor.sample))
            return [ai for ps in (mons, unks)
                    for ai in sorted(ps, key=hkey)]

        else:
            return sorted(self.monitor_positions.itervalues(), key=hkey)

    def add_position(self, pid, identifier, sample, x, y, j, jerr, use):
        pos = MonitorPosition(identifier=identifier,
                              sample=sample,
                              hole_id=pid,
                              x=x, y=y,

                              saved_j=j, saved_jerr=jerr,
                              theta=math.atan2(x, y),
                              use=use)

        self.monitor_positions[identifier] = pos
        # self.positions_dirty = True

    def set_predicted_j(self):
        reg = self._regressor
        if reg:
            if self.tool.use_monte_carlo:
                pts = array([[p.x, p.y] for p in self.positions])
                nominals = reg.predict(pts)
                errors = monte_carlo_error_estimation(reg, nominals, pts,
                                                      ntrials=self.tool.monte_carlo_ntrials)
                for p, j, je in zip(self.positions, nominals, errors):
                    oj = p.saved_j

                    p.j = j
                    p.jerr = je

                    p.dev = (oj - j) / j * 100
            else:
                for p in self.positions:
                    j = reg.predict([(p.x, p.y)])[0]
                    je = reg.predict_error([[(p.x, p.y)]])[0]
                    oj = p.saved_j

                    p.j = j
                    p.jerr = je

                    p.dev = (oj - j) / j * 100

            self.positions_dirty = True

    def set_position_j(self, identifier, **kw):
        if identifier in self.monitor_positions:
            mon = self.monitor_positions[identifier]
            mon.trait_set(**kw)
            # print mon.x, mon.y, mon.mean_j, mon.mean_jerr
        else:
            self.warning('invalid identifier {}'.format(identifier))

    def _get_dump_tool(self):
        pass

    def _rebuild_graph(self):
        try:
            x, y, z, ze = array([(pos.x, pos.y, pos.mean_j, pos.mean_jerr)
                                 for pos in self.monitor_positions.itervalues()
                                 if pos.use]).T

        except ValueError:
            self.debug('no monitor positions to fit')
            return

        if len(x) > 3:
            #n = z.shape[0] * 10
            r = max((max(abs(x)), max(abs(y))))
            r *= 1.25
            reg = self._regressor_factory(x, y, z, ze)
            self._regressor = reg
            if self.tool.plot_kind == 'Contour':
                self._rebuild_contour(x, y, z, r, reg)
            else:
                self._rebuild_hole_vs_j(x, y, r, reg)

    def _rebuild_hole_vs_j(self, x, y, r, reg):
        g = Graph()
        self.graph = g

        p = g.new_plot(xtitle='Hole (Theta)',
                       ytitle='J',
                       padding=[90, 5, 5, 40])

        p.y_axis.tick_label_formatter = lambda x: floatfmt(x, n=2, s=3)

        xs = arctan2(x, y)
        ys = reg.ys
        yserr = reg.yserr

        scatter, _ = g.new_series(xs, ys,
                                  yerror=yserr,
                                  type='scatter', marker='circle')

        ebo = ErrorBarOverlay(component=scatter,
                              orientation='y')
        scatter.overlays.append(ebo)
        self._add_inspector(scatter)

        a = max((abs(min(xs)), abs(max(xs))))

        fxs = linspace(-a, a)

        a = r * sin(fxs)
        b = r * cos(fxs)
        pts = vstack((a, b)).T

        fys = reg.predict(pts)

        g.new_series(fxs, fys)
        g.set_x_limits(-3.2, 3.2)

    def _add_inspector(self, scatter):
        from pychron.graph.tools.point_inspector import PointInspector
        from pychron.graph.tools.point_inspector import PointInspectorOverlay

        point_inspector = PointInspector(scatter)
        pinspector_overlay = PointInspectorOverlay(component=scatter,
                                                   tool=point_inspector)

        scatter.overlays.append(pinspector_overlay)
        scatter.tools.append(point_inspector)

    def _rebuild_contour(self, x, y, z, r, reg):

        g = ContourGraph(container_dict={'kind': 'h'})
        self.graph = g

        p = g.new_plot(xtitle='X', ytitle='Y')

        ito = IrradiationTrayOverlay(component=p,
                                     geometry=self.geometry,
                                     show_labels=self.tool.show_labels)
        self.irradiation_tray_overlay = ito
        p.overlays.append(ito)

        m = self._model_flux(reg, r)
        s, p = g.new_series(z=m,
                            xbounds=(-r, r),
                            ybounds=(-r, r),
                            levels=self.tool.levels,
                            cmap=self.tool.color_map_name,
                            colorbar=True,
                            style='contour')
        g.add_colorbar(s)

        # pts = vstack((x, y)).T
        s = g.new_series(x, y,
                         z=z,
                         style='cmap_scatter',
                         color_mapper=s.color_mapper,
                         marker='circle',
                         marker_size=self.tool.marker_size)
        self.cmap_scatter = s[0]

    def _regressor_factory(self, x, y, z, ze):
        if self.tool.model_kind == 'Bowl':
            klass = BowlFluxRegressor
        else:
            klass = PlaneFluxRegressor

        x = array(x)
        y = array(y)
        xy = vstack((x, y)).T
        wf = self.tool.use_weighted_fit
        if wf:
            ec = 'SD'
        else:
            ec = self.tool.predicted_j_error_type

        reg = klass(xs=xy, ys=z, yserr=ze,
                    error_calc_type=ec,
                    use_weighted_fit=wf)
        # error_calc_type=self.tool.predicted_j_error_type)
        reg.calculate()
        return reg

    def _model_flux(self, reg, r):

        n = reg.n * 10
        gx, gy = make_grid(r, n)

        nz = zeros((n, n))
        for i in xrange(n):
            pts = vstack((gx[i], gy[i])).T
            nz[i] = reg.predict(pts)

        self.max_j = maj = max(nz)
        self.min_j = mij = min(nz)
        self.percent_j_change = (maj - mij) / maj * 100

        x1, y1 = unravel_index(nz.argmax(), nz.shape)
        x2, y2 = unravel_index(nz.argmin(), nz.shape)

        d = 2 * r / n * ((x1 - y2) ** 2 + (y1 - y2) ** 2) ** 0.5
        self.j_gradient = self.percent_j_change / d

        return nz

    @on_trait_change('tool:show_labels')
    def _handle_labels(self):
        if self.irradiation_tray_overlay:
            self.irradiation_tray_overlay.show_labels = self.tool.show_labels
            self.irradiation_tray_overlay.invalidate_and_redraw()

    @on_trait_change('monitor_positions:[use, j, jerr]')
    def _handle_monitor_pos_change(self, obj, name, old, new):
        if not self.suppress_update:
            self.refresh_j()

    @on_trait_change('tool:[color_map_name, levels, model_kind, plot_kind, marker_size]')
    def _handle_tool_change(self, name, new):
        if name == 'marker_size':
            self.cmap_scatter.marker_size = new
            # self.cmap_scatter.invalidate_and_redraw()
        else:
            self.rebuild_graph()
            if name == 'model_kind':
                self.refresh_j()

    @on_trait_change('tool:group_positions')
    def _handle_group_monitors(self):
        self.positions_dirty = True

    def refresh_j(self):
        self.suppress_update = True
        self.rebuild_graph()
        self.set_predicted_j()
        self.suppress_update = False

    def _recalculate_button_fired(self):
        self.refresh_j()

    def _save_all_button_fired(self):
        for pp in self.positions:
            pp.save = self._save_all

        self.positions_dirty = True
        self._save_all = not self._save_all

        self._save_unknowns = True

    def _save_unknowns_button_fired(self):
        for pp in self.positions:
            if not pp.sample == self.tool.monitor.sample:
                pp.save = self._save_unknowns
            else:
                pp.save = False

        self._save_unknowns = not self._save_unknowns
        self.positions_dirty = True

    def _graph_default(self):
        g = ContourGraph(container_dict={'kind': 'h'})
        g.new_plot(xtitle='X', ytitle='Y')
        g.add_colorbar()
        return g

    def _tool_default(self):
        ft = FluxTool(mean_j_error_type='SEM, but if MSWD>1 use SEM * sqrt(MSWD)',
                      predicted_j_error_type='SEM, but if MSWD>1 use SEM * sqrt(MSWD)')

        db = self.processor.db
        fs = []
        with db.session_ctx():
            fm = db.get_flux_monitors()
            if fm:
                fs = [FluxMonitorRecordView(fi) for fi in fm]

        ft.monitors = fs
        if fs:
            ft.monitor = fs[-1]

        return ft

    def traits_view(self):
        def column(klass=ObjectColumn, editable=False, **kw):
            return klass(text_font='arial 10', editable=editable, **kw)

        cols = [
            column(klass=CheckboxColumn, name='use', label='Use', editable=True, width=30),
            column(name='hole_id', label='Hole'),
            column(name='identifier', label='Identifier'),
            column(name='sample', label='Sample', width=115),
            #column(name='x', label='X', format='%0.3f', width=50),
            #column(name='y', label='Y', format='%0.3f', width=50),
            #column(name='theta', label=u'\u03b8', format='%0.3f', width=50),
            column(name='n', label='N'),
            column(name='saved_j', label='Saved J',
                   format_func=lambda x: floatfmt(x, n=6, s=4)),
            column(name='saved_jerr', label=u'\u00b1\u03c3',
                   format_func=lambda x: floatfmt(x, n=6, s=4)),
            column(name='percent_saved_error',
                   label='%',
                   format_func=lambda x: floatfmt(x, n=2)),
            column(name='mean_j', label='Mean J',
                   format_func=lambda x: floatfmt(x, n=6, s=4) if x else ''),
            column(name='mean_jerr', label=u'\u00b1\u03c3',
                   format_func=lambda x: floatfmt(x, n=6, s=4) if x else ''),
            column(name='percent_mean_error',
                   label='%',
                   format_func=lambda x: floatfmt(x, n=2) if x else ''),
            column(name='j', label='Pred. J',
                   format_func=lambda x: floatfmt(x, n=8, s=4),
                   width=75),
            column(name='jerr',
                   format_func=lambda x: floatfmt(x, n=10, s=4),
                   label=u'\u00b1\u03c3',
                   width=75),
            column(name='percent_pred_error',
                   label='%',
                   format_func=lambda x: floatfmt(x, n=2) if x else ''),
            column(name='dev', label='dev',
                   format='%0.2f',
                   width=70),
            column(klass=CheckboxColumn, name='save', label='Save', editable=True, width=30)]

        editor = TableEditor(columns=cols, sortable=False,
                             reorderable=False)

        jfloatfmt = lambda x: floatfmt(x, n=2)
        v = View(VSplit(
            UItem('graph',
                  style='custom',
                  editor=InstanceEditor(), height=0.72),
            VGroup(HGroup(UItem('recalculate_button'),
                          Item('min_j', format_func=jfloatfmt,
                               style='readonly',
                               label='Min. J'),
                          Item('max_j',
                               style='readonly',
                               format_func=jfloatfmt, label='Max. J'),
                          Item('percent_j_change',
                               style='readonly',
                               format_func=floatfmt,
                               label='Delta J(%)'),
                          Item('j_gradient',
                               style='readonly',
                               format_func=floatfmt,
                               label='Gradient J(%/cm)'),
                          spring, icon_button_editor('save_unknowns_button', 'dialog-ok-5',
                                                     tooltip='Toggle "save" for unknown positions'),
                          icon_button_editor('save_all_button', 'dialog-ok-apply-5',
                                             tooltip='Toggle "save" for all positions')),
                   UItem('positions', editor=editor, height=0.28))))
        return v

#============= EOF =============================================
