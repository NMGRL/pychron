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
from pyface.tasks.action.task_action import TaskAction

from pychron.envisage.resources import icon

#============= standard library imports ========================
#============= local library imports  ==========================

class AddTextBoxAction(TaskAction):
    method = 'add_text_box'
    name = 'Annotate'
    image = icon('annotate.png')


class SaveFigureAction(TaskAction):
    method = 'save_figure'
    name = 'Save Figure'
    image = icon('database_save.png')


class SaveAsFigureAction(TaskAction):
    method = 'save_as_figure'
    name = 'Save As Figure'
    image = icon('database_save.png')


class SavePDFFigureAction(TaskAction):
    method = 'save_pdf_figure'
    name = 'Save PDF Figure'
    image = icon('file_pdf.png')


class OpenFigureAction(TaskAction):
    method = 'open_figure'
    name = 'Open Figure'
    image = icon('page_white_database.png')


class NewIdeogramAction(TaskAction):
    name = 'New Ideogram'
    method = 'tb_new_ideogram'
    image = icon('histogram')


class NewSpectrumAction(TaskAction):
    name = 'New Spectrum'
    method = 'tb_new_spectrum'
    image = icon('chart_curve.png')


class RefreshActiveEditorAction(TaskAction):
    name = 'Refresh Plot'
    method = 'refresh_active_editor'
    image = icon('refresh')

#============= EOF =============================================
# class AppendSpectrumAction(TaskAction):
#     name = 'Append Spectrum'
#     method = 'append_spectrum'
#     tooltip = '''Add selected analyses to current spectrum.
# If no analyses selected add all from the selected sample'''
#
#     image = icon('chart_curve_add.png')
# class AppendIdeogramAction(TaskAction):
#     name = 'Append Ideogram'
#     method = 'append_ideogram'
#     tooltip = '''Add selected analyses to current ideogram.
# If no analyses selected add all from the selected sample'''
#
#     image = icon('ideo_add.png')
