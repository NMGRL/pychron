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
from traits.api import HasTraits, List, Int, Float, Any, Instance, on_trait_change, \
    Str, Button, Property, Bool, DelegatesTo
from traitsui.api import View, VGroup, Readonly, HGroup, UItem, InstanceEditor, TabularEditor
from traitsui.group import Tabbed
from traitsui.tabular_adapter import TabularAdapter
from enable.component_editor import ComponentEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.core.stats.core import calculate_weighted_mean, calculate_mswd, get_mswd_limits
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.processing.plotter_options_manager import IdeogramOptionsManager, SpectrumOptionsManager
from pychron.processing.plotters.ideogram.ideogram_model import IdeogramModel
from pychron.processing.plotters.spectrum.spectrum_model import SpectrumModel


class AnalysisAdapter(TabularAdapter):
    columns = [('RunID', 'record_id'),
               ('Age', 'age'),
               ('Err', 'age_err'),
               ('Err Wo/J', 'age_err_wo_j'),
               ('Tag', 'tag')]
    font = '10'

    age_text = Property
    age_err_text = Property
    age_err_wo_j_text = Property

    def _get_age_text(self):
        return floatfmt(self.item.age)

    def _get_age_err_text(self):
        return floatfmt(self.item.age_err)

    def _get_age_err_wo_j_text(self):
        return floatfmt(self.item.age_err_wo_j)


class OptionsView(HasTraits):
    model = Any
    title = Str

    def traits_view(self):
        v = View(UItem('model',
                       style='custom',
                       editor=InstanceEditor()),
                 title=self.title,
                 resizable=True,
                 kind='livemodal',
                 buttons=['OK'])

        return v


class ComprehensiveEditorTool(HasTraits):
    ideogram_options_button = Button
    spectrum_options_button = Button
    spectrum_visible = Bool(True)
    ideogram_visible = Bool(True)

    def traits_view(self):
        igrp=VGroup(UItem('ideogram_visible'),
                    icon_button_editor('ideogram_options_button', 'cog', enabled_when='ideogram_visible'),
                    label='Ideogram',show_border=True)

        sgrp=VGroup(
                    UItem('spectrum_visible'),
                    icon_button_editor('spectrum_options_button', 'cog', enabled_when='spectrum_visible'),
                    label='Spectrum',show_border=True)

        v=View(VGroup(igrp,sgrp))
        return v


class ComprehensiveEditor(BaseTraitsEditor):
    analyses = List
    min_age = Float
    max_age = Float
    n = Int
    mean = Float
    weighted_mean = Float
    mswd = Float
    mswd_low = Float
    mswd_high = Float

    ideogram_graph = Any
    ideogram_model = Instance(IdeogramModel)
    ideogram_options = Instance(IdeogramOptionsManager)

    spectrum_graph = Any
    spectrum_model = Instance(SpectrumModel)
    spectrum_options = Instance(SpectrumOptionsManager)

    spectrum_visible=DelegatesTo('tool')
    ideogram_visible=DelegatesTo('tool')
    tool = Instance(ComprehensiveEditorTool, ())

    def _create_ideogram(self):
        self.ideogram_options = IdeogramOptionsManager()
        model = IdeogramModel(analyses=self.analyses,
                              plot_options=self.ideogram_options.plotter_options)
        model.refresh_panels()
        p = model.next_panel()
        self.ideogram_graph = p.make_graph()
        self.ideogram_model = model

    def _create_spectrum(self):
        self.spectrum_options = SpectrumOptionsManager()
        model = SpectrumModel(analyses=self.analyses,
                              plot_options=self.spectrum_options.plotter_options)
        model.refresh_panels()
        p = model.next_panel()
        self.spectrum_graph = p.make_graph()
        self.spectrum_model = model

    def load(self):
        ans = self.analyses
        ages = [ai.age for ai in ans]
        errors = [ai.age_err_wo_j for ai in ans]

        self.min_age = min(ages)
        self.max_age = max(ages)
        self.n = n = len(self.analyses)
        self.mean = sum(ages) / float(n)

        wm, we = calculate_weighted_mean(ages, errors)
        self.weighted_mean = wm

        mswd = calculate_mswd(ages, errors, wm=wm)
        self.mswd = mswd
        self.mswd_low, self.mswd_high = get_mswd_limits(n)

        self._create_ideogram()

        self._create_spectrum()
    
    #handlers
    @on_trait_change('tool:ideogram_options_button')
    def _ideogram_options_button_fired(self):
        v = OptionsView(model=self.ideogram_options,
                        title='Edit Ideogram Options')
        v.edit_traits()

    @on_trait_change('tool:spectrum_options_button')
    def _spectrum_options_button_fired(self):
        v = OptionsView(model=self.spectrum_options,
                        title='Edit Spectrum Options')
        v.edit_traits()

    @on_trait_change('ideogram_options:plotter_options:refresh_plot')
    def _ideogram_update(self):
        model = self.ideogram_model
        model.refresh_panels()
        p = model.next_panel()
        self.ideogram_graph = p.make_graph()

    #views
    def traits_view(self):
        ideogram_grp = VGroup(UItem('ideogram_graph',
                                    visible_when='ideogram_visible',
                                    editor=ComponentEditor()),
                              label='Ideogram')

        spectrum_grp = VGroup(UItem('spectrum_graph',
                                    visible_when='spectrum_visible',
                                    editor=ComponentEditor()),
                              label='Spectrum')

        fmt = '%0.4f'
        age_grp = HGroup(Readonly('min_age', format_str=fmt, label='Min.'),
                         Readonly('max_age', format_str=fmt, label='Max.'),
                         Readonly('mean', format_str=fmt, ),
                         Readonly('weighted_mean', format_str=fmt, label='Wtd. Mean'),
                         label='Age',
                         show_border=True)

        mswd_grp = HGroup(Readonly('mswd', format_str=fmt, label='MSWD'),
                          HGroup(Readonly('mswd_low', format_str=fmt, label='Low'),
                                 Readonly('mswd_high', format_str=fmt, label='High'),
                                 show_border=True, label='Acceptable Range'))

        analyses_grp = UItem('analyses', editor=TabularEditor(adapter=AnalysisAdapter()))

        stats_grp = VGroup(Readonly('n'),
                           analyses_grp,
                           age_grp,
                           mswd_grp,
                           label='Stats')

        vg = Tabbed(stats_grp, ideogram_grp, spectrum_grp)
        v = View(vg)
        return v

# ============= EOF =============================================



