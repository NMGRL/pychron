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

from pychron.pychron_constants import INTERFERENCE_KEYS


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
                irradiations = irrad_selector.irradiations[1:4]
                # irradiations = irrad_selector.selected
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

        gen_cols = [('Irradiation', '', ''),
                    ('Duration (hrs)', 'duration', '0.#'), ]

        pr_cols = [('(40/39)K', 'K4039', '0.###'),
                   ('(38/39)K', 'K3839', '0.###'),
                   ('(37/39)K', 'K3739', '0.###'),
                   ('(39/37)Ca', 'Ca3937', '0.###'),
                   ('(38/37)Ca', 'Ca3837', '0.###'),
                   ('(36/37)Ca', 'Ca3637', '0.###'),
                   ('(36/38)Cl', 'Cl3638', '0.###')]
        cols = gen_cols + pr_cols
        row = 0
        for i, (label, key, fmt) in enumerate(cols):
            sh.write(row, i, label)

        for j, irrad in enumerate(irrads):
            self._make_irradiation_line(sh, j + 1, irrad, cols)
        wb.save('/Users/ross/Desktop/foo.xls')

    def _make_irradiation_line(self, sheet, row, irradname, cols):
        dvc = self.dvc
        chron = dvc.get_chronology(irradname)
        _, prod = dvc.meta_repo.get_production(irradname, 'A')

        sheet.write(row, 0, irradname)
        for i, (label, key, fmt) in enumerate(cols[1:]):
            style = XFStyle()
            if key == 'duration':
                v = chron.duration
            elif key in INTERFERENCE_KEYS:
                v = getattr(prod, key)

            style.num_format_str = fmt
            sheet.write(row, i + 1, v, style)

# ============= EOF =============================================
