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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.resources import icon
from pychron.envisage.ui_actions import UIAction
from pychron.envisage.view_util import open_view


class BuildApplicationAction(UIAction):
    name = "Build"
    image = icon("bricks")

    def perform(self, event):
        app = event.task.window.application
        up = app.get_service("pychron.updater.updater.Updater")
        up.build()


class CheckForUpdatesAction(UIAction):
    name = "Check For Updates"
    image = icon("update-product")

    description = "Check for updates to Pychron by examining the public Github."

    def perform(self, event):
        app = event.task.window.application
        up = app.get_service("pychron.updater.updater.Updater")
        up.check_for_updates(inform=True)


class ManageVersionAction(UIAction):
    name = "Manage Version"
    image = icon("update-product")
    accelerator = "Ctrl+;"

    def perform(self, event):
        app = event.task.window.application
        up = app.get_service("pychron.updater.updater.Updater")
        up.manage_version()


class ManageBranchAction(UIAction):
    name = "Manage Branch"
    image = icon("update-product")
    accelerator = "Ctrl+."

    def perform(self, event):
        app = event.task.window.application
        up = app.get_service("pychron.updater.updater.Updater")
        up.manage_branches()


class LibraryAction(UIAction):
    name = "Library Manager"

    def perform(self, event):
        from pychron.updater.package_manager import LibraryManager
        pm = LibraryManager()
        pm.load_libraries()
        open_view(pm)

# ============= EOF =============================================
