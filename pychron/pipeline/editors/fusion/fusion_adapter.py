# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Int
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.editors.base_adapter import BaseAdapter, BaseGroupAdapter
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA


class FusionTableAdapter(BaseAdapter):
    columns = [
        # ('Identifier', 'labnumber'),
        # ('N', 'aliquot_step_str'),
        ('RunID', 'record_id'),
        ('Power', 'extract_value'),
        ('Mol. Ar40', 'moles_Ar40'),
        ('Ar40', 'ar40'),
        (PLUSMINUS_ONE_SIGMA, 'ar40_err'),

        ('Ar39', 'ar39'),
        (PLUSMINUS_ONE_SIGMA, 'ar39_err'),

        ('Ar38', 'ar38'),
        (PLUSMINUS_ONE_SIGMA, 'ar38_err'),

        ('Ar37', 'ar37'),
        (PLUSMINUS_ONE_SIGMA, 'ar37_err'),

        ('Ar36', 'ar36'),
        (PLUSMINUS_ONE_SIGMA, 'ar36_err'),
        ('%40Ar*', 'rad40_percent'),

        ('40Ar*/39ArK', 'F'),
        ('Age', 'age'),
        (PLUSMINUS_ONE_SIGMA, 'age_error'),
        ('K/Ca', 'kca'),
        (PLUSMINUS_ONE_SIGMA, 'kca_error'),
        ('', 'blank_column')]

    record_id_width = Int(60)

class FusionGroupTableAdapter(BaseGroupAdapter):
    pass

# ============= EOF =============================================
