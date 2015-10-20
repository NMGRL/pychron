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

# ============= standard library imports ========================
# ============= local library imports  ==========================
from functools import partial
from datetime import datetime
import uuid

import xlrd
import yaml

from pychron.core.xls.xls_parser import XLSParser
from pychron.experiment.utilities.identifier import make_runid
from pychron.loggable import Loggable
from pychron.pychron_constants import alpha_to_int, ARGON_KEYS


class IsotopeSpec(object):
    name = ''
    detector = ''
    value = 0
    error = 0
    baseline = None
    blank = None


class ImportSpec(object):
    @property
    def record_id(self):
        return make_runid(self.identifier, self.aliquot, self.step)

    @property
    def increment(self):
        """
            return an int
        """
        s = self.step
        if isinstance(s, (str, unicode)):
            s = alpha_to_int(s)

        return s


class BaseAnalysisLoader(Loggable):
    _path = None

    def import_analyses(self):
        pass

    def import_analysis(self):
        pass

    def _import_analysis(self, spec):
        db = self.db
        with db.session_ctx():
            dbprj = db.add_project(spec.project)
            dbmat = db.add_material(spec.material)

            dbsam = db.add_sample(spec.sample, project=dbprj, material=dbmat)
            dbln = db.add_labnumber(spec.identifier, sample=dbsam)

            self._add_analysis(db, dbln, spec)

    def _add_analysis(self, db, dbln, spec):
        dban = db.get_unique_analysis(dbln.identifier, spec.aliquot, spec.step)
        if dban:
            print '{} already exists'.format(spec.record_id)
            # return

        dban = db.add_analysis(dbln, aliquot=spec.aliquot,
                               step=spec.step,
                               uuid=str(uuid.uuid4()),
                               import_id=spec.import_id,
                               increment=spec.increment,
                               comment=spec.comment)

        self._add_measurement(db, dban, spec)
        self._add_isotopes(db, dban, spec)

    def _add_measurement(self, db, dban, spec):
        db.add_measurement(dban, spec.analysis_type, spec.mass_spectrometer)

    def _add_isotopes(self, db, dban, spec):
        dbhist = db.add_fit_history(dban)
        for iso in spec.isotopes.values():
            dbiso = db.add_isotope(dban, iso.name, iso.detector, kind='signal')
            db.add_isotope_result(dbiso, dbhist,
                                  signal_=iso.value,
                                  signal_err=iso.error)

            dbiso = db.add_isotope(dban, iso.baseline.name, iso.baseline.detector, kind='baseline')
            db.add_isotope_result(dbiso, dbhist,
                                  signal_=iso.baseline.value,
                                  signal_err=iso.baseline.error)

    def _add_import(self):
        db = self.db
        with db.session_ctx():
            dbim = db.add_import(source=self._path)
            return int(dbim.id)

    def _delete_analysis(self, i):
        # delete isotope results
        db = self.db
        with db.session_ctx() as sess:
            ln = self.get_identifier(i)
            ai = self.get_aliquot(i)
            st = self.get_step(i)

            dban = db.get_unique_analysis(ln, ai, st)

            sess.delete(dban.measurement)

            for iso in dban.isotopes:
                sess.delete(iso)

            for hist in dban.fit_histories:
                for ri in hist.results:
                    sess.delete(ri)
                sess.delete(hist)
            sess.delete(dban)


