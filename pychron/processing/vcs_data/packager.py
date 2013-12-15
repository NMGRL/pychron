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

#============= standard library imports ========================
import yaml
from git import Repo
#============= local library imports  ==========================
from pychron.helpers.filetools import unique_path
from pychron.loggable import Loggable
from pychron.paths import paths


class Packager(Loggable):
    def package(self, ans):
        yans = []
        for ai in ans:
            d = {'labnumber': ai.labnumber,
                 'aliquot': ai.aliquot,
                 'step': ai.step}

            isos = []
            for iso in ai.isotopes.itervalues():
                i = {'name': iso.name,
                     'detector': iso.detector,
                     'data': iso.pack()}
                isos.append(i)

            d['isotopes'] = isos

            yans.append(d)

        root=os.path.join(paths.data_dir, 'vcs')

        p, _ = unique_path(root, 'data')

        with open(p, 'w') as fp:
            yaml.dump_all(yans, fp)

        self._add_to_repo(root,p)

    def _add_to_repo(self, root, p):
        repo=self._get_repo(root)
        name=os.path.basename(p)
        index=repo.index
        index.add([name])
        index.commit('added {}'.format(p))

    def _get_repo(self, root):
        if not os.path.isdir(root):
            os.mkdir(root)
        if not os.path.isdir(os.path.join(root,'.git')):
            repo=Repo.init(root)
        else:
            repo=Repo(root)

        return repo


#============= EOF =============================================

