# ===============================================================================
# Copyright 2016 ross
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
import time
from threading import Thread

from traits.api import String, Color, HasTraits

from pychron.core.ui.gui import invoke_in_main_thread


def make_pattern_gen(flash, period, label, color):
    def pattern_gen():
        """
            infinite generator
        """
        pattern = ((flash * period, True, label, color), ((1 - flash) * period, False, '', 'black'))
        i = 0
        while 1:
            try:
                yield pattern[i]
                i += 1
            except IndexError:
                yield pattern[0]
                i = 1

    return pattern_gen()


class ExperimentStatus(HasTraits):
    label = String
    color = Color

    _gen = None
    _flash_daemon = None

    def reset(self):
        self.end()
        self.label = ''

    def set_state(self, state, flash, color, period=1):
        label = state.upper()

        if flash:
            self._gen = make_pattern_gen(flash, period, label, color)

            if not self._flash_daemon:
                t = Thread(target=self._flash_loop)
                t.setDaemon(True)
                t.start()
                self._flash_daemon = t

        else:
            self._gen = None
            invoke_in_main_thread(self.trait_set, color=color, label=label)

    def end(self):
        self._gen = None

    def _flash_loop(self):
        while 1:
            if self._gen:
                t, state, label, color = next(self._gen)
                invoke_in_main_thread(self.trait_set, color=color, label=label)
            else:
                invoke_in_main_thread(self.trait_set, label='')
                break
            time.sleep(t)

        self._flash_daemon = None

# ============= EOF =============================================
