# ===============================================================================
# Copyright 2013 Jake Ross
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
from pyface.file_dialog import FileDialog
from pyface.message_dialog import information
from traits.api import Str, List
# from pyface.action.action import Action
# from pyface.tasks.action.task_action import TaskAction

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.resources import icon
from pychron.envisage.tasks.actions import myTaskAction
from pychron.envisage.tasks.actions import PAction as Action


class ActivateBlankAction(myTaskAction):
    name = 'Activate Blanks'
    task_ids = ['pychron.processing.figures', 'pychron.recall']
    method = 'activate_blanks_task'


class ActivateRecallAction(myTaskAction):
    name = 'Activate Recall'
    task_ids = ['pychron.processing.figures', 'pychron.processing.blanks']
    method = 'activate_recall_task'


class ActivateIdeogramAction(myTaskAction):
    name = 'Activate Ideogram'
    task_ids = ['pychron.processing.blanks', 'pychron.recall']
    method = 'activate_ideogram_task'


class FigureTaskAction(myTaskAction):
    task_ids = List(['pychron.processing.figures', ])


class GraphGroupSelectedAction(FigureTaskAction):
    name = 'Graph Group Selected'
    dname = 'Graph Group Selected'
    method = 'graph_group_selected'


class GraphGroupbySampleAction(FigureTaskAction):
    name = 'Graph Group by Sample'
    dname = 'Graph Group by Sample'
    method = 'graph_group_by_sample'


class GroupAction(FigureTaskAction):
    image = icon('blockdevice-3')


class GroupSelectedAction(GroupAction):
    name = 'Group Selected'
    dname = 'Group Selected'
    method = 'group_selected'
    # image = icon('placeholder')


# def perform(self, event):
# task = event.task
# if task.id == 'pychron.processing.figures':
# task.group_selected()

class GroupbySampleAction(GroupAction):
    name = 'Group by Sample'
    dname = 'Group by Sample'
    method = 'group_by_sample'
    # image = icon('placeholder')


class GroupbyLabnumberAction(GroupAction):
    name = 'Group by Labnumber'
    dname = 'Group by Labnumber'
    method = 'group_by_labnumber'
    # image = icon('placeholder')


class GroupbyAliquotAction(GroupAction):
    name = 'Group by Aliquot'
    dname = 'Group by Aliquot'
    method = 'group_by_aliquot'
    # image = icon('placeholder')


class ClearGroupAction(GroupAction):
    name = 'Clear Grouping'
    dname = 'Clear Grouping'
    method = 'clear_grouping'
    # image = icon('placeholder')


class AnalysisAction(myTaskAction):
    task_ids = List(['pychron.processing.figures',
                     'pychron.processing.blanks',
                     'pychron.processing.isotope_evolution',
                     'pychron.processing.ic_factor',
                     'pychron.processing.flux',
                     'pychron.processing.batch',
                     'pychron.processing.discrimination'])


class MakeAnalysisGroupAction(AnalysisAction):
    name = 'Make Analysis Group'
    dname = 'Make Analysis Group'
    method = 'make_analysis_group'
    image = icon('database_add')


class DeleteAnalysisGroupAction(AnalysisAction):
    name = 'Delete Analysis Group'
    dname = 'Delete Analysis Group'
    method = 'delete_analysis_group'
    image = icon('database_delete')


# ===============================================================================
#
# ===============================================================================
class EquilibrationInspectorAction(Action):
    name = 'Equilibration Inspector...'

    def perform(self, event):
        from pychron.processing.utils.equil import EquilibrationInspector

        eq = EquilibrationInspector()
        eq.refresh()
        app = event.task.window.application
        app.open_view(eq)


# ===============================================================================
# figures
# ===============================================================================
class FigureAction(Action):
    method = Str

    def perform(self, event):
        app = event.task.window.application
        task = app.get_task('pychron.processing.figures')
        if hasattr(task, self.method):
            getattr(task, self.method)()


