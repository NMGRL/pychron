# ===============================================================================
# Copyright 2011 Jake Ross
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
import math
import os

from chaco.api import AbstractOverlay
from numpy import array, transpose, linspace, sin, pi, append, arange, asarray, diff, roll, \
    gradient, sign, hstack
from scipy import signal
from traits.api import Bool, Float, Button, Instance, Range, Str, Property, Enum, on_trait_change
from traits.has_traits import HasTraits
from traitsui.api import View, Item, Group, HGroup, RangeEditor, spring, VGroup, Tabbed, UItem

from pattern_generators import square_spiral_pattern, line_spiral_pattern, random_pattern, \
    polygon_pattern, arc_pattern, line_pattern, trough_pattern, rubberband_pattern, raster_rubberband_pattern
from pychron.graph.graph import Graph
from pychron.lasers.pattern.pattern_generators import circular_contour_pattern
from pychron.pychron_constants import NULL_STR

POLYGONS = ['triangle', 'diamond', 'pentagon', 'hexagon', 'heptagon', 'octogon', 'nonagon', 'decagon']


class DirectionOverlay(AbstractOverlay):
    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            gc.clip_to_rect(other_component.x, other_component.y,
                            other_component.width, other_component.height)
            a, b = self.component.map_screen([(0, 0), (self.olength / 2.0, self.owidth)])
            l, w = b[0] - a[0], b[1] - a[1]
            ox, oy = self.component.map_screen([(0, 0)])[0]

            gc.translate_ctm(ox, oy)
            gc.rotate_ctm(self.rotation)
            gc.translate_ctm(-ox, -oy)
            gc.translate_ctm(ox + l, oy)

            # draw 1-2
            self._draw_indicator(gc, False)

            if self.use_x:
                theta = abs(math.atan(w / (2. * l)))
                o = l * 0.5
                # draw 2-3
                with gc:
                    gc.translate_ctm(o, 0)
                    gc.translate_ctm(l - o, 0)
                    gc.rotate_ctm(theta)
                    gc.translate_ctm(-l + o, 0)
                    self._draw_indicator(gc, True)

                # draw 4-1
                with gc:
                    gc.translate_ctm(o, -w)

                    gc.translate_ctm(l - o, 0)
                    gc.rotate_ctm(-theta)
                    gc.translate_ctm(-l + o, 0)
                    self._draw_indicator(gc, True)

                # draw 3-4
                gc.translate_ctm(0, -w)
                self._draw_indicator(gc, False)

            else:
                if w > 8:
                    # draw verticals
                    # draw 2-3
                    with gc:
                        gc.translate_ctm(l, -w / 2.)
                        self._draw_indicator(gc, True, False)
                        # draw 4-1
                    with gc:
                        gc.translate_ctm(-l, -w / 2.)
                        self._draw_indicator(gc, False, False)

                # draw 3-4
                gc.translate_ctm(0, -w)
                self._draw_indicator(gc, True)

    def _draw_indicator(self, gc, left_or_down, horizontal=True):
        if left_or_down:
            if horizontal:
                gc.move_to(4, 3)
                gc.line_to(0, 0)
                gc.line_to(4, -3)
            else:
                gc.move_to(-3, 4)
                gc.line_to(0, 0)
                gc.line_to(3, 4)
        else:
            if horizontal:
                gc.move_to(-4, 3)
                gc.line_to(0, 0)
                gc.line_to(-4, -3)
            else:
                gc.move_to(-3, -4)
                gc.line_to(0, 0)
                gc.line_to(3, -4)

        gc.stroke_path()


class TargetOverlay(AbstractOverlay):
    target_radius = Float
    cx = Float
    cy = Float

    def overlay(self, component, gc, *args, **kw):
        with gc:
            x, y = self.component.map_screen([(self.cx, self.cy)])[0]
            pts = self.component.map_screen([(0, 0), (self.target_radius, 0)])
            r = abs(pts[0][0] - pts[1][0])

            gc.begin_path()
            gc.arc(x, y, r, 0, 360)
            gc.stroke_path()


