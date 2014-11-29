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
from traits.api import Any, List, Instance, String, on_trait_change, \
    Button, Tuple
from traitsui.api import View, Item, VGroup
from enable.component_editor import ComponentEditor
from enable.base_tool import BaseTool
# ============= standard library imports ========================
import os
# import Image
# from numpy import array
# ============= local library imports  ==========================
from pychron.loggable import Loggable
# from pychron.core.helpers.parsers.xml_parser import XMLParser
# #from pychron.core.ui.custom_label_editor import CustomLabelEditor
# from pychron.graph.tools.xy_inspector import XYInspectorOverlay, XYInspector
# from pychron.graph.image_underlay import ImageUnderlay
# from pychron.core.geometry.reference_point import ReferencePoint
from chaco.abstract_overlay import AbstractOverlay
from pyface.file_dialog import FileDialog
from pyface.constant import OK
# from pychron.regex import make_image_regex
from pychron.media_server.image_viewer import ImageViewer
from pychron.media_server.finder import Finder


class ReferencePointsTool(BaseTool):
    current_position = Tuple
    points = List
    def normal_left_down(self, event):
        pos = event.x, event.y
        self.current_position = pos
#        dp = self.component.map_data(pos, all_values=True)
        self.points.append(pos)

class ReferencePointsOverlay(AbstractOverlay):
    tool = Any
    _cached_points = None

#    def do_layout(self):
#        self._cached_points = None

    def overlay(self, component, gc, *args, **kw):
        if self.tool.points:
            with gc:
                if self._cached_points is None:
    #                    print self.tool.points
                    self._cached_points = self.tool.points  # self.component.map_screen(self.tool.points)
    #                    self._cached_points = component.map_data(self.tool.points, all_values=True)
                elif len(self._cached_points) != len(self.tool.points):
                        self._cached_points = self.tool.points  # self.component.map_screen(self.tool.points)

                if self._cached_points is not None:
                    gc.set_stroke_color((1, 1, 0))
                    gc.set_fill_color((1, 1, 0))
                    for x, y in self._cached_points:
                        gc.arc(x, y, 3, 0, 360)
                        gc.draw_path()

# class Hierarchy(HasTraits):
#    files = List
#    directories = List
#    selected = String
## ===============================================================================
# # handlers
## ===============================================================================
#    def traits_view(self):
#        v = View(Item('files',
#                      show_label=False,
#                      editor=ListStrEditor(editable=False,
#                                           operations=[],
#                                           selected='selected'
#                                           )))
#        return v

class Viewer(ImageViewer):
#    container = Instance(HPlotContainer, ())
    name = String
#    plot = Any
    open_button = Button
#    define_points = Button
#    define_points_label = String
#    _defining_points = False
    reference_pt1 = None

    def traits_view(self):
        v = View(VGroup(
#                        HGroup(
#                               Item('open_button', show_label=False),
#                               Item('define_points',
#                                    enabled_when='plot',
#                                    editor=ButtonEditor(label_value='define_points_label'),
#                                    show_label=False),
#                               spring, CustomLabel('name', color='maroon', size=16,
#                                                   height= -25,
#                                                   width=100,
#                                                   ), spring),
                        Item('container', show_label=False, editor=ComponentEditor()),
                        )
                 )
        return v

class MediaBrowser(Loggable):
    client = Any
    finder = Instance(Finder)
    viewer = Instance(Viewer, ())
    root = 'images'
    def get_selected_image_name(self):
        sel = self.finder.selected
        if sel is not None:
            return '/{}/{}'.format(self.root, sel)

    def load_remote_directory(self, name, ext=None):
        self.root = name
        client = self.client
        try:
            resp = client.propfind(name)
        except Exception, e:
            self.warning_dialog('Could not connect to Media server at {}:{}'.format(self.client.host, self.client.port))
            return

        self.finder.load(resp)

        return True

