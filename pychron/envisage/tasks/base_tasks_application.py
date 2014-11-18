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
from pyface.dialog import Dialog
from traits.api import List, Instance
from envisage.ui.tasks.tasks_application import TasksApplication
from pyface.tasks.task_window_layout import TaskWindowLayout
#============= standard library imports ========================
import weakref
#============= local library imports  ==========================
from pychron.globals import globalv
from pychron.loggable import Loggable
from pychron.hardware.core.i_core_device import ICoreDevice


class BaseTasksApplication(TasksApplication, Loggable):
    about_dialog = Instance(Dialog)

    uis = List

    def about(self):
        self.about_dialog.open()

    def start(self):
        if globalv.open_logger_on_launch:
            self._load_state()
            self.get_task('pychron.logger')

        return super(BaseTasksApplication, self).start()

    def get_open_task(self, tid):
        for win in self.windows:
            if win.active_task:
                if win.active_task.id == tid:
                    return win, win.active_task, True
        else:
            win = self.create_window(TaskWindowLayout(tid))
            return win, win.active_task, False

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
            win = self.create_window(TaskWindowLayout(tid))
            if activate:
                win.open()

        if win:
            return win.active_task

    def open_task(self, tid):
        return self.get_task(tid, True)

    def add_view(self, ui):
        self.uis.append(weakref.ref(ui)())

    def open_view(self, obj, **kw):
        info = obj.edit_traits(**kw)
        self.add_view(info)
        return info

    def exit(self, **kw):

        self._cleanup_services()

        uis = self.uis
        #         uis = copy.copy(self.uis)
        for ui in uis:
            try:
                ui.dispose(abort=True)
            except AttributeError:
                pass

        super(BaseTasksApplication, self).exit(**kw)

    def _cleanup_services(self):
        for si in self.get_services(ICoreDevice):
            si.close()


#============= EOF =============================================
