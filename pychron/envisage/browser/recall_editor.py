# ===============================================================================
# Copyright 2013 Jake Ross
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
from __future__ import absolute_import

from traits.api import Instance, Str, Int
from traitsui.api import View, UItem, InstanceEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_editor import BaseTraitsEditor


class BaseRecallEditor(BaseTraitsEditor):
    basename = Str
    instance_id = Int

    def set_name(self, name):
        if self.instance_id:
            name = '{} #{}'.format(name, self.instance_id + 1)

        self.name = name


class RecallEditor(BaseRecallEditor):
    analysis = Instance('pychron.processing.analyses.analysis.Analysis')
    analysis_view = Instance('pychron.processing.analyses.view.analysis_view.AnalysisView')

    def __init__(self, analysis, av, *args, **kw):
        self.analysis = analysis
        self.analysis_view = av
        self.basename = analysis.record_id
        super(RecallEditor, self).__init__(*args, **kw)

    def traits_view(self):
        v = View(UItem('analysis_view', style='custom', editor=InstanceEditor()))
        return v

# ============= EOF =============================================
