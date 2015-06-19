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
from chaco.abstract_overlay import AbstractOverlay
from chaco.label import Label
from traits.api import Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.plot.editors.interpreted_age_editor import InterpretedAgeEditor
from pychron.processing.analyses.file_analysis import InterpretedAgeAnalysis, FileAnalysis
from pychron.pipeline.plot.models.ideogram_model import IdeogramModel


class Caption(AbstractOverlay):
    label = Instance(Label, ())

    def __init__(self, text, *args, **kw):
        super(Caption, self).__init__(*args, **kw)
        self.label.text = text

    def _draw_component(self, gc, view_bounds=None, mode="normal"):
        print 'casdcasd'

    def _draw_overlay(self, gc, view_bounds=None, mode="normal"):
        print 'asdfasdfasdf'

    def _draw_underlay(self, gc, view_bounds=None, mode="normal"):
        print 'unasdf'

    def draw(self, gc, view_bounds=None, mode="default"):
        print 'dafasfasfd'
        with gc:
            self.label.draw()


class IdeogramEditor(InterpretedAgeEditor):
    # plotter_options_manager = Instance(IdeogramOptionsManager, ())
    figure_model_klass = IdeogramModel
    basename = 'ideo'

    def plot_interpreted_ages(self, iages):
        def construct(a):
            i = InterpretedAgeAnalysis(record_id='{} ({})'.format(a.sample, a.identifier),
                                       sample=a.sample,
                                       age=a.age,
                                       age_err=a.age_err)
            return i

        self.disable_aux_plots()

        ans = [construct(ia) for ia in iages]
        self.analyses = ans
        self._update_analyses()
        self.dump_tool()

    def disable_aux_plots(self):
        po = self.plotter_options_manager.plotter_options
        for ap in po.aux_plots:
            if ap.name.lower() not in ('ideogram', 'analysis number', 'analysis number stacked'):
                ap.use = False
                ap.enabled = False

    # def get_component(self, ans, plotter_options):
    # if plotter_options is None:
    #         pom = IdeogramOptionsManager()
    #         plotter_options = pom.plotter_options
    #
    #     from pychron.processing.plotters.ideogram.ideogram_model import IdeogramModel
    #
    #     model, component = self._make_component(IdeogramModel, ans, plotter_options)
    #     return model, component

    # def get_component(self, ans, plotter_options):
    # # meta = None
    # # if self.figure_model:
    #     #     meta = self.figure_model.dump_metadata()
    #
    #     if plotter_options is None:
    #         pom = IdeogramOptionsManager()
    #         plotter_options = pom.plotter_options
    #
    #     model = self.figure_model
    #     container = self.figure_container
    #     if not model:
    #         from pychron.processing.plotters.ideogram.ideogram_model import IdeogramModel
    #
    #         model = IdeogramModel(plot_options=plotter_options,
    #                               titles=self.titles)
    #
    #         self.figure_model = model
    #
    #     model.trait_set(plot_options=plotter_options,
    #                     titles=self.titles,
    #                     analyses=ans)
    #
    #     if not container:
    #         container = FigureContainer(model=model)
    #         self.figure_container = container
    #
    #     container.refresh()
    #     component = container.component
    #     # print self.figure_container
    #     # print self.figure_model
    #     # po = plotter_options
    #     # m = po.mean_calculation_kind
    #     # s = po.nsigma
    #     # es = po.error_bar_nsigma
    #     # ecm = po.error_calc_method
    #     # captext = u'Mean: {} +/-{}\u03c3 Data: +/-{}\u03c3. ' \
    #     #           u'Error Type:{}. Analyses omitted from calculation \n' \
    #     #           u'indicated by open squares. Dashed line represents ' \
    #     #           u'cumulative probability for all analyses'.format(m, s, es, ecm)
    #     #
    #     # self._add_caption(component, plotter_options, default_captext=captext)
    #
    #     # if meta:
    #     #     model.load_metadata(meta)
    #
    #     return model, component

    def _get_items_from_file(self, parser):
        # ans = []
        def gen():
            for d in parser.itervalues():
                if d['age'] is not None:
                    f = FileAnalysis(age=float(d['age']),
                                     age_err=float(d['age_err']),
                                     record_id=d['runid'],
                                     sample=d.get('sample', ''),
                                     aliquot=int(d.get('aliquot', 0)),
                                     group_id=int(d.get('group', 0)))
                    yield f

        ans = list(gen())
        # ans.append(f)

        # ans = [construct(args)
        #        for args in par.itervalues()]

        po = self.plotter_options_manager.plotter_options
        for ap in po.aux_plots:
            if ap.name.lower() not in ('ideogram', 'analysis number', 'analysis number stacked'):
                ap.use = False
                ap.enabled = False
            else:
                ap.enabled = True
        return ans

# ============= EOF =============================================
