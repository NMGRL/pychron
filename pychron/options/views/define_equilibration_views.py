# ===============================================================================
# Copyright 2018 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
from pychron.options.options import MainOptions, object_column, checkbox_column


class DefineEquilibrationMainOptions(MainOptions):
    def _get_columns(self):
        cols = [object_column(name='name', editable=False),
                # checkbox_column(name='plot_enabled', label='Plot'),
                checkbox_column(name='save_enabled', label='Enabled'),
                object_column(name='truncate', label='Trunc.'),
                ]
        return cols


VIEWS = {'main': DefineEquilibrationMainOptions}
# ============= EOF =============================================
