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
import struct

from traits.api import Instance

# ============= standard library imports ========================
import binascii
# ============= local library imports  ==========================
from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter
from pychron.entry.export.base_irradiation_exporter import BaseIrradiationExporter


SRC_PR_KEYS = ('Ca3637', 'Ca3637_err',
               'Ca3937', 'Ca3937_err',
               'K4039', 'K4039_err',
               'Cl3638', 'Cl3638_err',
               'Ca3837', 'Ca3837_err',
               'K3839', 'K3839_err',
               'K3739', 'K3739_err',
               'Cl_K', 'Cl_K',
               'Ca_K', 'Ca_K')


def generate_production_ratios_id(vs):
    txt = ''.join([struct.pack('>f', vi) for vi in vs])
    return binascii.crc32(''.join(txt))


def generate_source_pr_id(dbpr):
    if dbpr:
        vs = [getattr(dbpr, k) for k in SRC_PR_KEYS]
    else:
        vs = [0]

    return generate_production_ratios_id(vs)


class MassSpecIrradiationExporter(BaseIrradiationExporter):
    """
        export irradiation from the pychron database to a mass spec database
    """
    destination = Instance(MassSpecDatabaseAdapter)

    def setup(self):
        """
            return True if connection to dest made
        """
        return self.destination.connect()

    def export_production_ratio(self):
        pass

    def export_chronology(self, irradname):
        with self.destination.session_ctx():
            with self.source.session_ctx():
                dbirrad = self.source.get_irradiation(irradname)
                self._export_chronology(dbirrad)

    def _export(self, dbirrad):
        # check if irradiation already exists
        dest = self.destination
        action = 'Skipping'

        irradname = dbirrad.name
        with dest.session_ctx():
            if not dest.get_irradiation_exists(irradname):
                self._export_chronology(dbirrad)
            else:
                self.debug('Irradiation="{}" already exists. {}'.format(irradname, action))

            for level in dbirrad.levels:
                self._export_level(irradname, level)

    def _export_chronology(self, src_irr):
        self.info('exporting chronology for "{}"'.format(src_irr.name))
        dest = self.destination

        for p, s, e in src_irr.chronology.get_doses():
            self.debug('adding dose power={} start={} end={}'.format(p, s, e))
            dest.add_irradiation_chronology_entry(src_irr.name, s, e)

    def _export_level(self, irradname, source_level):
        action = 'Skipping'
        dest = self.destination
        levelname = source_level.name

        dest_level = dest.get_irradiation_level(irradname, levelname)
        if not dest_level:
            dest_pr = self._export_production_ratios(dest, source_level.production)
            # dest_level = dest.add_irradiation_level(source_level.name, dest_pr)
        else:
            self.debug('Irradiation="{}", Level="{}" already exists. {}'.format(irradname, levelname, action))

        for pos in source_level.positions:
            self._export_position(dest, dest_level, pos)

    def _export_production_ratios(self, dest, source_pr):
        action = 'Skipping'
        pid = generate_source_pr_id(source_pr)
        dest_pr = dest.get_production_ratio_by_id(pid)
        # if not dest_pr:
        #     dest_pr = dest.add_production_ratios(source_pr)
        # else:
        #     self.debug('Production Ratios="{}" already exists. {}'.format(source_pr.name, action))
        #
        # return dest_pr

    def _export_position(self, dest, dest_level, pos):
        action = 'Skipping'

        # idn = pos.labnumber.identifier
        # dest_pos = dest.get_irradiation_position(idn)
        # if not dest_pos:
        #     dest.add_irradiation_position(idn, dest_level)
        # else:
        #     self.debug('Irradiation Position="{}" already exists {}'.format(idn, action))

# ============= EOF =============================================



