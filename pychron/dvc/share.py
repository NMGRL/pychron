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
import os
import re
import subprocess

from traits.api import HasTraits, Str, Bool, List
from traitsui.api import View, UItem, VGroup, TableEditor






# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.handler import Controller
from traitsui.table_column import ObjectColumn
from pychron.core.helpers.filetools import ilist_gits
from pychron.github import Organization
from pychron.paths import paths


class ShareableRepo(HasTraits):
    name = Str
    enabled = Bool
    remote_name = Str('origin')
    remote_url = Str('http://github.com')


remote_re = re.compile(r'\[remote ".+"\]')


class PushExperimentsModel(HasTraits):
    shareables = List

    def __init__(self, org, usr, pwd, root=None, *args, **kw):
        self._org = org
        self._usr = usr
        self._pwd = pwd

        super(PushExperimentsModel, self).__init__(*args, **kw)

        ss = []
        if root is None:
            root = paths.experiment_dataset_dir

        for exp in ilist_gits(root):
            cfg = os.path.join(root, exp, '.git', 'config')
            with open(cfg, 'r') as rfile:
                for line in rfile:
                    if remote_re.match(line):
                        break
                else:
                    ss.append(ShareableRepo(name=exp, enabled=True,
                                            root=os.path.join(root, exp)))

        self.shareables = ss

    def create_remotes(self):
        cmd = lambda x: ['git', 'remote', 'add', x.remote_name, x.remote_url]
        for si in self.shareables:
            if si.enabled:
                root = si.root
                ret = subprocess.call(cmd(si), cwd=root)

                # check if url exists
                if subprocess.call(['git', 'ls-remote'], cwd=root):
                    # add repo to github
                    org = Organization(self._org, self._usr, self._pwd)
                    # org.create_repo(si.name)


class PushExperimentsView(Controller):
    def closed(self, info, is_ok):
        if is_ok:
            self.model.create_remotes()

    def traits_view(self):
        cols = [CheckboxColumn(name='enabled', width=30),
                ObjectColumn(name='name', editable=False),
                ObjectColumn(name='remote_name', editable=False,
                             label='Remote', width=50),
                ObjectColumn(name='remote_url', editable=False,
                             label='URL', width=300),
                ]
        ev = View(UItem('name'),
                  UItem('enabled'),
                  VGroup(UItem('remote_name', label='Name'),
                         UItem('remote_url', label='URL')))

        v = View(UItem('shareables',
                       editor=TableEditor(columns=cols,
                                          edit_view=ev)),
                 title='Shareable Experiments',
                 buttons=['OK', 'Cancel'],
                 resizable=True)
        return v


if __name__ == '__main__':
    root = '/Users/ross/Sandbox/testdir'
    pm = PushExperimentsModel(root)
    pv = PushExperimentsView(model=pm)
    pv.configure_traits()
# ============= EOF =============================================
