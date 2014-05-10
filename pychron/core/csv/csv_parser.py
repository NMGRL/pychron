#===============================================================================
# Copyright 2014 Jake Ross
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
import csv

from traits.api import HasTraits, provides


#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.i_column_parser import IColumnParser


@provides(IColumnParser)
class BaseColumnParser(HasTraits):
    _header_offset = 1

    def load(self, p, header_idx=0, **kw):
        self._header_offset = header_idx + 1
        self._load(p, header_idx, **kw)

    def get_value(self, ri, ci):
        raise NotImplementedError

    def _load(self, p, **kw):
        raise NotImplementedError

    def has_key(self, key):
        if isinstance(key, int):
            return 0 <= key < len(self._header)
        else:
            return key in self._header

    def list_attributes(self):
        return self._header

    def get_values(self, keys=None):
        from numpy import array

        if keys is None:
            keys = self._header

        gv = self.get_value
        data = array([[gv(ri, ki) for ki in keys] for ri in self.iternrows()], dtype=float)
        return data.T

    def itervalues(self, keys=None):
        """
            returns a row iterator
            each iteration is a dictionary containing "keys"
            if keys is None return all values

        """
        if keys is None:
            keys = self._header
        gv = self.get_value
        return ({ki: gv(ri, ki) for ki in keys}
                for ri in self.iternrows())

    def iternrows(self):
        return xrange(self._header_offset, self.nrows, 1)

    def _get_index(self, ks):

        if not isinstance(ks, (list, tuple)):
            ks = (ks,)

        for k in ks:
            for ki in (k, k.upper(), k.lower(), k.capitalize(), k.replace('_', '')):
                try:
                    return self._header.index(ki)
                except ValueError, e:
                    print 'exep', e


class CSVParser(BaseColumnParser):
    def _load(self, p, header_idx):
        with open(p, 'U') as fp:
            reader = csv.reader(fp)
            self._lines = list(reader)
            self._header = map(str.strip, self._lines[header_idx])
            self._nrows = len(self._lines)

    def get_value(self, ri, ci):
        if not isinstance(ci, int):
            ci = self._get_index(ci)

        try:
            return self._lines[ri][ci]
        except IndexError:
            pass

    @property
    def nrows(self):
        return self._nrows

#============= EOF =============================================
