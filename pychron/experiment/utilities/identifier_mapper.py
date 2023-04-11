# ===============================================================================
# Copyright 2016 Jake Ross
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
from __future__ import absolute_import

import os

# ============= local library imports  ==========================
from pychron.core.yaml import yload
from pychron.loggable import Loggable
from pychron.paths import paths


def default_mapping():
    j = {"c-01-j": 4358, "c-02-j": 4416, "c-mc-j": 4418, "c-03-j": 4424}
    f = {"c-02-f": 4415, "c-mc-f": 4417, "c-03-f": 4423}

    o = {"c-01-o": 4359}
    return {"MassSpec": {"felix": f, "jan": j, "obama": o}}


class IdentifierMapper(Loggable):
    def map_to_value(self, value, spectrometer, destination="MassSpec"):
        mapping = self._get_spectrometer_mapping(spectrometer.lower(), destination)
        lvalue = value.lower()
        if lvalue in mapping:
            m = mapping[lvalue]
        else:
            self.debug(
                'value "{}" not in mapping for spectrometer "{}". '
                "Available keys={}".format(value, spectrometer, mapping.keys())
            )

            m = value

        self.debug('mapped "{}" to "{}"'.format(value, m))
        return m

    # private
    def _get_spectrometer_mapping(self, spec, destination):
        mapping = self._get_mapping()
        dmapping = mapping.get(destination, {})
        return dmapping.get(spec, {})

    def _get_mapping(self):
        p = paths.identifier_mapping_file
        if not os.path.isfile(p):
            self.warning(
                "Using the default identifier mapping because {} does not exist".format(
                    p
                )
            )
            return default_mapping()
        else:
            return yload(p)


# ============= EOF =============================================
