# ===============================================================================
# Copyright 2015 Jake Ross
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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change, List
from traitsui.api import View, UItem, Item, HGroup, VGroup, EnumEditor


# ============= standard library imports ========================
# ============= local library imports  ==========================

class DefinePeakCenterView(HasTraits):
    detector = Str
    isotope = Str
    detectors = List
    isotopes = List
    dac = Float

    def traits_view(self):
        v = View(VGroup(UItem('detector', editor=EnumEditor(name='detectors')),
                        UItem('isotope', editor=EnumEditor(name='isotopes')),
                        Item('dac', label='DAC')),
                 title='Define Peak Center',
                 kind='live_modal')
        return v

# ============= EOF =============================================
