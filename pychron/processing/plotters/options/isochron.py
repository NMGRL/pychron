#===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Bool, Float, Property, String
from traitsui.api import VGroup, HGroup, Item, Group
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.plotters.options.age import AgeOptions
from pychron.processing.plotters.options.option import InverseIsochronPlotOptions


class InverseIsochronOptions(AgeOptions):
    plot_option_name = 'Inv. Isochron'
    plot_option_klass = InverseIsochronPlotOptions

    fill_ellipses=Bool(False)

    show_nominal_intercept=Bool(False)
    nominal_intercept_label=String('Atm',enter_set=True, auto_set=False)
    nominal_intercept_value=Property(Float, depends_on='_nominal_intercept_value')
    _nominal_intercept_value=Float(295.5, enter_set=True, auto_set=False)
    invert_nominal_intercept=Bool(True)

    def _get_dump_attrs(self):
        attrs = super(AgeOptions, self)._get_dump_attrs()
        attrs += ['fill_ellipses',
                  'show_nominal_intercept',
                  'nominal_intercept_label',
                  '_nominal_intercept_value',
                  'invert_nominal_intercept']
        return attrs

    def _get_groups(self):
        g = Group(label='Calculations')

        g2 = Group(HGroup(Item('show_info', label='Show'),
                          label='Info'),
                   Item('fill_ellipses', ),
                   Item('label_box'),
                   VGroup(Item('show_nominal_intercept'),
                          HGroup(Item('nominal_intercept_label', label='Label', enabled_when='show_nominal_intercept'),
                          Item('_nominal_intercept_value', label='Value', enabled_when='show_nominal_intercept'),
                          Item('invert_nominal_intercept',label='Invert')),
                          label='Nominal Intercept'),
                   label='Display')

        # egrp=Group(
        #            label='Display')

        return (VGroup(self._get_title_group(),
                      # egrp,
                      g, g2, label='Options'),)

    def _set_nominal_value(self, v):
        self._nominal_intercept_value=v

    def _get_nominal_intercept_value(self):
        v=self._nominal_intercept_value
        if self.invert_nominal_intercept:
            v **= -1
        return v
#============= EOF =============================================
