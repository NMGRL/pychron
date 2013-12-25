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

#============= enthought library imports =======================


#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.analyses.analysis_group import StepHeatAnalysisGroup
from pychron.processing.tables.step_heat.csv_writer import StepHeatTableCSVWriter
from pychron.processing.tables.step_heat.pdf_writer import StepHeatPDFTableWriter
from pychron.processing.tables.step_heat.xls_writer import StepHeatTableXLSWriter
from pychron.processing.tasks.tables.editors.arar_table_editor import ArArTableEditor
from pychron.processing.tasks.tables.editors.step_heat.step_heat_adapter import StepHeatTableAdapter, StepHeatGroupTableAdapter


class StepHeatTableEditor(ArArTableEditor):
    pdf_writer_klass = StepHeatPDFTableWriter
    xls_writer_klass = StepHeatTableXLSWriter
    csv_writer_klass = StepHeatTableCSVWriter

    extract_label = 'Temp.'
    extract_units = 'C'

    analysis_group_klass = StepHeatAnalysisGroup
    adapter_klass = StepHeatTableAdapter
    analysis_groups_adapter_klass = StepHeatGroupTableAdapter
    #============= EOF =============================================
