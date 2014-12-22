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
from pyface.tasks.action.task_action import TaskAction

from pychron.envisage.resources import icon


# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
class MakePDFTableAction(TaskAction):
    name = 'Make PDF'
    method = 'make_pdf_table'
    image = icon('file_pdf')


class MakeXLSTableAction(TaskAction):
    name = 'Make Excel'
    method = 'make_xls_table'
    image = icon('file_xls')


class MakeCSVTableAction(TaskAction):
    name = 'Make CSV'
    method = 'make_csv_table'
    image = icon('file_csv')


class ToggleStatusAction(TaskAction):
    name = 'Toggle Status'
    method = 'toggle_status'
    image = icon('arrow_switch')
    tooltip = 'Toggle status'


class SummaryTableAction(TaskAction):
    name = 'Summary'
    method = 'open_summary_table'
    image = icon('report')
    tooltip = 'New summary table'


class AppendSummaryTableAction(TaskAction):
    method = 'append_summary_table'
    image = icon('report_add')
    tooltip = 'Append to current summary table'


class FusionTableAction(TaskAction):
    name = 'Laser'
    method = 'new_fusion_table'
    image = icon('report')
    tooltip = 'New fusion table'


class AppendTableAction(TaskAction):
    name = 'Append Table'
    method = 'append_table'
    image = icon('report_add')
    tooltip = 'Append to current table'

# class AppendFusionTableAction(TaskAction):
#    name='Append Fusion'
#    method = 'append_fusion_table'
#    image = icon('report_add',
#                         search_path=paths.icon_search_path
#                         )
#    tooltip = 'Append to current fusion table'

#class AppendStepHeatTableAction(TaskAction):
#    name='Append Step Heat'
#    method='append_step_heat_table'
#    image = icon('report_add',
#                         search_path=paths.icon_search_path
#                         )
#    tooltip = 'Append to current step heat table'
# ============= EOF =============================================
