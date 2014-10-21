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
from traits.api import HasTraits
from traitsui.api import View, UItem, TabularEditor
from traitsui.tabular_adapter import TabularAdapter
#============= standard library imports ========================
#============= local library imports  ==========================

class DetectorICTabularAdapter(TabularAdapter):
    pass

class DetectorICView(HasTraits):
    def __init__(self, an):
        self.tabular_adapter = DetectorICTabularAdapter()

        detcols = [(ai.detector.capitalize(), ai.detector) for ai in an.isotopes]
        cols = detcols
        self.tabular_adapter.columns = cols

    def traits_view(self):
        v = View(UItem('ratios', editor=TabularEditor(adapter=self.tabular_adapter)))
        return v

#============= EOF =============================================
