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
from traits.api import Bool, Float, Button, Instance, Range, Str, Property
from traits.has_traits import HasTraits
from traitsui.api import View, Item, Group, HGroup, RangeEditor, spring
from chaco.api import AbstractOverlay
# ============= standard library imports ========================
from numpy import array, transpose
#============= local library imports  ==========================
from pattern_generators import square_spiral_pattern, line_spiral_pattern, random_pattern, \
    polygon_pattern, arc_pattern, line_pattern, trough_pattern, rubberband_pattern, raster_rubberband_pattern

from pychron.graph.graph import Graph
import os
# from pychron.image.image import Image
# from chaco.data_range_1d import DataRange1D
# from chaco.linear_mapper import LinearMapper
import math
from pychron.lasers.pattern.pattern_generators import circular_contour_pattern


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
                #draw 2-3
                with gc:
                    gc.translate_ctm(o, 0)
                    gc.translate_ctm(l - o, 0)
                    gc.rotate_ctm(theta)
                    gc.translate_ctm(-l + o, 0)
                    self._draw_indicator(gc, True)

                #draw 4-1
                with gc:
                    gc.translate_ctm(o, -w)

                    gc.translate_ctm(l - o, 0)
                    gc.rotate_ctm(-theta)
                    gc.translate_ctm(-l + o, 0)
                    self._draw_indicator(gc, True)

                #draw 3-4
                gc.translate_ctm(0, -w)
                self._draw_indicator(gc, False)

            else:
                if w > 8:
                    #draw verticals
                    #draw 2-3
                    with gc:
                        gc.translate_ctm(l, -w / 2.)
                        self._draw_indicator(gc, True, False)
                    #draw 4-1
                    with gc:
                        gc.translate_ctm(-l, -w / 2.)
                        self._draw_indicator(gc, False, False)

                #draw 3-4
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
        gc.save_state()
        gc.clip_to_rect(component.x,
                        component.y,
                        component.width, component.height)

        xs = component.index.get_data()
        ys = component.value.get_data()
        gc.set_stroke_color((0, 0, 0, 0))

        pts = component.map_screen([(0, 0), (self.beam_radius, 0)])
        rad = abs(pts[0][0] - pts[1][0])
        i = 0
        for xi, yi in component.map_screen(zip(xs, ys)):
            #            gc.set_alpha(0.5)
            gc.set_fill_color((0, 0, 1, 1.0 / (0.75 * i + 1) * 0.5))
            gc.begin_path()
            gc.arc(xi, yi, rad, 0, 360)
            gc.draw_path()
            i += 1

        gc.restore_state()


