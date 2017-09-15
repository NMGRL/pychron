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
import json

from traits.api import Str, Int
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.abstract_device import AbstractDevice
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.core.data_helper import make_bitarray


class BaseDumper(CoreDevice):
    _dump_in_progress = False

    def energize(self):
        self._dump_in_progress = True
        self._energize()

    def denergize(self):
        self._denergize()
        self._dump_in_progress = False

    def _energize(self):
        raise NotImplementedError

    def _denergize(self):
        raise NotImplementedError

    def is_energized(self):
        raise NotImplementedError

    def _get_dump_state(self):
        raise NotImplementedError

    def dump_in_progress(self):
        state = False
        if self._dump_in_progress:
            state = self._get_dump_state()
            if not state:
                self._dump_in_progress = False
        return state


class NMGRLRotaryDumper(BaseDumper):
    nsteps = Int
    rpm = Int

    def load_additional_args(self, config):
        self.set_attribute(config, 'nsteps', 'Motion', 'nsteps')
        self.set_attribute(config, 'rpm', 'Motion', 'rpm')
        super(NMGRLMagnetDumper, self).load_additional_args(config)

    def energize(self):
        d = json.dumps({'command': 'EnergizeMagnets', 'nsteps': self.nsteps, 'rpm': self.rpm})
        self.ask(d)

    def denergize(self):
        d = json.dumps({'command': 'DenergizeMagnets', 'nsteps': self.nsteps})
        self.ask(d)

    def is_energized(self):
        ret = self.ask('IsEnergized', verbose=True) == 'OK'
        self._dump_in_progress = ret
        return ret


class NMGRLMagnetDumper(BaseDumper):
    def energize(self):
        d = json.dumps({'command': 'EnergizeMagnets', 'period': 3})
        self.ask(d)

    def denergize(self):
        self.ask('DenergizeMagnets')

    def is_energized(self):
        ret = self.ask('IsEnergized', verbose=True) == 'OK'
        self._dump_in_progress = ret
        return ret

# ============= EOF =============================================
