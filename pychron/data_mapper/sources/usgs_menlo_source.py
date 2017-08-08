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

# ============= standard library imports ========================
# ============= local library imports  ==========================
from datetime import datetime

from pychron.data_mapper.sources.file_source import FileSource
from pychron.experiment.automated_run.persistence_spec import PersistenceSpec
from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.processing.isotope import Isotope
from pychron.processing.isotope_group import IsotopeGroup


class USGSMenloSource(FileSource):
    _delimiter = '\t'

    def get_analysis_import_spec(self, p, delimiter=None):
        pspec = PersistenceSpec()

        rspec = AutomatedRunSpec()
        pspec.run_spec = rspec
        # spec = ImportSpec

        # analysis = Analysis()
        # spec.analysis = analysis

        # position = Position()
        # analysis.position = position

        if delimiter is None:
            delim = self._delimiter

        def gen():
            with open(p, 'r') as rfile:
                for line in rfile:
                    yield line.strip().split(delim)

        f = gen()
        row = f.next()
        # analysis.runid = row[0]
        rspec.runid = row[0]

        # irrad = Irradiation()
        rspec.irradiation = row[1]

        row = f.next()
        rspec.irradiation_level = row[1]

        row = f.next()
        rspec.sample = row[1]

        row = f.next()
        rspec.material = row[1]

        row = f.next()
        rspec.project = row[1]

        row = f.next()
        j = float(row[1])

        row = f.next()
        j_err = float(row[1])

        pspec.j, pspec.j_err = j, j_err
        row = f.next()
        d = row[1]
        row = f.next()
        t = row[1]

        rspec.analysis_timestamp = datetime.strptime('{} {}'.format(d, t), '%m/%d/%Y %H:%M:%S')
        row = f.next()
        abundance_sens = float(row[0])
        row = f.next()
        abundance_sens_err = float(row[0])

        row = f.next()
        air = float(row[0])
        disc = 295.5 / air

        pspec.discrimination = disc

        row = f.next()  # MD errpr
        row = f.next()  # peakhop cycles

        n40 = int(f.next()[0])
        n39 = int(f.next()[0])
        n38 = int(f.next()[0])
        n37 = int(f.next()[0])
        n36 = int(f.next()[0])
        n35 = int(f.next()[0])
        n355 = int(f.next()[0])

        f.next()

        row = f.next()
        b40 = map(float, row)
        b39 = map(float, row)
        b38 = map(float, row)
        b37 = map(float, row)
        b36 = map(float, row)
        b35 = map(float, row)
        b355 = map(float, row)
        for i, row in enumerate(f):
            if i > 36:
                break

        isotopes = {}
        isotopes['Ar40'] = self._get_isotope(f, 'Ar40', n40, b40)
        isotopes['Ar39'] = self._get_isotope(f, 'Ar39', n39, b39)
        isotopes['Ar38'] = self._get_isotope(f, 'Ar38', n38, b38)
        isotopes['Ar37'] = self._get_isotope(f, 'Ar37', n37, b37)
        isotopes['Ar36'] = self._get_isotope(f, 'Ar36', n36, b36)
        isotopes['Ar35'] = self._get_isotope(f, 'Ar35', n35, b35)
        isotopes['Ar35.5'] = self._get_isotope(f, 'Ar35.5', n355, b355)

        try:
            f.next()
            self.warning('Extra data in file')
        except StopIteration:
            pass

        pspec.isotope_group = IsotopeGroup(isotopes=isotopes)
        return pspec

    def _get_isotope(self, f, name, ncnts, bs):
        iso = Isotope(name, 'Detector1')
        # iso.baseline = Baseline(name, 'Detector1')
        # iso.baseline.value = bs
        iso.name = name
        rs = (f.next() for i in xrange(ncnts))
        xs, ys = zip(*((float(r[0]), float(r[1])) for r in rs))
        iso.xs = xs
        iso.ys = ys
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

    def _get_doses(self, irradname):
        # chrons = self.get_chronology_by_irradname(name)
        # i.doses = [(1.0, ci.StartTime, ci.EndTime) for ci in chrons]
        return []

    def _get_levels(self, irradname):

        return []

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
