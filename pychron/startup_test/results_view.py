# ===============================================================================
# Copyright 2014 Jake Ross
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
from threading import Thread
from pyface.confirmation_dialog import confirm
from pyface.constant import YES
import time
from traits.api import Instance, Int, Property, Any, Str, String
from traitsui.api import View, Controller, UItem, TabularEditor, VGroup, UReadonly
from pyface.timer.do_later import do_after
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.helpers.formatting import floatfmt
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.envisage.resources import icon
from pychron.pychron_constants import LIGHT_GREEN, LIGHT_RED, LIGHT_YELLOW
from pychron.startup_test.tester import TestResult


COLOR_MAP = {'Passed': LIGHT_GREEN,
             'Skipped': 'lightblue',
             'Failed': LIGHT_RED,
             'Invalid': LIGHT_YELLOW}
ICON_MAP = {'Passed': 'green_ball',
            'Skipped': 'gray_ball',
            'Failed': 'red_ball',
            'Invalid': 'yellow_ball'}


class ResultsAdapter(TabularAdapter):
    columns = [('', 'result_image'),
               ('Plugin', 'plugin'),
               ('Name', 'name'),
               ('Duration (s)', 'duration'),
               ('Result', 'result')]
    plugin_width = Int(200)
    name_width = Int(190)
    duration_width = Int(70)
    duration_text = Property
    result_image_image = Property
    result_image_text = Property

    def _get_result_image_text(self):
        return ''

    def _get_result_image_image(self):
        return icon(ICON_MAP[self.item.result])

    def get_bg_color(self, obj, trait, row, column=0):
        return COLOR_MAP[self.item.result]

    def _get_duration_text(self):
        return floatfmt(self.item.duration)  # '{:0.5f}'.format(self.item.duration)


class ResultsView(Controller):
    model = Instance('pychron.startup_test.tester.StartupTester')
    auto_close = 5
    selected = Instance(TestResult, ())

    base_help_str = 'Select any row to cancel auto close. Auto close in {}'
    help_str = String
    _auto_closed = False
    _cancel_auto_close = False

    def _selected_changed(self, new):
        self._cancel_auto_close = bool(new)

    def _timer_func(self):
        delay = self.auto_close
        st = time.time()
        while 1:
            time.sleep(0.25)
            ct = time.time() - st
            if ct > delay or self._cancel_auto_close:
                break
            self.help_str = self.base_help_str.format(delay - int(ct))

        if self._cancel_auto_close:
            self.help_str = 'Auto close canceled'
        else:
            invoke_in_main_thread(self._do_auto_close)

    def init(self, info):
        if self.auto_close and self.model.all_passed:
            t = Thread(target=self._timer_func)
            t.start()
            # do_after(self.auto_close * 1000, self._do_auto_close)
        else:
            self.help_str = ''

    def closed(self, info, is_ok):
        import sys

        if not self._auto_closed and not is_ok:
            if confirm(info.ui.control, 'Are you sure you want to Quit?') == YES:
                self.model.info('User quit because of Startup fail')

                sys.exit()
        else:
            if not self.model.ok_close():
                if confirm(info.ui.control, 'Pychron is not communicating with a Spectrometer.\n'
                                            'Are you sure you want to enter '
                                            'Spectrometer Simulation mode?') != YES:
                    sys.exit()

    def _do_auto_close(self):
        if not self._cancel_auto_close:
            self._auto_closed = True
            try:
                self.info.ui.dispose()
            except AttributeError:
                pass

    def traits_view(self):
        v = View(VGroup(UItem('results', editor=TabularEditor(adapter=ResultsAdapter(),
                                                              editable=False,
                                                              selected='controller.selected')),
                        VGroup(UReadonly('controller.selected.description'),
                               show_border=True,
                               label='Description'),
                        VGroup(UReadonly('controller.selected.error'),
                               show_border=True,
                               visible_when='controller.selected.error',
                               label='error'),
                        VGroup(UReadonly('controller.help_str'),
                               show_border=True,
                               visible_when='controller.help_str')),
                 title='Test Results',

                 buttons=['OK', 'Cancel'],
                 width=650,
                 kind='livemodal',
                 resizable=True)
        return v

# ============= EOF =============================================



