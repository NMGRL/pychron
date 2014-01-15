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
from datetime import datetime

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.experiment.utilities.identifier import make_runid
from pychron.processing.easy.base_easy import BaseEasy


class EasySensitivity(BaseEasy):
    def _make(self, ep):
        doc = ep.doc('sensitivity')
        # print doc['mass_spectrometer']
        project=doc['project']
        prog=self.open_progress(n=2)
        for ms in doc['mass_spectrometers']:
            mi = ms['name']
            for di in ms['dates']:
                s = datetime.strptime(di['start'], '%m-%d-%Y')
                e = datetime.strptime(di['end'], '%m-%d-%Y')
                for k in ('furnace','co2'):
                    value, error=di[k],0
                    self._set_device_sensitivity(s,e, mi, k, project,
                                                 value,error, prog)
        prog.close()

    def _set_device_sensitivity(self, s, e, mi, ed, project, v,err,prog):
        db=self.db
        with db.session_ctx():
            ans = db.get_analyses_date_range(s, e,
                                             mass_spectrometer=mi,
                                             extract_device=ed,
                                             project=project)
            prog.increase_max(len(ans))
            for ai in ans:
                r = make_runid(ai.labnumber.identifier,
                               ai.aliquot, ai.step)
                prog.change_message('Saving sensitivity for {}'.format(r))
                db.set_analysis_sensitivity(ai, v, err)




#============= EOF =============================================

