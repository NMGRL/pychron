# ===============================================================================
# Copyright 2017 ross
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
from traits.api import HasTraits, Any, List, Str
from traitsui.api import View, UItem, InstanceEditor, VGroup, Item, CheckListEditor, EnumEditor


class MFTableConfig(HasTraits):
    peak_center_config = Any
    detectors = List
    available_detectors = List

    isotopes = List
    isotope = Str

    def traits_view(self):
        pcc = VGroup(UItem('peak_center_config',
                           editor=InstanceEditor(),
                           style='custom'), label='Peak Center Config.', show_border=True)

        v = View(VGroup(Item('detectors',
                             style='custom', editor=CheckListEditor(name='available_detectors',
                                                                 cols=5)),
                        Item('isotope', editor=EnumEditor(name='isotopes')),
                        pcc),

                 kind='livemodal',
                 buttons=['OK', 'Cancel'])
        return v

# ============= EOF =============================================
