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
from traits.api import HasTraits, Bool, Str, Tuple, Either, Callable

from pychron.pipeline.tables.util import value, error
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA


class Column(HasTraits):
    enabled = Bool
    attr = Str
    label = Either(Str, Tuple)
    units = Str
    func = Callable

    def _label_default(self):
        return ''

    def _units_default(self):
        return ''

    def _enabled_default(self):
        return True


class VColumn(Column):
    def _func_default(self):
        return value


class EColumn(Column):
    label = PLUSMINUS_ONE_SIGMA

    def _func_default(self):
        return error
# ============= EOF =============================================
