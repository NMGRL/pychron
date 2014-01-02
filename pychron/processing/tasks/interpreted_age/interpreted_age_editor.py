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
from itertools import groupby
import os
from traits.api import Any, List, Str, Button, Instance, on_trait_change
from traitsui.api import View, EnumEditor, HGroup, spring, \
    UItem, VGroup, TabularEditor, InstanceEditor

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
import yaml
from pychron.database.adapters.isotope_adapter import InterpretedAge
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.core.helpers.iterfuncs import partition
from pychron.core.pdf.options import PDFTableOptions
from pychron.processing.analyses.analysis_group import StepHeatAnalysisGroup
from pychron.processing.tables.step_heat.pdf_writer import StepHeatPDFTableWriter
from pychron.processing.tables.summary_table_pdf_writer import SummaryPDFTableWriter
from pychron.processing.tasks.browser.panes import AnalysisAdapter
from pychron.core.ui.custom_label_editor import CustomLabel


class InterpretedAgeAdapter(TabularAdapter):
    columns = [('Sample', 'sample'),
               ('Identifier', 'identifier'),
               ('Kind', 'age_kind'),
               ('Age', 'age'),
               ('Error', 'age_err'),
               ('NAnalyses', 'nanalyses'),
               ('MSWD', 'mswd')]

    font = 'arial 10'


class InterpretedAgeEditor(BaseTraitsEditor):
    selected_history = Any
    selected_history_name = Str
    selected_identifier = Str

    histories = List
    history_names = List
    analyses = List
    processor = Any

    append_button = Button
    replace_button = Button
    interpreted_ages = List

    pdf_table_options=Instance(PDFTableOptions, ())

    def open_table_recipe(self, p):
        self._open_recipe_file(p)

    def save_pdf_tables(self, p):
        self.save_summary_table(p)
        self.save_analysis_data_table(p)

    def save_analysis_data_table(self, p):
        w=StepHeatPDFTableWriter()

        ans=[]
        db=self.processor.db
        with db.session_ctx():
            for ia in self.interpreted_ages:
                hid=db.get_interpreted_age_history(ia.id)
                dbia=hid.interpreted_age
                ans.extend([si.analysis for si in dbia.sets])

            ans=self.processor.make_analyses(ans, calculate_age=True)
        '''
            group the analyses by labnumber
            then partition into step heat and fusion
        '''

        gs=[]
        key = lambda x: x.labnumber
        ans=sorted(ans, key=key)
        for ln, ais in groupby(ans, key=key):
            gs.append((ln, list(ais)))

        stepheat, fusion=partition(gs, lambda x: x[1][0].step!='')
        stepheat=list(stepheat)
        fusion=list(fusion)
        ans=[ai for _,ais in stepheat
                for ai in ais]
        groups=[StepHeatAnalysisGroup(sample=ais[0].sample,
                                      analyses=ais) for ln, ais in stepheat]
        # key = lambda x: x.sample
        # groups=[StepHeatAnalysisGroup(sample=sam, analyses=list(ais))
        #         for sam, ais in groupby(ans, key=key)]
        #
        # ans = groupby(ans, key=key)
        head, ext=os.path.splitext(p)
        p='{}.step_heat_data{}'.format(head, ext)
        w.build(p, ans, groups, title=self.get_title())

    def save_summary_table(self, p):
        w = SummaryPDFTableWriter()
        items = self.interpreted_ages
        title = self.get_title()

        opt=self.pdf_table_options
        # w.use_alternating_background=opt.use_alternating_background
        w.options=opt
        w.build(p, items, title)

        self._save_recipe_file(p)

    def get_title(self):
        opt=self.pdf_table_options
        if opt.auto_title:
            title=self._generate_title()
        else:
            title=opt.title
        return title

    def set_samples(self, samples):
        self.analyses = []
        self.selected_history_name = ''
        self.selected_history = InterpretedAge()

        if samples:
            lns = [si.labnumber for si in samples]
            db = self.processor.db
            with db.session_ctx():
                histories = db.get_interpreted_age_histories(lns)

                self.histories = [db.interpreted_age_factory(hi) for hi in histories]

                self.history_names = [hi.name for hi in self.histories]
                if self.history_names:
                    self.selected_history_name = self.history_names[-1]

    def _save_recipe_file(self, p):
        head, ext=os.path.splitext(p)
        p='{}.{}'.format(head, 'yaml')

        #assemble recipe
        d={'title':str(self.get_title()),
           'options':self.pdf_table_options.dump_yaml(),
           'ids':[int(ia.id) for ia in self.interpreted_ages]}

        with open(p, 'w') as fp:
            yaml.dump(d, fp)

    def _open_recipe_file(self, p):
        with open(p, 'r') as fp:
            d=yaml.load(fp)

        db=self.processor.db
        with db.session_ctx():
            ias=[]
            for hid in d['ids']:
                hist=db.get_interpreted_age_history(hid)
                ias.append(db.interpreted_age_factory(hist))

        self.interpreted_ages=ias

        self.pdf_table_options.load_yaml(d['options'])
        # self.pdf_table_options.trait_set(**d['options'])

    def _generate_title(self):
        return 'Table 1. Ar/Ar Summary Table'

    @on_trait_change('interpreted_ages[]')
    def _interpreted_ages_changed(self):
        self.pdf_table_options.title=self._generate_title()

    def _selected_history_name_changed(self):
        if self.selected_history_name:
            def func(a):
                # print a, a.plateau_step
                ir = IsotopeRecordView(is_plateau_step=a.plateau_step)
                ir.create(a.analysis)
                return ir

            db = self.processor.db

            hist = next((hi for hi in self.histories if hi.name == self.selected_history_name), None)
            self.selected_history = hist
            self.selected_identifier = '{} {}'.format(hist.sample, hist.identifier)

            with db.session_ctx():
                dbhist = db.get_interpreted_age_history(hist.id)
                s = dbhist.interpreted_age.sets

                self.analyses = [func(a) for a in s]


    def _append_button_fired(self):
        self.interpreted_ages.append(self.selected_history)

    def _replace_button_fired(self):
        self.interpreted_ages = [self.selected_history]

    def traits_view(self):
        histories_grp = HGroup(icon_button_editor('append_button', 'add'),
                               icon_button_editor('replace_button', 'arrow_refresh'),
                               spring,
                               CustomLabel('selected_identifier'),
                               spring, UItem('selected_history_name', editor=EnumEditor(name='history_names')))
        analyses_grp = UItem('analyses', editor=TabularEditor(adapter=AnalysisAdapter()))
        selected_grp = UItem('selected_history', style='custom', editor=InstanceEditor())

        interpreted_grp = UItem('interpreted_ages',
                                editor=TabularEditor(adapter=InterpretedAgeAdapter(),
                                                     operations=['move','delete'],
                                                     ))
        options_grp=UItem('pdf_table_options', style='custom')

        v = View(VGroup(histories_grp,
                        selected_grp,
                        analyses_grp,
                        options_grp,
                        interpreted_grp))
        return v

#============= EOF =============================================