class OverlapOverlay(AbstractOverlay):
    beam_radius = Float(1)

    def overlay(self, component, gc, *args, **kw):
        # gc.save_state()
        with gc:
            gc.clip_to_rect(component.x,
                            component.y,
                            component.width, component.height)

            xs = component.index.get_data()
            ys = component.value.get_data()
            gc.set_stroke_color((0, 0, 0, 0.5))

            pts = component.map_screen([(0, 0), (self.beam_radius, 0)])
            rad = abs(pts[0][0] - pts[1][0])

            pts = component.map_screen(zip(xs, ys))

            # for i, (xi, yi) in enumerate(pts):
            #     # gc.set_fill_color((0, 0, 1, 1.0 / (0.75 * i + 1) * 0.5))
            #     gc.begin_path()
            #     gc.arc(xi, yi, rad, 0, 360)
            #     gc.draw_path()
            #     i += 1

            with gc:
                gc.set_line_join(0)
                gc.set_line_width(rad * 2)

                gc.move_to(*pts[0])

                for xi, yi in pts[1:]:
                    gc.line_to(xi, yi)

                gc.line_to(*pts[0])
                gc.line_to(*pts[1])
                gc.stroke_path()
                # gc.restore_state()


AMPLITUDE_PATTERNS = (NULL_STR, 'Sine', 'Square', 'Saw')


