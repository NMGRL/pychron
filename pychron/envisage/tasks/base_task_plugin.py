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

# ============= standard library imports ========================
import os
from operator import attrgetter

# ============= enthought library imports =======================
from envisage.service_offer import ServiceOffer
from envisage.ui.tasks.task_extension import TaskExtension
from traits.api import List

# ============= local library imports  ==========================
from pychron.core.helpers.filetools import add_extension
from pychron.envisage.tasks.base_plugin import BasePlugin
from pychron.paths import paths


class BaseTaskPlugin(BasePlugin):
    actions = List(contributes_to='pychron.actions')
    file_defaults = List(contributes_to='pychron.plugin.file_defaults')
    help_tips = List(contributes_to='pychron.plugin.help_tips')
    tasks = List(contributes_to='envisage.ui.tasks.tasks')
    service_offers = List(contributes_to='envisage.service_offers')
    available_task_extensions = List(contributes_to='pychron.available_task_extensions')
    task_extensions = List(contributes_to='envisage.ui.tasks.task_extensions')

    preferences = List(contributes_to='envisage.preferences')
    preferences_panes = List(
        contributes_to='envisage.ui.tasks.preferences_panes')

    managers = List(contributes_to='pychron.hardware.managers')

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

    def _task_extensions_default(self):
        extensions = [TaskExtension(actions=actions, task_id=eid) for eid, actions in self._get_extensions()]

        return extensions

    def _get_extensions(self):
        ctid = None
        xx = []
        sadditions = []
        for tid, action_id in sorted(self.application.get_task_extensions(self.id)):
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

        sadditions = sorted(sadditions, key=attrgetter('id'))
        if sadditions:
            xx.append((tid, sadditions))

        return xx

# ============= EOF =============================================
