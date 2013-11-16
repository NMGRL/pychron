#===============================================================================
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
#===============================================================================
from pyface.tasks.action.task_action import TaskAction
from pyface.image_resource import ImageResource
from pychron.paths import paths

#============= enthought library imports =======================
#============= standard library imports ========================
#============= local library imports  ==========================
class MakePDFTableAction(TaskAction):
    name = 'Make PDF'
    method = 'make_pdf_table'
    image = ImageResource(name='file_pdf.png',
                          search_path=paths.icon_search_path
    )


class MakeXLSTableAction(TaskAction):
    name = 'Make Excel'
    method = 'make_xls_table'
    image = ImageResource(name='file_xls.png',
                          search_path=paths.icon_search_path
    )


class MakeCSVTableAction(TaskAction):
    name = 'Make CSV'
    method = 'make_csv_table'
    image = ImageResource(name='file_csv.png',
                          search_path=paths.icon_search_path
    )


class ToggleStatusAction(TaskAction):
    name = 'Toggle Status'
    method = 'toggle_status'
    image = ImageResource(name='arrow_switch.png',
                          search_path=paths.icon_search_path
    )
    tooltip = 'Toggle status'


class SummaryTableAction(TaskAction):
    name = 'Summary'
    method = 'open_summary_table'
    image = ImageResource(name='report.png',
                          search_path=paths.icon_search_path
    )
    tooltip = 'New summary table'


class AppendSummaryTableAction(TaskAction):
    method = 'append_summary_table'
    image = ImageResource(name='report_add.png',
                          search_path=paths.icon_search_path
    )
    tooltip = 'Append to current summary table'


class FusionTableAction(TaskAction):
    name = 'Laser'
    method = 'new_fusion_table'
    image = ImageResource(name='report.png',
                          search_path=paths.icon_search_path
    )
    tooltip = 'New fusion table'


class AppendTableAction(TaskAction):
    name = 'Append Table'
    method = 'append_table'
    image = ImageResource(name='report_add.png',
                          search_path=paths.icon_search_path
    )
    tooltip = 'Append to current table'

# class AppendFusionTableAction(TaskAction):
#    name='Append Fusion'
#    method = 'append_fusion_table'
#    image = ImageResource(name='report_add.png',
#                         search_path=paths.icon_search_path
#                         )
#    tooltip = 'Append to current fusion table'

#class AppendStepHeatTableAction(TaskAction):
#    name='Append Step Heat'
#    method='append_step_heat_table'
#    image = ImageResource(name='report_add.png',
#                         search_path=paths.icon_search_path
#                         )
#    tooltip = 'Append to current step heat table'
#============= EOF =============================================
