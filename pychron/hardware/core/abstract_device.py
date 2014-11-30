# ===============================================================================
# Copyright 2011 Jake Ross
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

# =============enthought library imports=======================
from traits.api import Property, DelegatesTo, Instance, provides, CStr
# =============standard library imports ========================
# =============local library imports  ==========================
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.has_communicator import HasCommunicator
from pychron.rpc.rpcable import RPCable
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.core.scanable_device import ScanableDevice


@provides(ICoreDevice)
class AbstractDevice(ScanableDevice, RPCable, HasCommunicator):
    _cdevice = Instance(CoreDevice)
    _communicator = DelegatesTo('_cdevice')

    dev_klass = Property(depends_on='_cdevice')
    graph = DelegatesTo('_cdevice')

    def get_factory(self, package, klass):
        try:
            module = __import__(package, fromlist=[klass])
            if hasattr(module, klass):
                factory = getattr(module, klass)
                return factory
        except ImportError, e:
            self.warning(e)

    def close(self):
        if self._cdevice:
            self._cdevice.close()

    def set(self, v):
        if self._cdevice:
            self._cdevice.set(v)

    def get(self, *args, **kw):
        if self._cdevice:
            return self._cdevice.get(*args, **kw)

    def post_initialize(self, *args, **kw):
        self.graph.set_y_title(self.graph_ytitle)

        # use our scan configuration not the cdevice's
        self.setup_scan()
        self.setup_alarms()
        self.setup_scheduler()

        if self.auto_start:
            self.start_scan()

    def initialize(self, *args, **kw):
        if self._cdevice:
            return self._cdevice.initialize(*args, **kw)

    def load(self, *args, **kw):
        if self._cdevice:
            if not self._check_cdevice():
                self.warning('Invalid device '
                             '"{}" for abstract device "{}"'.format(self._cdevice.name,
                                                                    self.name))
                return

        config = self.get_configuration()
        if config:
            if self.load_additional_args(config):
                self._loaded = True
                self._cdevice.load()
                return True

    def __getattr__(self, attr):
        if hasattr(self._cdevice, attr):
            return getattr(self._cdevice, attr)

    def _get_dev_klass(self):
        return self._cdevice.__class__.__name__

    def _check_cdevice(self):
        return True


class AddressableAbstractDevice(AbstractDevice):
    address = CStr

    def load_additional_args(self, config):
        self.set_attribute(config, 'address', 'General', 'address')

    def get(self, *args, **kw):
        if self._cdevice:
            return self._cdevice.read_channel(self.address, *args, **kw)

    def _check_cdevice(self):
        if self._cdevice:
            if hasattr(self._cdevice, 'read_channel'):
                return True
        else:
            return True

# ============= EOF =====================================
