# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import HasTraits, Instance
from traitsui.api import View, Item, HGroup, Group

from pychron.loggable import Loggable

# ============= standard library imports ========================
# ============= local library imports  ==========================
from enable.component_editor import ComponentEditor
from pychron.canvas.canvas2D.scene.scene_canvas import SceneCanvas
from pychron.core.geometry.geometry import sort_clockwise
# from pychron.canvas.canvas2D.scene.primitives.primitives import Polygon, RasterPolygon
from pychron.core.geometry.scan_line import raster
from pychron.canvas.canvas2D.scene.primitives.laser_primitives import RasterPolygon

class SceneViewer(Loggable):
    canvas = Instance(SceneCanvas)
    def traits_view(self):
        v = View(
                 self._get_canvas_group(),
                 resizable=True,
                 width=700,
                 height=600
                 )
        return v

    def _get_canvas_group(self):
        g = HGroup(Item('object.canvas.scene',
                             show_label=False, style='custom',
                             width=0.3
                             ),
                        Item('canvas', editor=ComponentEditor(),
                             show_label=False, style='custom',
                             width=0.7
                             )
                        )
        return g


#    def _canvas_default(self):
#        c = SceneCanvas()
#        s = LaserMineScene(canvas=c)
#
# #        s.load(os.path.join(paths.canvas2D_dir, 'canvas.xml'))
#        s.load(os.path.join(paths.user_points_dir, 'foo.yaml'))
#        c.scene = s

#        return c

from traits.api import Any, on_trait_change
from pychron.graph.graph import Graph
from numpy import array, vstack

class CanvasGraphItem(HasTraits):
    canvas = Instance(SceneCanvas)
    graph = Instance(Graph)

    @on_trait_change('canvas:scene:selected')
    def _selected_changed(self, new):

        if isinstance(new, RasterPolygon):
            self._replot_polygon(new)

    @on_trait_change('canvas:_layout_needed')
    def _layout_needed_changed(self, new):
        if new:
            sel = self.canvas.scene.selected
            if isinstance(sel, RasterPolygon):
                self._replot_polygon(sel)

    def _replot_polygon(self, poly):
        pts = [(pi.x, pi.y) for pi in poly.points]
        pts = sort_clockwise(pts, pts)
#        pts = pts + pts[:1]
        pts = array(pts)
        scale = 1000
        pts *= scale
        use_convex_hull = False
        find_min = poly.find_min
        npoints, lens, theta = raster(pts,
                         step=poly.scan_size,
                         offset=-poly.offset if poly.use_outline else 0,
                         use_convex_hull=use_convex_hull,
                         find_min=find_min,
                         theta=poly.theta
                         )


        poly._set_theta(theta)
#        poly.trait_set(theta=theta)


        g = self.graph
        g.clear()

        g.plotcontainer.padding = 5
        g.new_plot(padding=[60, 30, 30, 50],
#                   bounds=[400, 400],
#                   resizable='h',
                   xtitle='X (microns)',
                   ytitle='Y (microns)')
        g.new_plot(padding=[50, 30, 30, 30],
               xtitle='Theta (degrees)',
               ytitle='Num. Scan Lines',
#               bounds=[400, 100],
#               resizable='h'
               )


        if find_min:
            ts, ls = zip(*lens)
            g.new_series(ts, ls, plotid=1)

        # plot original
        pts = vstack((pts, pts[:1]))
        xs, ys = pts.T
        self.graph.new_series(xs, ys, plotid=0)
        self.graph.set_x_limits(min(xs), max(xs), pad='0.1')
        self.graph.set_y_limits(min(ys), max(ys), pad='0.1')

        for ps in npoints:
            for i in range(0, len(ps), 2):
                p1, p2 = ps[i], ps[i + 1]
                g.new_series((p1[0], p2[0]),
                             (p1[1], p2[1]), color='black', plotid=0)

        if poly.use_outline:
            from pychron.core.geometry.polygon_offset import polygon_offset
            opoly = polygon_offset(pts, -1 * poly.offset)
            opoly = array(opoly)
            xs, ys, _ = opoly.T
            self.graph.new_series(xs, ys, plotid=0)

    def _graph_default(self):
        g = Graph(container_dict=dict(padding=5))
        return g

    def traits_view(self):
        tg = Group(
                   Item('canvas', editor=ComponentEditor(),
                             show_label=False, style='custom',
                             width=0.7
                             ),
                   Item('graph', style='custom', show_label=False),
                   layout='tabbed'
                   )
        v = View(tg)
        return v

class LaserMineViewer(SceneViewer):
    selected_polygon = Any
    canvas_graph_item = Instance(CanvasGraphItem)

    @on_trait_change('canvas')
    def _update_canvas_graph_item(self):
        self.canvas_graph_item.canvas = self.canvas

    def traits_view(self):
        g = HGroup(Item('object.canvas.scene',
                             show_label=False, style='custom',
                             width=0.3
                             ),
                    Item('canvas_graph_item', show_label=False,
                         style='custom', width=0.7)
                        )
        v = View(g,
                 resizable=True,
                 width=700,
                 height=600,
                 buttons=['OK', 'Cancel']
                 )
        return v

    def _replot(self):
        pass
#        if use_convex_hull:
#            poly = convex_hull(poly)
#            xs, ys = poly.T
#            xs = hstack((xs, xs[0]))
#            ys = hstack((ys, ys[0]))
#        else:
#            xs, ys = poly.T
#            xs = hstack((xs, xs[0]))
#            ys = hstack((ys, ys[0]))
#
#        # plot original
#        g.new_series(xs, ys)

    def _canvas_graph_item_default(self):
        g = CanvasGraphItem(canvas=self.canvas,
                            )
        return g


if __name__ == '__main__':
    from launchers.helpers import build_version
    build_version('_uv')
    sv = LaserMineViewer()
    sv.configure_traits()

# ============= EOF =============================================
