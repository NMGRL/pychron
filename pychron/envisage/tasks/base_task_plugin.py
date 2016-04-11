# ===============================================================================
# Copyright 2013 Jake Ross
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
import os

from envisage.service_offer import ServiceOffer
from envisage.ui.tasks.task_extension import TaskExtension
from traits.api import List

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import add_extension
from pychron.envisage.tasks.base_plugin import BasePlugin
from pychron.globals import globalv
from pychron.paths import paths


class BaseTaskPlugin(BasePlugin):
    actions = List(contributes_to='pychron.actions')
    file_defaults = List(contributes_to='pychron.plugin.file_defaults')
    help_tips = List(contributes_to='pychron.plugin.help_tips')
    tasks = List(contributes_to='envisage.ui.tasks.tasks')
    service_offers = List(contributes_to='envisage.service_offers')
    available_task_extensions = List(contributes_to='pychron.available_task_extensions')
    task_extensions = List(contributes_to='envisage.ui.tasks.task_extensions')
    # my_task_extensions = List(contributes_to=TASK_EXTENSIONS)
    # base_task_extensions = List(contributes_to=TASK_EXTENSIONS)

    preferences = List(contributes_to='envisage.preferences')
    preferences_panes = List(
        contributes_to='envisage.ui.tasks.preferences_panes')

    managers = List(contributes_to='pychron.hardware.managers')

    _tests = None

    def _preferences_factory(self, *names):
        ps = []
        for ni in names:
            pp = self._make_preferences_path(ni)
            if pp:
                ps.append(pp)

        return ps

    def _make_preferences_path(self, name):
        p = os.path.join(paths.preferences_dir, add_extension(name, '.ini'))
        if os.path.isfile(p):
            return 'file://{}'.format(p)

    def service_offer_factory(self, **kw):
        return ServiceOffer(**kw)

    def startup_test(self):
        if globalv.use_startup_tests:
            self.debug('doing start up tests')
            self.application.startup_tester.test_plugin(self)

    # def set_preference_defaults(self):
    #     """
    #         children should override and use self._set_preference_defaults(defaults, prefid)
    #         to set preferences
    #     :return:
    #     """
    #     pass

    def start(self):
        self.startup_test()
        # try:
        #     self.set_preference_defaults()
        # except AttributeError, e:
        #     print 'exception', e

    # def _set_preference_defaults(self, defaults, prefid):
    #     """
    #
    #     :param defaults: list(tuple) [(str, object),]
    #     :param prefid: str preference_path e.g pychron.update
    #     :return:
    #     """
    #     change = False
    #     prefs = self.application.preferences
    #     self.debug('setting default preferences for {} {}'.format(self.name, self.id))
    #     for k, d in defaults:
    #         if k not in prefs.keys(prefid):
    #             self.debug('Setting default preference {}={}'.format(k, d))
    #             prefs.set('{}.{}'.format(prefid, k), d)
    #             change = True
    #
    #     if change:
    #         prefs.flush()
    #     else:
    #         self.debug('defaults already set')

    # # defaults
    # def _preferences_panes_default(self):
    # return []
    #
    # def _preferences_default(self):
    # return []
    def _task_extensions_default(self):
        extensions = [TaskExtension(actions=actions, task_id=eid) for eid, actions in self._get_extensions()]

        return extensions

    def _get_extensions(self):
        # xx = []
        ctid = None
        xx = []
        sadditions = []
        # print self.id, self.name
        for tid, action_id in self.application.get_task_extensions(self.id):
            # print 'a', tid, action
            # for _, _, _, actions in self.available_task_extensions:
            #     for av in actions:
            #         print 'b', tid, action, av.id
            action = next((av for _, _, _, actions in self.available_task_extensions
                           for av in actions if av.id == action_id), None)
            if action is None:
                self.debug('no action found for {}'.format(action_id))
                continue

            if ctid is None:
                ctid = tid

                sadditions.append(action)

            else:
                if ctid != tid:
                    xx.append((ctid, sadditions))
                    sadditions = [action]
                    ctid = None
                else:
                    sadditions.append(action)

        if sadditions:
            xx.append((tid, sadditions))

        return xx

# ============= EOF =============================================
