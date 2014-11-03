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
from traits.api import HasTraits, Button, Instance
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter
from pychron.entry.export.base_irradiation_exporter import BaseIrradiationExporter


def generate_production_ratios_id(dbpr):
    return 0


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

    def _export(self, dbirr):
        # check if irradiation already exists
        dest = self.destination
        action = 'Skipping'
        with dest.session_ctx():
            dest_irr = dest.get_irradiation(dbirr.name)
            if not dest_irr:
                dest_irr = self._export_irradiation(dest, dbirr)
            else:
                self.debug('Irradiation="{}" already exists. {}'.format(dbirr.name, action))

            for level in dbirr.levels:
                self._export_level(dest, dest_irr, dbirr, level)

    def _export_irradiation(self, dest, source_irr):
        self.debug('export irradiation {}'.format(source_irr.name))
        dest_irr = dest.add_irradiation(source_irr.name)
        dest.add_irradiation_chronology(dest_irr, source_irr.chronology)
        return dest_irr

    def _export_level(self, dest, dest_irr, source_irr, source_level):
        action = 'Skipping'
        dest_level = dest.get_irradiation_level(source_irr.name, source_level.name)
        if not dest_level:
            dest_pr = self._export_production_ratios(dest, source_level.production)
            dest_level = dest.add_irradiation_level(dest_irr,
                                                    source_level.name,
                                                    dest_pr)
        else:
            self.debug('Irradiation="{}", Level="{}" already exists. {}'.format(source_irr.name, source_level.name,
                                                                                action))

        for pos in source_level.positions:
            self._export_position(dest, dest_level, pos)

    def _export_production_ratios(self, dest, source_pr):
        action = 'Skipping'
        pid = generate_production_ratios_id(source_pr)
        dest_pr = dest.get_production_ratios(pid)
        if not dest_pr:
            dest_pr = dest.add_production_ratios(source_pr)
        else:
            self.debug('Production Ratios="{}" already exists. {}'.format(source_pr.name, action))

        return dest_pr

    def _export_position(self, dest, dest_level, pos):
        action = 'Skipping'
        idn = pos.labnumber.identifier
        dest_pos = dest.get_irradiation_position(idn)
        if not dest_pos:
            dest.add_irradiation_position(idn, dest_level)
        else:
            self.debug('Irradiation Position="{}" already exists {}'.format(idn, action))

# ============= EOF =============================================



