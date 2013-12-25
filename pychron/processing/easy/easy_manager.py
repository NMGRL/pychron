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
from threading import Thread
from pychron.core.ui import set_toolkit

set_toolkit('qt4')

#============= enthought library imports =======================
from traits.api import HasTraits, Str, Int, Button, Instance, Callable, Bool
from traitsui.api import View, Item, UItem, VGroup, HGroup

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.core.ui.qt.progress_editor import ProgressEditor
from pychron.loggable import Loggable


class Progress(HasTraits):
    value = Int
    max = Int
    message = Str

    canceled=Bool
    accepted=Bool

    def soft_close(self):
        pass

    def close(self):
        pass

    def change_message(self, m, auto_increment=True):
        self.message = m
        if auto_increment:
            self.value += 1

    def increase_max(self, n):
        self.max += n


class EasyManager(Loggable):
    progress = Instance(Progress, ())

    execute_button = Button
    stop_button = Button
    cancel_button = Button
    func=Callable

    def wait_for_user(self):
        pass

    def _execute_button_fired(self):
        self._stopped = False
        t = Thread(target=self._execute)
        t.start()

    def _stop_button_fired(self):
        self._stopped = True

    def _execute(self):
        self._func()

    def traits_view(self):
        v = View(VGroup(
            HGroup(icon_button_editor('execute_button', 'play'),
                   icon_button_editor('stop_button', 'stop')),
            UItem('object.progress.value', editor=ProgressEditor(max_name='object.progress.max',
                                                        message_name='object.progress.message'))),
                 resizable=True)
        return v


if __name__ == '__main__':
    e = EasyManager()
    e.configure_traits()
#============= EOF =============================================

