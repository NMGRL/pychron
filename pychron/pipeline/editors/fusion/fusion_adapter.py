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
        # ('Mol. Ar40', 'moles_Ar40'),
        ('Ar40', 'Ar40'),
        (PLUSMINUS_ONE_SIGMA, 'Ar40_err'),

        ('Ar39', 'Ar39'),
        (PLUSMINUS_ONE_SIGMA, 'Ar39_err'),

        ('Ar38', 'Ar38'),
        (PLUSMINUS_ONE_SIGMA, 'Ar38_err'),

        ('Ar37', 'Ar37'),
        (PLUSMINUS_ONE_SIGMA, 'Ar37_err'),

        ('Ar36', 'Ar36'),
        (PLUSMINUS_ONE_SIGMA, 'Ar36_err'),
        ('%40Ar*', 'rad40_percent'),

        #     ('40Ar*/39ArK', 'F'),
        ('Age', 'age'),
        (PLUSMINUS_ONE_SIGMA, 'age_err'),
        ('K/Ca', 'kca'),
        (PLUSMINUS_ONE_SIGMA, 'kca_err'),
        #     ('', 'blank_column')
    ]

    record_id_width = Int(60)

class FusionGroupTableAdapter(BaseGroupAdapter):
    pass

# ============= EOF =============================================