class XLSAnalysisLoader(BaseAnalysisLoader):
    def load_analyses(self, p, header_idx=1):
        self._path = p
        parser = XLSParser()
        parser.load(p, header_idx)
        self.header_offset = header_idx + 1
        self.parser = parser
        return True

    def import_analyses(self):
        im_id = self._add_import()
        for i in self.parser.iternrows():
            self.import_analysis(im_id, i)

    def import_analysis(self, im_id, i):
        spec = ImportSpec()
        for attr in ('identifier', 'aliquot', 'step',
                     'material', 'project', 'sample', 'comment',
                     'analysis_type', 'mass_spectrometer'):
            setattr(spec, attr, getattr(self, 'get_{}'.format(attr))(i))

        d = {}
        for iso in ARGON_KEYS:
            isospec = IsotopeSpec()
            v = self.get_isotope(i, iso)
            if v:
                isospec.name = iso
                isospec.detector = self.get_isotope_detector(i, iso)
                self._get_signal(i, iso, isospec)

                bs = IsotopeSpec()
                bs.name = isospec.name
                bs.detector = isospec.detector
                bsk = '{}bs'.format(iso)
                self._get_signal(i, bsk, bs)
                isospec.baseline = bs

                bk = IsotopeSpec()
                bk.name = isospec.name
                bk.detector = isospec.detector

                d[iso] = isospec

        spec.isotopes = d
        spec.import_id = im_id

        self._import_analysis(spec)

    def _get_signal(self, i, k, spec):
        v = self._get_value(i, k)
        if isinstance(v, float):
            spec.value = v
            spec.error = self.get_isotope_error(i, k)

    def delete_analyses(self):
        for i in self.parser.iternrows():
            self._delete_analysis(i)

    def get_identifier(self, idx):
        v = self._get_value(idx, 'identifier', '{:n}')
        return v.replace(',', '')

    def get_analysis_time(self, idx):
        v = self._get_value(idx, 'analysis_time')
        v = xlrd.xldate_as_tuple(v, self.parser.workbook.datemode)
        return datetime(*v)

    def get_isotope(self, idx, k):
        return self._get_value(idx, k)

    def get_isotope_error(self, idx, k):
        return self._get_value(idx, '{}err'.format(k))

    def get_isotope_data(self, idx, k):
        v = self.get_isotope(idx, k)
        i = self.get_identifier(idx)
        a = self.get_aliquot(idx)
        s = self.get_step(idx)
        rid = make_runid(i, a, s)

        if isinstance(v, float):
            return [], []
        else:
            parser = self.parser
            sh = parser.sheet

            def g():
                parser.set_sheet(v, header_idx=0)
                cx, cy = parser.get_index('{}_xs'.format(k)), parser.get_index('{}_ys'.format(k))
                for row in parser.iterblock(0, rid):
                    yield row[cx].value, row[cy].value

            data = list(g())

            self.parser.set_sheet(sh)
            return map(list, zip(*data))

    def get_isotope_detector(self, idx, k):
        k = '{}det'.format(k)
        return self._get_value(idx, k)

    def __getattr__(self, item):
        if item.startswith('get_'):
            attr = item.replace('get_', '')
            return partial(self._get_value, attr=attr)

    def _get_value(self, idx, attr, fmt=None):
        try:
            v = self.parser.get_value(idx, attr)
            if fmt:
                v = fmt.format(v)
            return v

        except ValueError:
            pass


class YAMLAnalysisLoader(BaseAnalysisLoader):
    def load_analyses(self, p):
        with open(p, 'r') as rfile:
            try:
                for d in yaml.load_all(rfile.read()):
                    self._import_analysis(d)
            except yaml.YAMLError, e:
                print 'exception', e

    def _import_analysis(self, d):
        self._add_meta(d)

    def _add_meta(self, d):
        print d['project'], d['sample']


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('analysis_loader')
    # al = YAMLAnalysisLoader()
    # p = '/Users/ross/Sandbox/analysis_import_template.yml'
    # al.load_analyses(p)
    from pychron.database.isotope_database_manager import IsotopeDatabaseManager

    man = IsotopeDatabaseManager(bind=False, connect=False)
    db = man.db
    db.trait_set(kind='mysql',
                 username='root', password='Argon',
                 host='localhost',
                 name='pychrondata_dev')
    db.connect()
    al = XLSAnalysisLoader()
    al.db = db
    al.load_analyses('/Users/ross/Programming/git/pychron_dev/pychron/entry/tests/data/analysis_import.xls')
    al.import_analyses()

    # al.delete_analyses()
# ============= EOF =============================================

