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
# from threading import Thread
import time
from pychron.core.ui import set_toolkit
# from pychron.core.ui.thread import Thread
from pychron.core.ui.thread import Thread
from pychron.easy_parser import EasyParser
from pychron.envisage.icon_button_editor import icon_button_editor

set_toolkit('qt4')

#============= enthought library imports =======================
from traits.api import HasTraits, Str, Int, Button, Instance, Callable, Bool
from traitsui.api import View, UItem, VGroup, HGroup

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.ui.qt.progress_editor import ProgressEditor
from pychron.loggable import Loggable


class Progress(HasTraits):
    value = Int
    max = Int
    message = Str

    canceled = Bool
    accepted = Bool

    def get_value(self):
        return self.value

    def soft_close(self):
        pass

    def close(self):
        pass

    def change_message(self, m, auto_increment=True):
        self.message = m
        # invoke_in_main_thread(self.trait_set, message=m)
        if auto_increment:
            self.value += 1

    def increase_max(self, n):
        self.max += n


class EasyManager(Loggable):
    progress = Instance(Progress, ())

    execute_button = Button
    skip_button = Button
    stop_button = Button
    cancel_button = Button
    func = Callable

    _finished = False
    canceled = False
    accepted = False
    _skip=False
    _ready_to_continue = Bool(True)
    continue_button = Button

    def is_finished(self):
        return self._finished or self.canceled

    def _continue_button_fired(self):
        self._ready_to_continue = True

    def _skip_button_fired(self):
        self._skip=True
        self._ready_to_continue=True

    def was_skipped(self):
        return self._skip

    def wait_for_user(self):
        self._skip=False
        self.progress.increase_max(1)
        self.progress.change_message('Waiting for user')
        self.debug('waiting for user')
        self._ready_to_continue = False
        while not (self.canceled or self.accepted):
            if self._ready_to_continue:
                break
            time.sleep(0.05)
        return True

    def ok_continue(self):
        return not self.is_finished()

    def execute(self):
        self.canceled = False
        t = Thread(target=self._execute)
        t.start()
        self._t = t

    def _stop_button_fired(self):
        self.accepted = True

    def _execute(self):
        ep = EasyParser()
        with self.db.session_ctx() as sess:
            ok = self.func(ep, self)
            if not ok:
                sess.rollback()
        if ok:
            self.information_dialog('Changes saved to database')
        else:
            self.warning_dialog('Failed saving changes to database')

    def traits_view(self):
        v = View(VGroup(
            HGroup(icon_button_editor('stop_button', 'stop'),
                   icon_button_editor('continue_button', 'arrow_right',
                                      enabled_when='not _ready_to_continue'),
                   icon_button_editor('skip_button', 'arrow_turn_right',
                                      enabled_when='not _ready_to_continue')),

            UItem('object.progress.value', editor=ProgressEditor(max_name='object.progress.max',
                                                                 message_name='object.progress.message'))),
                 resizable=True,
                 width=500,
                 title='Easy Manager')
        return v


if __name__ == '__main__':
    e = EasyManager()
    e.configure_traits()
#============= EOF =============================================

