#===============================================================================
# Copyright 2011 Jake Ross
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
# from envisage.ui.workbench.api import WorkbenchApplication
from pyface.api import AboutDialog, SplashScreen
from pyface.image_resource import ImageResource
# from envisage.ui.tasks.tasks_application import TasksApplication
#============= standard library imports ========================
# import copy
#============= local library imports  ==========================
# from pychron.loggable import Loggable
import os
# from pyface.tasks.task_window_layout import TaskWindowLayout
from pychron.envisage.tasks.base_tasks_application import BaseTasksApplication
# from pychron.lasers.tasks.laser_preferences import FusionsLaserPreferences

from pychron.paths import paths


def get_resource_root():
    path = __file__
    from pychron.globals import globalv

    if not globalv.debug:
        while os.path.basename(path) != 'Resources':
            path = os.path.dirname(path)
    return path


# paths.set_icon_search_path(get_resource_root())
paths.set_search_paths(get_resource_root())

class PychronApplication(BaseTasksApplication):
    def _about_dialog_default(self):
        about_dialog = AboutDialog(
            image=ImageResource(name='about.png',
                                search_path=[paths.app_resources,
                                             paths.abouts]))
        return about_dialog

    def _splash_screen_default(self):
        sp = SplashScreen(
            image=ImageResource(name='splash.png',
                                search_path=[paths.app_resources,
                                             paths.splashes]))
        return sp


#============= views ===================================
#============= EOF ====================================
