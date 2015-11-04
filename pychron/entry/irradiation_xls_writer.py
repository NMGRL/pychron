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
from pyface.message_dialog import warning
from traits.api import HasTraits, List
from traitsui.api import View, UItem, ListStrEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from xlwt import Workbook, XFStyle
from xlwt.Style import default_style


class IrradiationSelector(HasTraits):
    selected = List
    irradiations = List

    def traits_view(self):
        v = View(UItem('irradiations', editor=ListStrEditor(multi_select=True,
                                                            selected='selected')),
                 kind='livemodal',
                 resizable=True,
                 title='Select Irradiations',
                 buttons=['OK', 'Cancel'])
        return v


class IrradiationXLSTableWriter(HasTraits):
    dvc = None

    def make(self, irrad_names):
        irrad_selector = IrradiationSelector(irradiations=irrad_names)
        while 1:
            info = irrad_selector.edit_traits()
            if info.result:
                irradiations = irrad_selector.selected
                if not irradiations:
                    warning('You must select one or more irradiations')
                else:
                    self._make(irradiations)
                    break
            else:
                break

    def _make(self, irrads):
        wb = Workbook()
        sh = wb.add_sheet('Irradiations')

        cols = [('Irradiation', ''), ('Duration (hrs)', 'duration')]
        row = 0
        for i, (label, key) in enumerate(cols):
            sh.write(row, i, label)

        for j, irrad in enumerate(irrads):
            self._make_irradiation_line(sh, j + 1, irrad, cols)
        wb.save('/Users/ross/Desktop/foo.xls')

    def _make_irradiation_line(self, sheet, row, irradname, cols):
        dvc = self.dvc
        for i, (label, key) in enumerate(cols[1:]):
            sheet.write(row, 0, irradname)

            chron = dvc.get_chronology(irradname)
            if key == 'duration':
                v = chron.duration
                style = XFStyle()
                style.num_format_str = '0.#'
            else:
                style = default_style

            sheet.write(row, i + 1, v, style)

# ============= EOF =============================================
