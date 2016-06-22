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
from git.exc import InvalidGitRepositoryError
from pyface.tasks.action.schema_addition import SchemaAddition

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.globals import globalv
from pychron.updater.tasks.actions import CheckForUpdatesAction
from pychron.updater.tasks.update_preferences import UpdatePreferencesPane
from pychron.updater.updater import Updater


def gen_commits(log):
    def _gen():
        lines = iter(log.split('\n'))
        commit = None
        while 1:
            try:
                if not commit:
                    commit = lines.next()

                author = lines.next()
                date = lines.next()
                message = []
                while 1:
                    line = lines.next()

                    if line.startswith('commit '):
                        commit = line
                        yield date, author, '\n'.join(message)
                        break
                    else:
                        if line.strip():
                            message.append(line.strip())

            except StopIteration:

                yield date, author, '\n'.join(message)
                break

    return _gen()


class UpdatePlugin(BaseTaskPlugin):
    name = 'Update'
    id = 'pychron.update.plugin'

    # plugin interface
    def test_repository(self):
        updater = self.application.get_service('pychron.updater.updater.Updater')
        return bool(updater.test_origin())

    def start(self):
        super(UpdatePlugin, self).start()

        updater = self.application.get_service('pychron.updater.updater.Updater')
        if updater.check_on_startup:
            updater.check_for_updates()
        try:
            globalv.active_branch = updater.active_branch
        except InvalidGitRepositoryError:
            pass

    # BaseTaskPlugin interface
    def check(self):
        try:
            from git import Repo

            return True
        except ImportError:
            return False

    def _preferences_default(self):
        return self._preferences_factory('update')

    # private
    def _updater_factory(self):
        u = Updater(application=self.application)
        u.bind_preferences()
        return u

    # defaults
    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=Updater,
                                        factory=self._updater_factory)
        return [so]

    def _preferences_panes_default(self):
        return [UpdatePreferencesPane]

    def _available_task_extensions_default(self):
        return [(self.id, '', self.name, [SchemaAddition(id='pychron.update.check_for_updates',
                                                         factory=CheckForUpdatesAction,
                                                         path='MenuBar/help.menu'),
                                          # SchemaAddition(id='pychron.update.build_app',
                                          #                factory=BuildApplicationAction,
                                          #                path='MenuBar/help.menu'),
                                          # SchemaAddition(id='pychron.update.manage_branch',
                                          #                factory=ManageBranchAction,
                                          #                path='MenuBar/help.menu'),
                                          # SchemaAddition(id='pychron.update.manage_version',
                                          #                factory=ManageVersionAction,
                                          #                path='MenuBar/help.menu')
                                          ])]

# ============= EOF =============================================
