#===============================================================================
# Copyright 2014 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg \
    as FigureCanvas

# noinspection PyUnresolvedReferences
from mpl_toolkits.mplot3d import Axes3D


class MPLFigureCanvas(FigureCanvas):
    pass


class _MPLFigureEditor(Editor):
    def init(self, parent):
        self.control = self._create_control(parent)

    def update_editor(self):
        pass

    def _create_control(self, parent):
        figure = self.value
        f = MPLFigureCanvas(figure)
        return f


class MPLFigureEditor(BasicEditorFactory):
    klass = _MPLFigureEditor

#============= EOF =============================================

