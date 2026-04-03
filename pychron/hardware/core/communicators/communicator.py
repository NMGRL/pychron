# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
from __future__ import absolute_import

# ============= local library imports  ==========================
import binascii
import codecs
import os
import time
from threading import RLock

from pychron.headless_config_loadable import HeadlessConfigLoadable


def prep_str(s):
    """ """
    ns = ""
    if s is None:
        s = ""
    for c in s:
        oc = ord(c)
        if not 0x20 <= oc <= 0x7E:
            c = "[{:02d}]".format(ord(c))
        ns += c
    return ns


def convert(re):
    if re is not None:
        if isinstance(re, bytes):
            try:
                re = re.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    re = codecs.decode(re, "hex")
                except binascii.Error:
                    re = "".join(("[{}]".format(str(b)) for b in re))

        return re


def replace_eol_func(s):
    s = convert(s)
    if s is not None:
        s = s.replace("\r", "[13]")
        s = s.replace("\n", "[10]")
        return s


def remove_eol_func(re):
    """ """
    re = convert(re)
    if re is not None:
        return re.strip()


def process_response(re, replace=None, remove_eol=True):
    """ """
    if remove_eol:
        re = remove_eol_func(re)

    if isinstance(replace, tuple):
        re = re.replace(replace[0], replace[1])

    return re


class Communicator(HeadlessConfigLoadable):
    """
    Base class for all communicators, e.g. SerialCommunicator, EthernetCommunicator
    """

    _lock = None
    simulation = True
    write_terminator = chr(13)  # '\r'
    read_terminator = ""
    handle = None
    scheduler = None
    address = None
    backend = "real"
    transport_adapter = None
    fixture_path = None
    scenario_path = None
    simulator_protocol = None
    simulator_seed = 1
    replay_mode = "strict"
    fault_names = None
    _comms_report_attrs = None

    def __init__(self, *args, **kw):
        """ """
        super(Communicator, self).__init__(*args, **kw)
        self._lock = RLock()

    def load(self, config, path):
        self.set_attribute(
            config,
            "verbose",
            "Communications",
            "verbose",
            default=False,
            optional=True,
            cast="boolean",
        )
        self.set_attribute(
            config,
            "write_terminator",
            "Communications",
            "write_terminator",
            default=chr(13),
            optional=True,
        )

        self.set_attribute(
            config,
            "read_terminator",
            "Communications",
            "read_terminator",
            default="",
            optional=True,
        )

        if self.write_terminator == "chr(10)":
            self.write_terminator = chr(10)
        if self.write_terminator == "chr(0)":
            self.write_terminator = chr(0)
        if self.write_terminator == "CRLF":
            self.write_terminator = "\r\n"

        if self.read_terminator == "chr(10)":
            self.read_terminator = chr(10)
        if self.read_terminator == "chr(0)":
            self.read_terminator = chr(0)
        if self.read_terminator == "CRLF":
            self.read_terminator = "\r\n"

        self.backend = self.config_get(
            config, "Communications", "backend", optional=True, default="real"
        )
        self.fixture_path = self.config_get(
            config, "Communications", "fixture_path", optional=True
        )
        self.scenario_path = self.config_get(
            config, "Communications", "scenario_path", optional=True
        )
        self.simulator_protocol = self.config_get(
            config, "Communications", "simulator_protocol", optional=True
        )
        self.simulator_seed = self.config_get(
            config,
            "Communications",
            "simulator_seed",
            cast="int",
            optional=True,
            default=1,
        )
        self.replay_mode = self.config_get(
            config, "Communications", "replay_mode", optional=True, default="strict"
        )
        faults = self.config_get(config, "Communications", "faults", optional=True)
        if faults:
            self.fault_names = [fault.strip() for fault in faults.split(",") if fault.strip()]

        self._configure_transport_backend(path)
        return True

    def report(self):
        self.debug("============ Communications Report ==============")
        self._generate_comms_report()
        self.debug("=================================================")

    def close(self):
        if self.transport_adapter is not None:
            self.transport_adapter.close()

    def delay(self, ms):
        """
        sleep ms milliseconds
        """
        time.sleep(ms / 1000.0)

    def ask(self, *args, **kw):
        pass

    def tell(self, *args, **kw):
        pass

    def write(self, *args, **kw):
        pass

    def read(self, *args, **kw):
        pass

    def set_transport_adapter(self, adapter, backend=None):
        self.transport_adapter = adapter
        if backend is not None:
            self.backend = backend
        if adapter is not None:
            self.simulation = True
        return adapter

    def clear_transport_adapter(self):
        self.transport_adapter = None
        self.backend = "real"

    def has_transport_adapter(self):
        return self.transport_adapter is not None

    def _configure_transport_backend(self, path):
        if self.backend in (None, "", "real"):
            return

        if self.transport_adapter is not None:
            return

        try:
            from pychron.hardware.core.simulation.factory import build_transport_adapter

            self.set_transport_adapter(
                build_transport_adapter(
                    self.backend,
                    transport_kind=self._transport_kind(),
                    fixture_path=self._resolve_backend_path(path, self.fixture_path),
                    scenario_path=self._resolve_backend_path(path, self.scenario_path),
                    mode=self.replay_mode,
                    protocol_name=self.simulator_protocol,
                    seed=self.simulator_seed,
                    fault_names=self.fault_names,
                ),
                backend=self.backend,
            )
        except BaseException:
            self.warning(
                "Failed configuring transport backend '{}'".format(self.backend)
            )
            self.debug_exception()

    def _resolve_backend_path(self, config_path, value):
        if not value:
            return
        if os.path.isabs(value):
            return value
        root = config_path
        if config_path and os.path.isfile(config_path):
            root = os.path.dirname(config_path)
        return os.path.join(root or "", value)

    def _transport_kind(self):
        return self.__class__.__name__.replace("Communicator", "").lower()

    def log_tell(self, cmd, info=None):
        """
        Log command as and INFO message
        """
        cmd = remove_eol_func(cmd)
        ncmd = prep_str(cmd)

        if ncmd:
            cmd = ncmd

        if info is not None:
            msg = "{}    {}".format(info, cmd)
        else:
            msg = cmd

        self.info(msg)

    def log_response(self, cmd, re, info=None):
        """
        Log command and response as an INFO message
        """
        cmd = replace_eol_func(cmd)

        ncmd = prep_str(cmd)
        if ncmd:
            cmd = ncmd

        if re and len(re) > 100:
            re = "{}...".format(re[:97])

        if info and info != "":
            msg = "{}    {} ===>> {}".format(info, cmd, re)
        else:
            msg = "{} ===>> {}".format(cmd, re)

        self.info(msg)

    @property
    def lock(self):
        return self._lock

    # private
    def _get_report_value(self, key):
        c = getattr(self, key)
        value = "---"
        return c, value

    def _generate_comms_report(self):
        if self._comms_report_attrs:
            self.debug("{:<10s} {:<20s}          Value".format("Param:", "Config:"))
            for key in self._comms_report_attrs:
                c, value = self._get_report_value(key)
                self.debug(
                    "{:<10s} {:<30s} {}".format(
                        "{}:".format(key.capitalize()), str(c), value
                    )
                )
        else:
            self.debug("Comms report not yet implemented")


# ============= EOF ====================================
