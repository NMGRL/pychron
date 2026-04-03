# ===============================================================================
# Copyright 2013 Jake Ross
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
from apptools.preferences.preference_binding import bind_preference
from traits.api import Instance, on_trait_change, List, Button, Bool, Str, Float, Property

# ============= standard library imports ========================
from threading import Thread
import os
import time

# ============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import convert_timestamp
from pychron.dashboard.config import DashboardConfigError, load_dashboard_config
from pychron.dashboard.constants import CRITICAL, NOERROR, WARNING
from pychron.dashboard.device import DashboardDevice
from pychron.dashboard.messages import (
    CONFIG_KIND,
    CRITICAL_KIND,
    ERROR_KIND,
    HEARTBEAT_KIND,
    TIMEOUT_KIND,
    VALUE_KIND,
    WARNING_KIND,
    encode_config_payload,
    encode_event,
    encode_legacy_config_payload,
    make_event,
    make_legacy_error_message,
    make_legacy_value_message,
)
from pychron.globals import globalv
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.core.helpers.filetools import add_extension
from pychron.hardware.dummy_device import DummyDevice
from pychron.loggable import Loggable
from pychron.messaging.notify.notifier import Notifier
from pychron.paths import paths
from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript


class DashboardServer(Loggable):
    devices = List
    values = List
    config_source = Str
    config_error = Str
    health_state = Str("stopped")
    notifier_bound = Bool(False)
    config_loaded = Bool(False)
    poll_thread_active = Bool(False)
    last_publish_time = Float
    last_publish_time_str = Property(depends_on="last_publish_time")
    last_device_error = Str
    selected_device = Instance(DashboardDevice)
    extraction_line_manager = Instance(
        "pychron.extraction_line.extraction_line_manager.ExtractionLineManager"
    )
    clear_button = Button("Clear")

    notifier = Instance(Notifier, ())
    emailer = Instance("pychron.social.emailer.Emailer")
    labspy_client = Instance("pychron.labspy.client.LabspyClient")

    use_db = False
    _alive = False
    _config = None
    _poll_thread = None
    _last_heartbeat = 0

    def _get_last_publish_time_str(self):
        if self.last_publish_time:
            return convert_timestamp(self.last_publish_time)
        return ""

    def bind_preferences(self):
        bind_preference(
            self.notifier, "enabled", "pychron.dashboard.server.notifier_enabled"
        )

    def activate(self):
        if self._alive:
            return

        emailer = self.application.get_service("pychron.social.emailer.Emailer")
        self.emailer = emailer

        if not self.extraction_line_manager:
            self.warning_dialog(
                "Extraction Line Plugin not initialized. Will not be able to take valve actions"
            )
        try:
            self.load_devices()
        except DashboardConfigError as exc:
            self.config_error = "\n".join(exc.issues)
            self.health_state = "config_error"
            self.warning_dialog(self.config_error)
            return

        self.setup_notifier()

        if self.devices:
            self.start_poll()

        if self.labspy_client:
            self.labspy_client.start()

    def deactivate(self):
        self._alive = False
        self.poll_thread_active = False
        self.health_state = "stopped"
        self.notifier_bound = False
        self.notifier.close()

    # def deactivate(self):
    # if self.use_db:
    # self.db_manager.stop()

    # def setup_database(self):
    # if self.use_db:
    # self.db_manager.start()

    def setup_notifier(self):
        if self.notifier.enabled:
            self.notifier.port = self._config.port if self._config else 8100
            self.notifier.add_request_handler("config", self._handle_config)
            self.notifier.add_request_handler("config_json", self._handle_config_json)
            self.notifier.setup(self.notifier.port)
            self.notifier_bound = True
        else:
            self.notifier_bound = False

    def start_poll(self):
        self.info("starting dashboard poll")
        self._alive = True
        self.health_state = "polling"
        self._poll_thread = Thread(name="poll", target=self._poll)
        self._poll_thread.setDaemon(1)
        self._poll_thread.start()
        self.poll_thread_active = True

    def load_devices(self):
        self._config = load_dashboard_config(
            paths.root_dir, script_validator=self._validate_script
        )
        self.config_source = self._config.source_path
        self.config_error = ""
        self.config_loaded = True
        self.health_state = "configured"

        app = self.application
        ds = []
        self.values = []
        for spec in self._config.devices:
            name = spec.name
            dev_name = spec.device
            device = app.get_service(ICoreDevice, query='name=="{}"'.format(dev_name))
            if device is None:
                self.warning('no device named "{}" available'.format(dev_name))
                self.last_device_error = 'No device named "{}" available'.format(
                    dev_name
                )
                if globalv.dashboard_simulation:
                    device = DummyDevice(name=dev_name)
                else:
                    continue

            d = DashboardDevice(name=name, use=spec.enabled, hardware_device=device)
            for value_spec in spec.values:
                if value_spec.bindname and not hasattr(device, value_spec.bindname):
                    msg = '{} missing bind "{}" for dashboard value "{}"'.format(
                        dev_name, value_spec.bindname, value_spec.name
                    )
                    self.last_device_error = msg
                    self.warning(msg)
                    continue

                pv = d.add_value(
                    name=value_spec.name,
                    tag=value_spec.tag,
                    func_name=value_spec.func_name,
                    period=value_spec.period,
                    enabled=value_spec.enabled,
                    threshold=value_spec.threshold,
                    units=value_spec.units,
                    timeout=value_spec.timeout,
                    record=value_spec.record,
                    bindname=value_spec.bindname,
                )
                self.values.append(pv)
                for conditional in value_spec.conditionals:
                    d.add_conditional(
                        pv,
                        conditional.severity,
                        teststr=conditional.teststr,
                        nfail=conditional.nfail,
                        script=conditional.script,
                        emails=conditional.emails,
                    )

            d.setup_graph()
            ds.append(d)

        self.devices = ds

    def _handle_config(self):
        """
        called by subscribers requesting the dashboard configuration

        return a pickled dictionary string
        """
        config = [pv for dev in self.devices for pv in dev.values]

        return encode_legacy_config_payload(config)

    def _handle_config_json(self):
        return encode_config_payload(self._config)

    def _poll(self):
        if not self.devices:
            self.poll_thread_active = False
            return

        if any((v.period == "on_change" for dev in self.devices for v in dev.values)):
            mperiod = 1
        else:
            mperiod = min((v.period for dev in self.devices for v in dev.values))

        self.debug("min period {}".format(mperiod))
        while self._alive:
            sst = time.time()
            self._publish_heartbeat()
            # self.debug('============= poll iteration start ============')
            for dev in self.devices:
                if not dev.use:
                    continue

                dev.trigger()

            st = time.time()
            pp = mperiod - (st - sst)
            if pp >= 3:
                self.debug("sleeping for {}".format(pp))

            while self._alive:
                if time.time() - st >= pp:
                    break
                time.sleep(0.1)

        self.poll_thread_active = False
        self.health_state = "stopped"

            # dur = time.time() - sst
            # self.debug('============= poll iteration finished dur={:0.1f}============'.format(dur))

    # def _set_error_flag(self, obj, msg):
    # self.notifier.send_message('error {}'.format(msg))

    def _validate_script(self, script_name):
        if self.extraction_line_manager:
            script = self._script_factory(script_name)
            if script:
                return script.syntax_ok()
        else:
            self.warning(
                "Extraction Line Manager not available. Cannot execute pyscript"
            )

    def _script_factory(self, script_name):
        if os.path.isfile(
            os.path.join(paths.extraction_dir, add_extension(script_name, ".py"))
        ):
            runner = self.application.get_service(
                "pychron.extraction_line.ipyscript_runner.IPyScriptRunner"
            )
            script = ExtractionPyScript(
                root=paths.extraction_dir,
                name=script_name,
                manager=self.extraction_line_manager,
                allow_lock=True,
                runner=runner,
            )
            return script

    def _do_script(self, script_name):
        self.info('doing script "{}"'.format(script_name))
        script = self._script_factory(script_name)
        if script:
            script.execute()

    def _send_email(self, emails, message):
        if self.emailer and emails:
            emails = emails.split(",")
            self.emailer.send_message(emails, message)

    def _get_device(self, name):
        return next((di for di in self.devices if di.name == name), None)

    def _update_labspy_device(self, dev, tag, val, units):
        if self.labspy_client:
            self.labspy_client.add_measurement(dev, tag, val, units)

    def _update_labspy_error(self, error):
        if self.labspy_client:
            self.labspy_client.update_status(error=error)

    def _publish_event(self, event, legacy_message=None):
        self.notifier.send_message(encode_event(event), verbose=False)
        self.last_publish_time = time.time()
        if legacy_message:
            self.notifier.send_message(legacy_message)

    def _publish_heartbeat(self):
        if time.time() - self._last_heartbeat < 2:
            return

        self._last_heartbeat = time.time()
        self._publish_event(
            make_event(
                HEARTBEAT_KIND,
                source=self.config_source,
                state=self.health_state,
            )
        )

    # handlers
    def _clear_button_fired(self):
        self.info("Clear Dashboard errors")
        fname = lambda x: "Warning" if x == WARNING else "Critical"
        for d in self.devices:
            for pv in d.values:
                if pv.flag:
                    self.info("clearing {} flag for {}".format(fname(pv.flag), pv.name))
                pv.flag = NOERROR

    @on_trait_change("devices:conditional_event")
    def _handle_conditional(self, obj, name, old, new):
        action, script, emails, message = new.split("|")
        if action == WARNING:
            self._publish_event(
                make_event(WARNING_KIND, device=obj.name, message=message),
                legacy_message=message,
            )
            self._send_email(emails, message)
        elif action == CRITICAL:
            self.notifier.send_message(message)
            self._publish_event(
                make_event(
                    CRITICAL_KIND,
                    device=obj.name,
                    message=message,
                    script=script,
                ),
                legacy_message=make_legacy_error_message(message),
            )
            self._do_script(script)
            self._send_email(emails, message)
            self._update_labspy_error(message)

    @on_trait_change("devices:update_value_event")
    def _handle_publish(self, obj, name, old, new):
        value_name, value, units = new
        pv = next((item for item in obj.values if item.name == value_name), None)
        tag = pv.tag if pv is not None else "<{},{}>".format(obj.name, value_name)
        self._publish_event(
            make_event(
                VALUE_KIND,
                device=obj.name,
                name=value_name,
                tag=tag,
                value=value,
                units=units,
            ),
            legacy_message=make_legacy_value_message(tag, value),
        )
        self._update_labspy_device(obj.name, value_name, value, units)

    @on_trait_change("devices:timeout_event")
    def _handle_timeout(self, obj, name, old, new):
        value_name, tag = new
        self._publish_event(
            make_event(TIMEOUT_KIND, device=obj.name, name=value_name, tag=tag)
        )
        # self._update_labspy_devices()
        # if self.use_db:
        #     self.db_manager.publish_device(obj)

        # @on_trait_change('devices:error_event')
        # def _handle_error(self, obj, name, old, new):
        # self._set_error_flag(obj, new)
        # self.notifier.send_message(new)

        # @on_trait_change('devices:values:+')
        # def _value_changed(self, obj, name, old, new):
        #     if name.startswith('last_'):
        #         return
        #
        #     print obj, name, old, new


