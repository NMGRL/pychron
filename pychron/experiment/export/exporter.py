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
import os
import struct
import base64

from pychron.loggable import Loggable
from pychron.experiment.utilities.mass_spec_database_importer import MassSpecDatabaseImporter

#============= standard library imports ========================
#============= local library imports  ==========================


class Exporter(Loggable):
    def export(self, *args, **kw):
        raise NotImplementedError

    def rollback(self):
        pass


class MassSpecExporter(Exporter):
    def __init__(self, destination, *args, **kw):
        '''
            destination: dict. 
                dict, required keys are (username, password, host, name)
        '''
        super(MassSpecExporter, self).__init__(*args, **kw)

        importer = MassSpecDatabaseImporter()
        db = importer.db
        for k in ('username', 'password', 'host', 'name'):
            setattr(db, k, destination[k])

        self.importer = importer
        db.connect()

    def export(self):
        self.info('committing current session to database')
        self.importer.db.commit()
        self.info('commit successful')

    #        self.extractor.db.close()

    def rollback(self):
        '''
            Mass Spec schema doesn't allow rollback
        '''

    #        self.info('rollback')
    #        self.extractor.db.rollback()
    #        self.extractor.db.reset()

    def add(self, spec):
        db = self.importer.db

        rid = spec.runid
        # convert rid
        if rid == 'c':
            if spec.mass_spectrometer == 'Pychron Jan':
                rid = '4359'
            else:
                rid = '4358'

        if db.get_analysis(rid, spec.aliquot, spec.step):
            self.debug('analysis {} already exists in database'.format(spec.record_id))
        else:
            self.importer.add_analysis(spec)
            self.importer.db.reset()
            return True


class XMLExporter(Exporter):
    def __init__(self, destination, *args, **kw):
        super(XMLExporter, self).__init__(*args, **kw)
        from pychron.core.xml.xml_parser import XMLParser

        xmlp = XMLParser()
        self._parser = xmlp
        self.destination = destination

    def add(self, spec):
        self._make_xml_analysis(self._parser, spec)
        return True

    def export(self):
        if os.path.isdir(os.path.dirname(self.destination)):
            self._parser.save(self.destination)

    def _make_timeblob(self, t, v):
        blob = ''
        for ti, vi in zip(t, v):
            blob += struct.pack('>ff', float(vi), float(ti))
        return blob

    def _make_xml_analysis(self, xmlp, spec):
        an = xmlp.add('analysis', '', None)
        meta = xmlp.add('metadata', '', an)
        xmlp.add('RID', spec.runid, meta)
        xmlp.add('Aliquot', spec.aliquot, meta)
        xmlp.add('Step', spec.step, meta)

        data = xmlp.add('data', '', None)
        sig = xmlp.add('signals', '', data)
        base = xmlp.add('baselines', '', data)
        blank = xmlp.add('blanks', '', data)

        for ((det, isok), si, bi, ublank, signal, baseline, sfit, bfit) in spec.iter():
            iso = xmlp.add(isok, '', sig)

            xmlp.add('detector', det, iso)
            xmlp.add('fit', sfit, iso)
            xmlp.add('value', signal.nominal_value, iso)
            xmlp.add('error', signal.std_dev, iso)

            t, v = zip(*si)
            xmlp.add('blob',
                     base64.b64encode(self._make_timeblob(t, v)), iso,
                     dt="binary.base64"
            )

            iso = xmlp.add(isok, '', base)
            xmlp.add('detector', det, iso)
            xmlp.add('fit', bfit, iso)
            xmlp.add('value', baseline.nominal_value, iso)
            xmlp.add('error', baseline.std_dev, iso)

            t, v = zip(*bi)
            xmlp.add('blob',
                     base64.b64encode(self._make_timeblob(t, v)), iso,
                     dt="binary.base64"
            )

            iso = xmlp.add(isok, '', blank)
            xmlp.add('detector', det, iso)
            xmlp.add('value', ublank.nominal_value, iso)
            xmlp.add('error', ublank.std_dev, iso)

#============= EOF =============================================
