# ===============================================================================
# Copyright 2013 Jake Ross
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
# ===============================================================================

#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.experiment.easy_parser import EasyParser
from pychron.experiment.importer.import_manager import ImportManager
from pychron.experiment.importer.import_mapper import MinnaBluffMapper


class EasyImporter(IsotopeDatabaseManager):
    def do_import(self):
        ep = EasyParser()
        meta = ep.doc('import')
        self._import_irradiations(meta)


    def _import_irradiations(self, meta):
        im = ImportManager(db=self.db)
        if self._set_source(meta, im):
            if self._set_destination(meta):
                self._set_importer(meta, im)

                if im.do_import(new_thread=False):
                    self.debug('import finished')
                else:
                    self.warning('import failed')

    def _set_importer(self, meta, im):
        imports = meta['imports']

        im.include_analyses = imports['atype'] == 'unknown'
        im.include_blanks = imports['blanks']
        im.include_airs = imports['airs']
        im.include_cocktails = imports['cocktails']

        im.import_kind = 'irradiation'

        im.selected = self._make_import_selection(meta)
        im.dry_run = imports['dry_run']

        im.extractor.mapper = MinnaBluffMapper()

    def _set_destination(self, meta):
        try:
            dest = meta['destination']
        except KeyError:
            return

        db = self.db
        db.name = dest['database']
        db.username = dest['username']
        db.password = dest['password']
        db.host = dest['host']
        return db.connect()

    def _set_source(self, meta, im):
        source = meta['source']
        dbconn_spec = im.extractor.dbconn_spec
        dbconn_spec.database = source['database']
        dbconn_spec.username = source['username']
        dbconn_spec.password = source['password']
        dbconn_spec.host = source['host']
        return im.db.connect()

    def _make_import_selection(self, meta):
        s = [(irrad['name'], map(str.strip, irrad['levels'].split(',')))
             for irrad in meta['irradiations']]
        return s

# ============= EOF =============================================
