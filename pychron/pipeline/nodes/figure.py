# ===============================================================================
# Copyright 2015 Jake Ross
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

from apptools.preferences.preference_binding import bind_preference
from traits.api import Any, Bool, Instance, Dict
from traitsui.api import View

from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.helpers.strtools import ratio
from pychron.core.progress import progress_iterator
from pychron.options.options_manager import IdeogramOptionsManager, OptionsController, SeriesOptionsManager, \
    SpectrumOptionsManager, InverseIsochronOptionsManager, VerticalFluxOptionsManager, XYScatterOptionsManager, \
    RadialOptionsManager, RegressionSeriesOptionsManager, FluxVisualizationOptionsManager
from pychron.options.views.views import view
from pychron.pipeline.editors.flux_visualization_editor import FluxVisualizationEditor
from pychron.pipeline.nodes.base import SortableNode
from pychron.pipeline.plot.plotter.series import RADIOGENIC_YIELD, PEAK_CENTER, \
    ANALYSIS_TYPE, AGE, LAB_TEMP, LAB_HUM, EXTRACT_VALUE, EXTRACT_DURATION, CLEANUP
from pychron.pychron_constants import COCKTAIL, UNKNOWN, DETECTOR_IC


class NoAnalysesError(BaseException):
    pass


class FigureNode(SortableNode):
    editor = Any
    editor_klass = Any
    options_view = Instance(View)
    plotter_options = Any
    plotter_options_manager_klass = Any
    plotter_options_manager = Any
    no_analyses_warning = Bool(False)
    # editors = List
    auto_set_items = True
    use_plotting = True
    editors = Dict

    def reset(self):
        super(FigureNode, self).reset()
        self.editors = {}
        self.editor = None

    def refresh(self):
        for e in self.editors.values():
            e.refresh_needed = True

    def run(self, state):
        self.plotter_options = self.plotter_options_manager.selected_options
        po = self.plotter_options
        if not po:
            state.canceled = True
            return

        try:
            use_plotting = po.use_plotting
        except AttributeError:
            use_plotting = True

        if not state.unknowns and self.no_analyses_warning:
            raise NoAnalysesError

        if use_plotting and self.use_plotting:
            for tab_id, unks in groupby_key(state.unknowns, 'tab_id'):
                if tab_id in self.editors:
                    editor = self.editors[tab_id]
                else:
                    editor = self._editor_factory()
                    self.editors[tab_id] = editor

                state.editors.append(editor)
                self.editor = editor
                if self.auto_set_items:
                    bind_preference(self, 'skip_meaning', 'pychron.pipeline.skip_meaning')
                    if self.name in self.skip_meaning.split(','):
                        unks = [u for u in unks if u.tag.lower() != 'skip']

                    editor.set_items(list(unks))
                    print('reefejs meeded run')
                    editor.refresh_needed = True
                    # if hasattr(editor, 'component'):
                    #     editor.component.invalidate_and_redraw()

        for name, es in groupby_key(state.editors, 'name'):
            for i, ei in enumerate(es):
                ei.name = ' '.join(ei.name.split(' ')[:-1])
                ei.name = '{} {:02n}'.format(ei.name, i + 1)

    def configure(self, refresh=True, pre_run=False, **kw):
        if not pre_run:
            self._manual_configured = True

        pom = self.plotter_options_manager
        if self.editor:
            pom.set_selected(self.editor.plotter_options)

        self._configure_hook()
        info = OptionsController(model=pom).edit_traits(view=self.options_view,
                                                        kind='livemodal')
        if info.result:
            self.plotter_options = pom.selected_options
            for e in self.editors.values():
                e.plotter_options = pom.selected_options

            if refresh:
                self.refresh()

            return True

    def _editor_factory(self):
        klass = self.editor_klass
        if isinstance(klass, (str, bytes, bytearray)):
            pkg, klass = klass.split(',')
            mod = __import__(pkg, fromlist=[klass])
            klass = getattr(mod, klass)

        editor = klass()

        editor.plotter_options = self.plotter_options
        return editor

    def _plotter_options_manager_default(self):
        return self.plotter_options_manager_klass()

    def _options_view_default(self):
        return view('{} Options'.format(self.name))


class XYScatterNode(FigureNode):
    name = 'XYScatter'
    editor_klass = 'pychron.pipeline.plot.editors.xyscatter_editor,XYScatterEditor'
    plotter_options_manager_klass = XYScatterOptionsManager

    def _configure_hook(self):
        pom = self.plotter_options_manager
        if self.unknowns:
            unk = self.unknowns[0]
            # names = []
            # iso_keys = unk.isotope_keys
            # names = iso_keys
            pom.set_names(unk.isotope_keys)


