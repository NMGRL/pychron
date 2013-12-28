# #===============================================================================
# # Copyright 2011 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# #===============================================================================
#
# #=============enthought library imports=======================
# from traits.api import DelegatesTo, \
#     HasTraits, Any, Color, Property, Int, on_trait_change, \
#     Enum
# from traitsui.api import View, Item, \
#     TextEditor, ColorEditor, Handler, Group, VGroup, HGroup
# #=============standard library imports ========================
# from wx import Colour
# import sys
# #=============local library imports  ==========================
# from pychron.graph.graph import VALID_FONTS
#
# class GraphEditorHandler(Handler):
#     def closed(self, info, is_ok):
#         '''
#         '''
#         obj = info.object
#         obj.graph_editor = None
#
# PADDING_KEYS = ['left', 'right', 'top', 'bottom']
#
# FONT_SIZES = [6, 8, 9, 10, 11, 12, 14, 16, 18, 20, 22,
#                24, 26, 28, 30, 32]
# class GraphEditor(HasTraits):
#     '''
#     '''
#     graph = Any
#     container = Property(depends_on='graph')
#     bgcolor = Property(depends_on='bgcolor_')
#     bgcolor_ = Color
#
#     title = DelegatesTo('graph', prefix='_title')
#     title_font = Enum(VALID_FONTS)
#     title_font_size = Enum(FONT_SIZES)
#     global_tick_font = Enum(VALID_FONTS)
#     global_tick_font_size = Enum(FONT_SIZES)
#     global_axis_title_font = Enum(VALID_FONTS)
#     global_axis_title_font_size = Enum(FONT_SIZES)
#
#     xspacing = Int
#     yspacing = Int
#
#     padding_left = Int
#     padding_right = Int
#     padding_top = Int
#     padding_bottom = Int
#
#     def sync(self):
#         '''
#         '''
#         g = self.graph
#         if not g:
#             return
#
#         gtf = g._title_font
#         if gtf is not None:
#             self.title_font = gtf
#
#         gtf = g._title_size
#         if gtf is not None:
#             self.title_font_size = gtf
#
#
# #        f = 'Helvetica 12'
# #        if g and g._title_font and g._title_size:
# #            f = '%s %s' % (g._title_font,
# #                               g._title_size
# #                               )
#         plot = g.plots[0]
#         if not plot:
#             return
#
#         f = plot.x_axis.tick_label_font
#         n = f.face_name
#         s = f.size
#         print f, n
#         if not n:
#             n = 'Helvetica'
#         if not s:
#             s = 10
#
#         self.global_tick_font = n
#         self.global_tick_font_size = s
#
#         f = plot.x_axis.title_font
#         n = f.face_name
#         s = f.size
#         if not n:
#             n = 'Helvetica'
#         if not s:
#             s = 10
#         self.global_axis_title_font = n
#         self.global_axis_title_font_size = s
#
#         for attr, v in zip(PADDING_KEYS ,
#                            plot.padding
#                            ):
#             setattr(self, 'padding_{}'.format(attr), v)
#
#     def _get_container(self):
#         '''
#         '''
#
#         return self.graph.plotcontainer
#
#     def _get_bgcolor(self):
#         '''
#         '''
#
#         bg = self.container.bgcolor
#         if isinstance(bg, str):
#             bg = Colour().SetFromName(bg)
#
#         return bg
#
#     def _set_bgcolor(self, v):
#         '''
#
#         '''
#
#         if sys.platform == 'win32':
#             v = [vi / 255. for vi in v]
#
#         self.container.bgcolor = v
# #        self.container.invalidate_and_redraw()
#         self.container.request_redraw()
# #
# #    def _font_changed(self):
# #        '''
# #        '''
# #        self._update_()
#
#     def _title_changed(self):
#         '''
#         '''
#         self._update_()
#
#     def _graph_changed(self):
#         '''
#         '''
#         self.sync()
#
#     @on_trait_change('title_font+')
#     def _update_(self):
#         '''
#         '''
# #        title_font, size = self._get_font_args(self.title_font)
# #        print title_font, size
#         self.graph.set_title(self.title,
#                              font=self.title_font,
#                               size=self.title_font_size)
#
# #    def _get_font_args(self, f):
# #
# #        args = str(f).split(' ')
# #        size = args[0]
# #
# #        title_font = ' '.join(args[2:])
# #        return title_font, size
#     @on_trait_change('global_tick_font+')
#     def _global_tick_font_changed(self):
#         self._change_global_font(
#                                  'tick',
#                                  'tick_label_font')
#
#     @on_trait_change('global_axis_title_font+')
#     def _global_axis_title_font_changed(self):
#         self._change_global_font(
#                                  'axis_title',
# #                                 self.global_axis_title_font,
#                                  'title_font')
#
#     def _change_global_font(self, f, key):
#         g = self.graph
#
#         fn = getattr(self, 'global_{}_font'.format(f))
#         fs = getattr(self, 'global_{}_font_size'.format(f))
#         font = '{} {}'.format(fn, fs)
#         print 'asdaSD', font
#         for po in g.plots:
#             setattr(po.x_axis, key, font)
#             setattr(po.y_axis, key, font)
#
#         self.graph.redraw()
#
#     def _xspacing_changed(self):
#         try:
#             self.graph.plotcontainer.spacing = (self.xspacing,
#                                                 self.yspacing)
#         except:
#             self.graph.plotcontainer.spacing = self.xspacing
#         self.graph.redraw()
#
#     def _yspacing_changed(self):
#         try:
#             self.graph.plotcontainer.spacing = (self.xspacing,
#                                                 self.yspacing)
#         except:
#             self.graph.plotcontainer.spacing = self.yspacing
#
#         self.graph.redraw()
#
#     @on_trait_change('padding_+')
#     def _padding_changed(self):
#         from pychron.graph.stacked_graph import StackedGraph
#         try:
# #            p = map(int, self.padding.split(','))
# #            if len(p) == 1:
# #                p = p[0]
#             padding = [getattr(self, 'padding_{}'.format(a)) for a in PADDING_KEYS]
#             l, r, t, b = padding
#             if isinstance(self.graph, StackedGraph):
#                 _pl, _pr, pt, _pb = self.graph.plots[0].padding
#                 _pl, _pr, pt2, _pb = self.graph.plots[-1].padding
#
#                 # dont change the top padding of the first plot and last
#
#                 self.graph.plots[0].padding = [l, r, pt, b]
#                 for ps in self.graph.plots[1:-1]:
#                     ps.padding = [l, r, 0, 0]
#
#                 self.graph.plots[-1].padding = [l, r, pt2, 0]
#             else:
#                 for pi in self.graph.plots:
#                     pi.padding = padding
#
#             self.graph.redraw()
#
#         except Exception, e:
#             print e
#             pass
#
#     def traits_view(self):
#         '''
#         '''
#         general_grp = Group(
#                             Item('title', editor=TextEditor(enter_set=True,
#                                                auto_set=False)),
#                             HGroup(Item('title_font', label='Font',),
#                                     Item('title_font_size', show_label=False)
#                                         ),
#                             Item('bgcolor', editor=ColorEditor()),
#                             label='General',
#                             show_border=True)
#         tick_grp = Group(
#                HGroup(Item('global_tick_font', label='Tick Font'),
#                       Item('global_tick_font_size', show_label=False)
#                       ),
#                HGroup(
#                       Item('global_axis_title_font', label='Title Font'),
#                       Item('global_axis_title_font_size', show_label=False)
#                       ),
#                label='Ticks',
#                show_border=True
#                )
#         spacing_grp = Group(
#                Item('xspacing', label='Horizontal'),
#                Item('yspacing', label='Vertical'),
#                show_border=True,
#                label='Spacing'
#                )
#         padding_grp = Group(
#                      Item('padding_left', label='Left'),
#                      Item('padding_right', label='Right'),
#                      Item('padding_top', label='Top'),
#                      Item('padding_bottom', label='Bottom'),
#                      show_border=True,
#                      label='Padding'
#                      )
#
#         v = View(VGroup(general_grp,
#                  tick_grp,
#                  spacing_grp,
#                  padding_grp),
#                  title='Graph Editor',
#                  resizable=True,
#                  handler=GraphEditorHandler,
#                  x=0.05,
#                  y=0.1,
#                )
#         return v
# #============= EOF =====================================
