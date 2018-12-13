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

from traits.api import Int

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice


class BaseDumper(CoreDevice):
    _dump_in_progress = False
    _dump_state_cnt = 0

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
        if self._dump_in_progress:
            state = self._get_dump_state()
            if not state:
                self._dump_state_cnt += 1
                if self._dump_state_cnt > 3:
                    self._dump_in_progress = False
            else:
                self._dump_state_cnt = 0

        return self._dump_in_progress


class NMGRLRotaryDumper(BaseDumper):
    nsteps = Int
    rpm = Int

    def load_additional_args(self, config):
        self.set_attribute(config, 'nsteps', 'Motion', 'nsteps', cast='int')
        self.set_attribute(config, 'rpm', 'Motion', 'rpm', cast='int')
        return super(NMGRLRotaryDumper, self).load_additional_args(config)

    def energize(self):
        d = json.dumps({'command': 'EnergizeMagnets', 'nsteps': self.nsteps, 'rpm': self.rpm})
        self.ask(d)
        self._dump_in_progress = True

    def denergize(self):
        d = json.dumps({'command': 'DenergizeMagnets', 'nsteps': self.nsteps})
        self.ask(d)
        self._dump_in_progress = False

    def is_energized(self):
        d = json.dumps({'command': 'IsEnergized'})
        ret = self.ask(d, verbose=True) == 'OK'
        return ret

    def is_moving(self):
        d = json.dumps({'command': 'RotaryDumperMoving'})
        ret = self.ask(d, verbose=True, retries=1) == 'OK'
        return ret

    def _get_dump_state(self):
        return self.is_moving()


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

# # ===============================================================================
# # Copyright 2015 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# # http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# # ===============================================================================
#
# # ============= enthought library imports =======================
# import json
#
# from traits.api import Str
# # ============= standard library imports ========================
# # ============= local library imports  ==========================
# from pychron.hardware.core.abstract_device import AbstractDevice
# from pychron.hardware.core.core_device import CoreDevice
#
#
# class NMGRLMagnetDumper(CoreDevice):
#     _dump_in_progress = False
#
#     def energize(self):
#         self._dump_in_progress = True
#         d = json.dumps({'command': 'EnergizeMagnets', 'period': 3})
#         self.ask(d)
#
#     def denergize(self):
#         self._dump_in_progress = False
#         self.ask('DenergizeMagnets')
#
#     def is_energized(self):
#         ret = self.ask('IsEnergized', verbose=True) == 'OK'
#         self._dump_in_progress = ret
#         return ret
#
#     # channel_address = Str
#     # in_progress_address = Str
#     # _dump_in_progress = False
#     #
#     # def load_additional_args(self, config):
#     #     self.set_attribute(config, 'channel_address', 'General', 'channel_address')
#     #     self.set_attribute(config, 'in_progress_address', 'General', 'in_progress_address')
#     #     super(NMGRLMagnetDumper, self).load_additional_args(config)
#     #
#     # def actuate(self):
#     #     if self._cdevice:
#     #         self._dump_in_progress = True
#     #         self._cdevice.open_channel(self.channel_address)
#     #
#     def dump_in_progress(self):
#         state = False
#         if self._dump_in_progress:
#             state = self.ask('GetMagnetsState')
#             if not state:
#                 self._dump_in_progress = False
#         return state
#
# # ============= EOF =============================================
