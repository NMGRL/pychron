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
from traits.api import HasTraits, Instance
from traitsui.api import View, Item, VGroup, Spring, HGroup, ButtonEditor, EnumEditor

#============= standard library imports ========================
#============= local library imports  ==========================

POSITION_TOOLTIP = '''Set the position for this analysis or group of analyses.
Examples:
1. 4 or p4 (goto position 4)
2. 3,4,5 (goto positions 3,4,5. treat as one analysis)
3. 7-12 (goto positions 7,8,9,10,11,12. treat as individual analyses)
4. 7:12 (same as #3)
5. 10:16:2 (goto positions 10,12,14,16. treat as individual analyses)
6. D1 (drill position 1)
7. T1-2 (goto named position T1-2 i.e transect 1, point 2)
8. L3 (trace path L3)
9. 1-6;9;11;15-20 (combination of rules 2. and 3. treat all positions as individual analyses)
'''

PATTERN_TOOLTIP = 'Select a pattern from Remote or Local Patterns. \
If unsure from which group to choice use a "Remote" pattern'


class FactoryView(HasTraits):
    model = Instance('pychron.experiment.automated_run.factory.AutomatedRunFactory')

    def trait_context(self):
        return {'object': self.model}

    def traits_view(self):
        v = View(self._get_group())
        return v

    def _get_group(self):
        sspring = lambda width=17: Spring(springy=False, width=width)
        extract_grp = VGroup(
            HGroup(sspring(width=33),
                   Item('extract_value', label='Extract',
                        tooltip='Set the extract value in extract units',
                        enabled_when='extractable'),
                   Item('extract_units',
                        show_label=False,
                        editor=EnumEditor(name='extract_units_names')),
                   Item('ramp_duration', label='Ramp Dur. (s)'), ),
            HGroup(
                Item('time_zero_offset',
                     label='T_o offset (s)',
                     tooltip='# of seconds afer inlet opens to set time zero'),
                Item('overlap', label='Overlap (s)', tooltip='Duration to wait before staring next run')),
            self._step_heat_group(),
            HGroup(
                Item('duration', label='Duration (s)',
                     tooltip='Set the number of seconds to run the extraction device.'),
                Item('cleanup', label='Cleanup (s)',
                     tooltip='Set the number of seconds to getter the sample gas')),
            Item('beam_diameter'),
            self._position_group(),
            label='Extract',
            show_border=True)
        return extract_grp

    def _position_group(self):
        grp = HGroup(
            Item('position',
                 tooltip=POSITION_TOOLTIP),
            Item('pattern',
                 show_label=False,
                 tooltip=PATTERN_TOOLTIP,
                 editor=EnumEditor(name='patterns')),
            Item('edit_pattern',
                 show_label=False,
                 editor=ButtonEditor(label_value='edit_pattern_label')))
        return grp

    def _step_heat_group(self):
        grp = HGroup(
            Item('template',
                 label='Step Heat Template',
                 editor=EnumEditor(name='templates'),
                 show_label=False, ),
            Item('edit_template',
                 show_label=False,
                 editor=ButtonEditor(label_value='edit_template_label')))
        return grp

        #============= EOF =============================================
