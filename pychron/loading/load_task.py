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
from traits.api import on_trait_change, Any, List, Str
# from traitsui.api import View, Item
from pyface.tasks.task_layout import PaneItem, TaskLayout
from pyface.constant import CANCEL, NO
from pyface.tasks.action.schema import SToolBar
#============= standard library imports ========================
#============= local library imports  ==========================

from pychron.envisage.tasks.base_task import BaseManagerTask
from pychron.loading.panes import LoadPane, LoadControlPane, LoadTablePane
from pychron.canvas.canvas2D.loading_canvas import LoadingCanvas
from pychron.loading.actions import SaveLoadingAction
from pychron.loading.loading_pdf_writer import LoadingPDFWriter
from apptools.preferences.preference_binding import bind_preference
import os
from pychron.paths import paths
from datetime import datetime
from pyface.timer.do_later import do_later


class LoadingTask(BaseManagerTask):
    name = 'Loading'
    load_pane = Any

    dirty = False
    control_pane = Any
    canvas = Any
    _positions = List

    save_directory = Str

    tool_bars = [SToolBar(SaveLoadingAction(),
                          image_size=(32, 32)
    )]

    def activated(self):
    #         self.manager.tray = 'A'
    #         self.manager.irradiation = 'NM-251'
    #         self.manager.level = 'H'
    #         self.manager.labnumber = '61311'

        if self.manager.setup():
            bind_preference(self, 'save_directory', 'pychron.loading.save_directory')
        else:
            do_later(self.window.close)


            #     def _manager_default(self):
            #         return LoadingManager()

    def _default_layout_default(self):
        return TaskLayout(
            left=PaneItem('pychron.loading.controls'),
            bottom=PaneItem('pychron.loading.positions')
        )

    def prepare_destroy(self):
        pass

    def create_dock_panes(self):

        self.control_pane = LoadControlPane(model=self.manager)
        self.table_pane = LoadTablePane(model=self.manager)
        #         self.irradiation_pane = LoadIrradiationPane(model=self.manager)
        return [self.control_pane,
                self.table_pane,
                #                 self.irradiation_pane

        ]

    def create_central_pane(self):
        self.load_pane = LoadPane()
        return self.load_pane

    def save(self):
        self.manager.save()

    def save_loading(self):
        p = LoadingPDFWriter()
        root = self.save_directory
        if not root or not os.path.isdir(root):
            root = paths.loading_dir

        positions = self.manager.positions
        ln = self.manager.load_name
        un = self.manager.loader_name

        dt = datetime.now()
        date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        meta = dict(load_name=ln, username=un,
                    load_date=date_str,
                    projects='Ross, Test'
        )
        path = os.path.join(root, '{}.pdf'.format(ln))
        p.build(path, positions, self.canvas, meta)

    #     @on_trait_change('manager:load_name')
    #     def _load_changed(self, new):
    #         if new:
    #             self.manager.tray = ''
    #             self.manager.load_load(new)

    @on_trait_change('manager:tray')
    def _tray_changed(self, new):
        if new:
            c = LoadingCanvas(
                view_x_range=(-2.2, 2.2),
                view_y_range=(-2.2, 2.2),

            )
            c.load_scene(new,
                         show_hole_numbers=self.manager.show_hole_numbers)

            self.canvas = c
            self.load_pane.component = c

            self.manager.canvas = c

            self.manager.positions = []


    @on_trait_change('window:closing')
    def _prompt_on_close(self, event):
        '''
            Prompt the user to save when exiting.
        '''
        if self.dirty:
            result = self._confirmation('ffoo')

            if result in (CANCEL, NO):
                event.veto = True
            else:
                self._save()

