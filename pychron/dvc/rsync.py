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
from traits.api import HasTraits, Str, CInt
from apptools.preferences.preference_binding import bind_preference
# ============= standard library imports ========================
# ============= local library imports  ==========================
import subprocess


class RsyncMixin(HasTraits):
    rsync_user = Str
    rsync_port = CInt(22)
    rsync_remote = Str
    rsync_options = Str
    path = Str

    def _bind_preferences(self):
        prefid = 'pychron.dvc'
        for r in ('rsync_user', 'rsync_remote', 'rsync_port', 'rsync_options'):
            bind_preference(self, r, '{}.{}'.format(prefid, r))

    def push(self):
        rsync_push(self.path, remote=self.rsync_remote, user=self.rsync_user)

    def pull(self):
        rsync_pull(self.path, remote=self.rsync_remote, user=self.rsync_user)


def rsync_pull(paths, **kw):
    return _rsync(paths, False, **kw)


def rsync_push(paths, **kw):
    return _rsync(paths, True, **kw)


def _rsync(paths, push_pull, **kw):
    cmd = _get_rsync_command(push_pull, **kw)

    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    p.communicate(input='\x00'.join(paths))


def _get_rsync_command(push, remote=None, port=None, user=None, options=None):
    cmd = ['rsync', '--from0', '--files-from=-']
    rshopts = []
    for v, f in ((user, '-l'), (port, '-p')):
        if v:
            rshopts.append(f)
            rshopts.append(v)
    if rshopts:
        cmd.append('--rsh=ssh {}'.format(' '.join(rshopts)))
    if options:
        cmd.extend(options.split(' '))

    src = './'
    dest = '{}/'.format(remote)
    if push:
        cmd.append(src)
        cmd.append(dest)
    else:
        cmd.append(dest)
        cmd.append(src)

    return cmd


# ============= EOF =============================================



