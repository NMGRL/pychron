# ===============================================================================
# Copyright 2018 ross
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

from __future__ import absolute_import
from __future__ import print_function
import os
import yaml

dataset = """
runid: 
  - 12343-01A
sample: 
  - Foo
project: 
  - Test
load: 
  - 1081
repository_identifier: 
  - Bar
irradiation: 
  - NM-234,A,FC-2
associated:
 - blank_air
 - air
 - cocktail
 - blank_cocktail
 - blank_unknown
"""
doc = """
- name: FitIso
  analysis_types:
    - unknown
  fits:
    - name: Ar40
      fit: Linear
    - name: Ar39
      fit: Linear
    - name: H1
      fit: Average
- name: FitIso
  analysis_types:
    - air
  fits:
    - name: Ar40
      fit: Linear
    - name: Ar39
      fit: Linear
    - name: H1
      fit: Average
- name: FitBlank
  analysis_types:
    - unknown
  reference_types:
    - blank_unknown
  fits:
    - name: Ar40
      fit: Average
    - name: Ar39
      fit: Average
- name: FitBlank
  reference_types:
    - blank_air
  analysis_types:
    - air
  fits:
    - name: Ar40
      fit: Average
    - name: Ar39
      fit: Average
- name: FitBlank
  reference_types:
    - blank_cocktail
  analysis_types:
    - cocktail
  fits:
    - name: Ar40
      fit: Average
    - name: Ar39
      fit: Average
"""


class DataSet:
    def __init__(self):
        self._analyses = []

    def get_analyses(self, atypes):
        return [a for a in self._analyses if a.analysis_type in atypes]


class DataReductionScript:
    def run(self, path):
        if os.path.isfile(path):
            with open(path, 'r') as rf:
                yd = yaml.load(rf)
        else:
            yd = yaml.load(path)

        for step in yd:
            self._do_step(step)

    def _do_step(self, step):
        name = step['name']
        func = getattr(self, '_do_{}'.format(name.lower()))
        func(step)

    def _do_fitiso(self, step):
        print('fitiso', step)

        ans = self.dataset.get_analyses(step['analysis_types'])
        fits = step['fits']
        keys = [f['name'] for f in fits]

        for a in ans:
            a.load_raw_data(keys)
            a.set_fits(fits)

    def _do_fitblank(self, step):
        print('fitblank', step)

        ans = self.dataset.get_analyses(step['analysis_types'])
        refs = self.dataset.get_analyses(step['reference_types'])

        fits = step['fits']
        keys = [f['name'] for f in fits]

        for a in ans:
            pass

    def _do_dataset(self, step):
        print('dodataset', step)

        self.dataset = DataSet()
        for k, v in step.items():
            if k == 'load':
                self._load_analyses_load(v)
            elif k == 'project':
                self._load_analyses_project(v)
            elif k == 'sample':
                self._load_analyses_samples(v)
            elif k == 'runid':
                self._load_analyses_runid(v)
            elif k == 'identifier':
                self._load_analyses_identifier(v)
            elif k == 'irradiation':
                self._load_analyses_irradiation(v)

        associated = step.get('associated', [])
        print('asdf', associated)

    def _load_analyses_load(self, v):
        pass

    def _load_analyses_project(self, v):
        pass

    def _load_analyses_samples(self, v):
        pass

    def _load_analyses_runid(self, v):
        pass

    def _load_analyses_identifier(self, v):
        pass

    def _load_analyses_irradiation(self, vs):
        for v in vs:
            args = v.split(',')
            try:
                irradiation, level, sample = args
            except ValueError:
                sample = None
                try:
                    irradiation, level = args
                except ValueError:
                    level = None
                    irradiation = args[0]

            print('asdf', irradiation, level, sample)


if __name__ == '__main__':
    c = DataReductionScript()
    c.run(doc)
# ============= EOF =============================================
