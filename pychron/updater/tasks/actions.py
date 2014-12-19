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
from traits.api import HasTraits, Button
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.menu import Action
from pychron.envisage.resources import icon


class CheckForUpdatesAction(Action):
    name = 'Check For Updates'
    image = icon('update-product')

    def perform(self, event):
        app = event.task.window.application
        up = app.get_service('pychron.updater.updater.Updater')
        up.check_for_updates(inform=True)


# ============= EOF =============================================



