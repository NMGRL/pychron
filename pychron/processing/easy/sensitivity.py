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
from pychron.processing.easy.base_easy import BaseEasy


class EasySensitivity(BaseEasy):
    def _make(self, ep):
        doc = ep.doc('sensitivity')
        # print doc['mass_spectrometer']
        # print doc['project']
        db=self.db
        for ms in doc['mass_spectrometers']:
            mi = ms['name']
            for di in ms['devices']:
                ed = di['name']
                s = datetime.strptime(di['start'], '%m-%d-%Y')
                e = datetime.strptime(di['end'], '%m-%d-%Y')
                with db.session_ctx():
                    ans=db.get_analyses_date_range(s,e,
                                               mass_spectrometer=mi,
                                               extract_device=ed)

                # for ed in ms:
                #     print ed, ms[ed]

                # for d in doc['dates']:
                #     s=datetime.strptime(d['start'],'%m-%d-%Y')
                #     e=datetime.strptime(d['end'],'%m-%d-%Y')
                #     db=self.db
                #     with db.session_ctx():
                # for mi in doc['mass_spectrometers']:
                # print db.get_analysis_date_range(s,e, mas)

#============= EOF =============================================

