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

#============= enthought library imports =======================
#============= standard library imports ========================
#============= local library imports  ==========================

from xlwt.Workbook import Workbook
from xlwt.Style import XFStyle, default_style
from xlwt.Formatting import Borders
from xlwt import Alignment

from pychron.processing.tables.fusion.text_writer import LaserTableTextWriter


class FusionTableXLSWriter(LaserTableTextWriter):
    default_style = default_style

    def _new_workbook(self):
        return Workbook()

    def _get_header_styles(self):
        s1 = XFStyle()
        al = Alignment()
        al.horz = Alignment.HORZ_CENTER
        s1.alignment = al

        s2 = XFStyle()
        borders = Borders()
        borders.bottom = 2
        s2.borders = borders

        return s1, s2


# ============= EOF =============================================
