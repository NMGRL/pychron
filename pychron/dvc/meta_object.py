# ===============================================================================
# Copyright 2018 ross
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
import json
import os
import time
from datetime import datetime

from uncertainties import ufloat, std_dev

from pychron.dvc import dvc_dump
from pychron.pychron_constants import INTERFERENCE_KEYS, RATIO_KEYS


class MetaObjectException(BaseException):
    def __init__(self, msg):
        self.msg = msg

    def __repr__(self):
        return self.msg


class MetaObject(object):
    def __init__(self, path=None, new=False):
        self.path = path
        if path is not None and os.path.isfile(path):
            with open(path, 'r') as rfile:
                self._load_hook(path, rfile)
        elif not new:
            msg = 'failed loading {} {}'.format(path, os.path.isfile(path))
            raise MetaObjectException(msg)

    def _load_hook(self, path, rfile):
        pass


class Gains(MetaObject):
    gains = None

    def __init__(self, *args, **kw):
        self.gains = {}
        super(Gains, self).__init__(*args, **kw)

    def _load_hook(self, path, rfile):
        self.gains = json.load(rfile)


class Chronology(MetaObject):
    _doses = None
    duration = 0
    use_irradiation_endtime = False

    def __init__(self, *args, **kw):
        self._doses = []
        super(Chronology, self).__init__(*args, **kw)

    @classmethod
    def from_lines(cls, lines):
        c = cls(new=False)
        c._load(lines)
        return c

    def _load_hook(self, path, rfile):
        self._load([line for line in rfile])

    def _load(self, lines):
        self._doses = []
        d = 0
        for line in lines:
            try:
                power, start, end = line.strip().split(',')
            except ValueError:
                continue

            start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
            ds = (end - start).total_seconds()
            d += ds
            self._doses.append((float(power), start, end))

        self.duration = d / 3600.

    def get_doses(self):
        return self._doses

    def get_chron_segments(self, analts):
        convert_days = lambda x: x.total_seconds() / (60. * 60 * 24)

        return [(p, convert_days(en - st), convert_days(analts - st), st, en) for p, st, en in self._doses]

    @property
    def total_duration_seconds(self):
        dur = 0
        for pwr, st, en in self._doses:
            dur += (en - st).total_seconds()
        return dur

    @property
    def irradiation_time(self):
        try:
            d_o = self._doses[0][1]
            return time.mktime(d_o.timetuple())
        except IndexError:
            return 0

    @property
    def start_date(self):
        """
            return date component of dose.
            dose =(pwr, %Y-%m-%d %H:%M:%S, %Y-%m-%d %H:%M:%S)

        """
        # doses = self.get_doses(tofloat=False)
        # d = datetime.strptime(doses[0][1], '%Y-%m-%d %H:%M:%S')
        # return d.strftime('%m-%d-%Y')
        # d = datetime.strptime(doses[0][1], '%Y-%m-%d %H:%M:%S')
        date = ''
        doses = self.get_doses()
        if doses:
            d = doses[0][1]
            date = d.strftime('%m-%d-%Y')
        return date


class Production2(MetaObject):
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
        with open(self.path, 'w') as wfile:
            for a in self.attrs:
                row = ','.join(map(str, (a, getattr(self, a), getattr(self, '{}_err'.format(a)))))
                wfile.write('{}\n'.format(row))


class Production(MetaObject):
    name = ''
    note = ''
    reactor = 'Triga'
    attrs = None

    @property
    def k_ca(self):
        return 1 / self.Ca_K

    @property
    def k_cl(self):
        return 1 / self.Cl_K

    @property
    def k_cl_err(self):
        return std_dev(1 / ufloat(self.Cl_K, self.Cl_K_err))

    @property
    def k_ca_err(self):
        return std_dev(1 / ufloat(self.Ca_K, self.Ca_K_err))

    def _load_hook(self, path, rfile):
        self.name = os.path.splitext(os.path.basename(path))[0]
        obj = json.load(rfile)

        attrs = []
        for k, v in obj.items():
            if k == 'reactor':
                self.reactor = v
            elif k == 'name':
                self.name = v
            else:
                setattr(self, k, float(v[0]))
                setattr(self, '{}_err'.format(k), float(v[1]))
                attrs.append(k)

        self.attrs = attrs

    def update(self, d):
        if self.attrs is None:
            self.attrs = []

        if isinstance(d, dict):
            for k, v in d.items():
                setattr(self, k, v)
                if not k.endswith('_err') and k not in self.attrs:
                    self.attrs.append(k)
        else:
            attrs = []
            for k in INTERFERENCE_KEYS + RATIO_KEYS:
                attrs.append(k)
                v = getattr(d, k)
                if v is None:
                    v = (0, 0)
                setattr(self, k, v[0])
                setattr(self, '{}_err'.format(k), v[1])
            self.attrs = attrs

    def to_dict(self, keys):
        return {t: ufloat(getattr(self, t),
                          getattr(self, '{}_err'.format(t)),
                          tag=t) for t in keys}

    def dump(self, path=None):
        if path is None:
            path = self.path

        obj = {}
        for a in self.attrs:
            obj[a] = (getattr(self, a), getattr(self, '{}_err'.format(a)))
        dvc_dump(obj, path)


class BaseHolder(MetaObject):
    holes = None

    def _load_hook(self, path, rfile):
        holes = []

        line = next(rfile)
        _, radius = line.split(',')
        radius = float(radius)

        for c, line in enumerate(rfile):
            # skip blank lines
            if not line.strip():
                continue

            # skip commented lines
            if line.strip().startswith('#'):
                continue

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
            if not hasattr(obj, '__cache__') or obj.__cache__ is None:
                obj.__cache__ = {}

            cache = obj.__cache__[func] if func in obj.__cache__ else {}
            if self.clear:
                if getattr(obj, self.clear):
                    cache = {}

            key = (func, name)
            force = kw.get('force', None)
            if not force:
                ret = cache.get(key)

            if ret is None:
                ret = func(obj, name, *args, **kw)

            cache[key] = ret
            obj.__cache__[func] = cache
            return ret

        return wrapper


cached = Cached

# ============= EOF =============================================
