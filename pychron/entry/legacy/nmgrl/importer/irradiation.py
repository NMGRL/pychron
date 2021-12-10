# ===============================================================================
# Copyright 2020 ross
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
import re
from datetime import datetime, time

from pychron.dvc.dvc import DVC
from pychron.dvc.meta_object import Production
from pychron.entry.editors.chronology import IrradiationDosage
from pychron.entry.editors.production import IrradiationProduction
from pychron.entry.legacy.nmgrl.importer import BaseImporter
from pychron.entry.legacy.util import CSVHeader, get_dvc

NMRE_NOLEVEL = re.compile(r'^NM-\d{3}$')
NMRE_LEVEL = re.compile(r'^NM-\d{3}[A-Z]$')


class IrradiationImporter(BaseImporter):
    def do_import(self, dbsam, run, j, irrad, level, position):
        print('Irradiation doing import run: {}'.format(run.runid))

        # get the irradiation info
        for c in self._cache:
            if c[0] == irrad and c[1] == level:
                ir = c
                break
        else:
            for c in self._cache:
                if c[0] == irrad and c[1] == 'ALL':
                    ir = c
                    break
            else:
                print('failed to find irradiation info')
                return

        print('irradiation: {}{}, {}, dbsam={}'.format(irrad, level, ir, dbsam))

        dvc = self._dvc
        if dvc:
            _, _, prod, doses = ir

            # import the irradiation if doesn't already exist
            # add irradiation
            dvc.add_irradiation(irrad, doses=doses)

            # add production to irradiation
            dvc.add_production(irrad, prod.name, prod)

            # add level
            dvc.add_irradiation_level(level, irrad, 'LegacyHolder', prod.name)

            # add position to level
            identifier = run.identifier
            dvc.add_irradiation_position(irrad, level, position, identifier, sample=dbsam)

            # set j for position
            e, mj, me = 0, 0, 0
            print('updating flux {}{} {} {} {}'.format(irrad, level, position, identifier, j))
            dvc.update_flux(irrad, level, position, identifier, j, e, mj, me)
        return True

    # private
    def _load(self):
        p = '../tests/data/IrradiationData.csv'
        skipping = []
        with open(p, 'r') as rfile:
            header = None
            for line in rfile:
                row = line.strip().split(',')
                if header is None:
                    header = CSVHeader(row)
                else:
                    err = self.process_row(header, row)
                    if isinstance(err, str):
                        skipping.append('{},{}'.format(err, line))
                    elif err:
                        self._cache.append(err)

        op = 'skipping_irradiations.csv'
        with open(op, 'w') as wfile:
            wfile.write(''.join(skipping))

    def process_row(self, header, r):
        # only import NM- irradiations
        irradname = header.get(r, 'Irradiation')
        if NMRE_NOLEVEL.match(irradname):
            level = 'ALL'
            # print('no level xirradiation: {}'.format(irradname))
        elif NMRE_LEVEL.match(irradname):
            # print('44444444444444444444 irradiation: {}'.format(irradname))
            level = irradname[-1]
            irradname = irradname[:-1]
        else:
            # print('skipping: {}'.format(irradname))
            return

        doses = make_doses(header, r)
        if isinstance(doses, str):
            return doses
        else:
            prod = make_production(header, r)
            if isinstance(prod, str):
                return prod

            return irradname, level, prod, doses
            # print('importing {}, {}, {}, {}'.format(irradname, level, prod.name, doses))
            # if dvc:
            #     # add irradiation
            #     dvc.add_irradiation(irradname, doses=doses)
            #
            #     # add production to irradiation
            #     dvc.add_production(irradname, prod.name, prod)
            #
            #     # add level
            #     dvc.add_irradiation_level(level, irradname, 'LegacyHolder', prod.name)


def make_production(header, row):
    p = Production(new=True)
    p.name = 'LegacyProduction'

    for k in ('Ca3637', 'Ca3937', 'K4039'):
        p.setattr(k, header.get(row, k, float),
                  header.get(row, '{}Er'.format(k), float))
    return p


def make_doses(header, row):
    ndoses = header.get(row, 'NDoses', int)
    starttime = header.get(row, 'starttime', float)

    def make_date(dt):
        try:
            dt = datetime.strptime(dt, '%m/%d/%y')
        except ValueError as e:
            try:
                dt = datetime.strptime(dt, '%m/%d/%Y')
            except ValueError as e:
                return 'invalid date "{}". exception={}'.format(dt, e)
        return dt

    startdate = make_date(header.get(row, 'startdate'))
    if isinstance(startdate, str):
        return startdate

    try:
        duration = header.get(row, 'duration', float)
    except ValueError:
        return 'invalid duration'

    dose = IrradiationDosage()
    dose.start_date = startdate

    def make_time(t):
        return time(hour=int(t),
                    minute=int(t * 60) % 60,
                    second=int(t * 3600) % 60)

    try:
        dose.start_time = make_time(starttime)
    except ValueError as e:
        return 'invalid time "{}". exception={}'.format(starttime, e)

    dose.set_end(duration)

    doses = [dose]
    idx = header.idx('startdate')

    for i in range(1, ndoses):
        j = idx + 3 * i

        dose = IrradiationDosage()
        duration = float(row[j + 2])

        st = make_date(row[j])
        if isinstance(st, str):
            return st

        dose.start_date = st
        t = row[j + 1]
        try:
            dose.start_time = make_time(float(t))
        except ValueError as e:
            return 'invalid time "{}". exception={}'.format(t, e)

        dose.set_end(duration)
        doses.append(dose)
    return [(1, d.sdt, d.edt) for d in doses]


# ============= EOF =============================================
