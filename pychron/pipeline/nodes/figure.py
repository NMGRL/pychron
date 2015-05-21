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
from traits.api import Any
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.nodes.base import BaseNode
# from pychron.processing.plot.editors.ideogram_editor import IdeogramEditor

from pychron.processing.plotter_options_manager import IdeogramOptionsManager, SpectrumOptionsManager, \
    SeriesOptionsManager


class FigureNode(BaseNode):
    editor = Any
    plotter_options = Any
    plotter_options_manager_klass = Any

    def refresh(self):
        if self.editor:
            # self.editor.force_update()
            self.editor.refresh_needed = True

    def run(self, state):
        pkg, klass = self.editor_klass.split(',')
        mod = __import__(pkg, fromlist=[klass])
        editor = getattr(mod, klass)()

        # editor = self.editor_klass()
        if not self.plotter_options:
            pom = self.plotter_options_manager_klass()
            self.plotter_options = pom.plotter_options

        editor.plotter_options = self.plotter_options

        self.editor = editor

        editor.set_items(state.unknowns)

        cnt = 1
        oname = editor.name
        for e in state.editors:
            if e.name == editor.name:
                editor.name = '{} {:02n}'.format(oname, cnt)
                cnt += 1

        self.name = editor.name
        state.editors.append(editor)

    def configure(self):
        pom = self.plotter_options_manager_klass()
        if self.editor:
            pom.plotter_options = self.editor.plotter_options

        info = pom.edit_traits(kind='livemodal')
        if info.result:
            self.plotter_options = pom.plotter_options
            return True

            # pom = self.editor.plotter_options_manager

            # info = pom.edit_traits(kind='livemodal')
            # if info.result:
            # return True


class IdeogramNode(FigureNode):
    name = 'Ideogram'
    editor_klass = 'pychron.processing.plot.editors.ideogram_editor,IdeogramEditor'
    plotter_options_manager_klass = IdeogramOptionsManager


class SpectrumNode(FigureNode):
    name = 'Spectrum'

    editor_klass = 'pychron.processing.plot.editors.spectrum_editor,SpectrumEditor'
    plotter_options_manager_klass = SpectrumOptionsManager


class SeriesNode(FigureNode):
    name = 'Series'
    editor_klass = 'pychron.processing.plot.editors.series_editor,SeriesEditor'
    plotter_options_manager_klass = SeriesOptionsManager

# ============= EOF =============================================



