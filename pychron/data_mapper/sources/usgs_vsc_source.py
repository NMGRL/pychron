# ===============================================================================
# Copyright 2016 ross
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
from __future__ import absolute_import
from traits.api import File, Directory
# ============= standard library imports ========================
from datetime import datetime, timedelta
from numpy import array
import os
# ============= local library imports  ==========================

from pychron.data_mapper.sources.file_source import FileSource, get_float, get_int, get_next, get_ufloat
from pychron.processing.isotope import Isotope, Baseline
from pychron.processing.isotope_group import IsotopeGroup
from pychron.pychron_constants import INTERFERENCE_KEYS
from six.moves import range
from six.moves import zip


def make_ed(s):
    k = s[3]
    ed = ''
    if k == 'L':
        ed = 'CO2'
    elif k == 'F':
        ed = 'Furnace'

    return ed


class USGSVSCSource(FileSource):
    _delimiter = '\t'
    irradiation_path = File
    directory = Directory

    def get_analysis_import_specs(self, delimiter=None):
        if self.directory:
            ps = []
            for di in os.listdir(self.directory):
                self.path = os.path.join(self.directory, di)
                try:
                    s = self.get_analysis_import_spec()
                    ps.append(s)
                except BaseException:
                    pass
        elif self.path:
            ps = [self.get_analysis_import_spec(delimiter)]

        return ps


class USGSVSCNuSource(USGSVSCSource):
    pass


class USGSVSCMAPSource(USGSVSCSource):

    # def _path_default(self):
    #     return '/Users/ross/Programming/github/pychron_dev/pychron/data_mapper/tests/data/16Z0071/16K0071A.TXT'
    #
    # def _irradiation_path_default(self):
    #     return '/Users/ross/Programming/github/pychron_dev/pychron/data_mapper/tests/data/IRR330.txt'
    #
    # def _directory_default(self):
    #     return '/Users/ross/Downloads/MAPdataToJake/Unknown/16Z0071'

    def get_irradiation_import_spec(self, *args, **kw):
        from pychron.data_mapper.import_spec import ImportSpec, Irradiation, Level, Position, Production
        spec = ImportSpec()
        delimiter = '\t'
        with open(self.irradiation_path, 'r') as rfile:

            i = Irradiation()
            i.name = next(rfile).strip()
            spec.irradiation = i
            note = next(rfile)

            _, nsteps = next(rfile).split(delimiter)
            doses = []
            for _ in range(int(nsteps)):
                duration, start, power = next(rfile).split(delimiter)

                sd = datetime.fromtimestamp(float(start))
                sd = sd.replace(year=sd.year - 66)
                ed = sd + timedelta(hours=float(duration))
                dose = (float(power), sd, ed)
                doses.append(dose)

            i.doses = doses

            level = Level()
            level.name = 'A'
            nlevels = [level]

            prod = Production()
            prod.name = i.name

            for line in rfile:
                name, v, e = line.split(delimiter)
                name = name.replace('/', '')
                for attr in INTERFERENCE_KEYS:
                    if name in (attr[1:], attr[2:]):
                        setattr(prod, attr, (float(v), float(e)))

            level.production = prod

            pp = Position()
            pp.position = 0
            pp.identifier = i.name
            poss = [pp]
            level.positions = poss
            i.levels = nlevels

        return spec

    def get_analysis_import_spec(self, delimiter=None):

        pspec = self.new_persistence_spec()
        rspec = pspec.run_spec

        f = self.file_gen(delimiter)
        row = next(f)

        rspec.identifier = row[0][:-1]
        rspec.aliquot = 1
        rspec.step = row[0][-1]

        rspec.extract_device = make_ed(row[0])

        rspec.irradiation = row[1]

        rspec.irradiation_position = get_int(f, 1)
        rspec.irradiation_level = 'A'

        for attr in ('sample', 'material', 'project'):
            setattr(rspec, attr, get_next(f, 1))

        for attr in ('j', 'j_err'):
            setattr(pspec, attr, get_float(f, 1))

        d = get_next(f, 1)
        t = get_next(f, 1)
        pspec.timestamp = datetime.strptime('{} {}'.format(d, t), '%m/%d/%Y %H:%M:%S')

        abundance_sens = get_float(f)
        abundance_sens_err = get_float(f)

        air = get_float(f)
        disc = 295.5 / air

        pspec.discrimination = disc

        row = next(f)  # MD errpr
        row = next(f)  # peakhop cycles

        n40 = get_int(f)
        n39 = get_int(f)
        n38 = get_int(f)
        n37 = get_int(f)
        n36 = get_int(f)
        n41 = get_int(f)
        n355 = get_int(f)
        _spare = next(f)

        int40 = next(f)
        int39 = next(f)
        int38 = next(f)
        int37 = next(f)
        int36 = next(f)
        int41 = next(f)
        int355 = next(f)

        bk40 = get_ufloat(f)
        bk39 = get_ufloat(f)
        bk38 = get_ufloat(f)
        bk37 = get_ufloat(f)
        bk36 = get_ufloat(f)
        bk41 = get_ufloat(f)

        bk40 += get_ufloat(f)
        bk39 += get_ufloat(f)
        bk38 += get_ufloat(f)
        bk37 += get_ufloat(f)
        bk36 += get_ufloat(f)
        bk41 += get_ufloat(f)

        bk40 += get_ufloat(f)
        bk39 += get_ufloat(f)
        bk38 += get_ufloat(f)
        bk37 += get_ufloat(f)
        bk36 += get_ufloat(f)
        bk41 += get_ufloat(f)

        isotopes = {'Ar40': self._get_isotope(f, 'Ar40', n40, bk40),
                    'Ar39': self._get_isotope(f, 'Ar39', n39, bk39),
                    'Ar38': self._get_isotope(f, 'Ar38', n38, bk38),
                    'Ar37': self._get_isotope(f, 'Ar37', n37, bk37),
                    'Ar36': self._get_isotope(f, 'Ar36', n36, bk36),
                    'Ar41': self._get_isotope(f, 'Ar41', n41, bk41)}

        xs, ys = self._get_baseline(f, n355)
        for iso in isotopes.values():
            bs = Baseline(iso.name, iso.detector)
            bs.set_fit('average')
            bs.set_fit_error_type('SEM')
            bs.xs = xs
            bs.ys = ys
            iso.baseline = bs

        try:
            next(f)
            self.warning('Extra data in file')
        except StopIteration:
            pass

        pspec.isotope_group = IsotopeGroup(isotopes=isotopes)
        return pspec

    def _get_baseline(self, f, ncnts):
        rs = (next(f) for i in range(ncnts))
        ys, xs = list(zip(*((float(r[0]), float(r[1])) for r in rs)))
        return array(xs), array(ys)

    def _get_isotope(self, f, name, ncnts, bk):
        iso = Isotope(name, 'Detector1')
        iso.set_ublank(bk)
        iso.name = name
        iso.set_fit('linear')
        iso.set_fit_error_type('SEM')

        rs = (next(f) for i in range(ncnts))
        ys, xs = list(zip(*((float(r[0]), float(r[1])) for r in rs)))
        iso.xs = array(xs)
        iso.ys = array(ys)
        return iso

# ============= EOF =============================================
