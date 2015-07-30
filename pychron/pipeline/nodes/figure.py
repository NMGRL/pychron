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
from traits.api import Any, Bool, List
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_editor import grouped_name
from pychron.pipeline.nodes.base import BaseNode
# from pychron.processing.plot.editors.ideogram_editor import IdeogramEditor

from pychron.pipeline.options.plotter_options_manager import IdeogramOptionsManager, SpectrumOptionsManager, \
    SeriesOptionsManager


class NoAnalysesError(BaseException):
    pass


class FigureNode(BaseNode):
    editor = Any
    editor_klass = Any
    plotter_options = Any
    plotter_options_manager_klass = Any
    plotter_options_manager = Any
    no_analyses_warning = Bool(False)
    # _configured = Bool(False)
    editors = List
    auto_set_items = True

    def refresh(self):
        if self.editor:
            # self.editor.force_update()
            # print 'editor refres'
            self.editor.refresh_needed = True
            # if self.editor.save_required:
            #     if confirm(None, 'Save Changes') == YES:
            #         self.editor.save_needed = True

    def run(self, state):
        # self._configured = True
        self.plotter_options = self.plotter_options_manager.plotter_options

        # if not self.plotter_options or not self._configured:
        #     if not self.configure(refresh=False):
        #         state.canceled = True
        #         return
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
        # pom = self.plotter_options_manager_klass()
        if self.editor:
            pom.plotter_options = self.editor.plotter_options

        self._configure_hook()
        info = pom.edit_traits(kind='livemodal')
        if info.result:
            self.plotter_options = pom.plotter_options
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

    def configure(self, refresh=True, pre_run=False, **kw):
        # self._configured = True
        if not pre_run:
            self._manual_configured = True

        pom = self.plotter_options_manager
        # pom = self.plotter_options_manager_klass()
        if self.editor:
            pom.plotter_options = self.editor.plotter_options

        info = pom.edit_traits(kind='livemodal')
        if info.result:
            self.plotter_options = pom.plotter_options
            if refresh:
                self.refresh()

            return True
# ============= EOF =============================================
