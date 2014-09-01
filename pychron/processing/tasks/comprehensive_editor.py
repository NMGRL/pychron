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
from enable.component_editor import ComponentEditor
from traits.api import HasTraits, List, Int, Float, Any, Instance, on_trait_change, \
    Str, Button
from traitsui.api import View, VGroup, Readonly, HGroup, UItem, VFold, spring, \
    InstanceEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.stats.core import calculate_weighted_mean, calculate_mswd, get_mswd_limits
from pychron.envisage.tasks.base_editor import BaseTraitsEditor


# class ATabularAdapter(TabularAdapter):
# columns=[()]
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.processing.plotter_options_manager import IdeogramOptionsManager
from pychron.processing.plotters.ideogram.ideogram_model import IdeogramModel


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
    ideogram_options_button = Button

    spectrum_graph = Any
    spectrum_defined = False

    def _ideogram_options_button_fired(self):
        v = OptionsView(model=self.ideogram_options,
                        title='Edit Ideogram Options')
        v.edit_traits()


    @on_trait_change('ideogram_options:plotter_options:refresh_plot')
    def _ideogram_update(self):
        # model = IdeogramModel(analyses=self.analyses,
        # plot_options=self.ideogram_options.plotter_options)
        model = self.ideogram_model
        model.refresh_panels()
        p = model.next_panel()
        self.ideogram_graph = p.make_graph()

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

        self.ideogram_options = IdeogramOptionsManager()

        model = IdeogramModel(analyses=self.analyses,
                              plot_options=self.ideogram_options.plotter_options)
        model.refresh_panels()
        p = model.next_panel()

        self.ideogram_graph = p.make_graph()
        self.ideogram_model = model

    def traits_view(self):
        mswd_grp = HGroup(Readonly('mswd', label='MSWD'),
                          HGroup(Readonly('mswd_low', label='Low'),
                                 Readonly('mswd_high', label='High'),
                                 show_border=True, label='Acceptable Range'))

        ideogram_grp = VGroup(HGroup(spring,
                                     icon_button_editor('ideogram_options_button',
                                                        'cog')),
                              UItem('ideogram_graph',
                                    editor=ComponentEditor()),
                              label='Ideogram')

        stats_grp = VGroup(Readonly('min_age'),
                           Readonly('max_age'),
                           Readonly('n'),
                           Readonly('mean'),
                           Readonly('weighted_mean'),
                           mswd_grp,
                           label='Stats')

        if self.spectrum_defined:
            spectrum_grp = VGroup(UItem('spectrum_graph',
                                        editor=ComponentEditor()),
                                  label='Spectrum')
            vf = VFold(stats_grp, ideogram_grp, spectrum_grp)
        else:
            vf = VFold(ideogram_grp, stats_grp)

        v = View(vf)
        return v

# ============= EOF =============================================



