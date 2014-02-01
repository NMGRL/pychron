#===============================================================================
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
#===============================================================================

#=============enthought library imports=======================
from traits.api import Property, DelegatesTo, Instance
#=============standard library imports ========================
#=============local library imports  ==========================
# from pychron.config_loadable import ConfigLoadable
from traits.has_traits import provides
from pychron.hardware.core.i_core_device import ICoreDevice
# from viewable_device import ViewableDevice
from pychron.has_communicator import HasCommunicator
from pychron.rpc.rpcable import RPCable
from pychron.hardware.core.core_device import CoreDevice
# from pychron.hardware.core.viewable_device import ViewableDevice
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

    def get(self):
        if self._cdevice:
            return self._cdevice.get()

    def post_initialize(self, *args, **kw):
        self.graph.set_y_title(self.graph_ytitle)

        #use our scan configuration not the cdevice's
        self.setup_scan()
        self.setup_alarms()
        self.setup_scheduler()

        if self.auto_start:
            self.start_scan()

    def load(self, *args, **kw):
        config = self.get_configuration()
        if config:

            if self.load_additional_args(config):
                self._loaded = True
                self._cdevice.load()
                return True
    def __getattr__(self, attr):
        #print 'abstrcat {}'.format(attr)
        if hasattr(self._cdevice, attr):
            return getattr(self._cdevice, attr)

    def _get_dev_klass(self):
        return self._cdevice.__class__.__name__

#============= EOF =====================================
