# ===============================================================================
# Copyright 2016 ross
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
import os

from traits.api import File, Directory
# ============= standard library imports ========================
from uncertainties import ufloat

# ============= local library imports  ==========================
from pychron.data_mapper.sources.dvc_source import DVCSource


def get_next(f, idx=0):
    return next(f)[idx]


def get_int(f, idx=0):
    return int(get_next(f, idx))


def get_float(f, idx=0):
    return float(get_next(f, idx))


def get_ufloat(f):
    v = [float(fi) for fi in next(f)]
    return ufloat(*v)
    # return ufloat(*list(map(float, next(f))))


class FileSource(DVCSource):
    selectable = False
    path = File
    _delimiter = ','
    directory = Directory

    def url(self):
        return '{}:{}'.format(self.__class__.__name__, self.path)

    def file_gen(self, delimiter):
        if delimiter is None:
            delim = self._delimiter

        def gen():
            with open(self.path, 'r') as rfile:
                for line in rfile:
                    yield line.strip().split(delim)

        return gen()

    def get_analysis_import_specs(self, delimiter=None):
        if self.directory:
            ps = []
            for di in os.listdir(self.directory):
                self.path = os.path.join(self.directory, di)
                print(os.path.isfile(self.path), self.path)
                # try:
                s = self.get_analysis_import_spec()
                ps.append(s)
                # except BaseException as e:
                #     print('get analysis import specs', e)
        elif self.path:
            ps = [self.get_analysis_import_spec(delimiter)]

        return ps

    # def traits_view(self):
    #     return View(VGroup(UItem('path'), show_border=True, label='File'))
# ============= EOF =============================================
