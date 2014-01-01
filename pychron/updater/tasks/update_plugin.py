#===============================================================================
# Copyright 2014 Jake Ross
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
import os
from envisage.plugin import Plugin
from git import Repo
from traits.api import List

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.helpers.logger_setup import new_logger
from pychron.loggable import confirmation_dialog
from pychron.updater.tasks.update_preferences import UpdatePreferencesPane

logger = new_logger('UpdatePlugin')


class UpdatePlugin(Plugin):
    preferences = List(contributes_to='envisage.preferences')
    preferences_panes = List(
        contributes_to='envisage.ui.tasks.preferences_panes')

    def start(self):
        logger.debug('starting update plugin')
        pref=self.application.preferences
        if pref.get('pychron.update.check_on_startup'):
            url=pref.get('pychron.update.update_url')
            if pref.get('pychron.update.use_development'):
                url=pref.get('pychron.update.update_url')

            if url:
                repo=self._setup_repo(url)
                logger.debug('pulling changes')
                origin=repo.remote('origin')

                if not repo.heads:
                    if self._out_of_date():
                        origin.pull('master')
                else:
                    info=origin.fetch()
                    if info:
                        info=info[0]
                        logger.debug('local  commit ={}'.format(repo.head.commit))
                        logger.debug('remote commit ={}'.format(info.commit))

                        if info.commit != repo.head.commit:
                            if self._out_of_date():
                                origin.pull('master')

    def _out_of_date(self):
        logger.info('updates are available')
        if confirmation_dialog('Updates are available. Would you like to install'):
            return True

    def _setup_repo(self, url):
        # p=os.path.join(paths.hidden_dir, 'updates')
        p='/Users/ross/Sandbox/updater_test/user_repo'
        if not os.path.isdir(p):
            os.mkdir(p)
            repo=Repo.init(p)
            # repo=Repo.init(p, bare=True)
        else:
            repo=Repo(p)

        # name = 'origin'
        # if hasattr(repo.remotes, name):
        #     repo.delete_remote(name)
        #
        # repo.create_remote(name, url)

        return repo

    def stop(self):
        logger.debug('stopping update plugin')

    def _preferences_panes_default(self):
        return [UpdatePreferencesPane]
#============= EOF =============================================

