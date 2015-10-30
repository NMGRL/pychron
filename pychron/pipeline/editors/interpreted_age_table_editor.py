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

from traits.api import List, on_trait_change, Int, Event
from traitsui.api import View, UItem, VGroup, TabularEditor
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.column_sorter_mixin import ColumnSorterMixin
# from pychron.database.interpreted_age import InterpretedAge
# from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.envisage.tasks.base_editor import BaseTraitsEditor


# from pychron.processing.tasks.browser.panes import AnalysisAdapter


class InterpretedAgeAdapter(TabularAdapter):
    columns = [('Sample', 'sample'),
               ('Identifier', 'identifier'),
               ('Kind', 'age_kind'),
               ('Age', 'display_age'),
               ('Error', 'display_age_err'),
               ('NAnalyses', 'nanalyses'),
               ('MSWD', 'mswd')]

    font = 'arial 10'
    sample_width = Int(100)
    identifier_width = Int(100)
    age_kind_width = Int(100)
    display_age_width = Int(75)
    display_age_err_width = Int(75)
    nanalyses_width = Int(75)


class InterpretedAgeTableEditor(BaseTraitsEditor, ColumnSorterMixin):
    interpreted_ages = List
    # analyses = List
    # pdf_table_options = Instance(PDFTableOptions, ())
    # saved_group_id = Int
    name = 'Untitled'
    refresh = Event

    # def save_summary_table(self, root, auto_view=False):
    #     name = '{}_summary'.format(self.name)
    #     w = SummaryPDFTableWriter()
    #     items = self.interpreted_ages
    #     title = self.get_title()
    #
    #     opt = self.pdf_table_options
    #     p, _ = unique_path(root, name, extension='.pdf')
    #     w.options = opt
    #     w.build(p, items, title)
    #     if auto_view:
    #         view_file(p)
    #
    # def get_title(self):
    #     opt = self.pdf_table_options
    #     if opt.auto_title:
    #         title = self._generate_title()
    #     else:
    #         title = opt.title
    #     return title

    def _generate_title(self):
        return 'Table 1. Ar/Ar Summary Table'

    @on_trait_change('interpreted_ages[]')
    # def _interpreted_ages_changed(self):
    #     if self.interpreted_ages:
    #         self.pdf_table_options.title = self._generate_title()
    #         self.pdf_table_options.age_units = self.interpreted_ages[0].display_age_units

    def traits_view(self):
        interpreted_grp = UItem('interpreted_ages',
                                editor=TabularEditor(adapter=InterpretedAgeAdapter(),
                                                     operations=['move', 'delete'],
                                                     column_clicked='column_clicked',
                                                     refresh='refresh'))
        v = View(VGroup(interpreted_grp))
        return v

# ============= EOF =============================================
# def _selected_history_name_changed(self):
#     if self.selected_history_name:
#         def func(a):
#             # print a, a.plateau_step
#             ir = IsotopeRecordView(is_plateau_step=a.plateau_step)
#             ir.create(a.analysis)
#             return ir
#
#         db = self.processor.db
#
#         hist = next((hi for hi in self.histories if hi.name == self.selected_history_name), None)
#         self.selected_history = hist
#         self.selected_identifier = '{} {}'.format(hist.sample, hist.identifier)
#
#         with db.session_ctx():
#             dbhist = db.get_interpreted_age_history(hist.id)
#             s = dbhist.interpreted_age.sets
#
#             self.analyses = [func(a) for a in s]
#     def _append_button_fired(self):
#         self.interpreted_ages.append(self.selected_history)
#
#     def _replace_button_fired(self):
#         self.interpreted_ages = [self.selected_history]

