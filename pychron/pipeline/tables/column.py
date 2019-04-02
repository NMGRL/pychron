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
from traits.api import HasTraits, Bool, Str, Tuple, Either, Callable, List, Int

from pychron.core.helpers.formatting import floatfmt
from pychron.pipeline.tables.util import value, error
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA


class Column(HasTraits):
    enabled = Bool
    attr = Str
    label = Either(Str, Tuple)
    units = Str
    func = Callable
    sigformat = Str
    fformat = List
    use_scientific = Bool
    width = None
    calculated_width = None
    nsigfigs = Int
    visible = Bool

    def calculate_width(self, txt):
        if self.calculated_width is None:
            self.calculated_width = self._calculate_label_width()

        if isinstance(txt, float):
            if self.nsigfigs:
                txt = floatfmt(txt, self.nsigfigs, use_scientific=self.use_scientific)
            else:
                txt = floatfmt(txt)

        self.calculated_width = max(self.calculated_width, len(str(txt))+5)

    def _calculate_label_width(self):
        label = self.label
        if isinstance(label, tuple):
            w = 0
            for i in label:
                for r in ('sub', 'sup'):
                    for rr in ('<{}>'.format(r), '</{}>'.format(r)):
                        i = i.replace(rr, '')
                w += len(i)
        else:
            w = len(label)
        return w+5

    def _label_default(self):
        return ''

    def _units_default(self):
        return ''

    def _enabled_default(self):
        return True
    def _visible_default(self):
        return True

class VColumn(Column):
    def _func_default(self):
        return value


class EColumn(Column):
    label = PLUSMINUS_ONE_SIGMA

    def _func_default(self):
        return error
# ============= EOF =============================================
