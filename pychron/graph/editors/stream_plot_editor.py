#===============================================================================
# Copyright 2011 Jake Ross
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



#=============enthought library imports=======================
from traits.api import Property, Float, Bool
from traitsui.api import Item, VGroup, TextEditor, HGroup, spring, Label
#=============standard library imports ========================

#=============local library imports  ==========================
from pychron.graph.editors.plot_editor import PlotEditor


class StreamPlotEditor(PlotEditor):
    '''
    '''
#    track_x_min = DelegatesTo('graph')
#    track_x_max = DelegatesTo('graph')
#
#    track_y_min = DelegatesTo('graph')
#    track_y_max = DelegatesTo('graph')

    track_x_max = Property(Bool(True), depends_on='graph.track_x_max')
    track_x_min = Property(Bool(True), depends_on='graph.track_x_min')
    track_y_max = Property(Bool(True), depends_on='graph.track_y_max')
    track_y_min = Property(Bool(True), depends_on='graph.track_y_min')

    data_limit = Property(Float(enter_set=True, auto_set=False),
                          depends_on='_data_limit')
    _data_limit = Float

    def __init__(self, *args, **kw):
        '''

        '''
        super(PlotEditor, self).__init__(*args, **kw)
        if self.graph:
            self._data_limit = self.graph.data_limits[self.id]
            self._build_series_editors()

            self.plot.index_mapper.on_trait_change(self.update_x, 'updated')
            self.plot.value_mapper.on_trait_change(self.update_y, 'updated')

    def _get_track_x_max(self):
        return self.graph.track_x_max

    def _set_track_x_max(self, v):
        self.graph.track_x_max = v

    def _get_track_x_min(self):
        return self.graph.track_x_min

    def _set_track_x_min(self, v):
        self.graph.track_x_min = v

    def _get_track_y_max(self):
        return self.graph.track_y_max[self.id]

    def _set_track_y_max(self, v):
        self.graph.track_y_max[self.id] = v

    def _get_track_y_min(self):
        return self.graph.track_y_min[self.id]

    def _set_track_y_min(self, v):
        self.graph.track_y_min[self.id] = v

    def update_x(self, o, oo, nn):
        '''
        '''
        if not isinstance(nn, bool):
            if self.track_x_min:
                self._xmin = nn.low
            if self.track_x_max:
                self._xmax = nn.high

    def update_y(self, o, n, nn):
        '''
        '''
        if not isinstance(nn, bool):
            if self.track_y_min:
                self._ymin = nn.low
            if self.track_y_max:
                self._ymax = nn.high

    def _track_x_min_changed(self):
        if not self.track_x_min:
            self.graph.set_x_limits(min_=self._xmin, plotid=self.id)
        else:
            self.graph.force_track_x_flag = True

    def _track_x_max_changed(self):
        if not self.track_x_max:
            self.graph.set_x_limits(max_=self._xmax, plotid=self.id)
        else:
            self.graph.force_track_x_flag = True

    def _track_y_min_changed(self):
        if not self.track_y_min:
            self.graph.set_y_limits(min_=self._ymin, plotid=self.id)

    def _track_y_max_changed(self):
        if not self.track_y_max:
            self.graph.set_y_limits(max_=self._ymax, plotid=self.id)

    def get_axes_group(self):
        editor = TextEditor(enter_set=True,
                            auto_set=False)
        xgrp = VGroup('xtitle',
                      HGroup(spring, Label('Track')),
                      HGroup(Item('xmin', editor=editor, format_str='%0.3f',
                                  enabled_when='not object.track_x_min'), spring,
                             Item('track_x_min', show_label=False)),
                      HGroup(Item('xmax', editor=editor, format_str='%0.3f',
                                  enabled_when='not object.track_x_max'), spring,
                             Item('track_x_max', show_label=False))
                      )
        ygrp = VGroup('ytitle',
                      HGroup(Item('ymin', editor=editor, format_str='%0.3f',
                                   enabled_when='not object.track_y_min'), spring,
                              Item('track_y_min', show_label=False)),
                      HGroup(Item('ymax', editor=editor, format_str='%0.3f',
                                  enabled_when='not object.track_y_max'), spring,
                              Item('track_y_max', show_label=False)),
                      )

        return VGroup(Item('data_limit'), xgrp, ygrp, show_border=True)

    def _get_data_limit(self):
        return self._data_limit

    def _set_data_limit(self, v):
        self._data_limit = v
        self.graph.data_limits[self.id] = v
        self.graph.force_track_x_flag = True

    def _validate_data_limit(self, v):
        try:
            return float(v)
        except ValueError:
            pass
#============= EOF ====================================
