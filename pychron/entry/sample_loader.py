# ===============================================================================
# Copyright 2019 ross
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
from datetime import datetime

import utm
from traits.api import Instance

from pychron.core.xls.xls_parser import XLSParser
from pychron.dvc.dvc_orm import SampleTbl, ProjectTbl
from pychron.loggable import Loggable


class BaseSampleLoader(Loggable):
    dvc = Instance('pychron.dvc.dvc.DVC')


def extract_value(row, tags):
    for tag in tags:
        if tag in row:
            return row[tag]


def extract_fvalue(row, tags):
    v = extract_value(row, tags)
    if v is not None:
        v = float(v)
    return v


def convert_utm(n, e, zone):
    """
    return lat, lon
    """

    zn = int(zone[:2])
    zl = zone[-1:]
    lat, lon = utm.to_latlon(e, n, zn, zl)
    return float(lat), float(lon)


class XLSSampleLoader(BaseSampleLoader):
    parser = None

    def load(self, p):
        parser = XLSParser()
        parser.load(p)
        self.parser = parser

    def do_import(self):
        dvc = self.dvc
        if self.parser and dvc:
            dvc.create_session()

            rows = list(self.parser.values(lowercase_keys=True))

            with dvc.session_ctx():
                for ri in rows:
                    self._import_principal_investigator(dvc, ri)

                for ri in rows:
                    self._import_project(dvc, ri)

                for ri in rows:
                    self._import_sample(dvc, ri)

    def _import_principal_investigator(self, dvc, row):
        name = extract_value(row, ('pi', 'principal_investigator', 'principal investigator'))
        aff = extract_value(row, ('affiliation',))
        p = dvc.db.add_principal_investigator(name, affiliation=aff)
        dvc.commit()
        row['principal_investigator_record'] = p

    def _import_project(self, dvc, row):
        name = extract_value(row, ('project', 'project_name', 'project name'))
        pi = row['principal_investigator_record']
        proj = None
        for p in pi.projects:
            if p.name == name:
                proj = p

        if proj is None:
            proj = ProjectTbl()
            proj.name = name
            proj.principal_investigator = row['principal_investigator_record']
            proj.checkin_date = datetime.now()
            dvc.add_item(proj)
            dvc.commit()

        row['project_record'] = proj

    def _import_sample(self, dvc, row):
        sam = SampleTbl()

        sam.name = extract_value(row, ('sample', 'sample_name', 'sample name'))
        sam.project = row['project_record']

        material = dvc.get_material(row['material'])
        sam.material = material

        sam.lithology = extract_value(row, ('lith', 'lithology'))
        sam.unit = extract_value(row, ('unit',))
        sam.approximate_age = extract_fvalue(row, ('approximate_age', 'approx. age', 'approximate age'))

        lat = extract_value(row, ('lat', 'latitude'))
        lon = extract_value(row, ('lon', 'long', 'longitude'))

        if lat is None and lon is None:
            northing = extract_value(row, ('n', 'northing', 'utm n', 'utm_n', 'n_utm', 'n utm'))
            easting = extract_value(row, ('e', 'easting', 'utm e', 'utm_e', 'e_utm', 'e utm'))
            zone = extract_value(row, ('zone', 'utm zone', 'utm_zone', 'zone_utm', 'zone utm'))

            lat, lon = convert_utm(northing, easting, zone)

        if lat is not None and lon is not None:
            sam.lat = lat
            sam.lon = lon

        dvc.add_item(sam)

# ============= EOF =============================================
