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
import xlrd

from pychron.entry.legacy.nmgrl.importer import BaseImporter
from pychron.entry.legacy.nmgrl.mappings import PIMAP, MATMAP
from pychron.entry.legacy.util import XLSHeader, get_dvc
from pychron.entry.tasks.sample.sample_entry import (
    SampleSpec,
    ProjectSpec,
    PISpec,
    MaterialSpec,
)

PIMAPPED = {}
MATMAPPED = {}
BADNAMES = []
BADMATERIALS = []
NAMES = []


class SampleImporter(BaseImporter):
    def _load(self):
        dpath = "../tests/data/Database 1-209 compilation.xls"
        wb = xlrd.open_workbook(dpath)
        sh = wb.sheet_by_index(0)
        header = None

        specs = []
        skipped = []
        for row in sh.get_rows():
            if header is None:
                header = XLSHeader([ri.value for ri in row])
            else:
                samplespec = process_row(header, row)
                if isinstance(samplespec, list):
                    specs.extend(samplespec)
                else:
                    skipped.append(
                        "{},{}".format(
                            samplespec, ",".join([str(r.value) for r in row])
                        )
                    )

        self._header = header
        self._cache = specs
        with open("./skipped_samples.csv", "w") as wfile:
            wfile.write("\n".join(skipped))

    def do_import(self, spec):
        return self._import_spec(spec)

    def fetch_irradiation_info(self, spec):
        print("Sample: importing spec: {}".format(spec))
        row = spec.source_row
        irradiation = self.fetch(row, "Irrad")
        level = self.fetch(row, "Tray")
        position = self.fetch(row, "Hole #", cast=int)
        return irradiation, level, position

    def fetch(self, row, key, **kw):
        return self._header.get(row, key, **kw)

    def find_spec(self, run):
        runid = run.runid
        fc = runid[0]
        if fc == "A":
            # irrad info for airs
            return
        elif fc == "B":
            return
        elif fc == "Z":
            return
        print("     finding spec for: {}".format(runid))

        sln = int(runid.split("-")[0])
        for i, s in enumerate(self._cache):
            # irrad = self._header.get(s.source_row, 'Irrad')
            try:
                ln = self._header.get(s.source_row, "Run (L#)", int)
            except ValueError:
                continue

            if sln == ln:
                return s

    def _import_spec(self, s):
        # add pi
        piname = s.project.principal_investigator.name
        if piname not in NAMES:
            print("adding pi: {}".format(piname))
            NAMES.append(piname)

        dvc = self._dvc
        if dvc:
            dvc.add_principal_investigator(piname)

        # add project
        pname = s.project.name
        if dvc:
            dvc.add_project(pname, piname)
        # dont add material

        projectname = s.project.name
        if projectname in ("J-Curve",):
            return

        # add sample
        args = (
            s.name,
            pname,
            piname,
            s.material.name,
            s.material.grainsize or None,
            s.igsn,
            s.unit,
            s.storage_location,
            s.lithology,
            s.lithology_class,
            s.lithology_group,
            s.lithology_type,
            s.location,
            s.approximate_age,
            s.elevation,
            s.lon,
            s.note,
        )

        line = "".join(["{:<30s}".format(a or "---") for a in args])
        print("adding {}".format(line))
        print("dvc {}".format(dvc))
        if dvc:
            return dvc.add_sample(
                s.name,
                pname,
                piname,
                s.material.name,
                s.material.grainsize or None,
                igsn=s.igsn,
                unit=s.unit,
                storage_location=s.storage_location,
                lithology=s.lithology,
                lithology_class=s.lithology_class,
                lithology_group=s.lithology_group,
                lithology_type=s.lithology_type,
                location=s.location,
                approximate_age=s.approximate_age,
                elevation=s.elevation,
                lat=s.lat,
                lon=s.lon,
                note=s.note,
            )


def get_piname(p):
    if "/" in p:
        ps = p.split("/")
    else:
        ps = (p,)

    for pi in ps:
        if pi in PIMAP:
            if pi not in PIMAPPED:
                PIMAPPED[p] = PIMAP[pi]

            return PIMAP[pi]


