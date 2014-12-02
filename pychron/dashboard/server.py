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
from traits.api import Instance, on_trait_change, List, Str
# ============= standard library imports ========================
from _socket import gethostname, gethostbyname
from threading import Thread
import os
import pickle
import time
# ============= local library imports  ==========================
from pychron.dashboard.constants import PUBLISH, WARN, CRITICAL
from pychron.dashboard.db_manager import DashboardDBManager
from pychron.dashboard.device import DashboardDevice
from pychron.globals import globalv
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.core.helpers.filetools import to_bool
from pychron.hardware.dummy_device import DummyDevice
from pychron.loggable import Loggable
from pychron.messaging.notify.notifier import Notifier
from pychron.paths import paths
from pychron.core.xml.xml_parser import XMLParser


class DashboardServer(Loggable):
    devices = List
    selected_device = Instance(DashboardDevice)
    db_manager = Instance(DashboardDBManager, ())
    notifier = Instance(Notifier, ())
    emailer = Instance('pychron.social.emailer.Emailer')

    url = Str
    use_db = False
    _alive = False

    def activate(self):
        self.setup_notifier()

        self._load_devices()
        if self.devices:
            if self.use_db:
                self.setup_database()
            self.start_poll()

    def deactivate(self):
        if self.use_db:
            self.db_manager.stop()

    def setup_database(self):
        if self.use_db:
            self.db_manager.start()

    def setup_notifier(self):
        parser = self._get_parser()

        port = 8100
        elem = parser.get_elements('port')
        if elem is not None:
            try:
                port = int(elem[0].text.strip())
            except ValueError:
                pass

        self.notifier.port = port
        host = gethostbyname(gethostname())
        self.url = '{}:{}'.format(host, port)
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

        parser = self._get_parser()
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

                func_name = self._get_xml_value(v, 'func', 'get')
                period = self._get_xml_value(v, 'period', 60)

                if not period == 'on_change':
                    try:
                        period = int(period)
                    except ValueError:
                        period = 60

                enabled = to_bool(self._get_xml_value(v, 'enabled', False))
                timeout = self._get_xml_value(v, 'timeout', 0)
                pv = d.add_value(n, tag, func_name, period, enabled, timeout)

                def set_nfail(elem, kw):
                    nfail = elem.find('nfail')
                    if nfail is not None:
                        try:
                            kw['nfail']=int(nfail.text.strip())
                        except ValueError:
                            pass

                conds = v.find('conditionals')
                if conds is not None:
                    for warn in conds.findall('warn'):
                        teststr = warn.text.strip()
                        kw = {'teststr': teststr}
                        set_nfail(warn, kw)
                        d.add_conditional(pv, WARN, **kw)

                    for critical in conds.findall('critical'):
                        teststr = critical.text.strip()

                        kw = {'teststr': teststr}
                        set_nfail(critical, kw)

                        script = critical.find('script')
                        if script is not None:
                            kw['script'] = script.text.strip()

                        d.add_conditional(pv, CRITICAL, **kw)

            d.setup_graph()
            ds.append(d)

        self.devices = ds

    def _get_xml_value(self, elem, tag, default):
        ret = default

        tt = elem.find(tag)
        if tt is not None:
            ret = tt.text.strip()

        return ret

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

    def _get_parser(self):
        p = os.path.join(paths.setup_dir, 'dashboard.xml')
        parser = XMLParser(p)
        return parser

    def _set_error_flag(self, obj, msg):
        self.notifier.send_message('error {}'.format(msg))

    # handlers
    @on_trait_change('devices:publish_event')
    def _handle_publish(self, obj, name, old, new):
        action, emails, message = new.split('|')
        self.notifier.send_message(message)
        if action == WARN:
            if self.emailer and emails:
                emails = emails.split(',')
                self.emailer.send_message(emails, message)
        elif action == CRITICAL:
            self._set_error_flag(obj, message)
            if self.emailer and emails:
                emails = emails.split(',')
                self.emailier.send_message(emails, message)

        if self.use_db:
            self.db_manager.publish_device(obj)

    # @on_trait_change('devices:error_event')
    # def _handle_error(self, obj, name, old, new):
    # self._set_error_flag(obj, new)
    # self.notifier.send_message(new)

    @on_trait_change('devices:values:+')
    def _value_changed(self, obj, name, old, new):
        if name.startswith('last_'):
            return

        print obj, name, old, new


# ============= EOF =============================================
