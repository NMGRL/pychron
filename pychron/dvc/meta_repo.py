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
from datetime import datetime
import os
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import list_directory2, ilist_directory2
from pychron.dvc.defaults import SIXHOLE, TRIGA
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.paths import paths


class MetaObject(object):
    def __init__(self, path):
        with open(path, 'r') as rfile:
            self._load_hook(path, rfile)

    def _load_hook(self, path, rfile):
        pass


class Chronology(MetaObject):
    _doses = None

    def _load_hook(self, path, rfile):
        self._doses = []
        d = 0
        for line in rfile:
            power, start, end = line.strip().split(',')
            start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
            ds = (end - start).total_seconds()
            d += ds
            self._doses.append((power, start, end))

        self.duration = d / 3600.

    def get_doses(self):
        return self._doses


class Production(MetaObject):
    name = ''
    note = ''

    def _load_hook(self, path, rfile):
        self.name = os.path.splitext(os.path.basename(path))[0]
        for line in rfile:
            if line.startswith('#-----'):
                break
            k, v, e = line.split(',')
            setattr(self, k, float(v))
            setattr(self, '{}_err'.format(k), float(e))
        self.note = rfile.read()


class IrradiationHolder(MetaObject):
    def _load_hook(self, path, rfile):
        holes = []
        for c, line in enumerate(rfile):
            args = line.split(',')
            if len(args) == 2:
                x, y = args
                r = 0.1
            else:
                x, y, r = args

            holes.append((float(x), float(y), float(r), str(c + 1)))

        self.holes = holes


class MetaRepo(GitRepoManager):
    def __init__(self, *args, **kw):
        super(MetaRepo, self).__init__(*args, **kw)
        self.path = paths.meta_dir
        self.open_repo(self.path)

        d = os.path.join(self.path, 'irradiation_holders')
        if not os.path.isdir(d):
            os.mkdir(d)
            if self.confirmation_dialog('You have no irradiation holders. Would you like to add some defaults?'):
                self._add_default_irradiation_holders()

        d = os.path.join(self.path, 'productions')
        if not os.path.isdir(d):
            os.mkdir(d)
            if self.confirmation_dialog('You have no irradiation productions. Would you like to add some defaults?'):
                self._add_default_irradiation_productions()

    def update_production(self, prod, irradiation=None):
        # ip = db.get_irradiation_production(prod.name)
        # if ip:
        if irradiation is None:
            p = os.path.join(self.path, 'productions', '{}.txt'.format(prod.name))
        else:
            p = os.path.join(self.path, irradiation, '{}.production.txt'.format(prod.name))

        ip = Production(p)
        self.debug('saving production {}'.format(prod.name))

        params = prod.get_params()
        for k, v in params.iteritems():
            self.debug('setting {}={}'.format(k, v))
            setattr(ip, k, v)

        ip.note = prod.note
        self.add(p, commit=False)
        self.commit('updated production {}'.format(prod.name))


    def add_chronology(self, irrad, chron):
        p = os.path.join(self.path, irrad, 'chronology.txt')
        with open(p, 'w') as wfile:
            for dose in chron.dosages:
                power = str(dose.power)
                start = dose.start()
                end = dose.end()
                wfile.write('{}\n'.format(','.join([power, start, end])))

        self.add(p)
        self.commit('Added chronology to {}'.format(irrad))

    def add_irradiation(self, name):
        os.mkdir(os.path.join(self.path, name))

    def get_chronology(self, name):
        p = os.path.join(self.path, name, 'chronology.txt')
        return Chronology(p)

    def get_irradiation_holder_names(self):
        return list_directory2(os.path.join(self.path, 'irradiation_holders'),
                               remove_extension=True)

    def get_irradiation_productions(self):
        # list_directory2(os.path.join(self.path, 'productions'),
        # remove_extension=True)
        prs = []
        root = os.path.join(self.path, 'productions')
        for di in ilist_directory2(root, extension='.txt'):
            pr = Production(os.path.join(root, di))
            prs.append(pr)
        return prs

    def get_irradiation_holder_holes(self, name):
        p = os.path.join(self.path, 'irradiation_holders', '{}.txt'.format(name))
        holder = IrradiationHolder(p)
        return holder.holes

    # private
    def _add_default_irradiation_productions(self):
        commit = False
        for name, txt in (('TRIGA.txt', TRIGA),):
            p = os.path.join(self.path, 'productions', name)
            if not os.path.isfile(p):
                with open(p, 'w') as wfile:
                    wfile.write(txt)
                self.add(p, commit=False)
                commit = True

        if commit:
            self.commit('added default irradiation productions')

    def _add_default_irradiation_holders(self):

        commit = False
        for name, txt in (('6Hole.txt', SIXHOLE),):
            p = os.path.join(self.path, 'irradiation_holders', name)
            if not os.path.isfile(p):
                with open(p, 'w') as wfile:
                    wfile.write(txt)
                self.add(p, commit=False)
                commit = True

        if commit:
            self.commit('added default irradiation holders')

# ============= EOF =============================================