def process_row(header, r):
    p = header.get(r, "Person")
    if not p:
        p = "NMGRL"

    p = p.strip().lower()
    piname = get_piname(p)
    if piname is None:
        if p not in BADNAMES:
            BADNAMES.append(p)
        return "Invalid pi: {}".format(p)

    pispec = PISpec(name=piname)

    project = header.get(r, "Project")
    if not project:
        return "Missing Project"

    pspec = ProjectSpec(name=project)
    pspec.principal_investigator = pispec

    # spec = SampleSpec()
    # spec.project = pspec
    #

    specs = []
    mspecs = make_mspecs(header, r)
    if isinstance(mspecs, str):
        return mspecs

    if not isinstance(mspecs, list):
        mspecs = (mspecs,)

    for mspec in mspecs:
        spec = SampleSpec(
            project=pspec, material=mspec, name=header.get(r, "Sample ID")
        )
        spec.source_row = r
        specs.append(spec)

    return specs


def make_mspecs(header, r):
    def make_mspec(mm):
        mm = mm.lower()
        if mm not in MATMAP:
            if mm not in BADMATERIALS:
                # print('Invalid Material "{}"'.format(mm))
                BADMATERIALS.append(mm)
            return 'Invalid Material "{}"'.format(mm)

        if mm not in MATMAPPED:
            MATMAPPED[mm] = MATMAP[mm]

        mspec = MaterialSpec(name=MATMAP[mm])
        return mspec

    m = header.get(r, "Mineral")
    if not m:
        return "Missing Material"

    if "/" in m:
        mspecs = []
        for mi in m.split("/"):
            mi = make_mspec(mi)
            if not isinstance(mi, MaterialSpec):
                return mi
            else:
                mspecs.append(mi)

        return mspecs
    else:
        return make_mspec(m)


# def import_spec(dvc, r, s):
#     # add pi
#     piname = s.project.principal_investigator.name
#     if piname not in NAMES:
#         # print('adding pi: {}'.format(piname))
#         NAMES.append(piname)
#     return
#     # dvc.add_principal_investigator(piname)
#
#     # add project
#     pname = s.project.name
#     # dont add material
#     # add sample
#
#     projectname = s.project.name
#     if projectname in ('J-Curve',):
#         return
#
#     args = (s.name,
#             pname,
#             piname,
#             s.material.name,
#             s.material.grainsize or None,
#             s.igsn,
#             s.unit,
#             s.storage_location,
#             s.lithology,
#             s.lithology_class,
#             s.lithology_group,
#             s.lithology_type,
#             s.location,
#             s.approximate_age,
#             s.elevation,
#             s.lon,
#             s.note)
#
#     line = ''.join(['{:<30s}'.format(a or '-') for a in args])
#     print('adding {}'.format(line))
#     print('row {}'.format(r))
#     dvc.add_sample(s.name,
#                    pname,
#                    piname,
#                    s.material.name,
#                    s.material.grainsize or None,
#                    igsn=s.igsn,
#                    unit=s.unit,
#                    storage_location=s.storage_location,
#                    lithology=s.lithology,
#                    lithology_class=s.lithology_class,
#                    lithology_group=s.lithology_group,
#                    lithology_type=s.lithology_type,
#                    location=s.location,
#                    approximate_age=s.approximate_age,
#                    elevation=s.elevation,
#                    lat=s.lat, lon=s.lon,
#                    note=s.note)


# def main():
#     dvc = get_dvc()

# dpath = './tests/data/Database 1-209 compilation.xls'
# wb = xlrd.open_workbook(dpath)
# sh = wb.sheet_by_index(0)
# header = None
#
# specs = []
# skipped = []
# for row in sh.get_rows():
#     if header is None:
#         header = XLSHeader([ri.value for ri in row])
#     else:
#         samplespec = process_row(header, row)
#         if isinstance(samplespec, list):
#             specs.extend(samplespec)
#         else:
#             skipped.append('{},{}'.format(samplespec, ','.join([str(r.value) for r in row])))
#
# with open('./skipped_samples.csv', 'w') as wfile:
#     wfile.write('\n'.join(skipped))

# for row, spec in sorted(specs, key=lambda a: a[1].project.principal_investigator.name):
#     import_spec(dvc, row, spec)
#
# for k, v in sorted(MATMAPPED.items()):
#     print('mapping {:<20s}->{}'.format(k, v))
#
# for k, v in sorted(PIMAPPED.items()):
#     print('mapping {:<20s}->{}'.format(k, v))
#
# # for mi in BADMATERIALS:
# #     print('bad mat: {}'.format(mi))
# print(len(BADNAMES))
# for bi in sorted(BADNAMES):
#     print('bad pi: {}'.format(bi))
# dbpi = dvc.get_principal_investigator(bi)
# if dbpi:
# print('bad pi: {}, {}'.format(bi, dbpi.name if dbpi else ''))
# print("'{}': '{}',".format(bi, dbpi.name))


# if __name__ == '__main__':
#     main()
# ============= EOF =============================================
