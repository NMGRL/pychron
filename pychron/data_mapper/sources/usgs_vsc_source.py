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
import os
from traits.api import File, Directory
# ============= standard library imports ========================
from datetime import datetime, timedelta
from numpy import array
# ============= local library imports  ==========================
from uncertainties import ufloat

from pychron.data_mapper.sources.file_source import FileSource
from pychron.experiment.utilities.identifier import make_step, make_increment
from pychron.processing.isotope import Isotope, Baseline
from pychron.processing.isotope_group import IsotopeGroup
from pychron.pychron_constants import INTERFERENCE_KEYS


def make_ed(s):
    k = s[3]
    ed = ''
    if k == 'L':
        ed = 'CO2'
    elif k == 'F':
        ed = 'Furnace'

    return ed


def get_int(f, idx=0):
    return int(next(f)[idx])


def get_float(f, idx=0):
    return float(next(f)[idx])


def get_ufloat(f):
    return ufloat(*map(float, next(f)))


class USGSVSCSource(FileSource):
    _delimiter = '\t'
    irradiation_path = File
    directory = Directory

    def _path_default(self):
        return '/Users/ross/Programming/github/pychron_dev/pychron/data_mapper/tests/data/16Z0071/16K0071A.TXT'

    def _irradiation_path_default(self):
        return '/Users/ross/Programming/github/pychron_dev/pychron/data_mapper/tests/data/IRR330.txt'

    # def _directory_default(self):
    #     return '/Users/ross/Downloads/MAPdataToJake/Unknown/16Z0071'

    def get_irradiation_import_spec(self, *args, **kw):
        from pychron.data_mapper.import_spec import ImportSpec, Irradiation, Level, \
            Sample, Project, Position, Production
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

    def get_analysis_import_spec(self, delimiter=None):

        pspec = self.new_persistence_spec()
        rspec = pspec.run_spec

        f = self.file_gen(delimiter)
        row = next(f)
        # rspec.runid = row[0]

        rspec.identifier = row[0][:-1]
        rspec.aliquot = 1
        rspec.step = row[0][-1]

        rspec.extract_device = make_ed(row[0])

        # irrad = Irradiation()
        rspec.irradiation = row[1]

        row = next(f)
        rspec.irradiation_position = int(row[1])
        rspec.irradiation_level = 'A'

        row = next(f)
        rspec.sample = row[1]

        row = next(f)
        rspec.material = row[1]

        row = next(f)
        rspec.project = row[1]

        j = get_float(f, 1)
        j_err = get_float(f, 1)

        pspec.j, pspec.j_err = j, j_err
        row = next(f)
        d = row[1]
        row = next(f)
        t = row[1]

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

        isotopes = {}
        isotopes['Ar40'] = self._get_isotope(f, 'Ar40', n40, bk40)
        isotopes['Ar39'] = self._get_isotope(f, 'Ar39', n39, bk39)
        isotopes['Ar38'] = self._get_isotope(f, 'Ar38', n38, bk38)
        isotopes['Ar37'] = self._get_isotope(f, 'Ar37', n37, bk37)
        isotopes['Ar36'] = self._get_isotope(f, 'Ar36', n36, bk36)
        isotopes['Ar41'] = self._get_isotope(f, 'Ar41', n41, bk41)

        xs,ys = self._get_baseline(f, n355)
        for iso in isotopes.values():
            bs = Baseline(iso.name, iso.detector)
            bs.set_fit('average')
            bs.set_fit_error_type('SEM')
            bs.xs = xs
            bs.ys = ys
            iso.baseline = bs

        #isotopes['Ar35'] = self._get_isotope(f, 'Ar35', n35, b35)
        #isotopes['Ar35.5'] = self._get_isotope(f, 'Ar35.5', n355, b355)

        try:
            next(f)
            self.warning('Extra data in file')
        except StopIteration:
            pass

        pspec.isotope_group = IsotopeGroup(isotopes=isotopes)
        return pspec

    def _get_baseline(self, f, ncnts):
        rs = (next(f) for i in xrange(ncnts))
        ys, xs = zip(*((float(r[0]), float(r[1])) for r in rs))
        return array(xs), array(ys)

    def _get_isotope(self, f, name, ncnts, bk):
        iso = Isotope(name, 'Detector1')
        iso.set_ublank(bk)
        iso.name = name
        iso.set_fit('linear')
        iso.set_fit_error_type('SEM')

        rs = (next(f) for i in xrange(ncnts))
        ys, xs = zip(*((float(r[0]), float(r[1])) for r in rs))
        iso.xs = array(xs)
        iso.ys = array(ys)
        return iso

    # def get_irradiation_import_spec(self, name):
    #     # from pychron.entry.import_spec import ImportSpec, Irradiation, Level, \
    #     #     Sample, Project, Position, Production
    #     # spec = ImportSpec()
    #
    #     i = Irradiation()
    #     i.name = name
    #     i.doses = self._get_doses(name)
    #
    #     spec.irradiation = i
    #
    #     levels = self._get_levels(name)
    #
    #     nlevels = []
    #     for li in levels:
    #         level = self._level_factory(li)
    #
    #         pos = []
    #         for ip in self.get_irradiation_positions(name, level.name):
    #             dbsam = ip.sample
    #             s = Sample()
    #             s.name = dbsam.Sample
    #             s.material = ip.Material
    #
    #             pp = Project()
    #             pp.name = ip.sample.project.Project
    #             pp.principal_investigator = ip.sample.project.PrincipalInvestigator
    #             s.project = pp
    #
    #             p = Position()
    #             p.sample = s
    #             p.position = ip.HoleNumber
    #             p.identifier = ip.IrradPosition
    #             p.j = ip.J
    #             p.j_err = ip.JEr
    #             p.note = ip.Note
    #             p.weight = ip.Weight
    #
    #             pos.append(p)
    #         level.positions = pos
    #         nlevels.append(level)
    #
    #         i.levels = nlevels
    #     return spec

    # def _level_factory(self, irradname, li):
    #     level = Level()
    #     level.name = li['name']
    #     level.holder = li['tray']
    #
    #     prod = self._production_factory(li)
    #     level.production = prod
    #     pos = [self._position_factory(ip)
    #            for ip in self.get_irradiation_positions(irradname, level.name)]
    #     level.positions = pos
    #
    #     return level
    #
    # def _position_factory(self, ip):
    #     dbsam = ip.sample
    #     s = Sample()
    #     s.name = dbsam.Sample
    #     s.material = ip.Material
    #
    #     pp = Project()
    #     pp.name = ip.sample.project.Project
    #     pp.principal_investigator = ip.sample.project.PrincipalInvestigator
    #     s.project = pp
    #
    #     p = Position()
    #     p.sample = s
    #     p.position = ip.HoleNumber
    #     p.identifier = ip.IrradPosition
    #     p.j = ip.J
    #     p.j_err = ip.JEr
    #     p.note = ip.Note
    #     p.weight = ip.Weight
    #
    #     return p
    #
    # def _production_factory(self, li):
    #     prod = Production()
    #     prod.name = li['production_name']
    #     p = li['production']
    #
    #     for attr in INTERFERENCE_KEYS:
    #         try:
    #             setattr(prod, attr, p[attr])
    #         except AttributeError:
    #             pass
    #
    #     prod.Ca_K = p['Ca_K']
    #     prod.Cl_K = p['Cl_K']
    #     prod.Cl3638 = p['Cl3638']
    #     return prod

# ============= EOF =============================================
