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
import json

from traits.api import Bool

# ============= standard library imports ========================
from datetime import datetime
import os
import shutil
# ============= local library imports  ==========================
from uncertainties import ufloat
from pychron.canvas.utils import iter_geom
from pychron.core.helpers.datetime_tools import ISO_FORMAT_STR
from pychron.core.helpers.filetools import list_directory2, ilist_directory2, add_extension
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.pychron_constants import INTERFERENCE_KEYS, RATIO_KEYS


class MetaObject(object):
    def __init__(self, path):
        self.path = path
        if os.path.isfile(path):
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
            for p, s, e in doses:
                if not isinstance(s, str):
                    s = s.strftime(ISO_FORMAT_STR)
                if not isinstance(s, str):
                    s = s.strftime(ISO_FORMAT_STR)
                if not isinstance(p, str):
                    p = '{:0.3f}'.format(p)

                line = '{},{},{}\n'.format(p, s, e)
                wfile.write(line)

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

    def dump(self):
        attrs = self.attrs
        with open(self.path, 'w') as wfile:
            for a in self.attrs:
                row = ','.join(map(str, (a, getattr(self, a), getattr(self, '{}_err'.format(a)))))
                wfile.write('{}\n'.format(row))


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

            force = kw.get('force', None)
            if not force and not clear:
                if name in obj.__cache__:
                    ret = obj.__cache__[name]

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

    # def __init__(self, path=None, *args, **kw):
    #     super(MetaRepo, self).__init__(*args, **kw)
    #     if path is None:
    #         path = paths.meta_dir
    #
    #     self.path = path

    def update_script(self, name, path_or_blob):
        self._update_text('scripts', name, path_or_blob)

    def update_experiment_queue(self, name, path_or_blob):
        self._update_text('experiments', name, path_or_blob)

    def add_production(self, name, obj, commit=False):
        p = self.get_production(name, force=True)
        p.attrs = []
        for k in INTERFERENCE_KEYS + RATIO_KEYS:
            v = getattr(obj, k)
            e = getattr(obj, '{}_err'.format(k))
            setattr(p, k, v)
            setattr(p, '{}_err'.format(k), e)
            p.attrs.append(k)

        p.dump()
        self.add(p.path, commit=commit)

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

    def add_level(self, irrad, level):
        p = self.get_level_path(irrad, level)
        with open(p, 'w') as wfile:
            json.dump([], wfile)

        self.add(p, commit=False)

    def get_level_path(self, irrad, level):
        return os.path.join(self.path, irrad, '{}.json'.format(level))

    def add_chronology(self, irrad, doses):
        p = os.path.join(self.path, irrad, 'chronology.txt')

        Chronology.dump(p, doses)
        self.add(p, commit=False)

    def add_irradiation(self, name):
        p = os.path.join(self.path, name)
        if not os.path.isdir(p):
            os.mkdir(p)
            # self.add(p, commit=False)

    def add_irradiation_holder(self, name, blob, commit=False):
        p = os.path.join(self.path, 'irradiation_holders', add_extension(name))
        with open(p, 'w') as wfile:
            holes = list(iter_geom(blob))
            n = len(holes)
            wfile.write('{},0.0175\n'.format(n))
            for idx, (x, y, r) in holes:
                wfile.write('{:0.4f},{:0.4f},{:0.4f}\n'.format(x, y, r))
        self.add(p, commit=commit)

    def add_load_holder(self, name, path_or_txt, commit=False):
        p = os.path.join(self.path, 'load_holders', name)
        if os.path.isfile(path_or_txt):
            shutil.copyfile(path_or_txt, p)
        else:
            with open(p, 'w') as wfile:
                wfile.write(path_or_txt)
        self.add(p, commit=commit)

    def update_j(self, irradiation, level, pos, identifier, j, e):
        p = self.get_level_path(irradiation, level)
        with open(p, 'r') as rfile:
            jd = json.load(rfile)

        njd = [ji if ji['position'] != pos else {'position': pos, 'j': j, 'j_err': e} for ji in jd]
        with open(p, 'w') as wfile:
            json.dump(njd, wfile)
        self.add(p, commit=False)

    def update_chronology(self, name, doses):
        p = self._chron_name(name)
        Chronology.dump(p, doses)
        self.add(p, commit=False)
        # if commit:
        #     self.commit('Updated {} chronology'.format(name))
        #     if push:
        #         self.push()

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

    def get_flux(self, irradiation, level, position):
        path = os.path.join(self.path, irradiation, add_extension(level, '.json'))
        j, e = 0, 0
        if os.path.isfile(path):
            with open(path) as rfile:
                positions = json.load(rfile)
            try:
                pos = positions[position - 1]
                j, e = pos['j'], pos['j_err']
            except IndexError:
                pass

        return ufloat(j, e)

    @cached('clear_cache')
    def get_production(self, pname, **kw):
        root = os.path.join(self.path, 'productions')
        if not os.path.isdir(root):
            os.mkdir(root)
        p = os.path.join(root, add_extension(pname))
        ip = Production(p)
        return ip

    @cached('clear_cache')
    def get_chronology(self, name):
        p = self._chron_name(name)
        return Chronology(p)

    @cached('clear_cache')
    def get_irradiation_holder_holes(self, name):
        p = os.path.join(self.path, 'irradiation_holders', add_extension(name))
        holder = IrradiationHolder(p)
        return holder.holes

    @cached('clear_cache')
    def get_load_holder_holes(self, name):
        p = os.path.join(self.path, 'load_holders', add_extension(name))
        holder = LoadHolder(p)
        return holder.holes

    # private
    def _chron_name(self, name):
        return os.path.join(self.path, name, 'chronology.txt')

    def _update_text(self, tag, name, path_or_blob):
        if not name:
            self.debug('cannot update text with no name. tag={} name={}'.format(tag, name))
            return

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

# ============= EOF =============================================