class Pattern(HasTraits):
    graph = Instance(Graph, (), transient=True)
    amplitude_graph = Instance(Graph, (), transient=True)
    cx = Float(transient=True)
    cy = Float(transient=True)
    target_radius = Range(0.0, 3.0, 1)

    show_overlap = Bool(False)
    beam_radius = Range(0.0, 3.0, 1)

    path = Str
    name = Property(depends_on='path')

    xbounds = (-5, 5)
    ybounds = (-5, 5)

    velocity = Float(1)
    calculated_transit_time = Float

    niterations = Range(1, 200)
    disable_at_end = Bool(False)
    xy_pattern_enabled = Bool(True)

    z_duration = Float
    power_duration = Float

    z_period = Float(1)
    z_duty = Float
    z_min = Float
    z_max = Float(10)
    z_offset = Float(10)
    z_sample = Float
    z_func = Enum(AMPLITUDE_PATTERNS)
    z_pattern_enabled = Bool
    z_use_transit_time = Bool

    power_period = Float
    power_duty = Float
    power_min = Float(1)
    power_max = Float(10)
    power_offset = Float(10)
    power_func = Enum(AMPLITUDE_PATTERNS)
    power_sample = Float
    power_pattern_enabled = Bool
    power_use_transit_time = Bool

    def __init__(self, *args, **kw):
        super(Pattern, self).__init__(*args, **kw)

        self.z_func = 'Saw'

        self.z_duration = 5
        self.z_sample = 0.5

    @property
    def kind(self):
        return self.__class__.__name__

    @property
    def power_pattern(self):
        return self.power_func != NULL_STR and self.power_pattern_enabled

    @property
    def z_pattern(self):
        return self.z_func != NULL_STR and self.z_pattern_enabled

    def generate_name(self):
        return '{}_BR{}'.format(self._basename(), self.beam_radius)

    def calculate_transit_time(self):
        try:
            self.calculated_transit_time = (self._get_path_length() * self.niterations) / self.velocity
        except ZeroDivisionError:
            pass

        if self.power_use_transit_time:
            self.power_duration = self.calculated_transit_time
        if self.z_use_transit_time:
            self.z_duration = self.calculated_transit_time

        return self.calculated_transit_time

    def set_stage_values(self, sm):
        pass

    def pattern_generator_factory(self, **kw):
        raise NotImplementedError

    def replot(self):
        self.plot()

    def replot_power_amplitude(self):
        x, y, sx, sy = self._calculate_power_series()
        self.amplitude_graph.set_data(x)
        self.amplitude_graph.set_data(y, axis=1)

        self.amplitude_graph.set_data(sx, series=2)
        self.amplitude_graph.set_data(sy, series=2, axis=1)

    def replot_z_amplitude(self):
        x, y, sx, sy = self._calculate_z_series()
        self.amplitude_graph.set_data(x, series=1)
        self.amplitude_graph.set_data(y, series=1, axis=1)
        self.amplitude_graph.set_data(sx, series=3)
        self.amplitude_graph.set_data(sy, series=3, axis=1)

    def plot(self):
        pgen_out = self.pattern_generator_factory()
        data_out = array([pt for pt in pgen_out])
        xs, ys = transpose(data_out)

        self.graph.set_data(xs)
        self.graph.set_data(ys, axis=1)
        self._plot_hook()

        return data_out[-1][0], data_out[-1][1]

    def points_factory(self):
        gen_out = self.pattern_generator_factory()
        return list(gen_out)

    def graph_view(self):
        v = View(UItem('graph', style='custom'),
                 handler=self.handler_klass,
                 title=self.name)
        return v

    def clear_graph(self):
        graph = self.graph
        graph.set_data([], series=1, axis=0)
        graph.set_data([], series=1, axis=1)
        graph.set_data([], series=2, axis=0)
        graph.set_data([], series=2, axis=1)

    def reset_graph(self, **kw):
        self.graph = self._graph_factory(**kw)

    def power_values(self):
        x, y, sx, sy = self._calculate_power_series()
        return sy

    def z_values(self):
        x, y, sx, sy = self._calculate_z_series()
        return sy

    # private
    def _basename(self):
        return self.kind

    def _get_name(self):
        if not self.path:
            return 'New Pattern'
        return os.path.basename(self.path).split('.')[0]

    def _get_path_length(self):
        pts = self.points_factory()
        p1 = (self.cx, self.cy)
        s = 0
        for p in pts + [p1, ]:
            d = ((p1[0] - p[0]) ** 2 + (p1[1] - p[1]) ** 2) ** 0.5
            s += d
            p1 = p

        return s

    def _get_delay(self):
        return 0

    def _calculate_power_series(self):
        # x, y, sx, sy = [], [], [], []
        # if self.power_func != NULL_STR:
        #     mi = self.power_min
        #     amp = self.power_max - self.power_min
        #     x, y, sx, sy = self._calculate_series(self.power_func, self.power_period, amp, mi, self.power_offset,
        #                                           self.power_sample, self.power_duty, self.power_duration)
        # return x, y, sx, sy
        return self._calculate_series('power')

    def _calculate_z_series(self):
        # x, y, sx, sy = [], [], [], []
        # if self.z_func != NULL_STR:
        #     mi = self.z_min
        #     amp = self.z_max - mi
        #     x, y, sx, sy = self._calculate_series(self.z_func, self.z_period, amp, mi, self.z_offset,
        #                                           self.z_sample, self.z_duty, self.z_duration)
        # return x, y, sx, sy
        return self._calculate_series('z')

    def _calculate_series(self, attr):
        mi = getattr(self, '{}_min'.format(attr))
        amp = getattr(self, '{}_max'.format(attr)) - mi

        funcname = getattr(self, '{}_func'.format(attr))
        period = getattr(self, '{}_period'.format(attr))
        offset = getattr(self, '{}_offset'.format(attr))
        speriod = getattr(self, '{}_sample'.format(attr))
        duty = getattr(self, '{}_duty'.format(attr))
        duration = getattr(self, '{}_duration'.format(attr))

        x, y, sx, sy = [], [], [], []
        if funcname != NULL_STR:
            if self.xy_pattern_enabled and getattr(self, '{}_use_transit_time'.format(attr)):
                t = self.calculate_transit_time()
            else:
                t = duration

            t = t or 1
            x = linspace(0, t, 500)

            speriod = speriod or 1
            sx = arange(0, t, speriod)
            if sx[-1] < t:
                sx = append(sx, t)

            if funcname == 'Sine':
                def func(xx):
                    return (mi + amp) + amp * sin(period * xx + offset)

                y = func(x)

            elif funcname == 'Square':
                def func(xx):
                    return 0.5 * amp * (signal.square(period * xx * 2 * pi + offset, duty=duty / 100.) + 1) + mi

                y = func(x)

                bx = asarray(diff(y), dtype=bool)
                bx = roll(bx, 1)

                sx = x[bx]
                sx = append(asarray([0]), sx)
                sx = append(sx, asarray([t]))

            elif funcname == 'Saw':
                def func(xx):
                    return 0.5 * amp * (signal.sawtooth(period * xx * 2 * pi + offset) + 1) + mi

                y = func(x)

                asign = sign(gradient(y))
                signchange = ((roll(asign, 1) - asign) != 0).astype(bool)
                signchange[0] = False
                nsx = x[signchange]
                sx = hstack((sx, nsx))

            sy = func(sx)

        return x, y, sx, sy

    # handlers
    def _beam_radius_changed(self):
        oo = self.graph.plots[0].plots['plot0'][0].overlays[1]
        oo.beam_radius = self.beam_radius
        self.replot()

    def _show_overlap_changed(self):
        oo = self.graph.plots[0].plots['plot0'][0].overlays[1]
        oo.visible = self.show_overlap
        oo.request_redraw()

    def _target_radius_changed(self):
        self.graph.plots[0].plots['plot0'][0].overlays[0].target_radius = self.target_radius

    @on_trait_change('z_+,p_+')
    def _handle_amplitude_change(self, obj, name, new):
        if name in ('z_sample', 'p_sample') and not new:
            return

        if name.startswith('z'):
            self.replot_z_amplitude()
        else:
            self.replot_power_amplitude()

    def _anytrait_changed(self, name, new):
        if name != 'calculated_transit_time':
            self.replot()
            self.calculate_transit_time()

    # factories
    def _amplitude_graph_factory(self):
        g = Graph()
        p = g.new_plot(show_legend='ul')
        p.index_range.tight_bounds = False
        p.value_range.tight_bounds = False

        x, y, spx, spy = self._calculate_power_series()
        g.new_series(x, y, type='line', color='red')
        g.set_series_label('Power')
        x, y, szx, szy = self._calculate_z_series()
        g.new_series(x, y, type='line', color='blue')
        g.set_series_label('Z')

        g.new_series(spx, spy, type='scatter', color='red')
        g.new_series(szx, szy, type='scatter', color='blue')

        # g.new_series(type='scatter', marker='circle')
        return g

    def _graph_factory(self, **kw):
        g = Graph(
            window_height=250,
            window_width=300,
            container_dict=dict(padding=0))
        g.new_plot(
            bounds=[250, 250],
            aspect_ratio=1,
            resizable='', padding=[30, 0, 0, 30])

        cx = self.cx
        cy = self.cy
        cbx = self.xbounds
        cby = self.ybounds
        tr = self.target_radius

        g.set_x_limits(*cbx)
        g.set_y_limits(*cby)

        lp, _plot = g.new_series()
        t = TargetOverlay(component=lp,
                          cx=cx,
                          cy=cy,
                          target_radius=tr)

        lp.overlays.append(t)
        overlap_overlay = OverlapOverlay(component=lp,
                                         visible=self.show_overlap)
        lp.overlays.append(overlap_overlay)

        self._graph_factory_hook(lp)

        g.new_series(type='scatter', marker='circle')
        g.new_series(type='line', color='red')
        return g

    def _plot_hook(self):
        pass

    def _graph_factory_hook(self, lp):
        pass

    # defaults
    def _amplitude_graph_default(self):
        return self._amplitude_graph_factory()

    def _graph_default(self):
        return self._graph_factory()

    # views
    def maker_group(self):
        para_grp = Group(self.get_parameter_group(),
                         show_border=True,
                         label='Parameters')
        pattern_grp = VGroup(HGroup(Item('disable_at_end', label='Disable at End',
                                         tooltip='Disable Laser at end of patterning'),
                                    Item('niterations', label='N. Iterations')),
                             HGroup(Item('velocity'),
                                    Item('calculated_transit_time',
                                         label='Time (s)',
                                         style='readonly',
                                         format_str='%0.1f')),
                             label='XY Pattern', show_border=True)

        display_grp = Group(Item('target_radius'),
                            Item('show_overlap'),
                            Item('beam_radius', enabled_when='show_overlap'),
                            show_border=True, label='Display')

        z_grp = self._get_amplitude_group('z', 'Z')
        power_grp = self._get_amplitude_group('power', 'Power')

        return Tabbed(VGroup(Item('xy_pattern_enabled'),
                             para_grp, pattern_grp, display_grp,
                             label='Pattern'), z_grp, power_grp)

    def _get_amplitude_group(self, tag, label):
        grp = VGroup(Item('{}_pattern_enabled'.format(tag), label='Enabled'),
                     VGroup(HGroup(Item('{}_use_transit_time'.format(tag)),
                                   Item('{}_duration'.format(tag), enabled_when='not {}_use_transit_time'.format(tag))),
                            HGroup(Item('{}_period'.format(tag)),
                                   Item('{}_duty'.format(tag), visible_when='{}_func=="Square"'.format(tag))),

                            Item('{}_offset'.format(tag)),
                            Item('{}_min'.format(tag)),
                            Item('{}_max'.format(tag)),
                            Item('{}_func'.format(tag)),
                            Item('{}_sample'.format(tag), visible_when='{}_func!="Square"'.format(tag)),
                            enabled_when='{}_pattern_enabled'.format(tag)),
                     # show_border=True,
                     label=label)
        return grp

    def maker_view(self):
        v = View(HGroup(self.maker_group(),
                        Tabbed(UItem('graph', style='custom'),
                               UItem('amplitude_graph', style='custom'))),
                 resizable=True)
        return v

    def traits_view(self):
        v = View(self.maker_group(),
                 buttons=['OK', 'Cancel'],
                 title=self.name,
                 resizable=True)
        return v

    def get_parameter_group(self):
        raise NotImplementedError


