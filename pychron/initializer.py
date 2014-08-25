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

#============= enthought library imports =======================
from traits.api import Any
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.initialization_parser import InitializationParser
from pychron.core.ui.progress_dialog import myProgressDialog
from pychron.globals import globalv


class Initializer(Loggable):
    """
    """

    pd = None
    name = 'Initializer'
    application = Any
    device_prefs = Any
    init_list = None

    def __init__(self, *args, **kw):

        super(Initializer, self).__init__(*args, **kw)
        self.parser = InitializationParser()
        self.init_list = []

    def add_initialization(self, a):
        """
        """
        self.debug('add initialization {}'.format(a))
        self.init_list.append(a)

    def run(self, application=None):

        self.application = application

        ok = True
        self.info('Running Initializer')
        nsteps = 1
        for idict in self.init_list:
            nsteps += self._get_nsteps(**idict)

        pd = self._load_progress(nsteps)

        for idict in self.init_list:
            ok = self._run(**idict)
            if not ok:
                break

        msg = ('Complete' if ok else 'Failed')
        self.info('Initialization {}'.format(msg))

        pd.close()

        return ok

    def info(self, msg, **kw):

        pd = self.pd
        if pd is not None:
            offset = pd.get_value()

            if offset == pd.max - 1:
                pd.max += 1

            pd.change_message(msg)

        super(Initializer, self).info(msg, **kw)

    def _run(self,
             name=None,
             device_dir=None,
             manager=None,
             plugin_name=None):

        if device_dir is None:
            device_dir = paths.device_dir

        parser = self.parser
        if manager is not None:
            self.info('Manager loading {}'.format(name))
            manager.application = self.application
            manager.load()

        else:
            return False

        managers = []
        devices = []
        flags = []
        timed_flags = []
        valve_flags_attrs = []

        mp, name = self._get_plugin(name, plugin_name)

        if mp is not None:
            if not globalv.ignore_required:
                if not self._check_required(mp):
                    return False

            managers = parser.get_managers(mp)
            devices = parser.get_devices(mp)
            flags = parser.get_flags(mp)
            timed_flags = parser.get_timed_flags(mp)
            valve_flags = parser.get_valve_flags(mp, element=True)

            if valve_flags:
                for vf in valve_flags:
                    vs = vf.find('valves')
                    if vs:
                        vs = vs.split(',')
                valve_flags_attrs.append((vf.text.strip(), vs))

            # set rpc server
            mode, _, port = parser.get_rpc_params(mp)
            if port and mode != 'client':
                manager.load_rpc_server(port)

        if managers:
            self.info('loading managers - {}'.format(', '.join(managers)))
            manager.name = name
            self._load_managers(manager, managers, device_dir)

        if devices:
            self.info('loading devices - {}'.format(', '.join(devices)))
            self._load_devices(manager, name, devices, plugin_name)

        if flags:
            self.info('loading flags - {}'.format(', '.join(flags)))
            self._load_flags(manager, flags)

        if timed_flags:
            self.info('loading timed flags - {}'.format(','.join(timed_flags)))
            self._load_timed_flags(manager, timed_flags)

        if valve_flags_attrs:
            self.info('loading valve flags - {}'.format(','.join(valve_flags_attrs)))
            self._load_valve_flags(manager, valve_flags_attrs)

        if manager is not None:
            self.info('finish {} loading'.format(name))
            manager.finish_loading()

        return True

    def _load_flags(self, manager, flags):
        for f in flags:
            self.info('loading {}'.format(f))
            manager.add_flag(f)

    def _load_timed_flags(self, manager, flags):
        for f in flags:
            self.info('loading {}'.format(f))
            manager.add_timed_flag(f)

    def _load_valve_flags(self, manager, flags):
        for f, v in flags:
            self.info('loading {}, valves={}'.format(f, v))
            manager.add_valve_flag(f, v)

    def _load_managers(self,
                       manager,
                       managers,
                       device_dir):

        for mi in managers:
            man = None

            self.info('load {}'.format(mi))
            mode, host, port = self.parser.get_rpc_params((mi, manager.name))
            remote = mode == 'client'
            try:
                man = getattr(manager, mi)
                if man is None:
                    man = manager.create_manager(mi, host=host,
                                                 port=port, remote=remote)
            except AttributeError, e:
                self.warning(e)
                try:
                    man = manager.create_manager(mi,
                                                 host=host,
                                                 port=port, remote=remote)
                except Exception:
                    import traceback
                    traceback.print_exc()

            if man is None:
                self.debug('trouble creating manager {}'.format(mi))
                continue

            if self.application is not None:
                # register this manager as a service
                man.application = self.application
                self.application.register_service(type(man), man)

            d = dict(name=mi, device_dir=device_dir, manager=man,
                     plugin_name=manager.name)

            self.add_initialization(d)

    def _check_required(self, subtree):
        # check the subtree has all required devices enabled
        devs = self.parser.get_devices(subtree, all_=True, element=True)
        for di in devs:
            required = True
            req = self.parser.get_parameter(di, 'required')
            if req:
                required = req.strip().lower() == 'true'

            enabled = di.get('enabled').lower() == 'true'

            if required and not enabled:
                name = di.text.strip().upper()
                msg = '''Device {} is REQUIRED but is not ENABLED.
                
Do you want to quit to enable {} in the Initialization File?'''.format(name, name)
                result = self.confirmation_dialog(msg, title='Quit Pychron')
                if result:
                    os._exit(0)

        return True

    def _load_devices(self, manager, name, devices, plugin_name, ):
        """
        """
        print manager
        devs = []
        if manager is None:
            return

        for device in devices:

            if device == '':
                continue

            pdev = self.parser.get_device(name, device, plugin_name, element=True)

            dev_class = pdev.find('klass')
            if dev_class is not None:
                dev_class = dev_class.text.strip()

            try:

                dev = getattr(manager, device)
                if dev is None:
                    dev = manager.create_device(device,
                                                dev_class=dev_class)
                else:
                    if dev_class and dev.__class__.__name__ != dev_class:
                        dev = manager.create_device(device,
                                                    dev_class=dev_class,
                                                    obj=dev)

            except AttributeError:
                dev = manager.create_device(device, dev_class=dev_class)

            if dev is None:
                self.warning('No device for {}'.format(device))
                continue

            self.info('loading {}'.format(dev.name))
            if dev.load():
                # register the device
                if self.application is not None:
                    # display with the HardwareManager
                    self.application.register_service(ICoreDevice, dev,
                                                      {'display': True})

                devs.append(dev)
                self.info('opening {}'.format(dev.name))
                if not dev.open(prefs=self.device_prefs):
                    self.info('failed connecting to {}'.format(dev.name))
            else:
                self.info('failed loading {}'.format(dev.name))

        for od in devs:
            self.info('Initializing {}'.format(od.name))
            result = od.initialize(progress=self.pd)
            if result is not True:
                self.warning('Failed setting up communications to {}'.format(od.name))
                od.set_simulation(True)

            elif result is None:
                self.debug('{} initialize function does not return a boolean'.format(od.name))
                raise NotImplementedError

            od.application = self.application
            od.post_initialize()

            manager.devices.append(od)

    def _load_progress(self, n):
        """
            n: int, initialize progress dialog with n steps

            return a myProgressDialog object
        """
        pd = myProgressDialog(max=n, message='Welcome',
                              size=(500, 50))
        self.pd = pd
        self.pd.open()
        self.pd.position = 100, 100
        return pd

    def _get_plugin(self, name, plugin_name):
        parser = self.parser
        if plugin_name is None:
            # remove manager from name
            name = name.replace('_manager', '')
            mp = parser.get_plugin(name)
        else:
            mp = parser.get_manager(name, plugin_name)
        if mp is None:
            mp = parser.get_root().find('plugins/{}'.format(name))
        return mp, name

    def _get_nsteps(self, name=None, plugin_name=None, **kw):
        parser = self.parser
        mp, name= self._get_plugin(name, plugin_name)

        ns = 0
        if mp is not None:
            ns += (2 * (len(parser.get_managers(mp)) + 1))
            ns += (3 * (len(parser.get_devices(mp)) + 1))
            ns += (len(parser.get_flags(mp)) + 1)
            ns += (len(parser.get_timed_flags(mp)) + 1)

        return ns


# ========================= EOF ===================================

#    def _get_option_list(self, config, section, option):
#        '''
#
#        '''
#        rlist = []
#        if config.has_option(section, option):
#            rlist = [d.strip() for d in config.get(section, option).split(',') if not d.strip().startswith('_')]
#        return rlist
