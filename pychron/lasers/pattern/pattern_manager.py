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
# #============= enthought library imports =======================
# from traits.api import Enum, Instance, Button, Str, Property, Event, Bool
# from traitsui.api import View, Item, HGroup, VGroup, InstanceEditor
# import apptools.sweet_pickle as pickle
#
# #============= standard library imports ========================
# import os
# import time
# #============= local library imports  ==========================
# from pychron.lasers.pattern.patterns import Pattern
# from pychron.managers.manager import Manager
# from pychron.paths import paths
#
# from pychron.core.ui.thread import Thread
#
# class PatternManager(Manager):
#     kind = Property(Enum(
#                          'Polygon',
# #                         'Arc',
# #                         'LineSpiral',
# #                        'SquareSpiral',
# #                        'Random',
# #                        'CircularContour'
#                         ),
#                         depends_on='_kind')
#     _kind = Str('Polygon')
#
#     pattern = Instance(Pattern)
#     load_button = Button('Load')
#     save_button = Button('Save')
#
#     execute_button = Event
#     execute_label = Property(depends_on='_alive')
#     _alive = Bool(False)
#
#     design_button = Button('Design')
#     pattern_name = Property(depends_on='pattern')
#
#     show_patterning = Bool(True)
#     record_patterning = Bool(False)
#
#     window_x = 0.75
#     window_y = 0.05
#
#     nominal_velocity = 2.5
#
#     def isAlive(self):
#         return self._alive
#
# #     def get_pattern_names(self):
# #         return self.get_file_list(paths.pattern_dir, extension='.lp')
#
#     def stop_pattern(self):
#         self.info('User requested stop')
#         self._alive = False
#         self.parent.stage_controller.stop()
#         if self.record_patterning:
#             self.parent.stop_recording()
#
#             self.close_ui()
#
#             # clear current pattern
#             self.pattern = None
#
#     def execute_pattern(self, pattern_name=None):
#         path = None
#         if pattern_name is not None:
#             path = os.path.join(paths.pattern_dir, '{}.lp'.format(pattern_name))
#             if not os.path.isfile(path):
#                 err = 'invalid pattern name. {} not in {}'.format(pattern_name, paths.pattern_dir)
#                 self.pattern = None
#                 self.warning(err)
#                 return err
#
#         #===================================================================
#         # for testing
#         # path = os.path.join(pattern_dir, 'testpattern.lp')
#         #===================================================================
#
#         self.load_pattern(path=path)
#
#         self._alive = True
#         if self.show_patterning:
#             self.open_view(self)
#
#
#         t = Thread(name='pattern.execute',
#                    target=self._execute_)
#         t.start()
#         self._execute_thread = t
#
#
#     def load_pattern(self, path=None):
#         if path is None:
#             path = self.open_file_dialog(default_directory=paths.pattern_dir)
#
#         if path is not None and os.path.isfile(path):
# #            self.pattern = None
#             with open(path, 'rb') as f:
#                 try:
#                     p = pickle.load(f)
#                     p.path = path
#                     self.pattern = p
#                     self._kind = self.pattern.__class__.__name__.partition('Pattern')[0]
#                     self.info('loaded {} from {}'.format(self.pattern_name, path))
#                     self.pattern.replot()
#                 except:
#                     if self.confirmation_dialog('Invalid Pattern File {}'.format(path)):
#                         os.remove(path)
#         else:
#             self.pattern = None
#
#
#     def save_pattern(self):
# #        if not self.pattern_name:
# #            path, _cnt = unique_path(pattern_dir, 'pattern', filetype='lp')
# #        else:
# #            path = os.path.join(pattern_dir, '{}.lp'.format(self.pattern_name))
#
#         path = self.save_file_dialog(default_directory=paths.pattern_dir)
#
#         if path:
#             if not path.endswith('.lp'):
#                 path += '.lp'
#             self.pattern.path = path
#             with open(path, 'wb') as f:
#                 pickle.dump(self.pattern, f)
#             self.info('saved {} pattern to {}'.format(self.pattern_name, path))
#
#     def _execute_(self):
#         controller = self.parent.stage_controller
#
#         # if the laser is moving wait until finished
#         controller.block()
#
#         self.info('started pattern {}'.format(self.pattern_name))
#
#         if self.record_patterning:
#             self.parent.start_recording(basename=self.pattern_name)
#
#         controller.update_axes()
#
#         pat = self.pattern
#         pat.cx = controller._x_position
#         pat.cy = controller._y_position
#
#         for ni in range(pat.niterations):
#             if not self.isAlive():
#                 break
#             self.info('doing pattern iteration {}'.format(ni + 1))
#             self._iteration()
#             time.sleep(0.05)
#
#         if self.isAlive():
#             controller.linear_move(pat.cx, pat.cy,
#                                    velocity=self.nominal_velocity,
#                                    block=True)
#
#
#         pat.graph.set_data([], series=1, axis=0)
#         pat.graph.set_data([], series=1, axis=1)
#
#         if self.isAlive():
#             self.info('finished pattern {}'.format(self.pattern_name))
#             self.parent.update_axes()
#             if self.record_patterning:
#                 self.parent.stop_recording()
#
#             self.close_ui()
#
#         self._alive = False
#
#     def _iteration(self):
#         pattern = self.pattern
#         controller = self.parent.stage_controller
#
#         pts = pattern.points_factory()
#         kind = pattern.kind
#         if kind == 'ArcPattern':
#             controller.single_axis_move('x', pattern.radius, block=True)
#             controller.arc_move(pattern.cx, pattern.cy, pattern.degrees, block=True)
#
#         elif kind == 'CircularContourPattern':
#             for ni in range(pattern.nsteps):
#                 r = pattern.radius * (1 + ni * pattern.percent_change)
#                 self.info('doing circular contour {} {}'.format(ni + 1, r))
#                 controller.single_axis_move('x', pattern.cx + r,
#                                             block=True)
#                 controller.arc_move(pattern.cx, pattern.cy, 360,
#                                     block=True)
#                 time.sleep(0.1)
#
#         else:
#             multipoint = False
#             if multipoint:
#                 controller.multiple_point_move(pts)
#             else:
#                 if controller.simulation:
#                     self._simulate_pattern(pattern)
#                 else:
# #                    graph = pattern.graph
#                     for x, y in pts:
#                         if self._alive:
# #                        graph.set_data([x], series=1, axis=0)
# #                        graph.set_data([y], series=1, axis=1)
# #                        graph.redraw()
#                             controller.linear_move(x, y, block=True,
#                                                velocity=pattern.velocity)
#     def _simulate_pattern(self, pat):
#         from numpy import linspace
#         def get_eq(x, y, px, py):
#             m = (y - py) / (x - px)
#             b = py - m * px
#             return m, b
#
#         px = None
#         py = None
#         graph = pat.graph
#         controller = self.parent.stage_controller
#         velo = pat.velocity
#         for i, (x, y) in enumerate(pat.points_factory()):
#             controller.linear_move(x, y, block=True, velocity=velo)
#             if i > 0:
#                 m, b = get_eq(x, y, px, py)
#                 for i in linspace(px, x, 10):
#                     yii = m * i + b
#                     graph.set_data([i], series=1, axis=0)
#                     graph.set_data([yii], series=1, axis=1)
#                     graph.redraw()
#                     if not self._alive:
#                         break
#                     time.sleep(0.05)
#
#             if not self._alive:
#                 break
#             px = x
#             py = y
# #===============================================================================
# # handlers
# #===============================================================================
#     def _execute_button_fired(self):
#         if self._alive:
#             self.stop_pattern()
#         else:
#             self.execute_pattern(pattern_name=self.pattern_name)
#
#     def _design_button_fired(self):
#         self.edit_traits(view='pattern_maker_view', kind='livemodal')
#
#     def _save_button_fired(self):
#         self.save_pattern()
#
#     def _load_button_fired(self):
#         self.load_pattern()
#
# #        info = self.pattern.edit_traits(kind='modal')
# #
# #        if not info.result:
# #            self.pattern = None
#
# #===============================================================================
# # property get/set
# #===============================================================================
#     def _get_kind(self):
#         return self._kind
#
#     def _set_kind(self, v):
#         self._kind = v
#         self.pattern = self.pattern_factory(v)
#
#     def _get_pattern_name(self):
#         if not self.pattern:
#             return 'Pattern'
#         else:
#             return self.pattern.name
#
#     def _get_execute_label(self):
#         return 'Execute' if not self._alive else 'Stop'
# #===============================================================================
# # factories
# #===============================================================================
#     def pattern_factory(self, kind):
#         name = '{}Pattern'.format(kind)
#         try:
#             factory = __import__('pychron.lasers.pattern.patterns',
#                              fromlist=[name])
#             pattern = getattr(factory, name)()
#     #        pattern = globals()['{}Pattern'.format(kind)]()
#             pattern.replot()
#             pattern.calculate_transit_time()
#             return pattern
#         except ImportError:
#             pass
# #===============================================================================
# # defaults
# #===============================================================================
#     def _pattern_default(self):
#         p = self.pattern_factory(self.kind)
#         return p
#
# #===============================================================================
# # view
# #===============================================================================
#     def execute_view(self):
#         v = View(VGroup(
# #                 Item('pattern', show_label=False,
# #                       style='custom',
# #                       editor=InstanceEditor(view='graph_view')),
#                  HGroup(Item('pattern_name', label='Name', style='readonly')),
#                  HGroup(self._button_factory('execute_button', 'execute_label', enabled='object.pattern is not None'),
#                         Item('design_button', show_label=False),
#                         Item('load_button', show_label=False)),
#                  ))
#         return v
#
#     def traits_view(self):
#         v = View(Item('pattern', show_label=False,
#                        style='custom',
#                        editor=InstanceEditor(view='graph_view')),
#                  handler=self.handler_klass,
#                  title=self.pattern_name,
#
#                  x=self.window_x,
#                  y=self.window_y
#                  )
#         return v
#
#     def pattern_maker_view(self):
#         v = View(HGroup(Item('save_button'), Item('load_button'), Item('kind'), show_labels=False),
#                  Item('pattern', style='custom', editor=InstanceEditor(view='maker_view'),
#                        show_label=False),
#                   resizable=True,
#                  width=425,
#                  height=605,
#                  title='Pattern Maker',
#                  buttons=['OK', 'Cancel']
# #                 kind='livemodal'
#                  )
#         return v
# if __name__ == '__main__':
#     from pychron.core.helpers.logger_setup import logging_setup
#     logging_setup('pattern')
#     paths.build('_test')
#     pm = PatternManager()
#     pm.configure_traits(view='pattern_maker_view')
# #    pm.configure_traits(view='execute_view')
# #============= EOF ====================================