# ============= EOF =============================================
# def _load_devices(self):
# # read devices from config
# app = self.application
#
# parser = get_parser()
# ds = []
# for dev in parser.get_elements('device'):
# name = dev.text.strip()
#
#         dname = dev.find('name')
#         if dname is None:
#             self.warning('no device name for {}. use a <name> tag'.format(name))
#             continue
#
#         dev_name = dname.text.strip()
#         device = None
#         if app:
#             # get device from app
#             device = app.get_service(ICoreDevice,
#                                      query='name=="{}"'.format(dev_name))
#             if device is None:
#                 self.warning('no device named "{}" available'.format(dev_name))
#                 if globalv.dashboard_simulation:
#                     device = DummyDevice(name=dev_name)
#                 else:
#                     continue
#
#         enabled = dev.find('use')
#         if enabled is not None:
#             enabled = to_bool(enabled.text.strip())
#
#         d = DashboardDevice(name=name, use=bool(enabled),
#                             _device=device)
#
#         for v in dev.findall('value'):
#
#             n = v.text.strip()
#             tag = '<{},{}>'.format(name, n)
#
#             func_name = get_xml_value(v, 'func', 'get')
#             period = get_xml_value(v, 'period', 60)
#             if not period == 'on_change':
#                 try:
#                     period = int(period)
#                 except ValueError:
#                     period = 60
#
#             enabled = to_bool(get_xml_value(v, 'enabled', False))
#             timeout = get_xml_value(v, 'timeout', 120)
#             threshold = float(get_xml_value(v, 'change_threshold', 1e-10))
#             units = get_xml_value(v, 'units', '')
#
#             pv = d.add_value(n, tag, func_name, period, enabled, threshold,
#                              units, timeout)
#
#             def set_nfail(elem, kw):
#                 nfail = elem.find('nfail')
#                 if nfail is not None:
#                     try:
#                         kw['nfail'] = int(nfail.text.strip())
#                     except ValueError:
#                         pass
#
#             conds = v.find('conditionals')
#             if conds is not None:
#                 for warn in conds.findall('warn'):
#                     teststr = warn.text.strip()
#                     kw = {'teststr': teststr}
#                     set_nfail(warn, kw)
#                     d.add_conditional(pv, WARNING, **kw)
#
#                 for critical in conds.findall('critical'):
#                     teststr = critical.text.strip()
#
#                     kw = {'teststr': teststr}
#                     set_nfail(critical, kw)
#
#                     script = critical.find('script')
#                     if script is not None:
#                         sname = script.text.strip()
#                         if self._validate_script(sname):
#                             kw['script'] = sname
#                         else:
#                             self.warning('Failed to add condition "{}". '
#                                          'Invalid script "scripts/extraction/{}"'.format(teststr, sname))
#                             continue
#
#                     d.add_conditional(pv, CRITICAL, **kw)
#
#         d.setup_graph()
#         ds.append(d)
#
#     self.devices = ds