# def save_pdf_tables(self, p):
#     self.save_summary_table(p)
#     self.save_analysis_data_tables(p, pdf=True, xls=False)
#
# def save_xls_tables(self, p):
#     self.save_analysis_data_tables(p, pdf=False, xls=True)
# def test_save_xls_tables(self):
#     p = '/Users/ross/Sandbox/datatables'
#     self.interpreted_ages = self.interpreted_ages[:4]
#     self.save_analysis_data_tables(p, pdf=False,
#                                    xls_summary=True, xls=True,
#                                    auto_view=True)
#
# def save_tables(self, t):
#     pdf_sum = t.use_pdf_summary
#     xls_sum = t.use_xls_summary
#     if pdf_sum:
#         self.save_summary_table(t.root,
#                                 auto_view=t.auto_view)
#
#     pdf = t.use_pdf_data
#     xls = t.use_xls_data
#     if pdf or xls or xls_sum:
#         self.save_analysis_data_tables(t.root, pdf=pdf,
#                                        xls=xls,
#                                        xls_summary=xls_sum,
#                                        auto_view=t.auto_view)
# def save_analysis_data_tables(self, root, pdf=True, xls=True,
#                               xls_summary=False,
#                               auto_view=False):
#
#     ias = self.interpreted_ages
#     db = self.processor.db
#     with db.session_ctx():
#         # partition into map/argus
#         def pred(ia):
#             hid = db.get_interpreted_age_history(ia.id)
#             ref = hid.interpreted_age.sets[0].analysis
#             return ref.measurement.mass_spectrometer.name.lower() == 'map'
#
#         part = partition(ias, pred)
#         map_spec, argus = map(list, part)
#
#     if pdf:
#         self.debug('saving pdf tables')
#         step_heat_title = 'Table E.1 MAP Step Heat <sup>40</sup>Ar/<sup>39</sup>Ar Data'
#         fusion_title = 'Table D.1 MAP Fusion <sup>40</sup>Ar/<sup>39</sup>Ar Data'
#         # self._save_pdf_data_table(root, map_spec, step_heat_title, fusion_title, 'map',
#         #                           auto_view=auto_view)
#
#         step_heat_title = 'Table G.1 Argus Step Heat <sup>40</sup>Ar/<sup>39</sup>Ar Data'
#         fusion_title = 'Table F.1 Argus Fusion <sup>40</sup>Ar/<sup>39</sup>Ar Data'
#         self._save_pdf_data_table(root, argus, step_heat_title, fusion_title, 'argus',
#                                   auto_view=auto_view)
#     if xls:
#         self.debug('saving xls tables')
#         step_heat_title = 'Table 1. MAP Step heat 40Ar/39Ar Data'
#         fusion_title = 'Table 2. MAP Fusion 40Ar/39Ar Data'
#         self._save_xls_data_table(root, map_spec, step_heat_title, fusion_title, 'map',
#                                   summary_sheet=xls_summary,
#                                   auto_view=auto_view)
#
#         step_heat_title = 'Table 3. Argus Step heat 40Ar/39Ar  Data'
#         fusion_title = 'Table 4. Argus Fusion 40Ar/39Ar Data'
#         self._save_xls_data_table(root, argus, step_heat_title, fusion_title, 'argus',
#                                   summary_sheet=xls_summary,
#                                   auto_view=auto_view)
#
# def _save_xls_data_table(self, root, ias, step_heat_title, fusion_title, spectrometer,
#                          summary_sheet=False,
#                          auto_view=False):
#
#     ext = '.xls'
#     app = 'Microsoft Office 2011/Microsoft Excel'
#     shgroups, fgroups = self._assemble_groups(ias)
#
#     if shgroups:
#         w = StepHeatTableXLSWriter()
#         name = '{}_{}_step_heat_data'.format(self.name, spectrometer)
#         p, _ = unique_path(root, name, extension=ext)
#
#         iagroups, shgroups = zip(*shgroups)
#         w.build(p, iagroups, shgroups, use_summary_sheet=summary_sheet,
#                 title=step_heat_title)
#         if auto_view:
#             view_file(p, application=app)
#
#     if fgroups:
#         w = FusionTableXLSWriter()
#         name = '{}_{}_fusion_data'.format(self.name, spectrometer)
#         p, _ = unique_path(root, name, extension=ext)
#         iagroups, fgroups = zip(*fgroups)
#         w.build(p, iagroups, fgroups, use_summary_sheet=summary_sheet,
#                 title=fusion_title)
#         if auto_view:
#             view_file(p, application=app)
#
# def _save_pdf_data_table(self, root, ias, step_heat_title, fusion_title, spectrometer, auto_view=False):
#
#     shgroups, fgroups = self._assemble_groups(ias)
#     ext = '.pdf'
#     if shgroups:
#         w = StepHeatPDFTableWriter()
#         # name = '{}_{}_step_heatdata'.format(self.name, spectrometer)
#         name = '{}stepheatdata'.format(spectrometer)
#         p, _ = unique_path(root, name, extension=ext)
#
#         iagroups, shgroups = zip(*shgroups)
#         w.build(p, shgroups, title=step_heat_title)
#         if auto_view:
#             view_file(p)
#
#     if fgroups:
#         w = FusionPDFTableWriter()
#         # name = '{}_{}_fusion_data'.format(self.name, spectrometer)
#         name = '{}fusiondata'.format(spectrometer)
#         p, _ = unique_path(root, name, extension=ext)
#         iagroups, fgroups = zip(*fgroups)
#         w.build(p, fgroups, title=fusion_title)
#         if auto_view:
#             view_file(p)
#
# def _assemble_groups(self, ias):
#     db = self.processor.db
#
#     with db.session_ctx():
#         # ias = [ia for ia in ias if ia.age_kind == 'Weighted Mean'][:1]
#
#         ans = [si.analysis for ia in ias
#                for si in db.get_interpreted_age_history(ia.id).interpreted_age.sets]
#
#         prog = self.processor.open_progress(len(ans), close_at_end=False)
#
#         def gfactory(klass, dbia):
#             hid = db.get_interpreted_age_history(dbia.id)
#             ia_ans = (si.analysis for si in hid.interpreted_age.sets)
#             all_ans = self.processor.make_analyses(ia_ans,
#                                                    calculate_age=True,
#                                                    use_cache=False,
#                                                    progress=prog)
#             # overwrite the tags for the analyses
#             for ai, sai in zip(all_ans, ia_ans):
#                 ai.set_tag(sai.tag)
#
#             ais = [ai for ai in all_ans if not 'omit' in ai.tag]
#             return klass(sample=ais[0].sample,
#                          all_analyses=all_ans,
#                          analyses=ais)
#
#         # partition fusion vs stepheat
#         fusion, step_heat = partition(ias, lambda x: x.age_kind == 'Weighted Mean')
#
#         shgroups = [(ia, gfactory(StepHeatAnalysisGroup, ia)) for ia in step_heat]
#         # shgroups = [(ia, gfactory(StepHeatAnalysisGroup, ia)) for ia in list(step_heat)[:3]]
#         # shgroups =[]
#
#         # fgroups = [(ia, gfactory(AnalysisGroup, ia)) for ia in fusion]
#         # fgroups = [(ia, gfactory(AnalysisGroup, ia)) for ia in list(fusion)[:3]]
#         fgroups = []
#
#         prog.close()
#
#     return shgroups, fgroups
# def add_latest_interpreted_ages(self, lns):
#     db = self.processor.db
#     with db.session_ctx():
#         for li in lns:
#             hist = db.get_latest_interpreted_age_history(li)
#             self.interpreted_ages.append(db.interpreted_age_factory(hist))
#
# def set_identifiers(self, lns):
#     """
#         only use th first identifier
#    """
#     self.analyses = []
#     self.selected_history_name = ''
#     self.selected_history = InterpretedAge()
#
#     if lns:
#         db = self.processor.db
#         with db.session_ctx():
#             histories = db.get_interpreted_age_histories(lns[:1])
#
#             hs = [db.interpreted_age_factory(hi) for hi in histories]
#             self.histories = [hi for hi in hs if hi]
#
#             self.history_names = [hi.name for hi in self.histories]
#             if self.history_names:
#                 self.selected_history_name = self.history_names[0]
#
# def set_samples(self, samples):
#     """
#        only use the first sample
#    """
#     self.set_identifiers([si.labnumber for si in samples[:1]])
#
# def update_group(self):
#     gid = self.saved_group_id
#     db = self.processor.db
#     with db.session_ctx() as sess:
#         hist = db.get_interpreted_age_group_history(gid)
#
#         for gs in hist.interpreted_ages:
#             sess.delete(gs)
#
#         for ia in self.interpreted_ages:
#             db.add_interpreted_age_group_set(hist, ia.id)
#
# def save_group(self, name, project, ids=None):
#     if ids is None:
#         if not self.interpreted_ages:
#             return
#
#         ids = (ia.id for ia in self.interpreted_ages)
#
#     db = self.processor.db
#     with db.session_ctx():
#         hist = db.add_interpreted_age_group_history(name, project=project)
#         for i in ids:
#             db.add_interpreted_age_group_set(hist, i)
#
# def open_group(self, gid):
#     db = self.processor.db
#     ias = []
#     with db.session_ctx():
#         hist = db.get_interpreted_age_group_history(gid)
#         prog = self.processor.open_progress(len(hist.interpreted_ages))
#         # self.interpreted_ages=[]
#         for gs in hist.interpreted_ages:
#             # print gs.id, gs.history, gs.history.id if gs.history else ''
#             ia = db.interpreted_age_factory(gs.history)
#             # self.interpreted_ages.append(ia)
#             prog.change_message('Interpreted age {}'.format(ia.identifier))
#             ias.append(ia)
#
#         prog.close()
#
#         self.interpreted_ages = ias
#
#         # self.set_identifiers([ia.identifier for ia in ias])
#         self.name = hist.name
#         self.saved_group_id = int(hist.id)
#
# def delete_groups(self, gids):
#     if not hasattr('gids', '__iter__'):
#         gids = (gids,)
#
#     db = self.processor.db
#     with db.session_ctx():
#         for di in gids:
#             self.delete_group(di)
#
# def delete_group(self, gid):
#     db = self.processor.db
#     with db.session_ctx() as sess:
#         hist = db.get_interpreted_age_group_history(gid)
#         for ia in hist.interpreted_ages:
#             sess.delete(ia)
#         sess.delete(hist)