class RubberbandPattern(Pattern):
    nominal_length = Range(0.0, 25.0, 15, mode='slider')
    offset = Range(0.0, 5.0, mode='slider')
    rotation = Range(0.0, 360., mode='slider')
    xbounds = (-25, 25)
    ybounds = (-25, 25)
    endpoint1 = None
    endpoint2 = None

    def set_stage_values(self, sm):
        self.rotation = sm.canvas.calibration_item.rotation

        ck = sm.temp_hole
        # smap = sm.get_stage_map()
        smap = sm.stage_map
        obj = smap.get_hole(ck)

        self.endpoint1 = smap.get_hole_pos(ck)
        self.endpoint2 = smap.get_hole_pos(obj.associated_hole)

    def get_parameter_group(self):
        return Group(Item('nominal_length', label='Length'),
                     Item('rotation'), Item('offset'), spring)

    @property
    def length(self):
        l = self.nominal_length
        if self.endpoint1 and self.endpoint2:
            l = abs(self.endpoint2[0] - self.endpoint1[0])
        return l

    def pattern_generator_factory(self, **kw):
        return rubberband_pattern(self.cx, self.cy, self.offset, self.length, self.rotation)


class RasterRubberbandPattern(RubberbandPattern):
    dx = Range(0.0, 5.0, 0.5, mode='slider')
    single_pass = Bool(True)

    def pattern_generator_factory(self, **kw):
        return raster_rubberband_pattern(self.cx, self.cy, self.offset, self.length, self.dx, self.rotation,
                                         self.single_pass)

    def get_parameter_group(self):
        return Group(Item('rotation'), Item('offset'), Item('dx'), Item('single_pass', label='Single Pass'))


