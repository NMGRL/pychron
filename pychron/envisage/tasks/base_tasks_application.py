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
from envisage.extension_point import ExtensionPoint
from envisage.ui.tasks.tasks_application import TasksApplication
from pyface.dialog import Dialog
from pyface.tasks.task_window_layout import TaskWindowLayout
from traits.api import List, Instance

from pychron.core.helpers.strtools import to_bool
from pychron.envisage.view_util import open_view, close_views, report_view_stats
from pychron.globals import globalv
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.startup_test.results_view import ResultsView
from pychron.startup_test.tester import StartupTester


class BaseTasksApplication(TasksApplication, Loggable):
    about_dialog = Instance(Dialog)
    startup_tester = Instance(StartupTester)
    uis = List
    available_task_extensions = ExtensionPoint(id='pychron.available_task_extensions')

    def _started_fired(self):
        st = self.startup_tester
        if st.results:
            v = ResultsView(model=st)
            open_view(v)

        if globalv.use_testbot:
            from pychron.testbot.testbot import TestBot

            testbot = TestBot(application=self)
            testbot.run()

    def get_boolean_preference(self, pid):
        return to_bool(self.preferences.get(pid))

    def get_task_extensions(self, pid):
        import yaml

        p = paths.task_extensions_file
        with open(p, 'r') as rfile:
            yl = yaml.load(rfile)
            for yi in yl:
                # print yi['plugin_id'], pid
                if yi['plugin_id'].startswith(pid):
                    tid = yi.get('task_id', '')
                    for ai in yi['actions']:
                        a, e = ai.split(',')
                        # print tid, a, e
                        if to_bool(e):
                            yield tid, a

    def about(self):
        self.about_dialog.open()

    def start(self):
        if globalv.open_logger_on_launch:
            self._load_state()
            self.open_task('pychron.logger')

        self.startup_tester = StartupTester()

        return super(BaseTasksApplication, self).start()

    def get_open_task(self, tid):
        for win in self.windows:
            if win.active_task:
                if win.active_task.id == tid:
                    return win, win.active_task, True
        else:
            win = self.create_window(TaskWindowLayout(tid))
            return win, win.active_task, False

    def task_is_open(self, tid):
        for win in self.windows:
            if win.active_task and win.active_task.id == tid:
                return win.active_task

    def is_open(self, win):
        return win in self.windows

    def get_task(self, tid, activate=True):
        for win in self.windows:
            if win.active_task:
                if win.active_task.id == tid:
                    if activate and win.control:
                        win.activate()
                    break
        else:
            w = TaskWindowLayout(tid)
            win = self.create_window(w)
            if activate:
                win.open()

        if win:
            win.active_task.window = win

            return win.active_task

    def open_task(self, tid, **kw):
        return self.get_task(tid, True, **kw)

        # def add_view(self, ui):
        #     self.uis.append(weakref.ref(ui)())

        # def open_view(self, obj, **kw):
        # open_view(obj, **kw)
        # info = obj.edit_traits(**kw)
        # self.add_view(info)
        # return info

    def exit(self, **kw):
        report_view_stats()
        close_views()

        self._cleanup_services()

        super(BaseTasksApplication, self).exit(**kw)

    def _cleanup_services(self):
        for si in self.get_services(ICoreDevice):
            si.close()


# ============= EOF =============================================
