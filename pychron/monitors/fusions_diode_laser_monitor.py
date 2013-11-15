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



#============= enthought library imports =======================
from traits.api import HasTraits, Bool, Float, Int, Str


#============= standard library imports ========================

#============= local library imports  ==========================
from pychron.monitors.fusions_laser_monitor import FusionsLaserMonitor

class MonitorSeries(HasTraits):
    '''
    '''
    name = Str
    show = Bool
    value = Float

class FusionsDiodeLaserMonitor(FusionsLaserMonitor):
    '''
    '''
    max_temp = Float(800)
    max_tempmin = Int(0)
    max_tempmax = Int(800)
#    update_max_temp = Property(depends_on = '_update_max_temp')
#    _update_max_temp = Float(0)

#    max_coolant_temp = Float(40)
#    max_coolant_tempmin = Int(0)
#    max_coolant_tempmax = Int(45)
#    update_max_coolant_temp = Property(depends_on = '_update_max_coolant_temp')
#    _update_max_coolant_temp = Float(0)
#
#    graph = Instance(TimeSeriesStreamGraph)
#
#    series_list = List
#    def _series_list_default(self):
#        '''
#        '''
#        sl = [MonitorSeries(name = 'coolant_temp'),
#                          MonitorSeries(name = 'laser_temp'),
#                          ]
#
#        for s in sl:
#            s.show = True
#        return sl
#
#    @on_trait_change('series_list.show')
#    def _update_series_list(self, object, name, old, new):
#        '''
#            @type object: C{str}
#            @param object:
#
#            @type name: C{str}
#            @param name:
#
#            @type old: C{str}
#            @param old:
#
#            @type new: C{str}
#            @param new:
#        '''
#        if name == 'show':
#            id = self.series_list.index(object)
#            #if self.graph is not None:
#            self.graph.set_series_visiblity(new, series = id)
#
#    def _graph_default(self):
#        '''
#        '''
#        g = TimeSeriesStreamGraph()
#        g.new_plot(data_limit = 15, scan_delay = self.sample_delay)
#
#        g.new_series()
#        g.new_series()
#
#
#        return g
#
#    def __update_max_temp_changed(self):
#        '''
#        '''
#        v = self._update_max_temp
#        self.graph.record(v, series = 1)
#        self.series_list[1].value = v
#
#    def __update_max_coolant_temp_changed(self):
#        '''
#        '''
#        v = self._update_max_coolant_temp
#        self.graph.record(v, series = 0)
#        self.series_list[0].value = v

    def load_additional_args(self, config):
        '''

        '''
        super(FusionsDiodeLaserMonitor, self).load_additional_args(config)
        self.set_attribute(config, 'max_temp',
                       'General', 'max_temp', cast='float', optional=True)

#    def _get_update_max_temp(self):
#        '''
#        updated every monitor interval
#        '''
#        return self._update_max_temp
#
#    def _get_update_max_coolant_temp(self):
#        '''
#        updated every monitor interval
#        '''
#        return self._update_max_coolant_temp

    def _fcheck_laser_temp(self):
        '''
        '''

        manager = self.manager
        # check laser temp
        self.info('Check laser internal temperature')
        lt = manager.get_laser_internal_temperature(verbose=False)
        if lt is None:
            self.warning('could not read laser internal temperature')

        # self._update_max_temp = lt
        if lt > self.max_temp:
            self.warning('Laser over temperature {:0.2f}'.format(lt))
            manager.emergency_shutoff(reason='Over temp {}'.format(lt))


#============= views ===================================
#    def traits_view(self):
#        '''
#        '''
#
#        sg = self._update_slider_group_factory([('max_temp', 'max_temp', None),
#                                       ('max_coolant_temp', 'max_coolant_temp', None)])
#
#        cols = [CheckboxColumn(name = 'show', editable = True),
#              ObjectColumn(name = 'name', editable = False),
#              ObjectColumn(name = 'value', format = '%0.2f', editable = False)]
#
#        editor = TableEditor(columns = cols,
#                           rows = 3)
#        v = View(
#               Group(
#                   HGroup(Item('sample_delay'), spring),
#                   VGroup(
#                          Item('series_list', editor = editor, show_label = False, height = 0.2),
#                          Item('graph', show_label = False, style = 'custom', height = 0.8),
#                          spring,
#                          ),
#            #       Item('max_laser_temp'),
#                    sg
#                   )
#             )
#        return v
#============= EOF ====================================
