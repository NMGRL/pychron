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
from traits.api import Str, Int, Property, Bool
from traitsui.api import Item, Group, HGroup, UItem

#============= standard library imports ========================
#============= local library imports  ==========================

import re
from pychron.processing.plotters.options.age import AgeOptions
from pychron.processing.plotters.options.option import SpectrumPlotOption

plat_regex = re.compile(r'\w{1,2}-{1}\w{1,2}$')


class SpectrumOptions(AgeOptions):
    step_nsigma = Int(2)
    plot_option_klass = SpectrumPlotOption

    force_plateau = Bool(False)
    plateau_steps = Property(Str)
    _plateau_steps = Str
    plot_option_name = 'age_spectrum'

    def _get_plateau_steps(self):
        return self._plateau_steps

    def _set_plateau_steps(self, v):
        self._plateau_steps = v

    def _validate_plateau_steps(self, v):
        if plat_regex.match(v):
            s, e = v.split('-')
            try:
                assert s < e
                return v
            except AssertionError:
                pass

    def _get_dump_attrs(self):
        attrs = super(SpectrumOptions, self)._get_dump_attrs()
        return attrs + ['step_nsigma',
                        'force_plateau',
                        '_plateau_steps']

    def _get_groups(self):

        plat_grp = Group(
            HGroup(
                Item('force_plateau',
                     tooltip='Force a plateau over provided steps'
                ),
                UItem('plateau_steps',
                      enabled_when='force_plateau',
                      tooltip='Enter start and end steps. e.g A-C '
                ),
            ),
            label='Plateau'
        )

        g = Group(
            plat_grp,
            label='Calculations'
        )
        return (g, )

    #============= EOF =============================================
