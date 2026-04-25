# ===============================================================================
# Copyright 2022 Jake Ross
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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from threading import Thread

from pychron.core.ui.gui import invoke_in_main_thread
from pychron.envisage.resources import icon
from pychron.envisage.ui_actions import UIAction


class ShareConfigurationAction(UIAction):
    name = "Share Configuration"

    def perform(self, event):
        app = event.task.window.application
        up = app.get_service("pychron.usage.worker.UsageWorker")
        self._perform(up)

    def _perform(self, up):
        up.share()


class ShareSetupfilesAction(ShareConfigurationAction):
    name = "Share Setupfiles"

    def _perform(self, up):
        up.share(share_setupfiles=True, share_scripts=False)


class ShareScriptsAction(ShareConfigurationAction):
    name = "Share Scripts"

    def _perform(self, up):
        up.share(share_setupfiles=False, share_scripts=True)


# ============= EOF =============================================
