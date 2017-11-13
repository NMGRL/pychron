# ===============================================================================
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
# ===============================================================================

# =============enthought library imports========================
import os

from traits.api import Enum, Float, Event, Property, Int, Button, Bool, Str, Any, on_trait_change, String
from traitsui.api import View, HGroup, Item, Group, VGroup, EnumEditor, RangeEditor, ButtonEditor, spring

# from pyface.timer.api import Timer

# =============standard library imports ========================
# import sys, os
# =============local library imports  ==========================
# sys.path.insert(0, os.path.join(os.path.expanduser('~'),
#                               'Programming', 'mercurial', 'pychron_beta'))

from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.graph.time_series_graph import TimeSeriesStreamStackedGraph

from pychron.graph.plot_record import PlotRecord
import time

from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.meter_calibration import MeterCalibration
from pychron.core.helpers.filetools import parse_file
from pychron.hardware.watlow.base_ezzone import BaseWatlowEZZone


class WatlowEZZone(BaseWatlowEZZone, CoreDevice):
    """
        WatlowEZZone represents a WatlowEZZone PM PID controller.
        this class provides human readable methods for setting the modbus registers
    """

    graph_klass = TimeSeriesStreamStackedGraph
    refresh = Button

    autotune = Event
    autotune_label = Property(depends_on='autotuning')
    autotuning = Bool

    configure = Button

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _autotune_fired(self):
        if self.autotuning:
            self.stop_autotune()
        else:
            self.start_autotune()
        self.autotuning = not self.autotuning

    def _configure_fired(self):
        self.edit_traits(view='autotune_configure_view')

    def _refresh_fired(self):
        self.initialization_hook()

    def graph_builder(self, g, **kw):
        g.new_plot(padding_left=40,
                   padding_right=5,
                   zoom=True,
                   pan=True,
                   **kw)
        g.new_plot(padding_left=40,
                   padding_right=5,
                   zoom=True,
                   pan=True,
                   **kw)

        g.new_series()
        g.new_series(plotid=1)

        g.set_y_title('Temp (C)')
        g.set_y_title('Heat Power (%)', plotid=1)

    def get_control_group(self):
        closed_grp = VGroup(
            HGroup(Item('use_pid_bin', label='Set PID',
                        tooltip='Set PID parameters based on setpoint'),
                   Item('use_calibrated_temperature',
                        label='Use Calibration'),
                   Item('coeff_string', show_label=False, enabled_when='use_calibrated_temperature')),
            Item('closed_loop_setpoint',
                 style='custom',
                 label='setpoint',
                 editor=RangeEditor(mode='slider',
                                    format='%0.2f',
                                    low_name='setpointmin', high_name='setpointmax')),
            visible_when='control_mode=="closed"')

        open_grp = VGroup(Item('open_loop_setpoint',
                               label='setpoint',
                               editor=RangeEditor(mode='slider',
                                                  format='%0.2f',
                                                  low_name='olsmin', high_name='olsmax'),
                               visible_when='control_mode=="open"'))

        tune_grp = HGroup(Item('enable_tru_tune'),
                          Item('tru_tune_gain', label='Gain', tooltip='1:Most overshot, 6:Least overshoot'))
        cg = VGroup(HGroup(
            Item('control_mode', editor=EnumEditor(values=['closed', 'open'])),
            Item('max_output', label='Max Output %', format_str='%0.1f'),
            icon_button_editor('advanced_values_button', 'cog')),
                    tune_grp,
                    closed_grp, open_grp)
        return cg

    def _advanced_values_button_fired(self):
        self.edit_traits(view='configure_view')

    def get_configure_group(self):
        """
        """

        output_grp = VGroup(Item('output_scale_low', format_str='%0.3f',
                                 label='Scale Low'),
                            Item('output_scale_high', format_str='%0.3f',
                                 label='Scale High'),
                            label='Output',
                            show_border=True)

        autotune_grp = HGroup(Item('autotune', show_label=False, editor=ButtonEditor(label_value='autotune_label')),
                              Item('configure', show_label=False, enabled_when='not autotuning'),
                              label='Autotune',
                              show_border=True)

        input_grp = Group(VGroup(Item('sensor1_type',
                                      # editor=EnumEditor(values=sensor_map),
                                      show_label=False),
                                 Item('thermocouple1_type',
                                      # editor=EnumEditor(values=tc_map),
                                      show_label=False,
                                      visible_when='_sensor1_type==95'),
                                 Item('input_scale_low', format_str='%0.3f',
                                      label='Scale Low', visible_when='_sensor1_type in [104,112]'),
                                 Item('input_scale_high', format_str='%0.3f',
                                      label='Scale High', visible_when='_sensor1_type in [104,112]')),
                          label='Input',
                          show_border=True)

        pid_grp = VGroup(HGroup(Item('Ph', format_str='%0.3f'),
                                Item('Pc', format_str='%0.3f')),
                         Item('I', format_str='%0.3f'),
                         Item('D', format_str='%0.3f'),
                         show_border=True,
                         label='PID')
        return Group(
            HGroup(spring, Item('refresh', show_label=False)),
            autotune_grp,
            HGroup(output_grp,
                   input_grp),
            pid_grp)

    def autotune_configure_view(self):
        v = View('autotune_setpoint',
                 Item('autotune_aggressiveness', label='Aggressiveness'),
                 VGroup(
                     'enable_tru_tune',
                     Group(
                         Item('tru_tune_band', label='Band'),
                         Item('tru_tune_gain', label='Gain', tooltip='1:Most overshot, 6:Least overshoot'),
                         enabled_when='enable_tru_tune'),
                     show_border=True,
                     label='TRU-TUNE+'
                 ),
                 title='Autotune Configuration',
                 kind='livemodal')
        return v

    def control_view(self):
        return View(self.get_control_group())

    def configure_view(self):
        return View(self.get_configure_group())


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('watlowezzone')
    w = WatlowEZZone(name='temperature_controller',
                     configuration_dir_name='diode')
    w.bootstrap()
    w.configure_traits(view='configure_view')
# ============================== EOF ==========================
