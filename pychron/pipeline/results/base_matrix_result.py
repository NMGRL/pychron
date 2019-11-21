# ===============================================================================
# Copyright 2019 ross
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
from traits.api import HasTraits, List, Str

from pychron.core.helpers.formatting import floatfmt


class BaseMatrixResult(HasTraits):
    values = List
    name = Str

    def __init__(self, ag, ags):
        self.values = self._calculate_values(ag, ags)
        self._set_name(ag)

    def _set_name(self, ag):
        self.name = '{}({})'.format(ag.identifier, ag.group_id)

    def _calculate_values(self, ag, others):
        raise NotImplementedError

    def get_value(self, row, column):
        if column == 0:
            return self.name
        elif column < row:
            return ''
        else:
            ret = self.values[column + 1]
            if ret:
                ret = self._format_value(ret)

        return ret

    def _format_value(self, v):
        return floatfmt(v, 3)

    def get_color(self, row, column):
        if column == 0:
            return 'white'
        elif column < row:
            return 'white'
        else:
            v = self.values[column + 1]
            return 'white' if not v or v < 0.05 else 'lightgreen'

# ============= EOF =============================================
