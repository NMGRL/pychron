#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
import os
import tempfile

from pyface.message_dialog import warning
from traits.api import Str, Password


#============= standard library imports ========================
#============= local library imports  ==========================
import yaml
from pychron.experiment.experiment_executor import ExperimentExecutor
from pychron.loggable import Loggable

try:
    import paramiko
except ImportError:
    warning(None, 'Paramiko is required for SysLogger')


class SysLogger(Loggable):
    """
        sandboxing/proof of concept.
        build a context
        send to remote machine which parses and displays in django app
    """
    _ssh = None
    _sftp = None
    host = Str
    username = Str
    password = Password
    executor = ExperimentExecutor

    def trigger(self, lm):
        """
            assemble ctx from current executor obj

            write ctx as yaml

            send to remote machine
        """
        ex = self.executor
        ctx = {}
        ctx['is_alive'] = 'Yes' if ex.isAlive() else "No"

        cr = ''
        ca = ''

        crun = ex.measuring_run
        if crun:
            cr = crun.runid
            if ex.measuring:
                ca = 'Measurement'
            elif ex.extracting:
                ca = 'Extraction'

        ctx['current_run'] = cr
        ctx['current_activity'] = ca
        ctx['last_message'] = lm

        #enivornmentatl
        ctx['pneumatics'] = ex.monitor.pneumatics
        ctx['cTemp'] = ex.monitor.ctemp
        ctx['humidity'] = ex.monitor.humidity

        self._push(ctx)

    def _push(self, ctx):
        if self._sftp is None:
            self._new_ssh()

        localpath = self._make_ctx(ctx)
        remotepath = self._make_remotepath()

        sftp = self._sftp

        sftp.put(localpath, remotepath)

        #remove localpath
        os.unlink(localpath)

    def _make_remotepath(self):
        root = '~'
        ms = self.executor.experiment_queue.mass_spectrometer.lower()
        return os.path.join(root,
                            'sys_stats',
                            'logs',
                            '{}_syslog.yaml'.format(ms))

    def _make_ctx(self, ctx):
        p = tempfile.mkstemp()
        with open(p, 'w') as fp:
            yaml.dump(ctx, fp)
        return p

    def _new_ssh(self):
        ssh = paramiko.SSHClient()
        ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
        ssh.connect(self.host,
                    username=self.username,
                    password=self.password)
        self._ssh = ssh
        self._sftp = self._ssh.open_sftp()


#============= EOF =============================================

