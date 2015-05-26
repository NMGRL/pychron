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
from traits.api import Str, Property, cached_property, Instance, Event
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable


class DVCIrradiationable(Loggable):
    dvc = Instance('pychron.dvc.dvc.DVC')

    level = Str
    levels = Property(depends_on='irradiation, updated')
    irradiation = Str
    irradiations = Property(depends_on='updated')

    updated = Event

    def verify_database_connection(self, inform=True):
        return self.dvc.db.connect(warn=inform)

    def load(self):
        pass

    def setup(self):
        pass

    @cached_property
    def _get_irradiations(self):
        if self.dvc.connected:
            with self.dvc.db.session_ctx():
                irs = self.dvc.db.get_irradiations()
                names = [i.name for i in irs]
                if names:
                    self.irradiation = names[0]
                return names
        else:
            return []

    @cached_property
    def _get_levels(self):
        if self.dvc.connected:
            with self.dvc.db.session_ctx():
                irrad = self.dvc.db.get_irradiation(self.irradiation)
                if irrad:
                    names = [li.name for li in irrad.levels]
                    if names:
                        self.level = names[0]
                    return names
                else:
                    return []
        else:
            return []

# ============= EOF =============================================