class TroughPattern(Pattern):
    width = Range(0.0, 20., 10, mode='slider')
    length = Range(0.0, 20., 10, mode='slider')
    use_x = Bool(True)
    rotation = Range(0.0, 360., mode='slider')

    xbounds = (-5, 25)
    ybounds = (-5, 25)

    show_direction = Bool(True)

    def set_stage_values(self, sm):
        self.rotation = sm.canvas.calibration_item.rotation

    def _plot_hook(self):
        self.dir_overlay.trait_set(
            rotation=math.radians(self.rotation),
            use_x=self.use_x,
            olength=self.length,
            owidth=self.width)

    def _graph_factory_hook(self, lp):
        self.dir_overlay = o = DirectionOverlay(component=lp,
                                                visible=self.show_direction,
                                                olength=self.length,
                                                owidth=self.width,
                                                use_x=self.use_x,
                                                rotation=self.rotation)
        lp.overlays.append(o)

    def pattern_generator_factory(self, **kw):
        return trough_pattern(self.cx, self.cy, self.length, self.width, self.rotation, self.use_x)

    def get_parameter_group(self):
        return Group(Item('length'),
                     Item('width'),
                     Item('rotation'),
                     Item('use_x', label='Use X Pattern'), )


class LinearPattern(Pattern):
    length = Float
    rotation = Range(0.0, 360., mode='slider')
    xbounds = (-12.5, 12.5)
    ybounds = (-12.5, 12.5)
    npasses = Range(1, 100, mode='spinner')
    cx = -10

    def _get_path_length(self):
        return self.length * self.npasses

    def pattern_generator_factory(self, **kw):
        return line_pattern(self.cx, self.cy, self.length, self.rotation, self.npasses)

    def get_parameter_group(self):
        return Group(Item('length'),
                     Item('rotation'),
                     Item('npasses', label='N. Passes',
                          tooltip='Number of times to zig zag between endpoints'))


