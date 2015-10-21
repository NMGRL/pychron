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
from visa import ResourceManager
# ============= local library imports  ==========================
from pychron.hardware.core.communicators.communicator import Communicator

RM = ResourceManager()


class GpibCommunicator(Communicator):
    """
        uses PyVisa as main interface to GPIB. currently (8/27/14) need to use a 32bit python version.
        The NI488.2 framework does not work with a 64bit distribution
    """

    primary_address = 0
    secondary_address = 0

    def open(self, *args, **kw):
        self.debug('opening gpib communicator')
        self.handle = RM.get_instrument('GPIB{}::{}::INSTR'.format(self.primary_address, self.secondary_address))
        if self.handle is not None:
            self.simulation = False
            return True

    def load(self, config, path, **kw):
        self.set_attribute(config, 'primary_address', 'Communications', 'primary_address')
        self.set_attribute(config, 'secondary_address', 'Communications', 'secondary_address', optional=False)
        return True

    def trigger(self):
        self.handle.trigger()

    def ask(self, cmd):
        return self.handle.ask(cmd)

    def tell(self, cmd):
        self.handle.write(cmd)

# ============= EOF ====================================
