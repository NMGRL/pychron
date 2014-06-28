# ===============================================================================
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

#============= standard library imports ========================
#============= local library imports  ==========================
import yaml

from pychron.loggable import Loggable


class BaseAnalysisLoader(Loggable):
    pass


class XLSAnalysisLoader(BaseAnalysisLoader):
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

