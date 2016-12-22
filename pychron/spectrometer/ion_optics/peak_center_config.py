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
import os

from apptools import sweet_pickle as pickle
from traits.api import HasTraits, Str, Bool, Float, List, Enum, Int, Any, Button
from traitsui.api import View, Item, HGroup, Handler, EnumEditor, UItem, VGroup, InstanceEditor, CheckListEditor

from pychron.core.helpers.filetools import add_extension, list_directory2
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.paths import paths
from pychron.pychron_constants import QTEGRA_INTEGRATION_TIMES


class PeakCenterConfigHandler(Handler):
    def closed(self, info, isok):
        if isok:
            info.object.dump()
        return isok


class PeakCenterConfig(HasTraits):
    name = Str

    detectors = List(transient=True)
    detector = Str
    # detector_name = Str

    additional_detectors = List
    available_detectors = List

    isotope = Str('Ar40')
    isotopes = List(transient=True)
    dac = Float
    use_current_dac = Bool(True)
    integration_time = Enum(QTEGRA_INTEGRATION_TIMES)
    directions = Enum('Increase', 'Decrease', 'Oscillate')

    window = Float(0.015)
    step_width = Float(0.0005)
    min_peak_height = Float(1.0)
    percent = Int(80)

    use_interpolation = Bool
    interpolation_kind = Enum('linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic')
    n_peaks = Enum(1, 2, 3, 4)
    select_n_peak = Int
    select_n_peaks = List

    use_dac_offset = Bool
    dac_offset = Float
    calculate_all_peaks = Bool

    def _integration_time_default(self):
        return QTEGRA_INTEGRATION_TIMES[4]  # 1.048576

    def _n_peaks_changed(self, new):

        self.select_n_peaks = [i + 1 for i in range(new)]

        if self.select_n_peak > new:
            self.select_n_peak = new

    def _detector_changed(self, new):
        if new:
            self.available_detectors = [d for d in self.detectors if d != new]

    def traits_view(self):
        degrp = VGroup(UItem('additional_detectors', style='custom',
                             editor=CheckListEditor(name='available_detectors',
                                                    cols=max(1, len(self.available_detectors)))),
                       show_border=True, label='Additional Detectors')

        m_grp = VGroup(HGroup(Item('use_current_dac',
                                   label='Use Current DAC'),
                              Item('dac', enabled_when='not use_current_dac')),
                       Item('integration_time'),
                       Item('directions'),
                       Item('window', label='Peak Width (V)'),
                       Item('step_width', label='Step Width (V)'),
                       show_border=True, label='Measure')
        pp_grp = VGroup(Item('min_peak_height', label='Min Peak Height (fA)'),
                        Item('percent', label='% Peak Height'),
                        HGroup(Item('use_interpolation', label='Use Interpolation'),
                               UItem('interpolation_kind', enabled_when='use_interpolation')),
                        Item('n_peaks', label='Deconvolve N. Peaks'),
                        Item('select_n_peak',
                             editor=EnumEditor(name='select_n_peaks'),
                             enabled_when='n_peaks>1', label='Select Peak'),
                        HGroup(Item('use_dac_offset', label='DAC Offset'),
                               UItem('dac_offset', enabled_when='use_dac_offset')),
                        Item('calculate_all_peaks'),
                        show_border=True, label='Post Process')

        v = View(VGroup(HGroup(Item('detector', editor=EnumEditor(name='detectors')),
                               Item('isotope', editor=EnumEditor(name='isotopes'))),
                        degrp,
                        m_grp,
                        pp_grp))
        return v

    @property
    def active_detectors(self):
        return [self.detector] + self.additional_detectors


class ItemConfigurer(HasTraits):
    active_item = Any

    active_name = Str
    names = List

    item_klass = None

    new_name = Str
    add_button = Button
    root = Str

    def dump(self):
        p = os.path.join(paths.hidden_dir, add_extension('config', '.p'))
        with open(p, 'wfile') as wfile:
            obj = {'name': self.active_name}
            pickle.dump(obj, wfile)

        self.dump_item(self.active_item)

    def load(self, **kw):
        names = list_directory2(self.root, remove_extension=True, extension='.p')
        if 'Default' not in names:
            item = self.item_klass()
            item.name = 'Default'
            self.dump_item(item)
            names = list_directory2(self.root, remove_extension=True, extension='.p')

        name = 'Default'
        p = os.path.join(paths.hidden_dir, add_extension('config', '.p'))
        if os.path.isfile(p):
            with open(p, 'rb') as rfile:
                obj = pickle.load(rfile)
                name = obj.get('name', 'Default')

        self.names = names
        self.active_name = name

        self.active_item.trait_set(**kw)

    def dump_item(self, item):
        name = item.name
        p = os.path.join(self.root, add_extension(name, '.p'))
        with open(p, 'wb') as wfile:
            pickle.dump(item, wfile)

    def get(self, name):
        p = os.path.join(self.root, add_extension(name, '.p'))
        if os.path.isfile(p):
            with open(p, 'rb') as rfile:
                obj = pickle.load(rfile)
        else:
            obj = self.item_klass()

        return obj

    def _load_names(self):
        names = list_directory2(self.root, remove_extension=True, extension='.p')
        self.names = names

    def _active_name_changed(self, name):
        if name:
            self.active_item = self.get(name)

    def _add_button_fired(self):
        v = View(UItem('new_name'),
                 kind='livemodal',
                 width=300,
                 buttons=['OK', 'Cancel'], title='New Configuration Name')
        info = self.edit_traits(view=v)
        if info.result:
            obj = self.active_item
            obj.name = self.new_name
            self.dump_item(obj)
            self._load_names()
            self.active_name = self.new_name

    def traits_view(self):
        v = View(VGroup(HGroup(UItem('active_name',
                                     width=200,
                                     editor=EnumEditor(name='names')),
                               icon_button_editor('add_button', 'add')),
                        UItem('_'),
                        UItem('active_item', style='custom', editor=InstanceEditor()),
                        UItem('_')),
                 buttons=['OK', 'Cancel'],
                 kind='livemodal',
                 title=self.title,
                 width=400,
                 handler=PeakCenterConfigHandler())
        return v


class PeakCenterConfigurer(ItemConfigurer):
    item_klass = PeakCenterConfig
    title = 'Peak Center Configuration'

    detectors = List
    isotopes = List
    available_detectors = List

    def _root_default(self):
        return paths.peak_center_config_dir

    def load(self, **kw):
        kw['detectors'] = self.detectors
        kw['isotopes'] = self.isotopes
        kw['available_detectors'] = self.detectors

        super(PeakCenterConfigurer, self).load(**kw)

        det = self.active_item.detector
        self.active_item.detector = ''
        self.active_item.detector = det

    def get(self, *args, **kw):
        item = super(PeakCenterConfigurer, self).get(*args, **kw)
        item.trait_set(detectors=self.detectors,
                       isotopes=self.isotopes,
                       available_detectors=self.detectors)

        det = item.detector
        item.detector = ''
        item.detector = det
        return item

# if __name__ == '__main__':
#     from pychron.paths import paths
#
#     paths.build('_dev')
#
#     p = PeakCenterConfigurer()
#     p.load()
#     p.configure_traits()

# ============= EOF =============================================
