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
import binascii
import struct

from traits.api import Instance
from uncertainties import std_dev, nominal_value

from pychron.entry.export.base_irradiation_exporter import BaseIrradiationExporter
from pychron.mass_spec.database.massspec_database_adapter import MassSpecDatabaseAdapter, PR_KEYS

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
        dest = MassSpecDatabaseAdapter(bind=False)
        dest.trait_set(**self.destination_spec)
        self.destination = dest

        return self.destination.connect()

    def export_chronology(self, irradname):
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
            dest.commit()

    def _export_chronology(self, src_irr):
        self.info('Exporting chronology for "{}"'.format(src_irr.name))
        dest = self.destination
        chron = self.source.get_chronology(src_irr.name)

        for p, s, e in chron.get_doses():
            self.debug('Adding dose power={} start={} end={}'.format(p, s, e))
            dest.add_irradiation_chronology_entry(src_irr.name, s, e)

    def _export_level(self, irradname, src_level):
        action = 'Skipping'
        dest = self.destination
        levelname = src_level.name

        dest_level = dest.get_irradiation_level(irradname, levelname)
        if not dest_level:
            self.debug('Exporting level {} {}'.format(irradname, levelname))
            dest_pr = self._export_production_ratios(irradname, levelname)
            try:
                holder = src_level.holder
            except AttributeError:
                holder = ''

            dest.add_irradiation_level(irradname, src_level.name,
                                       holder, dest_pr)
        else:
            self.debug('Irradiation="{}", Level="{}" already exists. {}'.format(irradname, levelname, action))

        for pos in src_level.positions:
            self._export_position(dest, irradname, src_level.name, pos)

    def _export_production_ratios(self, irrad, level):

        dest = self.destination
        action = 'Skipping'

        name, source_pr = self.source.get_production(irrad, level)
        pid = generate_source_pr_id(source_pr)
        dest_pr = dest.get_production_ratio_by_id(pid)
        if not dest_pr:
            self.debug('Add Production Ratios="{}"'.format(source_pr.name))
            pdict = pr_dict(source_pr)
            pdict['ProductionRatiosID'] = pid
            dest_pr = dest.add_production_ratios(pdict)
            dest.flush()
        else:
            self.debug('Production Ratios="{}" already exists. {}'.format(source_pr.name, action))

        return dest_pr

    def _export_position(self, dest, irrad, level, pos):
        action = 'Skipping'

        idn = pos.identifier
        if not idn:
            return

        dest_pos = dest.get_irradiation_position(idn)
        if not dest_pos:
            self.debug('Exporting position {} {}{}'.format(idn, irrad, level))
            try:
                mat = pos.sample.material.name
                dbmat = dest.get_material(mat)
                if not dbmat:
                    dest.add_material(mat)

            except AttributeError:
                mat = ''
            try:
                # f = pos.labnumber.selected_flux_history.flux
                # j, jerr = f.j, f.j_err
                uj = self.source.get_flux(irrad, level, pos.position)
                j, jerr = nominal_value(uj), std_dev(uj)
            except AttributeError:
                j, jerr = 0, 0

            note = pos.note
            sample_name = pos.sample.name
            sam = dest.get_sample(sample_name)
            if sam:
                sampleid = sam.SampleID
            else:
                try:
                    pname = pos.sample.project.name
                    proj = dest.get_project(pname)
                    if not proj:
                        proj = dest.add_project(pname,
                                                PrincipalInvestigator=pos.sample.project.principal_investigator.name)
                except AttributeError:
                    proj = None

                sam = dest.add_sample(sample_name)
                if proj:
                    sam.project = proj

                dest.commit()
                sam = dest.get_sample(sample_name)
                sampleid = sam.SampleID

            dest.add_irradiation_position(idn, '{}{}'.format(irrad, level), pos.position,
                                          material=mat,
                                          sample=sampleid,
                                          j=float(j), jerr=float(jerr), note=note)

        else:
            self.debug('Irradiation Position="{}" already exists {}'.format(idn, action))

# ============= EOF =============================================
