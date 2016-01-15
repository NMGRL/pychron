# ===============================================================================
# Copyright 2014 Jake Ross
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
import xlwt
# ============= local library imports  ==========================

IRRADIATION_COLUMNS = ('Name', 'Level', 'PR', 'Holder')
CHRONOLOGY_COLUMNS = ('Name', 'Start', 'End', 'Power')
POSITION_COLUMNS = ('Irradiation', 'Level', 'Position', 'Identifier',
                    'Sample', 'PrincipalInvestigator', 'Project', 'Material',
                    'Weight',
                    'Note')
CONFIG_COLUMNS = ('Name', 'Value', 'Description')
# CONFIG_ATTRS = (('autogenerate_labnumber', 'False', 'Automatically generate labnumbers'),
#                 ('base_irradiation_offset', 100,
#                  'Increment labnumbers by irradiation offset for each irradiation added'),
#                 ('base_level_offset', 0, 'Increment labnumbers by level offset for each level added'),
#                 ('quiet', 'False', 'If true do not ask for confirmation if project, material, sample does not exist, '
#                                    'just do it'))

CONFIG_ATTRS = (('quiet', 'False', 'If true do not ask for confirmation if project, material, sample does not exist, '
                                   'just do it'),)


class IrradiationTemplate(object):
    def make_template(self, p):
        wb = xlwt.Workbook()
        self._make_irradiations_sheet(wb)
        self._make_chronologies_sheet(wb)
        self._make_positions_sheet(wb)
        self._make_configuration_sheet(wb)
        wb.save(p)

    def _make_irradiations_sheet(self, wb):
        sheet = wb.add_sheet('Irradiations')
        self._make_header(sheet, IRRADIATION_COLUMNS)

    def _make_chronologies_sheet(self, wb):
        sheet = wb.add_sheet('Chronologies')
        self._make_header(sheet, CHRONOLOGY_COLUMNS)

    def _make_positions_sheet(self, wb):
        sheet = wb.add_sheet('Positions')
        self._make_header(sheet, POSITION_COLUMNS)

    def _make_configuration_sheet(self, wb):
        sheet = wb.add_sheet('Configuration')
        self._make_header(sheet, CONFIG_COLUMNS)
        for i, (ai, vi, di) in enumerate(CONFIG_ATTRS):
            sheet.write(i + 1, 0, ai)
            sheet.write(i + 1, 1, vi)
            sheet.write(i + 1, 2, di)

    def _make_header(self, sheet, columns, style=None):
        if style is None:
            style = xlwt.XFStyle()
            borders = xlwt.Borders()
            borders.bottom = 2
            style.borders = borders

        for i, c in enumerate(columns):
            sheet.write(0, i, c, style=style)

# ============= EOF =============================================



