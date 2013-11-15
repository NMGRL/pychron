#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Any, on_trait_change
# from traits.etsconfig.etsconfig import ETSConfig
from traits.api import Instance
from traitsui.api import View, Item
from enable.window import Window
# from enable.component_editor import _ComponentEditor
from pyface.tasks.editor import Editor
from pychron.graph.graph import Graph
from pychron.processing.plotter_options_manager import IdeogramOptionsManager, \
    PlotterOptionsManager
#============= standard library imports ========================
#============= local library imports  ==========================
# if ETSConfig.toolkit == 'wx':
#    from traitsui.wx.editor import Editor
# elif ETSConfig.toolkit == 'qt4':
#    from traitsui.qt4.editor import Editor
# else:
#    Editor = object

class ProcessingEditor(Editor):
    component = Any
    processor = Any
    options_manager = Instance(PlotterOptionsManager)

    _window = Any
    name = 'Untitled'
#    editor_area = Any
#    tooltip = None
    def create(self, widget):
#        g = Graph()
#        g.new_plot()
#        g.new_series(
#                   x=[1, 3, 4, 5, 10],
#                   y=[1, 34, 1235, 112, 312]
#                   )
#        self.graph = g
        self._window = Window(widget,
# #                              size=self.factory.size,
#                               component=self.value
                                component=self.component
                              )
        self.control = self._window.control
#    def rebuild(self):
#        self.processor.new_ideogram()

    def _component_changed(self):
        if self._window:
            self._window.component = self.component

#    @on_trait_change('processor:component')
#    def _component_update(self):
#        print 'procss upda'
#        if self._window:
#            self._window.component = self.processor.component




#        k = self.klass(widget)
#        print k.control
#============= EOF =============================================
