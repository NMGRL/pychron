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
import os
from datetime import datetime

from traits.api import Str, List

#============= standard library imports ========================
import yaml
#============= local library imports  ==========================
from pychron.experiment.utilities.identifier import make_runid
from pychron.processing.analyses.file_analysis import FileAnalysis


class WorkspaceAnalysis(FileAnalysis):
    path = Str
    blank_changes=List
    fit_changes = List

    def _sync(self, obj, *args, **kw):
        self.path = obj

        yd = self._load_yaml(obj)
        attrs=('labnumber','aliquot','step','sample','material','project','comment',
               'uuid',
               'irradiation','irradiation_pos','irradiation_level',
               'age','age_err','age_err_wo_j','age_err_wo_j_irrad',
               'timestamp','ar39decayfactor','ar37decayfactor',
               'cleanup','extract_value','duration','position','mass_spectrometer')
        for attr in attrs:
            if isinstance(attr, tuple):
                attr, ydattr=attr
            else:
                attr,ydattr = attr, attr
            setattr(self, attr, yd[ydattr])

        self.analysis_type = 'unknown'
        self.rundate = datetime.fromtimestamp(self.timestamp)
        self.set_j(yd['j'],yd['j_err'])
        self.record_id=make_runid(self.labnumber, self.aliquot, self.step)
        self.irradi
    def _load_yaml(self, path):
        runid=os.path.splitext(os.path.basename(path))[0]
        with open(path, 'r') as fp:
            return yaml.load(fp)[runid]


#============= EOF =============================================