class VerticalFluxNode(FigureNode):
    name = 'Vertical Flux'
    editor_klass = 'pychron.pipeline.plot.editors.vertical_flux_editor,VerticalFluxEditor'
    plotter_options_manager_klass = VerticalFluxOptionsManager

    def run(self, state):
        editor = super(VerticalFluxNode, self).run(state)
        editor.irradiation = state.irradiation
        editor.levels = state.levels


class FluxVisualizationNode(FigureNode):
    name = 'Flux Visualization'
    editor_klass = FluxVisualizationEditor
    plotter_options_manager_klass = FluxVisualizationOptionsManager
    no_analyses_warning = False

    def _options_view_default(self):
        return view('Flux Options')

    def run(self, state):
        self.editor = editor = self._editor_factory()
        state.editors.append(editor)
        if not editor:
            state.canceled = True
            return

        self.name = 'Flux Visualization {}'.format(state.irradiation, state.level)
        geom = state.geometry

        ps = state.monitor_positions

        if ps:
            po = self.plotter_options

            editor.plotter_options = po
            editor.geometry = geom
            editor.irradiation = state.irradiation
            editor.level = state.level
            editor.holder = state.holder

            editor.set_positions(ps)
            editor.name = 'Flux Visualization: {}{}'.format(state.irradiation, state.level)


class IdeogramNode(FigureNode):
    name = 'Ideogram'
    editor_klass = 'pychron.pipeline.plot.editors.ideogram_editor,IdeogramEditor'
    plotter_options_manager_klass = IdeogramOptionsManager


class HistoryIdeogramNode(FigureNode):
    name = 'Ideogram'
    editor_klass = 'pychron.pipeline.plot.editors.history_ideogram_editor,HistoryIdeogramEditor'
    plotter_options_manager_klass = IdeogramOptionsManager


class SpectrumNode(FigureNode):
    name = 'Spectrum'

    editor_klass = 'pychron.pipeline.plot.editors.spectrum_editor,SpectrumEditor'
    plotter_options_manager_klass = SpectrumOptionsManager


class SeriesNode(FigureNode):
    name = 'Series'
    editor_klass = 'pychron.pipeline.plot.editors.series_editor,SeriesEditor'
    plotter_options_manager_klass = SeriesOptionsManager

    def _configure_hook(self):
        pom = self.plotter_options_manager
        if self.unknowns:
            unk = self.unknowns[0]
            names = []
            iso_keys = unk.isotope_keys
            if iso_keys:
                names.extend(iso_keys)
                names.extend(['{}bs'.format(ki) for ki in iso_keys])
                names.extend(['{}ic'.format(ki) for ki in iso_keys])

                names.extend(ratio(iso_keys))

                if unk.analysis_type in (UNKNOWN, COCKTAIL):
                    names.append(AGE)
                    names.append(RADIOGENIC_YIELD)

                if unk.analysis_type in (DETECTOR_IC,):
                    isotopes = unk.isotopes
                    for vi in isotopes.values():
                        for vj in isotopes.values():
                            if vi == vj:
                                continue

                            names.append('{}/{} DetIC'.format(vj.detector, vi.detector))

            names.extend([PEAK_CENTER, ANALYSIS_TYPE, LAB_TEMP, LAB_HUM, EXTRACT_VALUE, EXTRACT_DURATION, CLEANUP])

            pom.set_names(names)


class RegressionSeriesNode(SeriesNode):
    name = 'Regression Series'
    editor_klass = 'pychron.pipeline.plot.editors.regression_series_editor,RegressionSeriesEditor'
    plotter_options_manager_klass = RegressionSeriesOptionsManager

    def run(self, state):
        po = self.plotter_options

        keys = [fi.name for fi in list(reversed([pi for pi in po.get_plotable_aux_plots()]))]

        def load_raw(x, prog, i, n):
            x.load_raw_data(keys)

        progress_iterator(state.unknowns, load_raw, threshold=1)
        super(RegressionSeriesNode, self).run(state)

    def _configure_hook(self):
        pom = self.plotter_options_manager
        if self.unknowns:
            unk = self.unknowns[0]
            names = []
            iso_keys = unk.isotope_keys
            if iso_keys:
                names.extend(iso_keys)
                names.extend(['{}bs'.format(ki) for ki in iso_keys])
                names.extend(['{}ic'.format(ki) for ki in iso_keys])

            pom.set_names(names)


class InverseIsochronNode(FigureNode):
    name = 'Inverse Isochron'
    editor_klass = 'pychron.pipeline.plot.editors.isochron_editor,InverseIsochronEditor'
    plotter_options_manager_klass = InverseIsochronOptionsManager


class RadialNode(FigureNode):
    name = 'Radial Plot'
    editor_klass = 'pychron.pipeline.plot.editors.radial_editor,RadialEditor'
    plotter_options_manager_klass = RadialOptionsManager

# ============= EOF =============================================
