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

# ============= enthought library imports =======================
from traits.api import Any, List

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.strtools import to_bool
from pychron.core.ui.progress_dialog import myProgressDialog
from pychron.envisage.initialization.initialization_parser import InitializationParser
from pychron.globals import globalv
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.loggable import Loggable


class InitializerError(BaseException):
    pass


class Initializer(Loggable):
    name = "Initializer"
    _init_list = List
    _parser = Any
    _pd = Any

    def add_initialization(self, a):
        """ """
        self.debug("add initialization {}".format(a))
        self._init_list.append(a)

    def run(self, application=None):
        self._parser = InitializationParser()
        self.info("Initialization Path: {}".format(self._parser.path))

        self.application = application

        ok = True
        self.info("Running Initializer")
        nsteps = (
            sum([self._get_nsteps(idict["plugin_name"]) for idict in self._init_list])
            + 1
        )

        pd = self._setup_progress(nsteps)
        try:
            for idict in self._init_list:
                ok = self._run(**idict)
                if not ok:
                    break

            msg = "Complete" if ok else "Failed"
            self.info("Initialization {}".format(msg))

            pd.close()
        except BaseException as e:
            import traceback

            traceback.print_exc()
            self.debug("Initializer Exception: {}".format(e))
            raise e

        return ok

    def info(self, msg, **kw):
        pd = self._pd
        if pd is not None:
            offset = pd.get_value()

            if offset == pd.max - 1:
                pd.max += 1

            pd.change_message(msg)

        super(Initializer, self).info(msg, **kw)

    def _run(self, name=None, manager=None, plugin_name=None):
        parser = self._parser
        if manager is not None:
            self.info("Manager loading {}".format(name))
            manager.application = self.application
            manager.load()
        else:
            return False

        managers = []
        if plugin_name:
            mp = self._get_plugin(plugin_name)
        else:
            mp, name = self._get_plugin_by_name(name)

        if mp is not None:
            if not globalv.ignore_initialization_required:
                if not self._check_required(mp):
                    return False

            managers = parser.get_managers(mp)

        if managers:
            self.info("loading managers - {}".format(", ".join(managers)))
            manager.name = name
            self._load_managers(manager, managers, plugin_name)

        self._load_elements(mp, manager, name, plugin_name)

        if manager is not None:
            self.info("finish {} loading".format(name))
            manager.finish_loading()

        return True

    def _load_elements(self, element, manager, name, plugin_name):
        mp = element
        parser = self._parser
        devices = parser.get_devices(mp)
        flags = parser.get_flags(mp)
        timed_flags = parser.get_timed_flags(mp)
        valve_flags = parser.get_valve_flags(mp, element=True)

        valve_flags_attrs = []
        if valve_flags:
            for vf in valve_flags:
                vs = vf.find("valves")
                if vs:
                    vs = vs.split(",")
            valve_flags_attrs.append((vf.text.strip(), vs))

        if devices:
            self.info("loading devices - {}".format(", ".join(devices)))
            self._load_devices(manager, name, devices, plugin_name)

        if flags:
            self.info("loading flags - {}".format(", ".join(flags)))
            self._load_flags(manager, flags)

        if timed_flags:
            self.info("loading timed flags - {}".format(",".join(timed_flags)))
            self._load_timed_flags(manager, timed_flags)

        if valve_flags_attrs:
            self.info("loading valve flags - {}".format(",".join(valve_flags_attrs)))
            self._load_valve_flags(manager, valve_flags_attrs)

    # loaders
    def _load_flags(self, manager, flags):
        for f in flags:
            self.info("loading {}".format(f))
            manager.add_flag(f)

    def _load_timed_flags(self, manager, flags):
        for f in flags:
            self.info("loading {}".format(f))
            manager.add_timed_flag(f)

    def _load_valve_flags(self, manager, flags):
        for f, v in flags:
            self.info("loading {}, valves={}".format(f, v))
            manager.add_valve_flag(f, v)

    def _load_devices(
        self,
        manager,
        name,
        devices,
        plugin_name,
    ):
        """ """
        devs = []
        if manager is None:
            return

        for device in devices:
            if not device:
                continue

            pdev = self._parser.get_device(name, device, plugin_name, element=True)

            dev_class = pdev.find("klass")
            if dev_class is not None:
                dev_class = dev_class.text.strip()

            try:
                dev = getattr(manager, device)
                if dev is None:
                    dev = manager.create_device(device, dev_class=dev_class)
                else:
                    if dev_class and dev.__class__.__name__ != dev_class:
                        dev = manager.create_device(
                            device, dev_class=dev_class, obj=dev
                        )

            except AttributeError:
                dev = manager.create_device(device, dev_class=dev_class)

            if dev is None:
                self.warning("No device for {}".format(device))
                continue

            self.info("loading {}".format(dev.name))

            dev.application = self.application
            if dev.load():
                # register the device
                if self.application is not None:
                    # display with the HardwareManager
                    self.info("Register device name={}, {}".format(dev.name, dev))
                    self.application.register_service(
                        ICoreDevice, dev, {"display": True}
                    )

                devs.append(dev)
                self.info("opening {}".format(dev.name))
                if not dev.open(prefs=self.device_prefs):
                    self.info("failed connecting to {}".format(dev.name))
            else:
                self.info("failed loading {}".format(dev.name))

        for od in devs:
            self.info("Initializing {}".format(od.name))
            result = od.initialize(progress=self._pd)
            if result is not True:
                self.warning("Failed setting up communications to {}".format(od.name))
                od.set_simulation(True)

            elif result is None:
                self.debug(
                    "{} initialize function does not return a boolean".format(od.name)
                )
                raise NotImplementedError

            od.application = self.application
            od.post_initialize()

            manager.devices.append(od)

    def _load_managers(self, manager, managers, plugin_name):
        for mi in managers:
            man = None

            self.info("load {}".format(mi))

            try:
                man = getattr(manager, mi)
                if man is None:
                    man = manager.create_manager(mi)
            except AttributeError as e:
                self.warning(e)
                try:
                    man = manager.create_manager(mi)
                except InitializerError:
                    import traceback

                    traceback.print_exc()

            if man is None:
                self.debug("trouble creating manager {}".format(mi))
                continue

            if self.application is not None:
                # register this manager as a service
                man.application = self.application
                self.application.register_service(type(man), man)

            man.load()

            element = self._get_manager(mi, plugin_name)
            if not globalv.ignore_initialization_required:
                if not self._check_required(element):
                    return False

            self._load_elements(element, man, mi, plugin_name)

            self.info("finish {} loading".format(mi))
            man.finish_loading()

    # helpers
    def _setup_progress(self, n):
        """
        n: int, initialize progress dialog with n steps

        return a myProgressDialog object
        """
        pd = myProgressDialog(
            max=n, message="Welcome", position=(100, 100), size=(500, 50)
        )
        self._pd = pd
        self._pd.open()
        return pd

    def _check_required(self, subtree):
        # check the subtree has all required devices enabled
        devs = self._parser.get_devices(subtree, all_=True, element=True)
        for di in devs:
            required = True
            req = self._parser.get_parameter(di, "required")
            if req:
                required = to_bool(req)

            enabled = to_bool(di.get("enabled"))

            if required and not enabled:
                name = di.text.strip().upper()
                msg = """Device {} is REQUIRED but is not ENABLED.

Do you want to quit to enable {} in the Initialization File?""".format(
                    name, name
                )
                result = self.confirmation_dialog(msg, title="Quit Pychron")
                if result:
                    raise InitializerError()

        return True

    def _get_manager(self, name, plugin_name):
        parser = self._parser
        man = parser.get_manager(name, plugin_name)
        return man

    def _get_plugin(self, name):
        parser = self._parser
        mp = parser.get_plugin(name)
        return mp

    def _get_nsteps(self, plugin_name):
        parser = self._parser
        mp = self._get_plugin(plugin_name)

        ns = 0
        if mp is not None:
            ns += 2 * (len(parser.get_managers(mp)) + 1)
            ns += 3 * (len(parser.get_devices(mp)) + 1)
            ns += len(parser.get_flags(mp)) + 1
            ns += len(parser.get_timed_flags(mp)) + 1

        return ns


# ========================= EOF ===================================