class RandomPattern(Pattern):
    walk_x = Float(1)
    walk_y = Float(1)
    npoints = Range(0, 50, 10)
    regenerate = Button

    def _regenerate_fired(self):
        self.plot()

    def get_parameter_group(self):
        return Group('walk_x',
                     'walk_y',
                     'npoints',
                     HGroup(spring, Item('regenerate', show_label=False)))

    def pattern_generator_factory(self, **kw):
        return random_pattern(self.cx, self.cy, self.walk_x,
                              self.walk_y, self.npoints, **kw)

    def points_factory(self):
        gen_out = self.pattern_generator_factory()
        return [pt for pt in gen_out]


class PolygonPattern(Pattern):
    nsides = Range(3, 200)
    radius = Range(0.0, 4.0, 0.5)
    rotation = Range(0.0, 360.0, 0.0)
    show_overlap = True

    # def _get_path_length(self):
    # return (self.nsides * self.radius *
    #             math.sin(math.radians(360 / self.nsides)) + 2 * self.radius)

    #     def _get_delay(self):
    #         return 0.1 * self.nsides
    def _basename(self):
        nsides = self.nsides
        if nsides < 11:
            bn = POLYGONS[nsides]
        else:
            bn = '{}gon'.format(nsides)
        return bn

    def get_parameter_group(self):
        return Group(Item('radius'),
                     Item('nsides'),
                     Item('rotation', editor=RangeEditor(mode='slider',
                                                         low=0,
                                                         high=360)))

    def pattern_generator_factory(self, **kw):
        return polygon_pattern(self.cx, self.cy,
                               self.radius, self.nsides, rotation=self.rotation)


class ArcPattern(Pattern):
    radius = Range(0.0, 1.0, 0.5)
    degrees = Range(0.0, 360.0, 90)

    def get_parameter_group(self):
        return Group('radius',
                     Item('degrees', editor=RangeEditor(mode='slider',
                                                        low=0,
                                                        high=360)))

    def pattern_generator_factory(self, **kw):
        return arc_pattern(self.cx, self.cy, self.degrees, self.radius)


class CircularPattern(Pattern):
    nsteps = Range(1, 10, 2)
    radius = Range(0.01, 0.5, 0.1)
    percent_change = Range(0.01, 5.0, 0.8)

    def get_parameter_group(self):
        return Group('radius',
                     'nsteps',
                     'percent_change')


class SpiralPattern(CircularPattern):
    def replot(self):
        ox, oy = self.plot()
        self.plot_in(ox, oy)

    def points_factory(self):
        gen_out = self.pattern_generator_factory()
        gen_in = self.pattern_generator_factory(direction='in')
        return [pt for pt in gen_out] + [pt for pt in gen_in]

    def plot_in(self, ox, oy):
        pgen_in = self.pattern_generator_factory(ox=ox,  # data_out[-1][0],
                                                 oy=oy,  # data_out[-1][1],
                                                 direction='in')
        data_in = array([pt for pt in pgen_in])

        xs, ys = transpose(data_in)


# self.graph.set_data(xs, series=1)
#        self.graph.set_data(ys, axis=1, series=1)


class LineSpiralPattern(SpiralPattern):
    step_scalar = Range(0, 20, 5)

    def get_parameter_group(self):
        g = super(LineSpiralPattern, self).get_parameter_group()
        g.content.append(Item('step_scalar'))
        return g

    def pattern_generator_factory(self, **kw):
        return line_spiral_pattern(self.cx, self.cy, self.radius,
                                   self.nsteps,
                                   self.percent_change,
                                   self.step_scalar,
                                   **kw)


class SquareSpiralPattern(SpiralPattern):
    def pattern_generator_factory(self, **kw):
        return square_spiral_pattern(self.cx, self.cy, self.radius,
                                     self.nsteps,
                                     self.percent_change,
                                     **kw)


class CircularContourPattern(CircularPattern):
    def pattern_generator_factory(self, **kw):
        return circular_contour_pattern(self.cx, self.cy, self.radius,
                                        self.nsteps,
                                        self.percent_change)


if __name__ == '__main__':
    p = PolygonPattern()
    p.configure_traits()
# ============= EOF ====================================
