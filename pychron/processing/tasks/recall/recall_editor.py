#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Property, Instance, Any
from traitsui.api import View, UItem, InstanceEditor
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_editor import BaseTraitsEditor


class RecallEditor(BaseTraitsEditor):
    #model = Any
    analysis_view = Instance('pychron.processing.analyses.analysis_view.AnalysisView')
    #analysis_summary = Any

    name = Property(depends_on='analysis_view.analysis_id')

    def traits_view(self):
        v = View(UItem('analysis_view',
                       style='custom',
                       editor=InstanceEditor()
        ))
        return v

    def _get_name(self):
        #if self.model and self.model.analysis_view:
        if self.analysis_view:
            return self.analysis_view.analysis_id
        else:
            return 'None'

#============= EOF =============================================