class Pattern(HasTraits):
    graph = Instance(Graph, (), transient=True)
    cx = Float(transient=True)
    cy = Float(transient=True)
    target_radius = Range(0.0, 3.0, 1)

    #    beam_radius = Float(1, enter_set=True, auto_set=False)
    show_overlap = Bool(False)
    beam_radius = Range(0.0, 3.0, 1)

    path = Str
    name = Property(depends_on='path')

    #    image_width = 640
    #    image_height = 480

    xbounds = (-3, 3)
    ybounds = (-3, 3)
    #    pxpermm = None

    velocity = Float(1)
    calculated_transit_time = Float

    niterations = Range(1, 200)

    # canceled = Event
    #    def map_pt(self, x, y):
    #
    #        return self.pxpermm * x + self.image_width / 2, self.pxpermm * y + self.image_height / 2
    #     def close(self, isok):
    #         self.canceled = True
    #         return True

    @property
    def kind(self):
        return self.__class__.__name__

    def _get_name(self):
        if not self.path:
            return 'New Pattern'
        return os.path.basename(self.path).split('.')[0]

    def _anytrait_changed(self, name, new):
        if name != 'calculated_transit_time':
            self.replot()
            self.calculate_transit_time()

    def calculate_transit_time(self):
        n = self.niterations

        c = -self._get_path_length()
        b = self.velocity

        acceleration = 1
        a = 0.5 * acceleration
        #         0 = -c+ b * t + 0.5 * a * t ** 2

        t1 = -b + (b ** 2 - 4 * a * c) / (2.0 * a)
        t2 = -b - (b ** 2 - 4 * a * c) / (2.0 * a)

        self.calculated_transit_time = (max(t1, t2) + self._get_delay()) * n

    #         self.calculated_transit_time = ((self._get_path_length() /
    #                                         max(self.velocity, 0.001)) + self._get_delay()) * self.niterations

    def _get_path_length(self):
        return 0

    def _get_delay(self):
        return 0

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

    #    def set_mapping(self, px):
    #        self.pxpermm = px / 10.0
    #
    #
    #    def set_image(self, data, graph=None):
    #        '''
    #            px,py pixels per cm x and y
    #        '''
    #        if graph is None:
    #            graph = self.graph
    #
    # #        p = graph.plots[0].plots['plot0'][0]
    # #        for ui in p.underlays:
    # #            if isinstance(ui, ImageUnderlay):
    # #                ui.image.load(img)
    # #                break
    # #        else:
    #        if isinstance(data, str):
    #            image = Image()
    #            image.load(data)
    #            data = image.get_array()
    #        else:
    #            data = data.as_numpy_array()
    #            data = data.copy()
    #            data = flipud(data)
    #
    # #            mmx = px / 10.0 * (self.xbounds[1] - self.xbounds[0])
    # #            mmy = py / 10.0 * (self.ybounds[1] - self.ybounds[0])
    # #
    # #            w = 640
    # #            h = 480
    # #            cb = [w / 2 - mmx, w / 2 + mmx, h / 2 - mmy, h / 2 + mmy]
    # #            cb = [h / 2 - mmy, h / 2 + mmy, w / 2 - mmx, w / 2 + mmx ]
    #
    #
    #        graph.plots[0].data.set_data('imagedata', data)
    #        graph.plots[0].img_plot('imagedata')
    #
    # #            io = ImageUnderlay(component=p, image=image, crop_rect=(640 / 2, 480 / 2, mmx, mmy))
    # #
    # #            p.underlays.append(io)
    #
    #        graph.redraw()
    def set_stage_values(self, sm):
        pass

    def pattern_generator_factory(self, **kw):
        raise NotImplementedError

    def replot(self):
        self.plot()

    def plot(self):
        pgen_out = self.pattern_generator_factory()
        data_out = array([pt for pt in pgen_out])
        xs, ys = transpose(data_out)

        #        if self.pxpermm is not None:
        #            xs, ys = self.map_pt(xs, ys)

        self.graph.set_data(xs)
        self.graph.set_data(ys, axis=1)
        self._plot_hook()

        return data_out[-1][0], data_out[-1][1]

    def points_factory(self):
        gen_out = self.pattern_generator_factory()
        return [pt for pt in gen_out]

    def graph_view(self):
        v = View(Item('graph',
                      style='custom', show_label=False),
                 handler=self.handler_klass,
                 title=self.name)
        return v

    #    def _get_crop_bounds(self):
    #        px = self.pxpermm
    # #        mmx = px / 10.0 * 1 / (self.xbounds[1] - self.xbounds[0])
    # #        mmy = py / 10.0 * 1 / (self.ybounds[1] - self.ybounds[0])
    #        windx = (self.xbounds[1] - self.xbounds[0])
    #        mmx = windx * px / 2
    #
    #        windy = (self.ybounds[1] - self.ybounds[0])
    #        mmy = windy * px / 2
    #
    #        w = self.image_width
    #        h = self.image_height
    #
    #        cbx = [w / 2 - mmx, w / 2 + mmx ]
    #        cby = [h / 2 - mmy, h / 2 + mmy]
    #
    #        return cbx, cby

    def clear_graph(self):
        graph = self.graph
        graph.set_data([], series=1, axis=0)
        graph.set_data([], series=1, axis=1)
        graph.set_data([], series=2, axis=0)
        graph.set_data([], series=2, axis=1)

    def reset_graph(self, **kw):
        self.graph = self._graph_factory(**kw)

    def _graph_factory(self, with_image=False):
        g = Graph(
            window_height=250,
            window_width=300,
            container_dict=dict(padding=0))
        g.new_plot(
            bounds=[250, 250],
            resizable='',
            padding=[30, 0, 0, 30])

        cx = self.cx
        cy = self.cy
        cbx = self.xbounds
        cby = self.ybounds
        tr = self.target_radius

        #        if with_image:
        #            px = self.pxpermm  #px is in mm
        #            cbx, cby = self._get_crop_bounds()
        #            #g.set_axis_traits(tick_label_formatter=lambda x: '{:0.2f}'.format((x - w / 2) / px))
        #            #g.set_axis_traits(tick_label_formatter=lambda x: '{:0.2f}'.format((x - h / 2) / px), axis='y')
        #
        #            bx, by = g.plots[0].bounds
        #            g.plots[0].x_axis.mapper = LinearMapper(high_pos=bx,
        #                                                    range=DataRange1D(low_setting=self.xbounds[0],
        #                                                                      high_setting=self.xbounds[1]))
        #            g.plots[0].y_axis.mapper = LinearMapper(high_pos=by,
        #                                                    range=DataRange1D(low_setting=self.ybounds[0],
        #                                                                      high_setting=self.ybounds[1]))
        #            cx += self.image_width / 2
        #            cy += self.image_height / 2
        #            tr *= px

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

    def _graph_default(self):
        return self._graph_factory()

    #        p = '/Users/ross/Desktop/foo2.tiff'
    #
    #        i = Image()#width=640, height=480)
    #        i.load(p)
    #
    #        self.set_image(i, px, px, graph=g)
    #        from chaco.image_data import ImageData
    #        image = ImageData.fromfile(p)
    # #        print image._data
    #        crop(i.source_frame, 0, 0, 300, 300)
    # self.pattern.graph.plots[0].plots['plot0'][0].overlays.append(ImageUnderlay(image=i))
    # self.pattern.graph.plots[0].plots[0].underlays.append(ImageUnderlay(image=i))
    #        io = ImageUnderlay(component=lp, image=i, visible=False)
    #        lp.overlays.append(io)

    def maker_group(self):
        return Group(
            self.get_parameter_group(),
            Item('niterations'),
            HGroup(Item('velocity'),
                   Item('calculated_transit_time',
                        label='Time (s)',
                        style='readonly',
                        format_str='%0.1f')),
            Item('target_radius'),
            Item('show_overlap'),
            Item('beam_radius', enabled_when='show_overlap'),

            show_border=True,
            label='Pattern')

    def maker_view(self):
        v = View(HGroup(
            self.maker_group(),
            Item('graph',
                 #                      resizable=False,
                 show_label=False, style='custom')),
                 #                  buttons=['OK', 'Cancel'],
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
    offset = Range(0.0, 5.0, mode='slider')
    rotation = Range(0.0, 360., mode='slider')
    xbounds = (-5, 25)
    ybounds = (-5, 25)
    endpoint1 = None
    endpoint2 = None

    def set_stage_values(self, sm):
        self.rotation = sm.canvas.calibration_item.rotation

        ck = sm.calibrated_position_entry
        smap = sm.get_stage_map()
        obj = smap.get_hole(ck)

        self.endpoint1 = smap.get_hole_pos(ck)
        self.endpoint2 = smap.get_hole_pos(obj.associated_hole)

    def get_parameter_group(self):
        return Group(Item('rotation'), Item('offset'), spring)

    @property
    def length(self):
        l = 15
        if self.endpoint1 and self.endpoint2:
            l = abs(self.endpoint2[0] - self.endpoint1[0])
        return l

    def pattern_generator_factory(self, **kw):
        return rubberband_pattern(self.cx, self.cy, self.offset, self.length, self.rotation)


class RasterRubberbandPattern(RubberbandPattern):
    dx = Range(0.0, 5.0, 0.5, mode='slider')
    single_pass = Bool(True)

    def pattern_generator_factory(self, **kw):
        return raster_rubberband_pattern(self.cx, self.cy, self.offset, self.length, self.dx, self.rotation, self.single_pass)

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

    def _get_path_length(self):
        if self.use_x:
            d = (self.length ** 2 + self.width ** 2) ** 0.5
            l = (self.length + d) * 2
        else:
            l = (self.length + self.width) * 2
        return l

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

    def _get_path_length(self):
        return (self.nsides * self.radius *
                math.sin(math.radians(360 / self.nsides)) + 2 * self.radius)

    #     def _get_delay(self):
    #         return 0.1 * self.nsides

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


#        self.graph.set_data(xs, series=1)
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
#============= EOF ====================================
