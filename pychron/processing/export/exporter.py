#===============================================================================
# Copyright 2012 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from traits.api import Instance, on_trait_change
from uncertainties import nominal_value, std_dev

from pychron.loggable import Loggable
from pychron.experiment.utilities.mass_spec_database_importer import MassSpecDatabaseImporter



#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.export.destinations import MassSpecDestination


class Exporter(Loggable):
    def start_export(self):
        return True

    def export(self, *args, **kw):
        raise NotImplementedError

    def rollback(self):
        pass


class MassSpecExporter(Exporter):
    destination = Instance(MassSpecDestination, ())

    def __init__(self, *args, **kw):
        """
            destination: dict.
                dict, required keys are (username, password, host, name)
        """
        super(MassSpecExporter, self).__init__(*args, **kw)
        importer = MassSpecDatabaseImporter()
        self.importer = importer

    @on_trait_change('destination:[username, password, host, name]')
    def set_destination(self, name, new):
        importer = self.importer
        db = importer.db
        # for k in ('username', 'password', 'host', 'name'):
        setattr(db, name, new)
        # db.connect()

    def start_export(self):
        self.importer.db.connect()
        return self.importer.db.connected

    def export(self):
        self.info('committing current session to database')
        self.importer.db.commit()
        self.info('commit successful')

    #        self.extractor.db.close()

    def rollback(self):
        """
            Mass Spec schema doesn't allow rollback
        """
        pass

    #        self.info('rollback')
    #        self.extractor.db.rollback()
    #        self.extractor.db.reset()

    def add(self, spec):
        db = self.importer.db

        # rid = spec.runid
        # convert rid
        # if rid == 'c':
        #     if spec.mass_spectrometer == 'Pychron Jan':
        #         rid = '4359'
        #     else:
        #         rid = '4358'
        rid = self.importer.get_identifier(spec)

        irrad = spec.irradiation
        level = spec.level

        prodid = self.importer.add_irradiation_production(spec.production_name,
                                                          spec.production_ratios,
                                                          spec.interference_corrections)

        self.importer.add_irradiation_chronology(irrad, spec.chron_dosages)

        self.importer.add_irradiation(irrad, level, prodid)
        self.importer.add_irradiation_position(spec.irradpos,
                                               '{}{}'.format(irrad, level),
                                               spec.irradiation_position,
                                               j=float(nominal_value(spec.j or 0)),
                                               jerr=float(std_dev(spec.j or 0))
                                               )

        if db.get_analysis(rid, spec.aliquot, spec.step):
            self.debug('analysis {} already exists in database'.format(rid))
        else:
            spec.update_rundatetime = True
            self.importer.add_analysis(spec)
            return True



#============= EOF =============================================
