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
from traits.api import Any, Bool, List, Instance
from traitsui.api import View

from pychron.envisage.tasks.base_editor import grouped_name
from pychron.options.options_manager import IdeogramOptionsManager, OptionsController, SeriesOptionsManager, \
    SpectrumOptionsManager, InverseIsochronOptionsManager, VerticalFluxOptionsManager, XYScatterOptionsManager
from pychron.options.views import view
from pychron.pipeline.nodes.base import BaseNode


class NoAnalysesError(BaseException):
    pass


class FigureNode(BaseNode):
    editor = Any
    editor_klass = Any
    options_view = Instance(View)
    plotter_options = Any
    plotter_options_manager_klass = Any
    plotter_options_manager = Any
    no_analyses_warning = Bool(False)
    editors = List
    auto_set_items = True

    def refresh(self):
        if self.editor:
            self.editor.refresh_needed = True

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

        self.unknowns = state.unknowns
        self.references = state.references

        if use_plotting:
            editor = self.editor
            if not editor:
                editor = self._editor_factory()
                self.editor = editor
                state.editors.append(editor)

            # print editor, state.unknowns
            if self.auto_set_items:
                editor.set_items(state.unknowns)

            oname = editor.name

            # self.name = editor.name
        else:
            a = list(set([ni.labnumber for ni in state.unknowns]))
            oname = '{} {}'.format(grouped_name(a), self.name)

        new_name = oname

        cnt = 1
        for e in state.editors:
            if e.name == new_name:
                new_name = '{} {:02n}'.format(oname, cnt)
                cnt += 1

        # self.name = new_name
        if use_plotting:
            self.editor.name = new_name

        return self.editor

    def configure(self, refresh=True, pre_run=False, **kw):
        # self._configured = True
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
            if self.editor:
                self.editor.plotter_options = pom.selected_options

            if refresh:
                self.refresh()

            return True

    def _editor_factory(self):
        klass = self.editor_klass
        if isinstance(klass, (str, unicode)):
            pkg, klass = klass.split(',')
            mod = __import__(pkg, fromlist=[klass])
            klass = getattr(mod, klass)

        editor = klass()

        editor.plotter_options = self.plotter_options
        return editor

    def _plotter_options_manager_default(self):
        return self.plotter_options_manager_klass()

    def _configure_hook(self):
        pass

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
            iso_keys = unk.isotope_keys
            names = iso_keys
            # if iso_keys:
            #     names.extend(iso_keys)
            #     names.extend(['{}bs'.format(ki) for ki in iso_keys])
            #     names.extend(['{}ic'.format(ki) for ki in iso_keys])
            #     if 'Ar40' in iso_keys:
            #         if 'Ar39' in iso_keys:
            #             names.append('Ar40/Ar39')
            #             names.append('uAr40/Ar39')
            #         if 'Ar36' in iso_keys:
            #             names.append('Ar40/Ar36')
            #             names.append('uAr40/Ar36')
            #
            # names.append('Peak Center')
            # names.append('AnalysisType')
        pom.set_names(names)


class VerticalFluxNode(FigureNode):
    name = 'Vertical Flux'
    editor_klass = 'pychron.pipeline.plot.editors.vertical_flux_editor,VerticalFluxEditor'
    plotter_options_manager_klass = VerticalFluxOptionsManager

    def run(self, state):
        editor = super(VerticalFluxNode, self).run(state)
        editor.irradiation = state.irradiation
        editor.levels = state.levels


class IdeogramNode(FigureNode):
    name = 'Ideogram'
    editor_klass = 'pychron.pipeline.plot.editors.ideogram_editor,IdeogramEditor'
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
                if 'Ar40' in iso_keys:
                    if 'Ar39' in iso_keys:
                        names.append('Ar40/Ar39')
                        names.append('uAr40/Ar39')
                    if 'Ar36' in iso_keys:
                        names.append('Ar40/Ar36')
                        names.append('uAr40/Ar36')
                    if 'Ar38' in iso_keys:
                        names.append('Ar40/Ar38')
                        names.append('uAr40/Ar38')

            if unk.analysis_type in ('unknown', 'cocktail'):
                names.append('Age')
                names.append('RadiogenicYield')

            names.append('Peak Center')
            names.append('AnalysisType')
            pom.set_names(names)


class InverseIsochronNode(FigureNode):
    name = 'Inverse Isochron'
    editor_klass = 'pychron.pipeline.plot.editors.isochron_editor,InverseIsochronEditor'
    plotter_options_manager_klass = InverseIsochronOptionsManager

# ============= EOF =============================================
