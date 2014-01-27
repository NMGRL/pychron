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
from traits.api import Any
from traitsui.handler import Controller
from pychron.core.ui.gui import invoke_in_main_thread

#============= standard library imports ========================
#============= local library imports  ==========================

class ApplicationController(Controller):
    application = Any
    def add_window(self, ui):
        try:
            if self.application is not None:
                self.application.uis.append(ui)
        except AttributeError:
            pass

    def open_view(self, obj, **kw):
        def _open_():
            ui = obj.edit_traits(**kw)
            self.add_window(ui)

        invoke_in_main_thread(_open_)
#============= EOF =============================================
