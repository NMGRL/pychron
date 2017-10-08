# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import provides

from pychron.entry.iimport_source import IImportSource
from pychron.entry.import_spec import ImportSpec, Irradiation, Level, \
    Sample, Project, Position, Production
from pychron.managers.data_managers.xls_data_manager import XLSDataManager

NAME = ('Name', 'irradiation', 'irrad')
PR = ('ProductionRatio', 'PR', 'Production Ratios', 'ProductionRatios', 'Production Ratio')
LEVEL = ('Level', 'Tray')
HOLDER = ('Holder',)
PROJECT = ('Project',)
SAMPLE = ('Sample',)
MATERIAL = ('Material',)
PI = ('Principal Investigator', 'Principal Investigator', 'PI')
NOTE = ('Note',)
WEIGHT = ('Weight',)
POSITION = ('Position', 'Hole')
Z = ('Height', 'Z')


@provides(IImportSource)
class XLSIrradiationSource:
    def __init__(self, p):
        self._dm = XLSDataManager()
        self._dm.open(p)

    def connect(self):
        return True

    def get_irradiation_names(self):
        dm = self._dm
        sheet = dm.get_sheet(('Irradiations', 0))
        nameidx = dm.get_column_idx(NAME, sheet)
        return list({r[nameidx].value for r in dm.iterrows(sheet, start=1)})

    def get_irradiation_import_spec(self, name):

        spec = ImportSpec()

        i = Irradiation()
        i.name = name

        spec.irradiation = i

        i.doses = self._get_doses(name)

        nlevels = []

        dm = self._dm
        sheet = dm.get_sheet(('Irradiations', 0))
        nameidx = dm.get_column_idx(NAME, sheet)
        levelidx = dm.get_column_idx(LEVEL, sheet)
        pridx = dm.get_column_idx(PR, sheet)
        holderidx = dm.get_column_idx(HOLDER, sheet)
        zidx = dm.get_column_idx(Z, sheet)
        noteidx = dm.get_column_idx(NOTE, sheet)

        z = 0
        for row in dm.iterrows(sheet, start=1):
            if row[nameidx].value == name:
                level = Level()
                level.name = row[levelidx].value
                level.z = row[zidx].value or z
                z = level.z + 1
                level.note = row[noteidx].value

                prod = Production()
                prod.name = row[pridx].value
                level.production = prod
                level.holder = row[holderidx].value

                pos = self._get_positions(name, level.name)
                level.positions = pos
                nlevels.append(level)

        i.levels = nlevels
        return spec

    def _get_doses(self, name):
        dm = self._dm
        sheet = dm.get_sheet(('Chronologies', 1))
        doses = []

        nameidx = dm.get_column_idx(NAME, sheet)
        poweridx = dm.get_column_idx(('Power',), sheet)
        startidx = dm.get_column_idx(('Start',), sheet)
        endidx = dm.get_column_idx(('End',), sheet)

        for row in dm.iterrows(sheet, start=1):
            if row[nameidx].value == name:
                p = row[poweridx].value
                s = row[startidx].value
                e = row[endidx].value

                doses.append((p, s, e))

        return doses

    def _get_positions(self, name, level):
        dm = self._dm
        sheet = dm.get_sheet(('Positions', 2))
        nameidx = dm.get_column_idx(NAME, sheet)
        levelidx = dm.get_column_idx(LEVEL, sheet)
        positionidx = dm.get_column_idx(POSITION, sheet)
        sampleidx = dm.get_column_idx(SAMPLE, sheet)
        materialidx = dm.get_column_idx(MATERIAL, sheet)
        projectidx = dm.get_column_idx(PROJECT, sheet)
        piidx = dm.get_column_idx(PI, sheet)
        noteidx = dm.get_column_idx(NOTE, sheet)
        weightidx = dm.get_column_idx(WEIGHT, sheet)

        ps = []
        for row in dm.iterrows(sheet, start=1):
            if row[nameidx].value == name and row[levelidx].value == level:
                pos = Position()

                pos.position = row[positionidx].value

                sample = Sample()
                sample.name = row[sampleidx].value
                sample.material = row[materialidx].value

                project = Project()
                project.name = row[projectidx].value
                project.principal_investigator = row[piidx].value
                sample.project = project
                pos.sample = sample

                pos.note = row[noteidx].value or ''
                pos.weight = row[weightidx].value or 0

                ps.append(pos)
        return ps

        # levels = self._get_irradiation_levels(name)
        # nlevels = []
        # for dbl in levels:
        #     level = Level()
        #     level.name = dbl.Level
        #
        #     prod = Production()
        #     dbprod = dbl.production
        #     prod.name = dbprod.Label.replace(' ', '_')
        #
        #     level.production = prod
        #     level.holder = dbl.SampleHolder
        #
        #     pos = []
        #     for ip in self.get_irradiation_positions(name, level.name):
        #         dbsam = ip.sample
        #         s = Sample()
        #         s.name = dbsam.Sample
        #         s.material = ip.Material
        #
        #         pp = Project()
        #         pp.name = ip.sample.project.Project
        #         pp.principal_investigator = ip.sample.project.PrincipalInvestigator
        #         s.project = pp
        #
        #         p = Position()
        #         p.sample = s
        #         p.position = ip.HoleNumber
        #         p.identifier = ip.IrradPosition
        #         p.j = ip.J
        #         p.j_err = ip.JEr
        #         p.note = ip.Note
        #         p.weight = ip.Weight
        #
        #         pos.append(p)
        #     level.positions = pos
        #     nlevels.append(level)
        # i.levels = nlevels
        # return spec


        # def load(self, p):
        #
        #     sheet = dm.get_sheet(('Irradiations', 0))

        # nameidx = dm.get_column_idx(NAME, sheet)
        # pridx = dm.get_column_idx(PR, sheet)
        # levelidx = dm.get_column_idx(LEVEL, sheet)
        # holderidx = dm.get_column_idx(HOLDER, sheet)

        # for igen in self.iterate_irradiations():
        #     for i, row in enumerate(igen):
        #         if i == 0:
        #             irrad = row[nameidx].value
        #             self._add_irradiation(irrad, dry_run=dry_run)
        #
        #         self._add_level(irrad, row[levelidx].value,
        #                         row[pridx].value, row[holderidx].value)
        #         if not dry_run and self.db:
        #             self.db.commit()

# ============= EOF =============================================
