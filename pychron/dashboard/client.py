# ===============================================================================
# Copyright 2013 Jake Ross
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
from __future__ import absolute_import
import time

from traits.api import HasTraits, List, Float, Property, Str, Bool, Dict

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import convert_timestamp
from pychron.dashboard.messages import (
    CRITICAL_KIND,
    ERROR_KIND,
    HEARTBEAT_KIND,
    TIMEOUT_KIND,
    VALUE_KIND,
    WARNING_KIND,
    decode_config_payload,
    decode_event_message,
    decode_legacy_config_payload,
)
from pychron.messaging.notify.subscriber import Subscriber


class DashboardValue(HasTraits):
    name = Str
    tag = Str
    units = Str
    value = Float
    last_time = Float
    last_time_str = Property(depends_on="last_time")
    timed_out = Bool
    stale = Bool

    def _get_last_time_str(self):
        r = ""
        if self.last_time:
            r = convert_timestamp(self.last_time)

        return r

    def handle_update(self, new):
        if new == "timeout":
            self.handle_timeout()

        else:
            self.value = float(new)
            self.last_time = time.time()
            self.timed_out = False
            self.stale = False

    def handle_timeout(self):
        if not self.timed_out:
            self.timed_out = True
        self.stale = True
        self.last_time = time.time()


class DashboardClient(Subscriber):
    values = List
    error_flag = Str
    last_config_error = Str
    active_alert = Str
    active_alerts = List(Str)
    server_url = Property(depends_on="host,port")
    value_map = Dict

    def _get_server_url(self):
        return "{}:{}".format(self.host, self.port)

    def load_configuration(self):
        self.config_loaded = False
        self.last_config_error = ""

        config = self.request("config_json")
        if config:
            try:
                payload = decode_config_payload(config)
                self._load_configuration_payload(payload)
                self.config_loaded = True
                return
            except (TypeError, ValueError) as exc:
                self.last_config_error = str(exc)

        legacy = self.request("config")
        if legacy:
            self._load_configuration(legacy)

    def set_error_flag(self, new):
        self.error_flag = new

    def _load_configuration(self, config):
        try:
            data = decode_legacy_config_payload(config)
        except (ImportError, TypeError, ValueError):
            self.last_config_error = "Could not load legacy dashboard configuration"
            self.warning("Could not load configuration: {}".format(config))
            return

        vs = []
        value_map = {}
        for di in data:
            pv = DashboardValue(name=di.name, tag=di.tag, units=getattr(di, "units", ""))
            vs.append(pv)
            value_map[di.tag] = pv
            self.subscribe(di.tag, pv.handle_update, verbose=True)

        self.subscribe("error", self.set_error_flag, verbose=True)
        self.values = vs
        self.value_map = value_map
        self.config_loaded = True
        self.connection_state = "connected"

    def _load_configuration_payload(self, payload):
        devices = payload.get("devices", ())
        vs = []
        value_map = {}
        self.subscribe("dashboard", self._handle_dashboard_message, verbose=False)
        for device in devices:
            for value in device.get("values", ()):
                pv = DashboardValue(
                    name=value["name"],
                    tag=value["tag"],
                    units=value.get("units", ""),
                )
                vs.append(pv)
                value_map[pv.tag] = pv

        self.values = vs
        self.value_map = value_map
        self.config_loaded = True
        self.connection_state = "connected"
        self.last_config_error = ""

    def _handle_dashboard_message(self, payload):
        event = decode_event_message("dashboard {}".format(payload))
        if event is None:
            return

        kind = event.get("kind")
        self.last_message_time = time.time()
        if kind == HEARTBEAT_KIND:
            self.last_heartbeat_time = time.time()
            self.connection_state = "connected"
            return

        if kind == VALUE_KIND:
            value = self.value_map.get(event.get("tag"))
            if value is not None:
                value.handle_update(event.get("value"))
        elif kind == TIMEOUT_KIND:
            value = self.value_map.get(event.get("tag"))
            if value is not None:
                value.handle_timeout()
        elif kind in (WARNING_KIND, CRITICAL_KIND, ERROR_KIND):
            message = event.get("message", "")
            self.active_alert = message
            self.error_flag = message if kind in (CRITICAL_KIND, ERROR_KIND) else self.error_flag
            if message and message not in self.active_alerts:
                self.active_alerts.append(message)


# ============= EOF =============================================
