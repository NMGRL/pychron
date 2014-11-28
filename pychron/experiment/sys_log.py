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

#============= enthought library imports =======================
from pychron.core.helpers.logger_setup import logging_setup
from pychron.core.ui import set_qt

set_qt()
logging_setup('sys_log')
from traits.api import Instance


#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.experiment.sys_log.sys_logger_database_adapter import SysLoggerDatabaseAdapter
from pychron.loggable import Loggable


class SysLogger(Loggable):
    db = Instance(SysLoggerDatabaseAdapter)

    def _db_default(self):
        db = SysLoggerDatabaseAdapter(kind='mysql',
                                      host='localhost',
                                      password='Argon',
                                      username='root',
                                      name='labspy')
        db.connect()
        return db

    def trigger(self, lm):
        pass

    def add_analysis(self, an):
        db = self.db
        db.add_analysis(an)


def get_test_an():
    class Record(object):
        analysis_type = 'unknown'

        def __init__(self, uuid):
            self.uuid = uuid

    from pychron.processing.processor import Processor

    man = Processor(bind=False, connect=False)
    man.db.trait_set(name='pychrondata_dev',
                     kind='mysql',
                     username='root',
                     password='Argon')
    man.connect()

    #pychrondata_dev
    uuids = ['e1a893fd-8c1a-427f-8b2f-8135c2471902',
             'f51a8ed2-5ab3-4df7-a7a9-84b3ea8a1555',
             'b86f523f-ac9c-4e77-b347-c404784b407a',
             'c6846df2-b808-4aab-8018-2c747c83aa9b']

    return man.make_analysis(Record(uuid=uuids[0]))


if __name__ == '__main__':
    s = SysLogger()

    an = get_test_an()
    s.add_analysis(an)
# try:
#     import paramiko
# except ImportError:
#     warning(None, 'Paramiko is required for SysLogger')
#
# class SysLogger(Loggable):
#     """
#         sandboxing/proof of concept.
#         build a context
#         send to remote machine which parses and displays in django app
#     """
#     _ssh = None
#     _sftp = None
#     host = Str
#     username = Str
#     password = Password
#     executor = ExperimentExecutor
#
#     def trigger(self, lm):
#         """
#             assemble ctx from current executor obj
#
#             write ctx as yaml
#
#             send to remote machine
#         """
#         ex = self.executor
#         ctx = {}
#         ctx['is_alive'] = 'Yes' if ex.isAlive() else "No"
#
#         cr = ''
#         ca = ''
#
#         crun = ex.measuring_run
#         if crun:
#             cr = crun.runid
#             if ex.measuring:
#                 ca = 'Measurement'
#             elif ex.extracting:
#                 ca = 'Extraction'
#
#         ctx['current_run'] = cr
#         ctx['current_activity'] = ca
#         ctx['last_message'] = lm
#
#         #enivornmentatl
#         ctx['pneumatics'] = ex.monitor.pneumatics
#         ctx['cTemp'] = ex.monitor.ctemp
#         ctx['humidity'] = ex.monitor.humidity
#
#         self._push(ctx)
#
#     def _push(self, ctx):
#         if self._sftp is None:
#             self._new_ssh()
#
#         localpath = self._make_ctx(ctx)
#         remotepath = self._make_remotepath()
#
#         sftp = self._sftp
#
#         sftp.put(localpath, remotepath)
#
#         #remove localpath
#         os.unlink(localpath)
#
#     def _make_remotepath(self):
#         root = '~'
#         ms = self.executor.experiment_queue.mass_spectrometer.lower()
#         return os.path.join(root,
#                             'sys_stats',
#                             'logs',
#                             '{}_syslog.yaml'.format(ms))
#
#     def _make_ctx(self, ctx):
#         p = tempfile.mkstemp()
#         with open(p, 'w') as fp:
#             yaml.dump(ctx, fp)
#         return p
#
#     def _new_ssh(self):
#         ssh = paramiko.SSHClient()
#         ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
#         ssh.connect(self.host,
#                     username=self.username,
#                     password=self.password)
#         self._ssh = ssh
#         self._sftp = self._ssh.open_sftp()


# ============= EOF =============================================

