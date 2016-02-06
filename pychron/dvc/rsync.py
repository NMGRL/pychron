# ===============================================================================
# Copyright 2015 Jake Ross
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
from traits.api import HasTraits, Str, CInt

# ============= standard library imports ========================
# ============= local library imports  ==========================
import subprocess


class RsyncMixin(HasTraits):
    rsync_user = Str
    rsync_port = CInt(22)
    rsync_remote = Str
    rsync_options = Str
    lpath = Str
    rpath = Str

    def _bind_preferences(self):
        prefid = 'pychron.dvc'
        for r in ('rsync_user', 'rsync_remote', 'rsync_port', 'rsync_options'):
            bind_preference(self, r, '{}.{}'.format(prefid, r))

    def push(self):
        rsync_push(self.lpath, self.rpath,
                   True,
                   remote=self.rsync_remote, user=self.rsync_user)

    def pull(self):
        rsync_pull(self.lpath, self.rpath,
                   False,
                   remote=self.rsync_remote, user=self.rsync_user)


def rsync_pull(lpath, rpath, **kw):
    """
    return true if successful

    :param lpath:
    :param rpath:
    :param kw:
    :return:
    """
    return _rsync(lpath, rpath, False, **kw)


def rsync_push(lpath, rpath, **kw):
    """
    return true if successful

    :param lpath:
    :param rpath:
    :param kw:
    :return:
    """
    return _rsync(lpath, rpath, True, **kw)


def _rsync(lpath, rpath, push_pull, **kw):
    cmd = _get_rsync_command(lpath, rpath, push_pull, **kw)
    r = subprocess.check_call(cmd)
    return not r


def _get_rsync_command(lpath, rpath, push, remote=None, port=None, user=None, options=None):
    if remote:
        if port:
            rpath = '{}@{}:{}'.format(user, remote, rpath)
        else:
            rpath = '{}@{}:{}/{}'.format(user, remote, port, rpath)

    if push:
        cmd = ['rsync', '-a', lpath, rpath]
    else:
        cmd = ['rsync', '-a', rpath, lpath]

    return cmd


if __name__ == '__main__':
    lpath = '/Users/ross/Sandbox/payload.txt'
    rpath = '/Users/ross/Sandbox/payload.dropoff.txt'
    with open(lpath, 'w') as wfile:
        wfile.write('This it the paylasdfasdfoad')

    rsync_push(lpath, rpath)

    with open(rpath, 'w') as wfile:
        wfile.write('Nooooooooo this is the payload')
    rsync_pull(lpath, rpath)
# ============= EOF =============================================



