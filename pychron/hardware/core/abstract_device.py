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
from pychron.config_loadable import ConfigLoadable
from pychron.config_mixin import ConfigMixin
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.has_communicator import HasCommunicator
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.core.scanable_device import ScanableDevice

PACKAGES = dict(ProXRADC='pychron.hardware.ncd.adc',
                Eurotherm='pychron.hardware.eurotherm',
                NMGRLFurnaceFeeder='pychron.hardware.furnace.nmgrl.feeder',
                NMGRLFurnaceFunnel='pychron.hardware.furnace.nmgrl.funnel',
                NMGRLFurnaceEurotherm='pychron.hardware.furnace.nmgrl.eurotherm',
                MDriveMotor='pychron.hardware.mdrive',
                RPiGPIO='pychron.hardware.rpi_gpio')


@provides(ICoreDevice)
class AbstractDevice(ScanableDevice, ConfigLoadable, HasCommunicator):
    _cdevice = Instance(CoreDevice)
    communicator = DelegatesTo('_cdevice')

    dev_klass = Property(depends_on='_cdevice')
    graph = DelegatesTo('_cdevice')

    def load_additional_args(self, config):
        """

        """
        cklass = self.config_get(config, 'General', 'type')

        # if 'Argus' in klass:
        #     klass = 'ArgusGPActuator'

        # if klass is not None:
        #     if 'subsystem' in klass:
        #         pass
        #     else:
        factory = self.get_factory(PACKAGES[cklass], cklass)
        # self.debug('constructing cdevice: name={}, klass={}'.format(name, klass))
        self._cdevice = factory(name=cklass, configuration_dir_name=self.configuration_dir_name)
        return True

    @property
    def com_device_name(self):
        return self._cdevice.__class__.__name__

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

    def open(self, *args, **kw):
        self.debug('open device')

        return HasCommunicator.open(self, **kw)

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
        return super(AddressableAbstractDevice, self).load_additional_args(config)

    def get(self, force=False, *args, **kw):
        if self._cdevice:
            return self._cdevice.read_channel(self.address, *args, **kw)

    def _check_cdevice(self):
        if self._cdevice:
            if hasattr(self._cdevice, 'read_channel'):
                return True
        else:
            return True

# ============= EOF =====================================
