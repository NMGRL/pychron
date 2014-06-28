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
#===============================================================================

#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================
from functools import partial
from datetime import datetime

import xlrd

import yaml

from pychron.core.xls.xls_parser import XLSParser
from pychron.experiment.utilities.identifier import make_runid

from pychron.loggable import Loggable


class BaseAnalysisLoader(Loggable):
    pass


class XLSAnalysisLoader(BaseAnalysisLoader):
    def load_analyses(self, p, header_idx=1):
        parser = XLSParser()
        parser.load(p, header_idx)
        self.header_offset = header_idx + 1
        self.parser = parser
        return True

    def get_identifier(self, idx):
        v = self._get_value(idx, 'identifier', '{:n}')
        return v.replace(',', '')

    def get_analysis_time(self, idx):
        v = self._get_value(idx, 'analysis_time')
        v = xlrd.xldate_as_tuple(v, self.parser.workbook.datemode)
        return datetime(*v)

    def get_isotope(self, idx, k):
        return self._get_value(idx, k)

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

    def __getattr__(self, item):
        if item.startswith('get_'):
            attr = item.replace('get_', '')
            return partial(self._get_value, attr=attr)

    def _get_value(self, idx, attr, fmt=None):
        try:
            v = self.parser.get_value(idx + self.header_offset, attr)
            if fmt:
                v = fmt.format(v)
            return v

        except ValueError:
            pass


class YAMLAnalysisLoader(BaseAnalysisLoader):
    def load_analyses(self, p):
        with open(p, 'r') as fp:
            try:
                for d in yaml.load_all(fp.read()):
                    self._import_analysis(d)
            except yaml.YAMLError, e:
                print e

    def _import_analysis(self, d):
        self._add_meta(d)

    def _add_meta(self, d):
        print d['project'], d['sample']


if __name__ == '__main__':
    al = YAMLAnalysisLoader()
    p = '/Users/ross/Sandbox/analysis_import_template.yml'
    al.load_analyses(p)

#============= EOF =============================================

