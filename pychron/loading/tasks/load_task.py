# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Any, List
# from traitsui.api import View, Item
from pyface.tasks.task_layout import PaneItem, TaskLayout
from pyface.tasks.action.schema import SToolBar
# ============= standard library imports ========================
# ============= local library imports  ==========================

from pychron.envisage.tasks.base_task import BaseManagerTask
from pychron.globals import globalv
from pychron.loading.tasks.panes import LoadPane, LoadControlPane, LoadTablePane
from pychron.loading.tasks.actions import SaveLoadingPDFAction, ConfigurePDFAction, EntryAction, InfoAction, EditAction, \
    SaveLoadingDBAction, GenerateResultsAction
from apptools.preferences.preference_binding import bind_preference


class LoadingTask(BaseManagerTask):
    name = 'Loading'
    load_pane = Any

    dirty = False
    # control_pane = Any
    canvas = Any
    _positions = List

    tool_bars = [SToolBar(SaveLoadingPDFAction(),
                          ConfigurePDFAction()),
                 SToolBar(SaveLoadingDBAction(),
                          GenerateResultsAction()),
                 SToolBar(EntryAction(), InfoAction(), EditAction())]

    def activated(self):
        # self.manager.tray = 'bat'
        # self.manager.irradiation = 'NM-256'
        # self.manager.level = 'A'
        # self.manager.labnumber = '23261'
        # self.manager.load_name = '4'

        if self.manager.verify_database_connection(inform=True):
            if self.manager.load():
                self.manager.username = globalv.username
                if self.manager.setup():
                    bind_preference(self.manager, 'save_directory', 'pychron.loading.save_directory')
                    # self.manager.load_name = ''

    def _default_layout_default(self):
        return TaskLayout(
            left=PaneItem('pychron.loading.controls'),
            right=PaneItem('pychron.loading.positions'))

    def prepare_destroy(self):
        pass

    def create_dock_panes(self):

        control_pane = LoadControlPane(model=self.manager)
        table_pane = LoadTablePane(model=self.manager)

        return [control_pane, table_pane]

    def create_central_pane(self):
        self.load_pane = LoadPane(model=self.manager)
        return self.load_pane

    def save(self):
        self.manager.save()

    # actions
    def set_entry(self):
        self.manager.set_entry()

    def set_info(self):
        self.manager.set_info()

    def set_edit(self):
        self.manager.set_edit()

    def configure_pdf(self):
        self.manager.configure_pdf()

    def save_loading_pdf(self):
        self.manager.save_pdf()

    def save_loading_db(self):
        self.manager.save(inform=True)

    def save_tray_pdf(self):
        self.manager.save_tray_pdf()

    def generate_results(self):
        self.manager.generate_results()

    def _prompt_for_save(self):
        if self.manager.dirty:
            message = 'You have unsaved changes. Save changes to Database?'
            ret = self._handle_prompt_for_save(message)
            if ret == 'save':
                return self.manager.save()
            return ret
        return True

# ============= EOF =============================================
# def save_loading2(self):
# #         path = self.save_file_dialog()
# path = '/Users/ross/Sandbox/load_001.pdf'
# if path:
#
# from chaco.pdf_graphics_context import PdfPlotGraphicsContext
#
# #             doc = SimpleDocTemplate(path)
# #             fl = [ComponentFlowable(component=self.canvas),
# #                   ]
# #             doc.save()
# w, h = letter
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