class XYScatterAction(FigureAction):
    name = 'XY Scatter'
    dname = 'XY Scatter'
    method = 'new_xy_scatter'
    accelerator = 'Ctrl+Shift+x'


class IdeogramAction(FigureAction):
    name = 'Ideogram'
    dname = 'Ideogram'
    method = 'new_ideogram'
    image = icon('histogram')
    id = 'pychron.ideogram'


class CompositeAction(FigureAction):
    name = 'Composite'
    dname = 'Composite'
    method = 'new_composite'
    id = 'pychron.composite'


class SpectrumAction(FigureAction):
    name = 'Spectrum'
    dname = 'Spectrum'
    method = 'new_spectrum'
    id = 'pychron.spectrum'


class SeriesAction(FigureAction):
    name = 'Series'
    dname = 'Series'
    method = 'new_series'
    id = 'pychron.series'


class InverseIsochronAction(FigureAction):
    name = 'Inverse Isochron'
    dname = 'Inverse Isochron'
    method = 'new_inverse_isochron'
    id = 'pychron.inverse_isochron'


class TemplateAction(Action):
    template = ''
    fname = ''

    def perform(self, event):
        import os
        from pychron.globals import globalv
        from pychron.paths import paths

        name = self.fname
        if globalv.debug:
            p = os.path.join(paths.data_dir, '{}_template.txt'.format(name.lower()))
        else:
            p = None
            dlg = FileDialog(action='save as', default_directory=paths.data_dir)
            if dlg.open():
                p = dlg.path

        if p is not None:
            with open(p, 'w') as wfile:
                wfile.write(self.template)
            information(event.task.window.control, 'An example {} template was written to {}\n\n'
                                                   'Replace the placeholder data in the file with your data\n'
                                                   'Make sure to use "TABS" to deliminate columns'.format(name, p))


class IdeogramFileTemplate(TemplateAction):
    name = 'Make Ideogram File Template'
    dname = 'Make Ideogram File Template'
    fname = 'Ideogram'
    template = '''group\trunid\taliquot\tsample\tage\tage_err
0\t12345-01\t01\tFC-2\t10.1\t0.6
0\t12345-02\t02\tFC-2\t10.2\t0.1
0\t12345-03\t03\tFC-2\t10.3\t0.3
0\t12345-04\t04\tFC-2\t10.4\t0.4
0\t12345-05\t05\tFC-2\t10.1\t0.2
1\t12346-01\t01\tJR-2\t11.1\t0.6
1\t12346-02\t02\tJR-2\t11.2\t0.1
1\t12346-03\t03\tJR-2\t11.3\t0.3
1\t12346-04\t04\tJR-2\t11.4\t0.4
1\t12346-05\t05\tJR-2\t11.1\t0.2
'''


class SpectrumFileTemplate(TemplateAction):
    name = 'Make Spectrum File Template'
    dname = 'Make Spectrum File Template'
    fname = 'Spectrum'
    template = '''age\tage_err\tk39
1\t0.1\t1
1\t0.2\t1
1\t0.3\t1
1\t0.1\t1
1\t0.4\t1
1\t0.2\t1
1\t0.1\t1
'''


class IdeogramFromFile(FigureAction):
    name = 'Ideogram'
    dname = 'Ideogram From File'
    method = 'new_ideogram_from_file'
    accelerator = 'Ctrl+shift+j'


class SpectrumFromFile(FigureAction):
    name = 'Spectrum'
    dname = 'Spectrum From File'
    method = 'new_spectrum_from_file'


# ===============================================================================
#
# ===============================================================================
class TimeViewAction(Action):
    name = 'Time View'
    dname = 'Time View'
    accelerator = 'Ctrl+t'

    def perform(self, event):
        app = event.task.window.application
        from pychron.processing.tasks.browser.time_view import TimeViewModel
        from pychron.processing.tasks.browser.time_view import TimeView

        manager = app.get_service('pychron.database.isotope_database_manager.IsotopeDatabaseManager')

        m = TimeViewModel(db=manager.db,
                          context_menu_enabled=False)
        m.load()
        v = TimeView(model=m)
        app.open_view(v)


