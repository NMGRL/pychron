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

#============= enthought library imports=======================
from traits.api import Property, Int
from traitsui.tabular_adapter import TabularAdapter
#============= standard library imports ========================
from pychron.experiment.utilities.identifier import make_aliquot_step
from pychron.pychron_constants import EXTRACTION_COLOR, MEASUREMENT_COLOR, SUCCESS_COLOR, \
    SKIP_COLOR, NOT_EXECUTABLE_COLOR, CANCELED_COLOR, TRUNCATED_COLOR, \
    FAILED_COLOR, END_AFTER_COLOR
#============= local library imports  ==========================
COLORS = {'success': SUCCESS_COLOR,
          'extraction': EXTRACTION_COLOR,
          'measurement': MEASUREMENT_COLOR,
          'canceled': CANCELED_COLOR,
          'truncated': TRUNCATED_COLOR,
          'failed': FAILED_COLOR,
          'end_after': END_AFTER_COLOR,
          'invalid': 'red'}


class AutomatedRunSpecAdapter(TabularAdapter):
    font = 'arial 10'
    #===========================================================================
    # widths
    #===========================================================================

    labnumber_width = Int(80)
    aliquot_width = Int(40)
    sample_width = Int(50)
    position_width = Int(50)
    extract_value_width = Int(50)
    extract_units_width = Int(40)
    duration_width = Int(60)
    ramp_duration_width = Int(50)
    cleanup_width = Int(60)
    pattern_width = Int(80)
    beam_diameter_width = Int(65)

    overlap_width = Int(50)
    #    autocenter_width = Int(70)
    #    extract_device_width = Int(125)
    extraction_script_width = Int(80)
    measurement_script_width = Int(90)
    truncate_condition_width = Int(80)
    syn_extraction_width = Int(80)
    post_measurement_script_width = Int(90)
    post_equilibration_script_width = Int(90)

    comment_width = Int(125)
    #===========================================================================
    # number values
    #===========================================================================
    ramp_duration_text = Property
    extract_value_text = Property
    beam_diameter_text = Property
    duration_text = Property
    cleanup_text = Property
    # labnumber_text = Property
    aliquot_text = Property
    overlap_text = Property

    def get_bg_color(self, obj, trait, row, column):
        item = self.item
        if not item.executable:
            color = NOT_EXECUTABLE_COLOR
        else:
            if item.skip:
                color = SKIP_COLOR  # '#33CCFF'  # light blue
            elif item.state in COLORS:
                color = COLORS[item.state]
            elif item.end_after:
                color = COLORS['end_after']
            else:
                if row % 2 == 0:
                    color = 'white'
                else:
                    color = '#E6F2FF'  # light gray blue

        return color

    # def _get_labnumber_text(self, trait, item):
        # it = self.item
        # ln = it.labnumber
        # if it.user_defined_aliquot:
        #     ln = '{}-{:02n}'.format(it.labnumber, it.aliquot)
        # return ln

    def _get_overlap_text(self):
        return self._get_number('overlap', fmt='{:n}')

    def _get_aliquot_text(self, trait, item):
        al = ''
        it = self.item
        if it.aliquot != 0:
            al=make_aliquot_step(it.aliquot, it.step)

        return al

    def _get_ramp_duration_text(self, trait, item):
        return self._get_number('ramp_duration', fmt='{:n}')

    def _get_beam_diameter_text(self, trait, item):
        return self._get_number('beam_diameter')

    def _get_extract_value_text(self, trait, item):
        return self._get_number('extract_value')

    def _get_duration_text(self, trait, item):
        return self._get_number('duration')

    def _get_cleanup_text(self, trait, item):
        return self._get_number('cleanup')

    def _get_number(self, attr, fmt='{:0.2f}'):
        """
            dont display 0.0's
        """
        v = getattr(self.item, attr)
        if v:
            if isinstance(v, str):
                v = float(v)

            return fmt.format(v)
        else:
            return ''

    def _columns_default(self):
        return self._columns_factory()

    def _columns_factory(self):
        cols = [
            #                ('', 'state'),
            ('Labnumber', 'labnumber'),
            ('Aliquot', 'aliquot'),
            ('Sample', 'sample'),
            ('Position', 'position'),
            # #                 ('Autocenter', 'autocenter'),
            # #                 ('Overlap', 'overlap'),
            ('Extract', 'extract_value'),
            ('Units', 'extract_units'),

            ('Ramp (s)', 'ramp_duration'),
            ('Duration (s)', 'duration'),
            ('Cleanup (s)', 'cleanup'),
            ('Overlap (s)', 'overlap'),

            ('Beam (mm)', 'beam_diameter'),
            ('Pattern', 'pattern'),
            ('Extraction', 'extraction_script'),
            ('Measurement', 'measurement_script'),
            ('Truncate', 'truncate_condition'),
            ('SynExtraction', 'syn_extraction'),
            ('Post Eq.', 'post_equilibration_script'),
            ('Post Meas.', 'post_measurement_script'),
            ('Comment', 'comment')
        ]

        return cols


class UVAutomatedRunSpecAdapter(AutomatedRunSpecAdapter):
    def _columns_factory(self):
        cols = [
            #                ('', 'state'),
            ('Labnumber', 'labnumber'),
            ('Aliquot', 'aliquot'),
            ('Sample', 'sample'),
            ('Position', 'position'),

            ('Extract', 'extract_value'),
            ('Units', 'extract_units'),
            ('Rep. Rate', 'reprate'),
            ('Mask', 'mask'),
            ('Attenuator', 'attenuator'),
            ('Cleanup (s)', 'cleanup'),
            ('Extraction', 'extraction_script'),
            ('Measurement', 'measurement_script'),
            ('Truncate', 'truncate_condition'),
            ('SynExtraction','syn_extraction'),
            ('Post Eq.', 'post_equilibration_script'),
            ('Post Meas.', 'post_measurement_script'),
            ('Comment', 'comment')
        ]

        return cols

#============= EOF =============================================
