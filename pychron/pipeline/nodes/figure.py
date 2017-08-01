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
from itertools import groupby

from traits.api import Any, Bool, Instance
from traitsui.api import View

from pychron.options.options_manager import IdeogramOptionsManager, OptionsController, SeriesOptionsManager, \
    SpectrumOptionsManager, InverseIsochronOptionsManager, VerticalFluxOptionsManager, XYScatterOptionsManager, \
    RadialOptionsManager
from pychron.options.views.views import view
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.plot.plotter.series import RADIOGENIC_YIELD, PEAK_CENTER, \
    ANALYSIS_TYPE, AGE, AR4036, UAR4036, AR4038, UAR4038, AR4039, UAR4039, LAB_TEMP, LAB_HUM
from pychron.pychron_constants import COCKTAIL, UNKNOWN, AR40, AR39, AR36, AR38, DETECTOR_IC, AR37


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
    # editors = List
    auto_set_items = True
    use_plotting = True

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

        # oname = ''
        if use_plotting and self.use_plotting:
            editor = self.editor
            # editors = self.editors
            if not editor:
                # key = lambda x: x.graph_id
                #
                # for _, ans in groupby(sorted(state.unknowns, key=key), key=key):
                editor = self._editor_factory()
                state.editors.append(editor)
                self.editor = editor

            if self.auto_set_items:
                editor.set_items(state.unknowns)
                # self.editors.append(editor)
                    # oname = editor.name

            key = lambda x: x.name
            for name, es in groupby(sorted(state.editors, key=key), key=key):
                for i, ei in enumerate(es):
                    ei.name = '{} {:02n}'.format(ei.name, i + 1)
                    # else:
                    #     a = list(set([ni.labnumber for ni in state.unknowns]))
                    #     oname = '{} {}'.format(grouped_name(a), self.name)
                    #
                    #     new_name = oname
                    #     cnt = 1
                    #     for e in state.editors:
                    #         print 'a={}, b={}'.format(e.name, new_name)
                    #         if e.name == new_name:
                    #             new_name = '{} {:02n}'.format(oname, cnt)
                    #             cnt += 1
                    #     self.

                    # if self.editors:
                    #     self.editor = self.editors[0]

                    # cnt = 1
                    # for e in state.editors:
                    #     print 'a={}, b={}'.format(e.name, new_name)
                    #     if e.name == new_name:
                    #         new_name = '{} {:02n}'.format(oname, cnt)
                    #         cnt += 1

        # self.name = new_name
                    # if self.editor:
                    #     self.editor.name = new_name

                    # return self.editors

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
                if AR40 in iso_keys:
                    if AR39 in iso_keys:
                        names.extend([AR4039, UAR4039])
                    if AR36 in iso_keys:
                        names.extend([AR4036, UAR4036])
                    if AR38 in iso_keys:
                        names.extend([AR4038, UAR4038])

                if AR37 in iso_keys:
                    if AR39 in iso_keys:
                        names.extend([AR3739])


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

            names.extend([PEAK_CENTER, ANALYSIS_TYPE, LAB_TEMP, LAB_HUM])
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