class RecallAction(Action):
    name = 'Recall'
    dname = 'Recall'
    id = 'pychron.recall'

    def perform(self, event):
        app = event.task.window.application
        task = app.get_task('pychron.recall')


class ConfigureRecallAction(myTaskAction):
    name = 'Configure Recall'
    dname = 'Configure Recall'
    method = 'configure_recall'
    image = icon('cog')
    task_ids = ('pychron.recall', 'pychron.processing.figures',
                'pychron.processing.blanks',
                'pychron.processing.isotope_evolution',
                'pychron.processing.ic_factor',
                'pychron.processing.discrimination')


class OpenInterpretedAgeAction(Action):
    name = 'Browse Interpreted Ages'

    def perform(self, event):
        app = event.task.window.application
        task = app.open_task('pychron.processing.interpreted_age')


class SetInterpretedAgeAction(FigureTaskAction):
    name = 'Set Interpreted Age...'
    method = 'set_interpreted_age'


class SetInterpretedAgeTBAction(FigureTaskAction):
    name = 'Set Interpreted Age'
    method = 'set_interpreted_age'
    image = icon('database_add')


class BrowseInterpretedAgeTBAction(FigureTaskAction):
    name = 'Browse Interpreted Age'
    method = 'browse_interpreted_age'
    image = icon('application_view_list')


# class OpenAdvancedQueryAction(Action):
# name = 'Find Analysis...'
#     image = icon('find.png')
#
#     def perform(self, event):
#         app = event.task.window.application
#         task = app.open_task('pychron.advanced_query')
#         task.set_append_replace_enabled(False)


class ClearAnalysisCacheAction(Action):
    name = 'Clear Analysis Cache'
    dname = 'Clear Analysis Cache'
    image = icon('clear')

    def perform(self, event=None):
        from pychron.database.isotope_database_manager import ANALYSIS_CACHE, ANALYSIS_CACHE_COUNT

        ANALYSIS_CACHE.clear()
        ANALYSIS_CACHE_COUNT.clear()


class ExportAnalysesAction(Action):
    name = 'Export Analyses...'

    def perform(self, event):
        app = event.task.window.application
        app.open_task('pychron.export')


class SetSQLiteAction(Action):
    name = 'Set SQLite Dataset...'

    def perform(self, event):
        app = event.task.window.application
        man = app.get_service('pychron.processing.processor.Processor')
        man.set_sqlite_dataset()


class SetXMLAction(Action):
    name = 'Set XML Dataset...'
    accelerator = 'Ctrl+3'
    def perform(self, event):
        app = event.task.window.application
        man = app.get_service('pychron.processing.processor.Processor')
        man.set_xml_dataset()


class ModifyK3739Action(myTaskAction):
    name = 'Modify (37/39)K...'
    dname = 'Modify (37/39)K'
    method = 'modify_k3739'
    task_ids = ('pychron.processing.figures', 'pychron.recall', 'pychron.processing.isotope_evolution')


class ModifyIdentifierAction(myTaskAction):
    name = 'Modify Labnumber...'
    dname = 'Modify Labnumber'
    method = 'modify_analysis_identifier'
    task_ids = ('pychron.recall',)


class SplitEditorActionHor(myTaskAction):
    name = 'Split Editor Horizontal'
    task_ids = ('pychron.processing.figures', 'pychron.recall')
    method = 'split_editor_area_hor'


class SplitEditorActionVert(myTaskAction):
    name = 'Split Editor Vertical'
    task_ids = ('pychron.processing.figures', 'pychron.recall')
    method = 'split_editor_area_vert'
    image = icon('split_vertical')


# ============= EOF =============================================