#============= EOF =============================================
#     def save_loading2(self):
# #         path = self.save_file_dialog()
#         path = '/Users/ross/Sandbox/load_001.pdf'
#         if path:
#
#             from chaco.pdf_graphics_context import PdfPlotGraphicsContext
#
# #             doc = SimpleDocTemplate(path)
# #             fl = [ComponentFlowable(component=self.canvas),
# #                   ]
# #             doc.save()
#             w, h = letter
#             gc = PdfPlotGraphicsContext(filename=path,
#                                         pagesize='letter',
# #                                         dest_box=(0.5, hh / 2. - 0.5,
# #                                                   -0.5,
# #                                                   hh / 2.)
#                                         )
#             component = self.canvas
# #             component.use_backbuffer = False
#
#             man = self.manager
#
#             n = len(man.positions)
#             idx = int(round(n / 2.))
#             p1 = man.positions[:idx + 1]
#             p2 = man.positions[idx - 1:]
# #
#             t1 = self._make_table(p1)
#             t2 = self._make_table(p2)
#
#             single_page = True
#             if not single_page:
#
#                 gc.render_component(component)
#                 gc.gc.showPage()
#                 t1.wrapOn(gc.gc, w, h)
#
#                 hh = h - t1._height - 0.5 * inch
#                 t1.drawOn(gc.gc, 0.5 * inch, hh)
#
#                 t2.wrapOn(gc.gc, w, h)
#
#                 hh = h - t2._height - 0.5 * inch
#                 t2.drawOn(gc.gc, 0.5 * inch + w / 2.0, hh)
#
#             else:
#                 hh = h - component.height - 1 * inch
#                 left = t1.split(w, hh)
#                 right = t2.split(w, hh)
#
#                 t = left[0]
#                 t.wrapOn(gc.gc, w, hh)
#                 t.drawOn(gc.gc, 0, 0)
#
#                 th = t._height
#
#                 t = right[0]
#                 t.wrapOn(gc.gc, w, hh)
#
#                 dh = th - t._height
#                 t.drawOn(gc.gc, w / 2.0 - 0.4 * inch, dh)
#
#                 gc.render_component(component)
#                 gc.gc.showPage()
#
#                 if len(left) > 1:
#                     t = left[1]
#                     th = t._height
#                     t.wrapOn(gc.gc, w, h)
#                     t.drawOn(gc.gc, 0.5 * inch,
#                              h - 0.5 * inch - th)
#
#                     if len(right) > 1:
#                         t = right[1]
#                         t.wrapOn(gc.gc, w, h - inch)
#                         t.drawOn(gc.gc, w / 2 + 0.5 * inch,
#                                  h - 0.5 * inch - th)
#             gc.save()
# if new in self._positions:
#                 new.fill = False
#                 self._positions.remove(new)
#             else:
#                 new.fill = True
#                 self._positions.append(new)
#                 new.labnumber = man.labnumber
#                 new.args = (man.labnumber, irrad_str, man.sample)
#
#             pos = sorted(self._positions,
#                          key=lambda x: int(x.identifier))
#
#             man.positions = []
#             for g, ps in groupby(pos, key=lambda x:x.labnumber):
#
#                 pi = ps.next()
#                 lp = LoadPosition(labnumber=pi.args[0],
#                                   irradiation_str=pi.args[1],
#                                   sample=pi.args[2],
#                                   positions=[pi.identifier]
#                                  )
#                 man.positions.append(lp)
#                 pp = int(pi.identifier)
#
#                 for pi in ps:
#                     pid = int(pi.identifier)
# #                     print g, pp, pi.identifier
#                     if pp is not None and pp + 1 != pid:
#                         lp = LoadPosition(labnumber=pi.args[0],
#                                           irradiation_str=pi.args[1],
#                                           sample=pi.args[2],
#                                           positions=[pid]
#                                          )
#                         man.positions.append(lp)
# #                         print 'new'
#                     else:
#                         lp.positions.append(pid)
#
#                     pp = int(pid)
#
#                 for i, pi in enumerate(man.positions):
#                     if int(new.identifier) in pi.positions:
#                         man.scroll_to_row = i
#                         break
