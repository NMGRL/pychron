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
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.hardware.core.core_device import CoreDevice


class ChannelSelect(CoreDevice):
    prefix = ''
    suffix = ''

    def load_additional_args(self, config):
        self.config_get(config, 'Communication','prefix', optional=False)
        self.config_get(config, 'Communication','suffix', optional=False)

        return True

    def set_channel(self, ch):

        cmd = '{}{}{}'.format(self.prefix, ch, self.suffix)
        self.ask(cmd)




#============= EOF =============================================



