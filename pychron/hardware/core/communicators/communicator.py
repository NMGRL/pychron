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
import time
from threading import RLock

from pychron.headless_config_loadable import HeadlessConfigLoadable


def prep_str(s):
    """
    """
    ns = ''
    if s is None:
        s = ''
    for c in s:
        oc = ord(c)
        if not 0x20 <= oc <= 0x7E:
            c = '[{:02d}]'.format(ord(c))
        ns += c
    return ns


def convert(re):
    if re is not None:
        if isinstance(re, bytes):
            try:
                re = re.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    re = codecs.decode(re, 'hex')
                except binascii.Error:
                    re = ''.join(('[{}]'.format(str(b)) for b in re))

        return re


def replace_eol_func(s):
    s = convert(s)
    if s is not None:
        s = s.replace('\r', '[13]')
        s = s.replace('\n', '[10]')
        return s


def remove_eol_func(re):
    """
    """
    re = convert(re)
    if re is not None:
        return re.strip()


def process_response(re, replace=None, remove_eol=True):
    """
    """
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
    handle = None
    scheduler = None
    address = None

    def __init__(self, *args, **kw):
        """
        """
        super(Communicator, self).__init__(*args, **kw)
        self._lock = RLock()

    def load(self, config, path):
        self.set_attribute(config, 'verbose', 'Communications', 'verbose', default=False, optional=True, cast='boolean')
        self.set_attribute(config, 'write_terminator', 'Communications', 'write_terminator',
                           default=chr(13),
                           optional=True)

        if self.write_terminator == 'chr(10)':
            self.write_terminator = chr(10)
        if self.write_terminator == 'chr(0)':
            self.write_terminator = chr(0)

        return True

    def report(self):
        self.debug('============ Communications Report ==============')
        self._generate_comms_report()
        self.debug('=================================================')

    def close(self):
        pass

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

    def log_tell(self, cmd, info=None):
        """
        Log command as and INFO message
        """
        cmd = remove_eol_func(cmd)
        ncmd = prep_str(cmd)

        if ncmd:
            cmd = ncmd

        if info is not None:
            msg = '{}    {}'.format(info, cmd)
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
            re = '{}...'.format(re[:97])

        if info and info != '':
            msg = '{}    {} ===>> {}'.format(info, cmd, re)
        else:
            msg = '{} ===>> {}'.format(cmd, re)

        self.info(msg)

    @property
    def lock(self):
        return self._lock

    # private
    def _get_report_value(self, key):
        c = getattr(self, key)
        value = '---'
        return c, value

    def _generate_comms_report(self):
        if self._comms_report_attrs:
            self.debug('{:<10s} {:<20s}          Value'.format('Param:', 'Config:'))
            for key in self._comms_report_attrs:
                c, value = self._get_report_value(key)
                self.debug('{:<10s} {:<30s} {}'.format('{}:'.format(key.capitalize()),
                                                       str(c), value))
        else:
            self.debug('Comms report not yet implemented')
# ============= EOF ====================================
