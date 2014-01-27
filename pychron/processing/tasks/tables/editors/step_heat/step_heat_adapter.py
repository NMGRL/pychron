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

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.tasks.tables.editors.base_adapter import BaseAdapter, PM, BaseGroupAdapter


class StepHeatTableAdapter(BaseAdapter):
    columns = [
        ('Identifier', 'labnumber'),
        ('N', 'aliquot_step_str'),
        ('Temp', 'extract_value'),
        ('Mol. Ar40', 'moles_Ar40'),
        ('Ar40', 'ar40'),
        (PM, 'ar40_err'),

        ('Ar39', 'ar39'),
        (PM, 'ar39_err'),

        ('Ar38', 'ar38'),
        (PM, 'ar38_err'),

        ('Ar37', 'ar37'),
        (PM, 'ar37_err'),

        ('Ar36', 'ar36'),
        (PM, 'ar36_err'),
        ('%40Ar*', 'rad40_percent'),

        ('40Ar*/39ArK', 'F'),
        ('Age', 'age'),
        (PM, 'age_error'),
        ('K/Ca', 'kca'),
        (PM, 'kca_error'),
        ('', 'blank_column')
    ]


class StepHeatGroupTableAdapter(BaseGroupAdapter):
    pass

#============= EOF =============================================
