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
import csv
import hashlib
import os
import shutil

from numpy import asarray, array, nonzero, polyval
from scipy.optimize import leastsq, optimize
from traits.api import HasTraits, List, Str, Dict, Bool, Property, Event

from pychron.core.helpers.filetools import add_extension
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR
from pychron.spectrometer import set_mftable_name, get_mftable_name


def get_detector_name(det):
    if not isinstance(det, (str, unicode)):
        det = det.name
    return det


def least_squares(func, xs, ys, initial_guess):
    xs, ys = asarray(xs), asarray(ys)
    errfunc = lambda p, x, v: func(p, x) - v
    ret, info = leastsq(errfunc, initial_guess, args=(xs, ys))
    return ret


class FieldItem(HasTraits):
    isotope = Str

    def to_csv(self, keys, fmt):
        return [self.isotope] + [fmt(getattr(self, k)) for k in keys]


class MagnetFieldTable(Loggable):
    """
        map a voltage to a mass
    """
    items = List
    molweights = Dict

    _mftable = None
    _detectors = None

    db = None
    spectrometer_name = Str
    use_local_archive = Bool
    use_db_archive = Bool
    path = Property(depends_on='_path_dirty')
    _path_dirty = Event
    mass_cal_func = 'cubic'
    _test_path = None

    def __init__(self, bind=True, *args, **kw):
        super(MagnetFieldTable, self).__init__(*args, **kw)
        # p = paths.mftable
        # if not os.path.isfile(p):
        # self.warning_dialog('No Magnet Field Table. Create {}'.format(p))
        # else:
        # self.load_mftable()

        # if os.environ.get('RTD', 'False') == 'False':
        if bind:
            self.bind_preferences()

    def initialize(self, molweights):
        self.molweights = molweights
        # p = paths.mftable
        p = self.path
        if not os.path.isfile(p):
            self.warning_dialog('No Magnet Field Table. Create {}'.format(p))
        else:
            self.load_mftable(load_items=True)

    def bind_preferences(self):
        from apptools.preferences.preference_binding import bind_preference

        prefid = 'pychron.spectrometer'
        bind_preference(self, 'use_local_archive',
                        '{}.use_local_mftable_archive'.format(prefid))
        bind_preference(self, 'use_db_archive',
                        '{}.use_db_mftable_archive'.format(prefid))

    def map_dac_to_mass(self, dac, detname):
        detname = get_detector_name(detname)

        d = self.mftable.get_table()

        _, xs, ys, p = d[detname]
        if self.polynominal_mass_func:
            def func(x, *args):
                c = list(p)
                c[-1] -= dac
                return polyval(c, x)

            try:
                mass = optimize.brentq(func, 0, 200)
                return mass
            except ValueError, e:
                self.debug('DAC does not map to an isotope. DAC={}, Detector={}'.format(dac, detname))
        else:
            try:
                idx = ys.index(dac)
                return xs[idx]
            except IndexError:
                self.debug('DAC does not map to an isotope. DAC={}, Detector={}'.format(dac, detname))

    def map_mass_to_dac(self, mass, detname):

        if isinstance(mass, str):
            mass = self.molweights[mass]

        self.debug('Mapping mass to dac mass func: "{}"'.format(self.mass_cal_func))
        detname = get_detector_name(detname)
        d = self.get_table()
        _, xs, ys, p = d[detname]

        if self.polynominal_mass_func:
            self.debug('{} map mass coeffs = {}'.format(detname, p))
            dac = polyval(p, mass)
        else:
            self.debug('using discrete mass mapping')
            dac = self.get_dac(detname, mass)

        return dac

    def get_dac(self, det, mass):
        det = get_detector_name(det)
        d = self._get_mftable()
        dac = next((d for i, m, d in zip(*d[det][:3]) if abs(m - mass) < 1e-5), None)
        return dac

        # isotope = next((i for i, m in self.molweights.iteritems() if abs(m-mass)<1e-5), None)
        # if isotope is not None:
        # isos, xs, ys = map(array, d[det][:3])
        # isos, mws, dacs = map(array, d[det][:3])
        # refindex = min(nonzero())
        # refindex = min(nonzero(isos == isotope)[0])
        # return ys[refindex]

    @property
    def polynominal_mass_func(self):
        return self.mass_cal_func in ('linear', 'parabolic', 'cubic')

    def update_field_table(self, det, isotope, dac, message):
        """

            dac needs to be in axial units
        """
        det = get_detector_name(det)

        self.info('update mftable {} {} {} message={}'.format(det, isotope, dac, message))
        d = self._get_mftable()

        isos, xs, ys = map(array, d[det][:3])

        try:
            refindex = min(nonzero(isos == isotope)[0])

            delta = dac - ys[refindex]
            # need to calculate all ys
            # using simple linear offset
            # ys += delta
            for k, (iso, xx, yy, _) in d.iteritems():
                ny = yy + delta
                initial_guess = self._get_initial_guess(ny, xx)
                if initial_guess:
                    p = least_squares(polyval, xx, ny, initial_guess)
                else:
                    p = None
                d[k] = iso, xx, ny, p

            self.dump(isos, d, message)
            # self._mftable = isos, xs, ys

        except ValueError:
            import traceback

            e = traceback.format_exc()
            self.debug('Magnet update field table {}'.format(e))

    def set_path_name(self, name):
        if name and self.path != name:
            self.path = name
            self.info('Using MFTable {}'.format(self.path))
            self.load_mftable()

    def get_table(self):
        mt = self._get_mftable()
        return mt

    def load(self):
        pass

    def save(self):
        detectors = self._detectors
        p = self.path
        p = '{}.temp'.format(p)
        fmt = lambda x: '{:0.5f}'.format(x)
        with open(p, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['iso'] + detectors)
            for fi in self.items:
                writer.writerow(fi.to_csv(detectors, fmt))

        self._set_mftable_hash(p)
        self._add_to_archive(p, message='manual modification')

    def dump(self, isos, d, message):
        detectors = self._detectors
        p = self.path
        with open(p, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['iso'] + detectors)

            for i, iso in enumerate(isos):
                a = [iso]
                for hi in detectors:
                    iso, xs, ys, _ = d[hi]
                    a.append('{:0.5f}'.format(ys[i]))

                writer.writerow(a)

        self._set_mftable_hash(p)
        self._add_to_archive(p, message)

    # @property
    # def mftable_path(self):
    # return os.path.join(paths.spectrometer_dir, 'mftable.csv')

    @property
    def mftable_archive_path(self):
        return os.path.join(paths.spectrometer_dir,
                            '{}_mftable_archive'.format(self.spectrometer_name))

    def load_mftable(self, path=None, load_items=False):
        """
            mftable format- first line is a header followed by
            Isotope, Dac_i, Dac_j,....

            Dac_i is the magnet dac setting to center Isotope on detector i
            example::

                iso, H2,     H1,      AX,     L1,     L2,     CDD
                Ar40,5.78790,5.895593,6.00675,6.12358,6.24510,6.35683
                Ar39,5.89692,5.788276,5.89692,5.89692,5.89692,5.89692
                Ar36,5.56072,5.456202,5.56072,5.56072,5.56072,5.56072

        """
        if path is None:
            path = self.path

        self.debug('Using mftable located at {}'.format(path))

        mws = self.molweights

        self._set_mftable_hash(path)
        items = []

        with open(path, 'U') as f:
            reader = csv.reader(f)
            table = []

            line0 = next(reader)
            if line0[0].strip() == 'iso':
                detline = line0
                mass_func = 'cubic'
            else:
                mass_func = line0[0].strip()
                detline = next(reader)
            detectors = map(str.strip, detline[1:])

            self.mass_cal_func = mass_func
            for line in reader:
                iso = line[0]
                try:
                    mw = mws[iso]
                except KeyError, e:
                    self.warning('"{}" not in molweights {}'.format(iso, mws))
                    continue

                # dacs = map(float, line[1:])
                dacs = []
                for di in line[1:]:
                    try:
                        di = float(di)
                    except ValueError:
                        di = NULL_STR
                    dacs.append(di)

                if load_items:
                    fi = FieldItem(isotope=iso)
                    for di, v in zip(detectors, dacs):
                        fi.add_trait(di, Str(v))
                    items.append(fi)

                row = [iso, mw] + dacs
                table.append(row)

            self._report_mftable(detectors, items)
            self.items = items

            table = zip(*table)
            isos, mws = list(table[0]), list(table[1])

            d = {}

            for i, k in enumerate(detectors):
                ys = table[2 + i]
                idx, ys = zip(*((i, y) for i, y in enumerate(ys) if y != NULL_STR))
                xs = [mws[i] for i in idx]

                initial_guess = self._get_initial_guess(ys, xs)
                if initial_guess:
                    try:
                        c = least_squares(polyval, xs, ys, initial_guess=initial_guess)
                    except TypeError:
                        c = (0, 1, ys[0])
                else:
                    c = None

                d[k] = (isos, xs, ys, c)

            self._mftable = d
            # self._mftable={k: (isos, mws, table[2 + i], )
            # for i, k in enumerate(detectors)}
            self._detectors = detectors

    def _get_initial_guess(self, y, x):
        initial_guess = None
        mass_func = self.mass_cal_func
        if mass_func == 'linear':
            initial_guess = [y[0], x[0]]
        elif mass_func == 'parabolic':
            initial_guess = [y[0], x[0], 0]
        elif mass_func == 'cubic':
            initial_guess = [y[0], x[0], 0, 0]
        return initial_guess

    def _report_mftable(self, detectors, items):
        self.debug('============ MFtable ===========')
        self.debug('{:<8s} {}'.format('Isotope', ''.join(['{:<7s}'.format(di) for di in detectors])))
        for it in items:
            vs = ['{:0.4f}'.format(getattr(it, di)) for di in detectors]
            self.debug('{:<8s} {}'.format(it.isotope, ' '.join(vs)))
        self.debug('================================')

    def _get_mftable(self):
        if not self._mftable or not self._check_mftable_hash():
            self.debug('using mftable at {}'.format(self.path))
            self.load_mftable()

        return self._mftable

    def _check_mftable_hash(self):
        """
            return True if mftable externally modified
        """
        # p = paths.mftable
        current_hash = self._make_hash(self.path)
        return self._mftable_hash != current_hash

    def _make_hash(self, p):
        with open(p, 'U') as rfile:
            return hashlib.md5(rfile.read())

    def _set_mftable_hash(self, p):
        self._mftable_hash = self._make_hash(p)

    def _add_to_archive(self, p, message):
        if self.use_db_archive:
            if self.db:
                self.info('db archiving mftable')
                with open(p, 'r') as rfile:
                    self.db.add_mftable(self.spectrometer_name, rfile.read())
            else:
                self.debug('no db instance available for archiving')

        if self.use_local_archive:
            try:
                from pychron.git_archive.git_archive import GitArchive
            except ImportError:
                self.warning('GitPython >=0.3.2RC1 required for local MFTable Archiving')
                return

            archive = GitArchive(self.mftable_archive_path)

            # copy
            dest = os.path.join(self.mftable_archive_path, os.path.basename(p))
            shutil.copyfile(p, dest)
            archive.add(dest, msg=message)
            archive.close()
            self.info('locally archiving mftable')

    def _set_path(self, name):
        set_mftable_name(name)

    # @cached_property
    def _get_path(self):
        p = self._test_path
        if not p:
            name = get_mftable_name()
            p = os.path.join(paths.mftable_dir, add_extension(name, '.csv'))
        return p

    def _name_to_path(self, name):
        if name:
            name = os.path.join(paths.mftable_dir, add_extension(name, '.csv'))
        return name or ''
        #
        # def _set_path(self, v):
        #     self._path = self._name_to_path(v)
        #
        # def _get_path(self):
        #     if self._path:
        #         p = self._path
        #     else:
        #         p = paths.mftable
        #     return p

# ============= EOF =============================================
