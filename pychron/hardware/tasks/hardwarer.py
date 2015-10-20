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
import ConfigParser
import os
from traits.api import HasTraits, Button, Instance, List, Str, \
    Any, Enum, CStr, Int, Float
from traits.trait_types import Bool, String
from traitsui.api import View, Item, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================

from pychron.core.helpers.filetools import backup
from pychron.core.pychron_traits import IPAddress
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.loggable import Loggable
from pychron.paths import paths


class ConfigGroup(HasTraits):
    config_obj = Instance(ConfigParser.ConfigParser)

    def _anytrait_changed(self, name, new):
        """
            update the config object with the current user value
        """
        if self.config_obj:
            if self.config_obj.has_option(self.tag, name):
                self.config_obj.set(self.tag, name, new)


class ScanGroup(ConfigGroup):
    tag = 'Scan'
    enabled = Bool
    graph = Bool
    record = Bool
    auto_start = Bool
    period = Float


class CommunicationGroup(ConfigGroup):
    tag = 'Communications'


class SerialCommunicationGroup(CommunicationGroup):
    port = Str
    baudrate = Enum(300, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200, 230400)

    def load_from_config(self, cfg):
        self.port = cfg('port')
        self.baudrate = cfg('baudrate', cast='int')

    def traits_view(self):
        v = View(VGroup(Item('port'),
                        Item('baudrate')))
        return v


class EthernetCommunicationGroup(CommunicationGroup):
    host = IPAddress
    port = Int
    kind = Enum('TCP', 'UDP')

    def load_from_config(self, cfg):
        self.port = cfg('port', cast='int')
        self.host = cfg('host', default='localhost')
        self.kind = cfg('kind', default='UDP')

    def traits_view(self):
        v = View(Item('host'),
                 Item('port'),
                 Item('kind'))
        return v


CKLASS_DICT = {'ethernet': EthernetCommunicationGroup,
               'serial': SerialCommunicationGroup}


class DeviceConfigurer(Loggable):
    config_path = Str
    config_name = Str
    save_button = Button
    _config = None

    kind = Enum('ethernet', 'serial')
    communication_grp = Instance(CommunicationGroup)
    scan_grp = Instance(ScanGroup, ())
    comms_visible = Bool(False)

    def set_device(self, device):
        p = device.config_path
        self._load_configuration(p)

    def _load_configuration(self, path):
        self.config_path = path
        self.config_name = os.path.relpath(path, paths.device_dir)
        self._config = cfg = ConfigParser.ConfigParser()

        cfg.read(path)

        section = 'Communications'
        if cfg.has_section(section):
            kind = cfg.get(section, 'type')
            klass = CKLASS_DICT.get(kind)
            if klass:
                self.communication_grp = klass()

                def func(option, cast=None, default=None, **kw):
                    f = getattr(cfg, 'get{}'.format(cast if cast else ''))
                    try:
                        v = f(section, option, **kw)
                    except ConfigParser.NoOptionError:
                        v = default
                        if v is None:
                            if cast == 'boolean':
                                v = False
                            elif cast in ('float', 'int'):
                                v = 0
                    return v

                self.communication_grp.load_from_config(func)
                self.communication_grp.config_obj = cfg
                self.comms_visible = True
        else:
            self.comms_visible = False
            self.communication_grp = CommunicationGroup()

        section = 'Scan'
        if cfg.has_section(section):
            bfunc = lambda *args: cfg.getboolean(*args)
            ffunc = lambda *args: cfg.getfloat(*args)
        else:
            bfunc = lambda *args: False
            ffunc = lambda *args: 0

        sgrp = self.scan_grp
        for attr in ('enabled', 'graph', 'record', 'auto_start'):
            try:
                v = bfunc(section, attr)
            except ConfigParser.NoOptionError:
                v = False
            setattr(sgrp, attr, v)

        for attr in ('period',):
            try:
                v = ffunc(section, attr)
            except ConfigParser.NoOptionError:
                v = 0
            setattr(sgrp, attr, v)

    def _save_button_fired(self):
        self._dump()

    def _dump(self):
        # backup previous file
        # putting the device dir under git control is a good idea

        self._backup()
        with open(self.config_path, 'w') as wfile:
            self._config.write(wfile)

    def _backup(self):
        bp, pp = backup(self.config_path, paths.backup_device_dir, extension='.cfg')
        self.info('{} - saving a backup copy to {}'.format(bp, pp))


class Hardwarer(Loggable):
    devices = List
    selected = Instance(ICoreDevice)
    device_configurer = Instance(DeviceConfigurer, ())

    def _selected_changed(self, new):
        if new:
            self.device_configurer.set_device(new)


if __name__ == '__main__':
    from pychron.hardware.tasks.hardware_pane import ConfigurationPane

    dc = DeviceConfigurer()
    p = '/Users/ross/Pychron_dev/setupfiles/devices/bone_micro_ion_controller.cfg'
    p = '/Users/ross/Pychron_dev/setupfiles/devices/apis_controller.cfg'
    dc._load_configuration(p)

    class A(HasTraits):
        device_configurer = dc

    pane = ConfigurationPane(model=A())
    pane.configure_traits()
# ============= EOF =============================================



