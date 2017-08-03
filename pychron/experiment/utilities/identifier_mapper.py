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
import os

import yaml
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths


def default_mapping():
    j = {'c-01-j': 4358,
         'c-02-j': 4416,
         'c-mc-j': 4418}
    f = {'c-02-f': 4415,
         'c-mc-f': 4417}

    o = {'c-01-o': 4359}
    return {'MassSpec': {'felix': f, 'jan': j, 'obama': o}}


class IdentifierMapper(Loggable):
    def map_to_value(self, value, spectrometer, destination='MassSpec'):
        mapping = self._get_spectrometer_mapping(spectrometer.lower(), destination)
        lvalue = value.lower()
        if lvalue in mapping:
            return mapping[lvalue]
        else:
            return value

    # private
    def _get_spectrometer_mapping(self, spec, destination):

        mapping = self._get_mapping()
        dmapping = mapping.get(destination, {})
        return dmapping.get(spec, {})

    def _get_mapping(self):
        p = paths.identifier_mapping_file
        if not os.path.isfile(p):
            self.warning('Using the default identifier mapping because {} does not exist'.format(p))
            return default_mapping()
        else:
            with open(p, 'r') as rfile:
                return yaml.load(rfile)

# ============= EOF =============================================



