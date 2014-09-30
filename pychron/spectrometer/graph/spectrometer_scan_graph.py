# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import List, Str, on_trait_change, Button, Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.graph.time_series_graph import TimeSeriesStreamGraph
from pychron.spectrometer.graph.marker_line_overlay import MarkerLineOverlay
from pychron.spectrometer.graph.marker_overlay import MarkerOverlay
from pychron.spectrometer.graph.marker_tool import MarkerTool


class SpectrometerScanGraph(TimeSeriesStreamGraph):
    marker_text = Str
    visual_marker_counter = 0
    markers = List
    use_vertical_markers = False

    add_visual_marker_button = Button('Add Visual Marker')
    marker_text = Str
    marker_tool = Instance(MarkerTool)

    def _add_visual_marker_button_fired(self):
        self.add_visual_marker()

    def _marker_text_changed(self, new):
        self.graph.marker_text = new

    def _x_limits_changed_changed(self):
        self.invalidate_markers()

    def clear_markers(self):
        self.markers=[]

    def invalidate_markers(self):
        for o in self.get_marker_overlays():
            o._layout_needed = True
            o.do_layout()

    def get_marker_overlays(self):
        return [o for p in self.plots
                for o in p.overlays if isinstance(o, MarkerOverlay)]

    def add_visual_marker(self, text=None, bgcolor='white'):
        if text is None:
            text = self.marker_text

        for i, p in enumerate(self.plots):
            for t in p.overlays:
                if isinstance(t, MarkerOverlay):
                    xd = p.data.get_data('x1')
                    x = p.map_screen([(xd[-1], 0)])[0][0]
                    y = 500 + self.visual_marker_counter * 21
                    if y > p.y2 - 20:
                        self.visual_marker_counter = -1
                        y = p.y2 - 20

                    m = t.add_marker(x, y, text, bgcolor, vertical_marker=self.use_vertical_markers)
                    self.visual_marker_counter += 1
                    self.markers.append(m)
                    for u in p.underlays:
                        if isinstance(u, MarkerLineOverlay):
                            l = u.add_marker_line(x, bgcolor)
                            m.on_trait_change(l.set_visible, 'visible')
                            m.on_trait_change(l.set_x, 'x')
        self.redraw()

    def new_plot(self, *args, **kw):
        p = super(SpectrometerScanGraph, self).new_plot(*args, **kw)

        mo = MarkerOverlay(component=p, use_vertical_markers=self.use_vertical_markers)
        mu = MarkerLineOverlay(component=p)

        mt = MarkerTool(component=p, overlay=mo, underlay=mu,
                        use_vertical_markers=self.use_vertical_markers)
        mt.on_trait_change(self._update_markers, 'marker_added')
        self.marker_tool = mt
        p.tools.append(mt)
        p.overlays.append(mo)
        p.underlays.append(mu)

        return p

    def _marker_text_changed(self, new):
        for p in self.plots:
            for t in p.tools:
                if isinstance(t, MarkerTool):
                    t.text = new

    def _update_markers(self, new):
        self.markers.append(new)

    @on_trait_change('markers:x')
    def _handle_marker_layout(self, obj, name, old, new):
        if new<0:
            self.markers.remove(obj)

    @on_trait_change('markers[]')
    def _handle_markers_change(self, obj, name, old, new):
        if len(new)<len(old):
            clear = not self.markers

            def _get_underlay(pp):
                for u in p.underlays:
                    if isinstance(u,MarkerLineOverlay):
                        return u

            def _remove_lays(o, un):
                for j, ci in enumerate(o.labels):
                    if ci not in self.markers:
                        o.labels.pop(j)
                        un.lines.pop(j)

            def _clear_lays(o, un):
                o.labels=[]
                un.lines = []

            for p in self.plots:
                un = _get_underlay(p)

                for i, o in enumerate(p.overlays):
                    if isinstance(o, MarkerOverlay):
                        if clear:
                            _clear_lays(o, un)
                        else:
                            _remove_lays(o, un)

            self.invalidate_markers()
            self.redraw()
#============= EOF =============================================



