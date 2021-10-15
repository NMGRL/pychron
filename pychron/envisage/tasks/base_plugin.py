# ===============================================================================
# Copyright 2015 Jake Ross
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

from envisage.plugin import Plugin
from envisage.service_offer import ServiceOffer
from traits.api import List

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import add_extension
from pychron.loggable import Loggable
from pychron.paths import paths


class BasePlugin(Plugin, Loggable):
    actions = List(contributes_to='pychron.actions')
    file_defaults = List(contributes_to='pychron.plugin.file_defaults')
    help_tips = List(contributes_to='pychron.plugin.help_tips')
    service_offers = List(contributes_to='envisage.service_offers')
    preferences = List(contributes_to='envisage.preferences')
    preferences_panes = List(
        contributes_to='envisage.ui.tasks.preferences_panes')

    managers = List(contributes_to='pychron.hardware.managers')

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.init_logger()

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

    def check(self):
        return True

# ============= EOF =============================================
