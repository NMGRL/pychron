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
from traits.api import Bool
# ============= standard library imports ========================
from datetime import datetime
import os
import shutil
# ============= local library imports  ==========================
from uncertainties import ufloat
from pychron.core.helpers.filetools import list_directory2, ilist_directory2, add_extension
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.paths import paths


class MetaObject(object):
    def __init__(self, path):
        self.path = path
        with open(path, 'r') as rfile:
            self._load_hook(path, rfile)

    def _load_hook(self, path, rfile):
        pass


class Chronology(MetaObject):
    _doses = None

    @classmethod
    def dump(cls, path, doses):
        if doses is None:
            doses = []

        with open(path, 'w') as wfile:
            for ds in doses:
                wfile.write('{}\n'.format(','.join(ds)))

    def _load_hook(self, path, rfile):
        self._doses = []
        d = 0
        for line in rfile:
            power, start, end = line.strip().split(',')
            start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
            ds = (end - start).total_seconds()
            d += ds
            self._doses.append((float(power), start, end))

        self.duration = d / 3600.

    def get_doses(self):
        return self._doses


class Production(MetaObject):
    name = ''
    note = ''

    def _load_hook(self, path, rfile):
        self.name = os.path.splitext(os.path.basename(path))[0]
        attrs = []
        for line in rfile:
            if line.startswith('#-----'):
                break
            k, v, e = line.split(',')
            setattr(self, k, float(v))
            setattr(self, '{}_err'.format(k), float(e))
            attrs.append(k)

        self.attrs = attrs
        self.note = rfile.read()

    def to_dict(self, keys):
        return {t: ufloat(getattr(self, t), getattr(self, '{}_err'.format(t))) for t in keys}
        # return {t: getattr(self, t) for a in keys for t in (a, '{}_err'.format(a))}


class BaseHolder(MetaObject):
    holes = None

    def _load_hook(self, path, rfile):
        holes = []

        line = rfile.next()
        _, radius = line.split(',')
        radius = float(radius)

        for c, line in enumerate(rfile):
            args = line.split(',')
            if len(args) == 2:
                x, y = args
                r = radius
            else:
                x, y, r = args

            holes.append((float(x), float(y), float(r), str(c + 1)))

        self.holes = holes


class LoadHolder(BaseHolder):
    pass


class IrradiationHolder(BaseHolder):
    pass


class Cached(object):
    def __init__(self, clear=None):
        self.clear = clear

    def __call__(self, func):
        def wrapper(obj, name, *args, **kw):
            ret = None
            # if kw.get('use_cache'):
            if not hasattr(obj, '__cache__'):
                obj.__cache__ = {}

            clear = False
            if self.clear:
                clear = getattr(obj, self.clear)

            if not clear:
                if name in obj.__cache__:
                    ret = obj.__cache__[name]
                    print 'using chace'

            if ret is None:
                ret = func(obj, name, *args, **kw)

            if clear:
                setattr(obj, self.clear, False)

            obj.__cache__[name] = ret

            return ret

        return wrapper


cached = Cached


class MetaRepo(GitRepoManager):
    clear_cache = Bool

    def __init__(self, *args, **kw):
        super(MetaRepo, self).__init__(*args, **kw)
        self.path = paths.meta_dir
        self.open_repo(self.path)

    def update_script(self, name, path_or_blob):
        self._update_text('scripts', name, path_or_blob)

    def update_experiment_queue(self, name, path_or_blob):
        self._update_text('experiments', name, path_or_blob)

    def _update_text(self, tag, name, path_or_blob):
        root = os.path.join(self.path, tag)
        if not os.path.isdir(root):
            os.mkdir(root)

        p = os.path.join(root, name)
        # action = 'updated' if os.path.isfile(p) else 'added'
        if os.path.isfile(path_or_blob):
            shutil.copyfile(path_or_blob, p)
        else:
            with open(p, 'w') as wfile:
                wfile.write(path_or_blob)

        self.add(p, commit=False)
        # if self.has_staged():
        # self.commit('updated {} {}'.format(tag, action, name))

        # hexsha = self.shell('hash-object', '--path', p)
        # return hexsha

    def update_production(self, prod, irradiation=None):
        # ip = db.get_irradiation_production(prod.name)
        # if ip:
        # if irradiation is None:
        #     p = os.path.join(self.path, 'productions', '{}.txt'.format(prod.name))
        # else:
        #     p = os.path.join(self.path, irradiation, '{}.production.txt'.format(prod.name))
        #
        # ip = Production(p)
        ip = self.get_production(prod.name)
        self.debug('saving production {}'.format(prod.name))

        params = prod.get_params()
        for k, v in params.iteritems():
            self.debug('setting {}={}'.format(k, v))
            setattr(ip, k, v)

        ip.note = prod.note

        self.add(ip.path, commit=False)
        self.commit('updated production {}'.format(prod.name))

    def add_chronology(self, irrad, doses):
        p = os.path.join(self.path, irrad, 'chronology.txt')
        Chronology.dump(p, doses)
        self.add(p, commit=False)
        self.commit('Added chronology to {}'.format(irrad))

    def add_irradiation(self, name):
        os.mkdir(os.path.join(self.path, name))

    def add_load_holder(self, name, path_or_txt):
        p = os.path.join(self.path, 'load_holders', name)
        if os.path.isfile(path_or_txt):
            shutil.copyfile(path_or_txt, p)
        else:
            with open(p, 'w') as wfile:
                wfile.write(path_or_txt)

    def update_chronology(self, name, doses):
        p = self._chron_name(name)
        Chronology.dump(p, doses)

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

    @cached('clear_cache')
    def get_production(self, pname):
        p = os.path.join(self.path, 'productions', add_extension(pname, '.txt'))
        ip = Production(p)
        return ip

    @cached('clear_cache')
    def get_chronology(self, name):
        print 'opening chconolog'
        p = self._chron_name(name)
        return Chronology(p)

    @cached('clear_cache')
    def get_irradiation_holder_holes(self, name):
        p = os.path.join(self.path, 'irradiation_holders', '{}.txt'.format(name))
        holder = IrradiationHolder(p)
        return holder.holes

    @cached('clear_cache')
    def get_load_holder_holes(self, name):
        p = os.path.join(self.path, 'load_holders', '{}.txt'.format(name))
        holder = LoadHolder(p)
        return holder.holes

    # private
    def _chron_name(self, name):
        return os.path.join(self.path, name, 'chronology.txt')

# ============= EOF =============================================
