# ===============================================================================
# Copyright 2014 Jake Ross
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
import hashlib
import os
from traits.api import HasTraits, Button, Str, Int, Bool
from traitsui.api import View, Item, UItem, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
import yaml
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.loggable import Loggable
from pychron.pychron_constants import SCRIPT_NAMES

EXPERIMENT_ATTRS = ('username', 'mass_spectrometer',
                    'extract_device', 'name', 'start_timestamp')


class enabled_dec(object):
    def __init__(self):
        pass

    def __call__(self, method):
        def wrapper(obj, *args, **kw):
            if obj.enabled:
                method(*args, **kw)

        return wrapper


# def wrapped_f(*args, **kw):
# obj = args[0]
#             msg = args[1]
#             hmsg = hash(msg)
#             ido = id(obj)
#             if not ido in self._registry:
#                 self._registry[ido] = []
#
#             msgs = self._registry[ido]
#             if not hmsg in msgs:
#                 msgs.append(hmsg)
#                 f(*args)
#
#         return wrapped_f


class LabspyUpdater(Loggable):
    spectrometer_name = Str
    labspy_root = Str
    enabled = False

    # def __init__(self, *args, **kw):
    #     super(LabspyUpdater, self).__init__(*args, **kw)

    @enabled_dec()
    def add_experiment(self, exp):
        path, yl = self._load_experiment()

        yl.insert(0, {k: getattr(exp, k) for k in EXPERIMENT_ATTRS})
        yl = yl[-10:]

        with open(path, 'w') as fp:
            yaml.dump(yl, fp)

        self.repo.add(path, commit=True)

    @enabled_dec()
    def update_experiment(self, exp, err_msg):
        path, yl = self._load_experiment()

        def hfunc(yi):
            h = hashlib.md5()
            for ai in EXPERIMENT_ATTRS:
                h.update(yi[ai])
            return h.hexdigest()

        hkey = hfunc(exp)
        yy = next((yi for yi in yl if hfunc(yi) == hkey))
        yy['Status'] = err_msg or 'Successful'

        self.repo.truncate_repo()

    @enabled_dec()
    def add_run(self, run):
        root = self.repo.path
        path = os.path.join(root, '_data', 'labspy_context.yaml')
        with open(path, 'r') as fp:
            yl = yaml.load(fp)

        yl.insert(0, self._make_analysis(run))
        yl = yl[-50:]
        with open(path, 'w') as fp:
            yaml.dump(yl, fp)

        self.repo.add(path, commit=True)

    def _load_experiment(self):
        root = self.repo.path
        path = os.path.join(root, '_data', 'labspy_experiment_context.yaml')
        with open(path, 'r') as fp:
            yl = yaml.load(fp)
        return path, yl

    def _make_analysis(self, run):
        spec = run.spec

        d = {k: getattr(spec, k) for k in ('record_id', 'analysis_type', 'sample',
                                           'extract_value', 'duration', 'cleanup', 'position',
                                           'comment', 'material', 'project',
                                           'mass_spectrometer',
                                           'extract_device')}

        d['date'] = spec.analysis_timestamp.strftime('%m-%d-%Y %H:%M:%S')

        for si in SCRIPT_NAMES:
            d[si] = getattr(run, si)

        return d

    def _labspy_root_changed(self, new):
        if new:
            self.repo = GitRepoManager()
            if os.path.isdir(new):
                self.repo.open_repo(new)
            else:
                self.repo.clone('https://github.com/NMGRL/pychron')
                self.repo.create_remote('https://github.com/NMGRL/pychron')
                self.repo.checkout_branch('gh-pages')

            self.enabled = True
# ============= EOF =============================================



