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
from traits.api import Instance, on_trait_change, List, Str, Button
# ============= standard library imports ========================
from _socket import gethostname, gethostbyname
from threading import Thread
import os
import pickle
import time
# ============= local library imports  ==========================
from pychron.dashboard.constants import CRITICAL, NOERROR, WARNING
from pychron.dashboard.db_manager import DashboardDBManager
from pychron.dashboard.device import DashboardDevice
from pychron.globals import globalv
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.core.helpers.filetools import to_bool, add_extension
from pychron.hardware.dummy_device import DummyDevice
from pychron.loggable import Loggable
from pychron.messaging.notify.notifier import Notifier
from pychron.paths import paths
from pychron.core.xml.xml_parser import XMLParser
from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript


def get_parser():
    p = os.path.join(paths.setup_dir, 'dashboard.xml')
    parser = XMLParser(p)
    return parser


def get_xml_value(elem, tag, default):
    ret = default

    tt = elem.find(tag)
    if tt is not None:
        ret = tt.text.strip()

    return ret


class DashboardServer(Loggable):
    devices = List
    selected_device = Instance(DashboardDevice)
    # db_manager = Instance(DashboardDBManager, ())
    extraction_line_manager = Instance('pychron.extraction_line.extraction_line_manager.ExtractionLineManager')
    clear_button = Button('Clear')

    notifier = Instance(Notifier, ())
    emailer = Instance('pychron.social.emailer.Emailer')
    labspy_client = None

    # url = Str
    use_db = False
    _alive = False

    def activate(self):
        if not self.extraction_line_manager:
            self.warning_dialog('Extraction Line Plugin not initialized. Will not be able to take valve actions')

        self.setup_notifier()

        self._load_devices()
        if self.devices:
            # if self.use_db:
            # self.setup_database()
            self.start_poll()

    def deactivate(self):
        pass

    # def deactivate(self):
    # if self.use_db:
    # self.db_manager.stop()

    # def setup_database(self):
    #     if self.use_db:
    #         self.db_manager.start()

    def setup_notifier(self):
        parser = get_parser()

        port = 8100
        elem = parser.get_elements('port')
        if elem is not None:
            try:
                port = int(elem[0].text.strip())
            except ValueError:
                pass

        self.notifier.port = port
        host = gethostbyname(gethostname())
        # self.url = '{}:{}'.format(host, port)
        # add a config request handler
        self.notifier.add_request_handler('config', self._handle_config)

    def start_poll(self):
        self.info('starting dashboard poll')
        self._alive = True
        t = Thread(name='poll',
                   target=self._poll)

        t.setDaemon(1)
        t.start()

    def _load_devices(self):
        # read devices from config
        app = self.application

        parser = get_parser()
        ds = []
        for dev in parser.get_elements('device'):
            name = dev.text.strip()

            dname = dev.find('name')
            if dname is None:
                self.warning('no device name for {}. use a <name> tag'.format(name))
                continue

            dev_name = dname.text.strip()
            device = None
            if app:
                # get device from app
                device = app.get_service(ICoreDevice,
                                         query='name=="{}"'.format(dev_name))
                if device is None:
                    self.warning('no device named "{}" available'.format(dev_name))
                    if globalv.dashboard_simulation:
                        device = DummyDevice(name=dev_name)
                    else:
                        continue

            enabled = dev.find('use')
            if enabled is not None:
                enabled = to_bool(enabled.text.strip())

            d = DashboardDevice(name=name, use=bool(enabled),
                                _device=device)

            for v in dev.findall('value'):

                n = v.text.strip()
                tag = '<{},{}>'.format(name, n)

                func_name = get_xml_value(v, 'func', 'get')
                period = get_xml_value(v, 'period', 60)

                if not period == 'on_change':
                    try:
                        period = int(period)
                    except ValueError:
                        period = 60

                enabled = to_bool(get_xml_value(v, 'enabled', False))
                timeout = get_xml_value(v, 'timeout', 0)
                threshold = float(get_xml_value(v, 'change_threshold', 1e-10))
                pv = d.add_value(n, tag, func_name, period, enabled, threshold, timeout)

                def set_nfail(elem, kw):
                    nfail = elem.find('nfail')
                    if nfail is not None:
                        try:
                            kw['nfail'] = int(nfail.text.strip())
                        except ValueError:
                            pass

                conds = v.find('conditionals')
                if conds is not None:
                    for warn in conds.findall('warn'):
                        teststr = warn.text.strip()
                        kw = {'teststr': teststr}
                        set_nfail(warn, kw)
                        d.add_conditional(pv, WARNING, **kw)

                    for critical in conds.findall('critical'):
                        teststr = critical.text.strip()

                        kw = {'teststr': teststr}
                        set_nfail(critical, kw)

                        script = critical.find('script')
                        if script is not None:
                            sname = script.text.strip()
                            if self._validate_script(sname):
                                kw['script'] = sname
                            else:
                                self.warning('Failed to add condition "{}". '
                                             'Invalid script "scripts/extraction/{}"'.format(teststr, sname))
                                continue

                        d.add_conditional(pv, CRITICAL, **kw)

            d.setup_graph()
            ds.append(d)

        self.devices = ds

    def _handle_config(self):
        """
            return a pickled dictionary string
        """
        config = [pv for dev in self.devices
                  for pv in dev.values]

        return pickle.dumps(config)

    def _poll(self):

        mperiod = min([v.period for dev in self.devices
                       for v in dev.values])
        if mperiod == 'on_change':
            mperiod = 1

        self.debug('min period {}'.format(mperiod))
        while self._alive:
            for dev in self.devices:
                if not dev.use:
                    continue

                dev.trigger()
            time.sleep(mperiod)

    # def _set_error_flag(self, obj, msg):
    #     self.notifier.send_message('error {}'.format(msg))

    def _validate_script(self, script_name):
        script = self._script_factory(script_name)
        if script:
            return script.syntax_ok()

    def _script_factory(self, script_name):
        if os.path.isfile(os.path.join(paths.extraction_dir, add_extension(script_name, '.py'))):
            runner = self.application.get_service('pychron.extraction_line.ipyscript_runner.IPyScriptRunner')
            script = ExtractionPyScript(root=paths.extraction_dir,
                                        name=script_name,
                                        manager=self.extraction_line_manager,
                                        allow_lock=True,
                                        runner=runner)
            return script

    def _do_script(self, script_name):
        self.info('doing script "{}"'.format(script_name))
        script = self._script_factory(script_name)
        if script:
            script.execute()

    def _send_email(self, emails, message):
        if self.emailer and emails:
            emails = emails.split(',')
            self.emailer.send_message(emails, message)

    def _update_labspy_devices(self):
        if self.labspy_client:
            pass

    def _update_labspy_error(self, error):
        if self.labspy_client:
            self.labspy_client.update_state(error=error)

    # handlers
    def _clear_button_fired(self):
        self.info('Clear Dashboard errors')
        fname = lambda x: 'Warning' if x == WARNING else 'Critical'
        for d in self.devices:
            for pv in d.values:
                if pv.flag:
                    self.info('clearing {} flag for {}'.format(fname(pv.flag), pv.name))
                pv.flag = NOERROR

    @on_trait_change('devices:conditional_event')
    def _handle_conditional(self, obj, name, old, new):
        action, script, emails, message = new.split('|')

        self.notifier.send_message(message)
        if action == WARNING:
            self._send_email(emails, message)
        elif action == CRITICAL:
            self.notifier.send_message('error {}'.format(message))
            self._do_script(script)
            self._send_email(emails, message)


    @on_trait_change('devices:update_value_event')
    def _handle_publish(self, obj, name, old, new):
        self.notifier.send_message(new)
        self._update_labspy_devices()
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
