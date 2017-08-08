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
from traitsui.api import View, UItem, InstanceEditor, VGroup, Item, EnumEditor, TableEditor
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import TableColumn


class Detector(HasTraits):
    name = Str
    enabled = Str
    deflection = Str

    def __init__(self, obj):
        self.name = obj.name
        self.enabled = False
        self.deflection = obj.deflection


class MFTableConfig(HasTraits):
    peak_center_config = Any
    detectors = List
    available_detector_names = List
    finish_detector = Str
    finish_isotope = Str

    isotopes = List
    isotope = Str

    def get_finish_position(self):
        return self.finish_isotope, self.finish_detector

    def set_detectors(self, dets):
        self.detectors = [Detector(d) for d in dets]
        self.available_detector_names = [di.name for di in self.detectors]

    def traits_view(self):
        pcc = VGroup(UItem('peak_center_config',
                           editor=InstanceEditor(),
                           style='custom'), label='Peak Center Config.', show_border=True)

        cols = [CheckboxColumn(name='enabled'), TableColumn(name='name'),
                TableColumn(name='deflection')]

        v = View(VGroup(

            Item('detectors',
                 editor=TableEditor(columns=cols)),
            Item('isotope', editor=EnumEditor(name='isotopes')),
            VGroup(Item('finish_detector', editor=EnumEditor(name='available_detector_names')),
                   Item('finish_isotope', editor=EnumEditor(name='isotopes')),
                   show_border=True, label='End Position'),
            pcc),

            kind='livemodal',
            buttons=['OK', 'Cancel'])
        return v

# ============= EOF =============================================
