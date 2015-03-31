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
from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter, PR_KEYS
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
    """
        use a crc32 to generate a hash for this set of pr ratio values.
        pack each value as a binary single, concat, then calculate
    :param vs:
    :return:
    """
    txt = ''.join([struct.pack('>f', vi) for vi in vs])
    return binascii.crc32(txt)


def generate_source_pr_id(dbpr):
    if dbpr:
        vs = [getattr(dbpr, k) or 0 for k in SRC_PR_KEYS]
    else:
        vs = [0]

    return generate_production_ratios_id(vs)


def pr_dict(dbpr):
    d = {dk: getattr(dbpr, sk) for sk, dk in zip(SRC_PR_KEYS, PR_KEYS)}

    dd = {dk: getattr(dbpr, sk) for sk, dk in zip(('name',), ('Label',))}
    d.update(dd)

    return d


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

    def _export_level(self, irradname, src_level):
        action = 'Skipping'
        dest = self.destination
        levelname = src_level.name

        dest_level = dest.get_irradiation_level(irradname, levelname)
        if not dest_level:
            self.debug('exporting level {} {}'.format(irradname, levelname))
            dest_pr = self._export_production_ratios(src_level.production)
            try:
                holder = src_level.holder.name
            except AttributeError:
                holder = ''

            dest.add_irradiation_level(irradname, src_level.name,
                                                    holder, dest_pr)
        else:
            self.debug('Irradiation="{}", Level="{}" already exists. {}'.format(irradname, levelname, action))

        for pos in src_level.positions:
            self._export_position(dest, '{}{}'.format(irradname, src_level.name), pos)

    def _export_production_ratios(self, source_pr):
        dest = self.destination
        action = 'Skipping'
        pid = generate_source_pr_id(source_pr)
        dest_pr = dest.get_production_ratio_by_id(pid)
        if not dest_pr:
            pdict = pr_dict(source_pr)
            pdict['ProductionRatiosID']=pid
            dest_pr = dest.add_production_ratios(pdict)
            dest.flush()
        else:
            self.debug('Production Ratios="{}" already exists. {}'.format(source_pr.name, action))

        return dest_pr

    def _export_position(self, dest, irradiation_level, pos):
        action = 'Skipping'

        idn = pos.labnumber.identifier
        dest_pos = dest.get_irradiation_position(idn)
        if not dest_pos:
            self.debug('Exporting position {} {}'.format(idn, irradiation_level))
            dest.add_irradiation_position(idn, irradiation_level, pos.position)

        else:
            self.debug('Irradiation Position="{}" already exists {}'.format(idn, action))

# ============= EOF =============================================



