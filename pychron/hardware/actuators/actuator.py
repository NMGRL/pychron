# ===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================

# ============= standard library imports ========================
import time

# ============= local library imports  ==========================
from pychron.hardware.actuators import PACKAGES
from pychron.hardware.core.abstract_device import AbstractDevice


def simulate(wrapper):
    def wrapped(obj, *args, **kw):
        r = wrapper(obj, *args, **kw)
        if obj.simulation and r is not None:
            time.sleep(0.01)
        return r
    return wrapped


class Actuator(AbstractDevice):
    """
    """
    _type = None

    def load_additional_args(self, config):
        """

        """

        # old style
        klass = name = self.config_get(config, 'General', 'type')
        if klass:
            if 'qtegra' in klass.lower():
                klass = 'QtegraGPActuator'
            elif 'agilent' in klass.lower():
                klass = 'AgilentGPActuator'

        # new style
        name = self.config_get(config, 'General', 'name', default=name)
        klass = self.config_get(config, 'General', 'klass', default=klass)

        self._type = klass
        if klass is not None:
            try:
                factory = self.get_factory(PACKAGES[klass], klass)
            except KeyError:
                self.warning_dialog('Failed construction device with klass={}'.format(klass))
                return

            self.debug('constructing cdevice: name={}, klass={}'.format(name, klass))
            self._cdevice = factory(name=name,
                                    application=self.application,
                                    configuration_dir_name=self.configuration_dir_name)
            return True

    def open_channel(self, *args, **kw):
        """

        """
        return self._actuate('open', *args, **kw)

    def close_channel(self, *args, **kw):
        """

        """
        return self._actuate('close', *args, **kw)

    @simulate
    def _actuate(self, tag, *args, **kw):
        if self._cdevice is not None:
            func = getattr(self._cdevice, '{}_channel'.format(tag))
            return func(*args, **kw)

    @simulate
    def get_channel_state(self, *args, **kw):
        """

        """

        if self._cdevice is not None:
            return self._cdevice.get_channel_state(*args, **kw)

# ============= EOF ====================================
