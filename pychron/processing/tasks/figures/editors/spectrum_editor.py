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

#============= enthought library imports =======================

from traits.api import Instance

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.analyses.file_analysis import SpectrumFileAnalysis
from pychron.processing.tasks.figures.figure_editor import FigureEditor
from pychron.processing.plotters.figure_container import FigureContainer
from pychron.processing.plotter_options_manager import SpectrumOptionsManager
#from pychron.processing.tasks.figures.editors.auto_controls import AutoSpectrumControl


class SpectrumEditor(FigureEditor):
    plotter_options_manager = Instance(SpectrumOptionsManager, ())
    basename = 'spec'

    def _set_preferred_age_kind(self, ias):
        for ia in ias:
            if ia.plateau_age:
                ia.preferred_age_kind = 'Plateau'
            else:
                ia.preferred_age_kind = 'Integrated'

    def get_component(self, ans, plotter_options):
        if plotter_options is None:
            pom = SpectrumOptionsManager()
            plotter_options = pom.plotter_options

        from pychron.processing.plotters.spectrum.spectrum_model import SpectrumModel

        model = SpectrumModel(plot_options=plotter_options)
        model.analyses = ans
        iv = FigureContainer(model=model)
        component = iv.component

        c = u'Plateau age calculated as weighted mean of plateau steps. ' \
            u'Integrated age calculated as isotopic recombination of all steps.\n' \
            u'Plateau and Integrated Age uncertainties \u00b1{}\u03c3.' \
            u'GMC=Groundmass Concentrate, Kaer=Kaersutite, Plag=Plagioclase'

        self._add_caption(component, plotter_options, default_captext=c)

        return model, component

    def _check_for_necessary_attributes(self, d):
        ms = [k for k in ['age', 'age_err', 'k39']
              if not k in d]
        return ms

    def _get_items_from_file(self, parser):
        ans = []
        for i, d in enumerate(parser.itervalues()):
            missing_keys = self._check_for_necessary_attributes(d)
            if not missing_keys:
                f = SpectrumFileAnalysis(age=float(d['age']),
                                         age_err=float(d['age_err']),
                                         k39_value=float(d['k39']),
                                         record_id=d.get('runid', ''),
                                         sample=d.get('sample', ''))
                ans.append(f)
            else:
                self.warning('Invalid analysis. Number = {}. Missing Keys={}'.format(i, ','.join(missing_keys)))

                # ans = [construct(args)
                #        for args in par.itervalues()]

        po = self.plotter_options_manager.plotter_options
        for ap in po.aux_plots:
            if ap.name.lower() not in ('age',):
                ap.use = False
                ap.enabled = False
            #clear overlay positions
            ap.overlay_positions = {}

        return ans

#class AutoSpectrumEditor(SpectrumEditor):
#    auto_figure_control = Instance(AutoSpectrumControl, ())

# ============= EOF =============================================
