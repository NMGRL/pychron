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
from traits.api import HasTraits, on_trait_change, Any
from traitsui.api import View, Item
from pychron.envisage.tasks.base_task import BaseTask
from pychron.logger.tasks.logger_panes import DisplayPane
from pychron.displays.gdisplays import gLoggerDisplay, gWarningDisplay
from pyface.timer.do_later import do_later
#============= standard library imports ========================
#============= local library imports  ==========================

class LoggerTask(BaseTask):
    name = 'Logger'

    warning_display = Any
    info_display = Any
    _opened = False

    @on_trait_change('warning_display:text_added')
    def _handle_warning(self, obj, name, old, new):
        self.display_pane.selected = obj.model

    def create_central_pane(self):
        self.warning_display = gWarningDisplay
        self.info_display = gLoggerDisplay

        self.display_pane = DisplayPane(loggers=[gLoggerDisplay,
                                                 gWarningDisplay])
        return self.display_pane

    @on_trait_change('window:opening')
    def _handle_window_open(self, evt):
        """
            ensure only one logger window open at a time

            veto the opening evt if there is a logger window already open
        """
        app = self.window.application
        for win in app.windows:
            if win.active_task:
                if win.active_task.id == 'pychron.logger':
                    evt.veto = True


#============= EOF =============================================