# ===============================================================================
# handlers
# ===============================================================================
    @on_trait_change('viewer:open_button')
    def _open_fired(self):
        dlg = FileDialog(action='open')
        if dlg.open() == OK:
            with open(dlg.path, 'rb') as fp:
                self.viewer.set_image(fp)
                self.hierarchy.files.append(os.path.basename(dlg.path))

            self.client.cache(dlg.path)

#    @on_trait_change('hierarchy:selected')
    @on_trait_change('finder:selected')
    def _update_selection(self, name):
#        root = '{}/{}'.format(self.root, name)
#        buf = self.client.retrieve(root.format(name))
        buf = self.client.retrieve(name)
        if buf:
            buf.seek(0)
            self.viewer.set_image(buf)

    def _finder_default(self):
        f = Finder(filesystem=self.client)
        return f

if __name__ == '__main__':

    from pychron.media_server.client import MediaClient
    from pychron.core.helpers.logger_setup import logging_setup
    logging_setup('media')
    mc = MediaClient(host='localhost',
                     use_cache=True,
                     cache_dir='/Users/ross/Sandbox/cache',
                     port=8008)
    mb = MediaBrowser(client=mc)
    mb.load_remote_directory('images')
    mb.configure_traits()
# ============= EOF =============================================
#    def modal_view(self):
#        return self._view_factory(buttons=['OK', 'Cancel'])
#
#    def traits_view(self):
#        return self._view_factory()
#
#    def _view_factory(self, **kw):
#        v = View(HSplit(
#                        Item('finder', width=0.25, style='custom', show_label=False),
#                        Item('viewer', width=0.75, style='custom', show_label=False)
#                        ),
#                    width=800,
#                    height=650,
#                    resizable=True,
#                    title='Image Browser', **kw
#                 )
#        return v
#    def set_image(self, buf):
#        '''
#            buf is a file-like object
#        '''
#        self.container = HPlotContainer()
#        pd = ArrayPlotData(x=[0, 640],
#                           y=[0, 480])
#        plot = Plot(data=pd, padding=[30, 5, 5, 30],
# #                    default_origin=''
#                    )
#        self.plot = plot.plot(('x', 'y'),)[0]
#        self.plot.index.sort_order = 'ascending'
#        imo = ImageUnderlay(self.plot, path=buf)
#        self.plot.overlays.append(imo)
#
#        self._add_tools(self.plot)
#
#        self.container.add(plot)
#        self.container.request_redraw()
#
#    def _add_tools(self, plot):
#        inspector = XYInspector(plot)
#        plot.tools.append(inspector)
#        plot.overlays.append(XYInspectorOverlay(inspector=inspector,
#                                                component=plot,
#                                                align='ul',
#                                                bgcolor=0xFFFFD2
#                                                ))
#
# #        zoom = ZoomTool(component=plot,
# #                        enable_wheel=False,
# #                        tool_mode="box", always_on=False)
# #        pan = PanTool(component=plot, restrict_to_data=True)
# #        plot.tools.append(pan)
# #
# #        plot.overlays.append(zoom)

