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
from datetime import datetime
from traits.api import List
from pyface.api import SplashScreen
from pyface.image_resource import ImageResource
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.paths import paths
from pychron.applications.about_dialog import myAboutDialog
from pychron.envisage.tasks.base_tasks_application import BaseTasksApplication


def get_resource_root():
    path = __file__
    from pychron.globals import globalv

    if not globalv.debug:
        while os.path.basename(path) != 'Resources':
            path = os.path.dirname(path)
    return path


paths.set_search_paths(get_resource_root())


def revision_str(rev):
    if rev is None:
        rev = ''
    else:
        if not isinstance(rev, str):
            t = datetime.fromtimestamp(rev.committed_date)
            h, b = rev.name_rev.split(' ')
            rev = '{} ({}) {}'.format(b, h[:8], t.strftime('%m-%d-%Y'))
    return rev


class PychronApplication(BaseTasksApplication):
    about_additions = List

    def set_changes(self, changelist):
        self.about_dialog.changes = changelist

    def set_revisions(self, local, remote):
        local = revision_str(local)
        remote = revision_str(remote)

        self.about_dialog.local_rev = local
        self.about_dialog.remote_rev = remote

    def _about_dialog_default(self):
        about_dialog = myAboutDialog(
            image=ImageResource(name='about.png',
                                search_path=paths.icon_search_path))

        about_dialog.version_info = self.get_version_info()
        about_dialog.additions = self.about_additions
        return about_dialog

    def _splash_screen_default(self):
        sp = SplashScreen(
            image=ImageResource(name='splash.png',
                                search_path=paths.icon_search_path))
        return sp

    def get_version_info(self):
        from pychron import version

        return '{} {}'.format(self.name, version.__version__)


#============= views ===================================
#============= EOF ====================================
