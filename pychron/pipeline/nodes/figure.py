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
from pychron.processing.tasks.figures.editors.ideogram_editor import IdeogramEditor
from pychron.processing.tasks.figures.editors.spectrum_editor import SpectrumEditor


class FigureNode(BaseNode):
    editor = Any

    def run(self, state):
        editor = self.editor_klass()
        editor.analyses = state.unknowns
        editor.set_name()
        editor.rebuild()
        self.editor = editor
        state.editors.append(editor)

    def configure(self):
        if self.editor:
            pom = self.editor.plotter_options_manager
            info = pom.edit_traits(kind='livemodal')
            if info.result:
                return True


class IdeogramNode(FigureNode):
    name = 'Ideogram'
    editor_klass = IdeogramEditor


class SpectrumNode(FigureNode):
    name = 'Spectrum'
    editor_klass = SpectrumEditor


# ============= EOF =============================================



