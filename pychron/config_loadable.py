#!/usr/bin/python
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
from pychron.config_mixin import ConfigMixin
from loggable import Loggable
# ============= standard library imports ========================
# ============= local library imports  ==========================

class ConfigLoadable(ConfigMixin, Loggable):
    """
    """

    def update_configuration(self, **kw):
        config = self.get_configuration()
        for section, options in kw.iteritems():
            if not config.has_section(section):
                config.add_section(section)

            for option, value in options.iteritems():
                config.set(section, option, value)
        self.write_configuration(config)

    def bootstrap(self, *args, **kw):
        """
        """

        self.info('load')
        if self.load(*args, **kw):
            self.info('open')
            if self.open(*args, **kw):
                self.info('initialize')
                self.initialize(*args, **kw)
                return True
            else:
                self.initialize(*args, **kw)
                self.warning('failed opening')
        else:
            self.warning('failed loading')

    def open(self, *args, **kw):
        """
        """

        return True

    def load(self, *args, **kw):
        """
        """
        return True

    def load_additional_args(self, *args, **kw):
        return True

    def _load_hook(self, config):
        pass

    def initialize(self, *args, **kw):
        """
        """

        return True

    def convert_config_name(self, name):
        """
        """
        nname = ''
        if '_' in name:
            for s in name.split('_'):
                if s == 'co2':
                    s = 'CO2'
                else:
                    s = s.capitalize()
                nname += s
        else:
            nname = name
        return nname

# ============= EOF =============================================

