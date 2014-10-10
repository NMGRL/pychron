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
import os

from enable.colors import ColorTrait
from enable.markers import MarkerTrait
from traits.api import Str, Range, on_trait_change, Bool, Dict, Enum, Property, Button
from traitsui.api import View, Item, EnumEditor, HGroup, VGroup, UItem


#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.csv.csv_parser import CSVColumnParser
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.processing.plotters.options.base import BasePlotterOptions
from pychron.pychron_constants import FIT_TYPES, NULL_STR

TIME_SCALARS = {'h': 3600., 'm': 60., 's': 1.0, 'days': (3600. * 24)}

DATABASE_ATTRS = {'Ar41': '01:Ar41',
                  'Ar40': '02:Ar40',
                  'Ar39': '03:Ar39',
                  'Ar38': '04:Ar38',
                  'Ar37': '05:Ar37',
                  'Ar36': '06:Ar36',
                  'Ar35': '07:Ar35',
                  'Ar40/Ar39': '08:Ar40/Ar39',
                  'Ar40/Ar38': '09:Ar40/Ar38',
                  'Ar40/Ar36': '10:Ar40/Ar36',
                  'timestamp': '11:Analysis Time',
                  'cleanup': '12:Cleanup',
                  'extract_value': '13:Extract Value',
                  'duration': '14:Extract Duration',
                  'uage': '15:Age',
                  'uage_wo_j_err': '16:Age w/o Jerr'}


class XYScatterOptions(BasePlotterOptions):
    # update_needed = Event
    auto_refresh = Bool

    index_attr = Str('Ar40')
    value_attr = Str('Ar39')

    marker_size = Range(0.0, 10., 2.0)
    marker = MarkerTrait
    marker_color = ColorTrait

    attrs = Dict(DATABASE_ATTRS)
    index_error = Bool
    value_error = Bool

    index_end_caps = Bool
    value_end_caps = Bool

    index_nsigma = Enum(1, 2, 3)
    value_nsigma = Enum(1, 2, 3)

    index_time_units = Enum('h', 'm', 's', 'days')
    index_time_scalar = Property

    value_time_units = Enum('h', 'm', 's', 'days')
    value_time_scalar = Property
    fit = Enum([NULL_STR] + FIT_TYPES)

    datasource = Enum('Database', 'File')

    file_source_path = Str
    datasource_name = Property(depends_on='file_source_path')
    use_file_source = Property(depends_on='datasource')
    open_file_button = Button
    _parser = None

    def get_marker_dict(self):
        kw = dict(marker=self.marker,
                  marker_size=self.marker_size,
                  color=self.marker_color)
        return kw

    def get_parser(self):
        p = self._parser
        if p is None:
            p = CSVColumnParser()
            p.load(self.file_source_path)
            self._parser = p
        return p

    def _load_hook(self):
        if self.use_file_source:
            self._load_file_source()

    def _load_file_source(self):
        p = self.get_parser()
        keys = p.list_attributes()
        self.attrs = {ai: '{:02n}:{}'.format(i, ai) for i, ai in enumerate(keys)}
        self.index_attr = keys[0]
        self.value_attr = keys[1]

    def _datasource_changed(self, new):
        if new == 'Database':
            self.attrs = DATABASE_ATTRS

    def _get_dump_attrs(self):
        return ['index_attr', 'index_error', 'index_end_caps', 'index_nsigma', 'index_time_units',
                'value_attr', 'value_error', 'value_end_caps', 'value_nsigma', 'value_time_units',
                'fit',
                'marker_color', 'marker', 'marker_size',
                'auto_refresh', 'datasource', 'file_source_path']

    def _get_index_time_scalar(self):
        return TIME_SCALARS[self.index_time_units]

    def _get_value_time_scalar(self):
        return TIME_SCALARS[self.value_time_units]

    def _get_use_file_source(self):
        return self.datasource == 'File'

    def _get_datasource_name(self):
        p = ''
        if os.path.isfile(self.file_source_path):
            p = os.path.basename(self.file_source_path)
        return p

    def _open_file_button_fired(self):

        # dlg=FileDialog(action='open', default_directory=paths.data_dir)
        # dlg.open()
        # if dlg.path:
        #     self.file_source_path=dlg.path
        #     self._load_file_source()

        p = '/Users/ross/Sandbox/xy_scatter_test.csv'
        self.file_source_path = p
        self._load_file_source()

    @on_trait_change('index_+, value_+, marker+')
    def _refresh(self):
        if self.auto_refresh:
            # self.update_needed = True
            self.refresh_plot_needed = True

    def traits_view(self):
        index_grp = VGroup(HGroup(Item('index_attr',
                                       editor=EnumEditor(name='attrs'),
                                       label='X Attr.'),
                                  Item('index_time_units',
                                       label='Units',
                                       visible_when='index_attr=="timestamp"')),
                           HGroup(Item('index_error', label='Show'),
                                  Item('index_end_caps', label='End Caps', enabled_when='index_error'),
                                  Item('index_nsigma', label='NSigma', enabled_when='index_error')),
                           label='X Error',
                           show_border=True)
        value_grp = VGroup(HGroup(Item('value_attr',
                                       editor=EnumEditor(name='attrs'),
                                       label='Y Attr.'),
                                  Item('value_time_units',
                                       label='Units',
                                       visible_when='value_attr=="timestamp"')),
                           HGroup(Item('value_error', label='Show'),
                                  Item('value_end_caps', label='End Caps', enabled_when='value_error'),
                                  Item('value_nsigma', label='NSigma', enabled_when='value_error')),
                           label='Y Error',
                           show_border=True)

        marker_grp = VGroup(
            Item('marker'),
            Item('marker_size', label='Size'),
            Item('marker_color', label='Color'),
            show_border=True)

        datasource_grp = HGroup(Item('datasource'),
                                UItem('datasource_name',
                                      style='readonly',
                                      visible_when='use_file_source'),
                                icon_button_editor('open_file_button', 'document-open',
                                                   visible_when='use_file_source"'))
        v = View(
            HGroup(Item('auto_refresh'),
                   icon_button_editor('refresh_plot_needed', 'refresh')),
            datasource_grp,
            index_grp,
            value_grp,
            marker_grp,
            Item('fit'),
            resizable=True)
        return v

#============= EOF =============================================


