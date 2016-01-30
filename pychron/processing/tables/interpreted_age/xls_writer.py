# ===============================================================================
# Copyright 2015 Jake Ross
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

# ============= enthought library imports =======================
# ============= standard library imports ========================
from xlwt import Alignment
from xlwt.Formatting import Borders
from xlwt.Style import XFStyle, default_style
from xlwt.Workbook import Workbook
# ============= local library imports  ==========================
from pychron.processing.tables.interpreted_age.text_writer import InterpretedAgeTextWriter


class InterpretedAgeXLSTableWriter(InterpretedAgeTextWriter):
    default_style = default_style

    def _new_workbook(self):
        return Workbook()

    def _style_factory(self):
        return XFStyle()

    def _get_header_style(self):
        # s1 = self._style_factory()
        al = Alignment()
        al.horz = Alignment.HORZ_CENTER
        # s1.alignment = al

        s2 = self._style_factory()
        borders = Borders()
        borders.bottom = 2
        s2.borders = borders
        s2.alignment = al

        return s2

# ============= EOF =============================================
