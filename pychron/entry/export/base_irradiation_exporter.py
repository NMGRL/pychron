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
from traits.api import Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable


class BaseIrradiationExporter(Loggable):
    source = Instance('pychron.dvc.dvc.DVC')

    def do_export(self, irradiations):
        """
        irradiations: list of str
        """
        if self.setup():
            db = self.source
            with db.session_ctx():
                for irr in irradiations:
                    dbirr = db.get_irradiation(irr)
                    self.info('exporting irradiation {}'.format(dbirr.name))
                    self._export(dbirr)

    def setup(self):
        return True

    def _export(self, dbirr):
        raise NotImplementedError

# ============= EOF =============================================