## ===============================================================================
# # handlers
## ===============================================================================
#
#    def _set_reference_point(self, pt):
#        '''
#             assumes no rotation of the reference frames
#             only scale and translate
#        '''
#        rp = ReferencePoint(pt)
#        info = rp.edit_traits()
#        if info.result:
#            plot = self.plot
#            if not self.reference_pt1:
#                self.reference_pt1 = (rp.x, rp.y), pt
#            else:
#                # calculate bounds
#                dp1, sp1 = self.reference_pt1
#                dp2, sp2 = (rp.x, rp.y), pt
#
#
#                w = plot.width
#                h = plot.height
#                if sp1[0] < sp2[0]:
#                    sx1, sx2 = sp1[0], sp2[0]
#                    x1, x2 = dp1[0], dp2[0]
#                else:
#                    sx2, sx1 = sp1[0], sp2[0]
#                    x2, x1 = dp1[0], dp2[0]
#
#                if sp1[1] < sp2[1]:
#                    sy1, sy2 = sp1[1], sp2[1]
#                    y1, y2 = dp1[1], dp2[1]
#                else:
#                    sy2, sy1 = sp1[1], sp2[1]
#                    y2, y1 = dp1[1], dp2[1]
#
#                pxperunit = abs((sx2 - sx1) / (x2 - x1))
#
#                li = x1 - sx1 / pxperunit
#                hi = x2 + (w - sx2) / pxperunit
#                lv = y1 - sy1 / pxperunit
#                hv = y2 + (h - sy2) / pxperunit
#
#                plot.index_range.low_setting = li
#                plot.index_range.high_setting = hi
#                plot.value_range.low_setting = lv
#                plot.value_range.high_setting = hv
#
#            plot.request_redraw()
#
#
#    def _define_points_fired(self):
#        if self.plot:
#            plot = self.plot
#            if not self._defining_points:
#                st = ReferencePointsTool(plot)
#                st.on_trait_change(self._set_reference_point, 'current_position')
#                self.points_tool = st
#                plot.tools.insert(0, st)
#                self.define_points_label = 'Finish'
#
#                plot.overlays.append(ReferencePointsOverlay(tool=st, component=plot))
#
#            else:
#                self.define_points_label = 'Define Points'
#                self.points_tool.on_trait_change(self._set_reference_point, 'current_position', remove=True)
#                plot.tools.pop(0)
#                plot.overlays.pop(-1)
#
#            self._defining_points = not self._defining_points

# class ScaleTool(BaseTool):
#
#    step = 0
#    current_pos = None
#    invisible_layout = False
#    visible = True
#    active = False
#
#    point1 = None
#    point2 = None
#
#    constrain = Enum('x', 'y')
#
#    px_distance = Int(1)
#
#    def normal_mouse_move(self, event):
#        if self.step == 1:
#            self.current_pos = event.x, event.y
#
#        self.component.request_redraw()
#
#    def normal_left_down(self, event):
#        sp = event.x, event.y
#        if self.step == 0:
#            self.step = 1
#            self.point1 = sp
#        else:
#            self.point2 = sp
#            self.step = 0
#
# #            comp = self.component
#            sp1 = self.point1
# #            dp1 = comp.map_index([sp1])
#
# #            dp2 = comp.map_index([sp])
# #            print 'd', self._distance(dp1, dp2, constrain=self.constrain)
#            print 's', self._distance(sp1, sp, constrain=self.constrain)
#            spx = self._distance(sp1, sp, constrain=self.constrain)
#            self.px_distance = int(spx)
#        event.handled = True
#
#    def _distance(self, p1, p2, constrain=None):
#        if constrain == 'x':
#            return abs(p1[0] - p2[0])
#        elif constrain == 'y':
#            return abs(p1[1] - p2[1])
#        else:
#            def diffsq(p1, p2, index=0):
#                return (p1[index] - p2[index]) ** 2
#
#            return (diffsq(p1, p2, 0) + diffsq(p1, p2, 1)) ** 0.5
#
#    def do_layout(self):
#        print 'asdffasdf'
#        pass
#
#    def overlay(self, component, gc, *args, **kw):
#        with gc:
#            if self.point1:
#                gc.set_line_width(4)
#                gc.set_stroke_color((1, 0.5, 0))
#                gc.move_to(*self.point1)
#
#                if self.current_pos:
#                    p2 = self.current_pos
#                elif self.point2:
#                    p2 = self.point2
#
#                if p2:
#                    if self.constrain == 'x':
#                        p2 = p2[0], self.point1[1]
#                    elif self.constrain == 'y':
#                        p2 = self.point1[0], p2[1]
#
#                    gc.line_to(*p2)
#
#                gc.stroke_path()

